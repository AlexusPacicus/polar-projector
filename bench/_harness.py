"""Shared measurement harness for the E1-E4 benchmark suite.

Every experiment in bench/ reports through this module so that a reader
comparing two of them is comparing measurements, not measurement styles. It
owns four things: the frozen corpus loader, the timing protocol, the host and
environment disclosure, and the on-disk result format.

Timing protocol
---------------
Latency is sampled per call, not amortized over a bulk loop. At the operation
sizes this suite measures (single-digit microseconds) a bulk figure hides the
tail, and the tail is where a hot-path operator is actually judged. The cost is
one perf_counter_ns pair per sample, which is ~50-100 ns against operations of
~6 us -- under 2%, and identical across arms, so it cancels in every ratio this
suite reports.

Three controls, each for a specific noise source:

  warmup      Discarded iterations, to fault in pages and load L1/L2 before the
              first recorded sample.
  reps        Independent repetitions, aggregated by median-of-medians. The
              spread across reps is reported rather than hidden, and is the
              honest error bar on every figure downstream.
  interleave  Arms run round-robin across reps instead of one arm to
              completion. The published host is a passively cooled M1 (see the
              manuscript, section 3), so sustained runs throttle; running arm A
              fully and then arm B charges B for a hotter machine. Round-robin
              spreads any thermal ramp evenly across all arms, which is what
              makes the *ratios* between arms trustworthy even when the
              absolute microseconds drift.

On CPU affinity
---------------
An earlier draft of this suite specified sched_setaffinity for process
isolation. That call is Linux-only and does not exist on the published host
(macOS/arm64), so it is not used here. Interleaving is the substitute: it
targets thermal drift, which is the dominant noise source on this machine,
rather than core migration, which is not.

On BLAS threading
-----------------
Thread pinning is recorded, not asserted. Measured on the published host,
pinning VECLIB_MAXIMUM_THREADS/OMP_NUM_THREADS to 1 changes dgemv at
d = 384, B in {64, 1024, 4096, 16384} by under 2% -- Accelerate does not
multithread a matrix-vector product at these shapes, which are
memory-bandwidth bound. Rather than re-exec the interpreter to enforce a
setting that provably does nothing here, thread_env() records the relevant
variables into every result file. A reader reproducing on a host where the
setting *does* matter can set it and compare against the recorded block.

numpy only -- no substrate dependency, and nothing from the [bench] extra.
"""

import gc
import json
import os
import platform
import sys
import time
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

import numpy as np

BENCH_DIR = Path(__file__).resolve().parent
DATA_DIR = BENCH_DIR / "data"
RESULTS_DIR = BENCH_DIR / "results"

SEED = 42
EPS = float(np.finfo(np.float64).eps)

#: Environment variables that change BLAS threading, recorded with every result.
THREAD_VARS = (
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
    "NUMEXPR_NUM_THREADS",
)


# --- corpus -----------------------------------------------------------------


def load_corpus() -> tuple[np.ndarray, list[str]]:
    """Frozen Spinoza embeddings in reading order, with their part labels.

    Digests and encoder revision for this artifact live in data/PROVENANCE.json.
    """
    vectors = np.load(DATA_DIR / "embeddings.npy").astype(np.float64)
    labels = json.loads((DATA_DIR / "labels.json").read_text(encoding="utf-8"))
    if len(labels) != vectors.shape[0]:
        raise SystemExit(
            f"ERR: {vectors.shape[0]} vectors but {len(labels)} labels — "
            "the frozen artifact is inconsistent; re-run the freezer."
        )
    return vectors, [entry["part"] for entry in labels]


def working_set_mb(n: int, d: int, itemsize: int = 8) -> float:
    """Bytes a corpus occupies, in MB. Disclosed because it decides the regime.

    A corpus that fits in cache and one that does not are different
    measurements of the same operator, and microsecond figures from the two are
    not comparable.
    """
    return n * d * itemsize / 1e6


# --- timing -----------------------------------------------------------------


def measure(fn: Callable[[int], Any], n_calls: int, *, warmup: int = 1000) -> np.ndarray:
    """Per-call latency of fn(i) for i in range(n_calls), in microseconds.

    fn must be self-contained: whatever it returns is discarded, and the caller
    is responsible for making sure it is not optimized away (all current arms
    return a value into a local, which numpy cannot elide).
    """
    for i in range(warmup):
        fn(i % n_calls)

    out = np.empty(n_calls, dtype=np.float64)
    gc_was_enabled = gc.isenabled()
    gc.disable()
    try:
        for i in range(n_calls):
            t0 = time.perf_counter_ns()
            fn(i)
            out[i] = time.perf_counter_ns() - t0
    finally:
        if gc_was_enabled:
            gc.enable()
    return out / 1000.0


def summarize(latencies_us: np.ndarray) -> dict[str, float]:
    """Central tendency and tail of one repetition."""
    return {
        "mean": float(np.mean(latencies_us)),
        "p50": float(np.percentile(latencies_us, 50)),
        "p95": float(np.percentile(latencies_us, 95)),
        "p99": float(np.percentile(latencies_us, 99)),
        "min": float(np.min(latencies_us)),
    }


def aggregate(reps: Sequence[dict[str, float]]) -> dict[str, float]:
    """Median across repetitions, plus the spread that median is hiding.

    Median rather than mean: a repetition interrupted by the OS is an outlier
    in one direction only, and averaging lets it move the headline figure.
    `spread` is the full peak-to-peak range of the per-rep means, relative to
    the median -- the error bar to quote alongside any figure from this suite.
    """
    stats = {key: float(np.median([r[key] for r in reps])) for key in reps[0]}
    means = [r["mean"] for r in reps]
    stats["spread"] = (max(means) - min(means)) / stats["mean"] if stats["mean"] > 0.0 else 0.0
    stats["reps"] = float(len(reps))
    return stats


def interleave(
    arms: dict[str, Callable[[int], Any]],
    n_calls: int,
    *,
    reps: int = 3,
    warmup: int = 1000,
    progress: bool = True,
) -> dict[str, dict[str, float]]:
    """Run every arm once per repetition, round-robin, and aggregate.

    Arm order is rotated each repetition so that no arm is permanently first
    (and therefore permanently measured on the coolest machine).
    """
    names = list(arms)
    per_arm: dict[str, list[dict[str, float]]] = {name: [] for name in names}

    for rep in range(reps):
        order = names[rep % len(names) :] + names[: rep % len(names)]
        for name in order:
            if progress:
                print(f"  rep {rep + 1}/{reps}: {name:<24}", end="\r", flush=True)
            per_arm[name].append(summarize(measure(arms[name], n_calls, warmup=warmup)))

    if progress:
        print(" " * 60, end="\r")
    return {name: aggregate(per_arm[name]) for name in names}


# --- disclosure and output --------------------------------------------------


def host_block() -> dict[str, str]:
    """The machine a figure was measured on. Absolute microseconds belong to it."""
    return {
        "platform": platform.platform(),
        "processor": platform.processor(),
        "python": sys.version.split()[0],
        "numpy": np.__version__,
    }


def thread_env() -> dict[str, str]:
    """BLAS threading variables as they actually were during the run."""
    return {var: os.environ.get(var, "unset") for var in THREAD_VARS}


def write_result(path: Path, *, experiment: str, config: dict[str, Any], results: dict[str, Any]) -> None:
    """Serialize one experiment in the suite's common shape.

    Same {config, host, results} envelope drift.py established, plus the
    experiment tag and the thread environment.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "experiment": experiment,
        "config": config,
        "host": host_block(),
        "thread_env": thread_env(),
        "results": results,
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"\nwrote {path}")


def print_header(experiment: str, subtitle: str) -> None:
    print(f"{experiment} — {subtitle}")
    host = host_block()
    print(f"host: {host['platform']} | python {host['python']} | numpy {host['numpy']}")
    pinned = {k: v for k, v in thread_env().items() if v != "unset"}
    print(f"blas threads: {pinned or 'unset (default)'}\n")


def print_table(headers: Sequence[str], rows: Sequence[Sequence[str]], widths: Sequence[int]) -> None:
    """Fixed-width table to stdout, matching the style drift.py established."""
    line = "".join(f"{h:>{w}}" if i else f"{h:<{w}}" for i, (h, w) in enumerate(zip(headers, widths, strict=True)))
    print(line)
    print("-" * len(line))
    for row in rows:
        print(
            "".join(
                f"{c:>{w}}" if i else f"{c:<{w}}"
                for i, (c, w) in enumerate(zip(row, widths, strict=True))
            )
        )
    print("-" * len(line))
