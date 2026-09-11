"""E2 — Hot-path latency against primitives of the same complexity class.

Question: what does the operator actually cost, relative to the cheapest thing
that could stand in for it?

Section 3.1 of the manuscript already splits the operator's own cost into
frame construction and per-stimulus work (13.68 us stateless, 6.87 prepare,
6.34 evaluate). What it does not say is whether 6.34 us is fast. A number is
only fast against something, so this experiment puts the prepared hot path
between a floor and a ceiling:

  floor    a random projection to 2D -- one (2, d) matrix-vector product, the
           least work any method can do and still produce a planar coordinate.
  ceiling  a sliding-window PCA -- a local SVD, which is what you reach for if
           you want a *locally adaptive* frame instead of an anchored one.

Arms
----
1. random_projection    (2, d) @ v. The O(d) speed floor.
2. multi_anchor_cosine  K = 3 dot products against fixed anchors, O(K*d).
                        What the operator would be without anchor isolation:
                        no orthogonal complement, no contrast axis, just
                        similarity to several reference points at once.
3. polar_evaluate       evaluate() against an invariant prepared frame.
                        The normalization reference -- every relative cost in
                        this experiment is quoted against this arm.
4. polar_project        project(), rebuilding the frame on every call.
5. sliding_window_pca   SVD over the trailing W = 32 vectors, then project
                        onto the top 2 right singular vectors.

Fairness notes, all of which cut against the operator
-----------------------------------------------------
Every arm returns two numbers per stimulus, so the arms are commensurable at
the output. But the polar arms return a Python tuple of boxed floats, while
the primitive arms return a numpy array -- the polar arms pay for boxing that
the baselines do not. Arm 2 is also given its anchors pre-normalized, so it is
charged for K dot products and nothing else. Both choices flatter the
baselines, which is the direction an author's thumb should press.

Arm 5's complexity is O(W^2 * d), not O(W * d^2): LAPACK's driver on a (32,
384) matrix costs quadratically in the *short* dimension. The suite's original
design named the latter; the former is what is measured.

Two corpora, because working set decides the regime
---------------------------------------------------
The frozen Spinoza corpus is 2,221 x 384 x 8 B = 6.8 MB, which largely fits in
this host's shared L2. The synthetic corpus is 25,000 x 384 x 8 B = 76.8 MB,
which does not, and is the one section 3.1's published figures were measured
on. Running both is the only way to report a Spinoza number without silently
changing the regime a reader compares it to. The synthetic arm set also uses
the same anchor and pole seeds as tools/decompose_polar_latency.py, so
`polar_project` here and the published 13.68 us there measure the same thing.

Deterministic, offline, CPU-only, numpy only.

Usage:
    python bench/latency.py
    python bench/latency.py --corpus spinoza --reps 5
    python bench/latency.py --smoke          # execution check, not a measurement
"""

import argparse
from collections.abc import Callable
from pathlib import Path
from typing import Any

import numpy as np
from _harness import (
    RESULTS_DIR,
    SEED,
    dipole_poles,
    interleave,
    load_corpus,
    print_header,
    print_table,
    working_set_mb,
    write_result,
)

from polar_projector import PolarProjector
from polar_projector.fixtures import random_unit_vector

D = 384
N_SYNTHETIC = 25_000
WINDOW = 32
K_ANCHORS = 3
REPS = 3
WARMUP = 1_000

# Same seeds as tools/decompose_polar_latency.py, so the synthetic arms are
# directly comparable to the figures already published in section 3.1.
SEED_ANCHOR, SEED_POLE_A, SEED_POLE_B, SEED_BASE = 1, 2, 3, 1000

REFERENCE_ARM = "polar_evaluate"

# Dimension sweep (section 3.1.2). Exploratory: added after E2's headline run,
# to answer a question that run raised rather than one it was designed to ask.
SWEEP_DIMS = (16, 64, 256, 384, 1024, 4096, 8192)
N_SWEEP = 1_000


def synthetic_corpus(n: int, d: int) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Random unit vectors and a frame, reproducing the section 3.1 setup."""
    vectors = np.asarray([random_unit_vector(d, SEED_BASE + i) for i in range(n)])
    return (
        np.ascontiguousarray(vectors),
        random_unit_vector(d, SEED_ANCHOR),
        random_unit_vector(d, SEED_POLE_A),
        random_unit_vector(d, SEED_POLE_B),
    )


def spinoza_corpus() -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """The frozen corpus, with a frame built from its own semantic structure."""
    vectors, parts = load_corpus()
    c_A, c_B = dipole_poles(vectors, parts)
    return np.ascontiguousarray(vectors), vectors.mean(axis=0), c_A, c_B


def build_arms(
    vectors: np.ndarray,
    c_1: np.ndarray,
    c_A: np.ndarray,
    c_B: np.ndarray,
    projector: PolarProjector,
) -> dict[str, Callable[[int], Any]]:
    """One callable per arm, each mapping a stimulus index to two numbers."""
    d = vectors.shape[1]
    rng = np.random.default_rng(SEED)
    frame = projector.prepare(c_1, c_A, c_B)

    # Arm 1: the O(d) floor. Scaled so the projection is variance-preserving,
    # which costs nothing at call time but makes the output a real embedding.
    rp = np.ascontiguousarray(rng.standard_normal((2, d)) / np.sqrt(d))

    # Arm 2: K fixed anchors, pre-normalized so only the dot products are timed.
    anchors = rng.standard_normal((K_ANCHORS, d))
    anchors /= np.linalg.norm(anchors, axis=1, keepdims=True)
    anchors = np.ascontiguousarray(anchors)

    # Arm 5: a wrapped copy, so every call gets exactly W contiguous trailing
    # rows with no per-call index arithmetic or allocation to charge the arm for.
    padded = np.ascontiguousarray(np.vstack([vectors[-WINDOW:], vectors]))

    def random_projection(i: int) -> Any:
        return rp @ vectors[i]

    def multi_anchor_cosine(i: int) -> Any:
        return anchors @ vectors[i]

    def polar_evaluate(i: int) -> Any:
        return projector.evaluate(vectors[i], frame, i)

    def polar_project(i: int) -> Any:
        return projector.project(vectors[i], c_1, c_A, c_B, i)

    def sliding_window_pca(i: int) -> Any:
        window = padded[i : i + WINDOW]
        centered = window - window.mean(axis=0)
        basis = np.linalg.svd(centered, full_matrices=False)[2][:2]
        return basis @ vectors[i]

    return {
        "random_projection": random_projection,
        "multi_anchor_cosine": multi_anchor_cosine,
        "polar_evaluate": polar_evaluate,
        "polar_project": polar_project,
        "sliding_window_pca": sliding_window_pca,
    }


def run_corpus(name: str, n_calls: int, reps: int, warmup: int) -> dict[str, Any]:
    """Measure every arm over one corpus and report costs relative to evaluate()."""
    if name == "spinoza":
        vectors, c_1, c_A, c_B = spinoza_corpus()
    else:
        vectors, c_1, c_A, c_B = synthetic_corpus(n_calls or N_SYNTHETIC, D)

    n_calls = min(n_calls, vectors.shape[0]) if n_calls else vectors.shape[0]
    projector = PolarProjector()
    arms = build_arms(vectors, c_1, c_A, c_B, projector)

    mb = working_set_mb(*vectors.shape)
    print(f"[{name}] N={vectors.shape[0]} d={vectors.shape[1]} "
          f"working set {mb:.1f} MB | {n_calls} calls x {reps} reps")

    stats = interleave(arms, n_calls, reps=reps, warmup=warmup)

    reference = stats[REFERENCE_ARM]["mean"]
    for arm in stats:
        stats[arm]["relative_cost"] = stats[arm]["mean"] / reference

    print_table(
        ["arm", "mean us", "p50", "p95", "p99", "rel. cost", "spread"],
        [
            [
                arm,
                f"{s['mean']:.2f}",
                f"{s['p50']:.2f}",
                f"{s['p95']:.2f}",
                f"{s['p99']:.2f}",
                f"{s['relative_cost']:.2f}x",
                f"{s['spread'] * 100:.1f}%",
            ]
            for arm, s in stats.items()
        ],
        [22, 10, 9, 9, 9, 11, 9],
    )
    print(f"relative cost is against {REFERENCE_ARM}; spread is peak-to-peak "
          f"across {reps} reps\n")

    return {"n_calls": n_calls, "n_corpus": int(vectors.shape[0]),
            "d": int(vectors.shape[1]), "working_set_mb": mb, "arms": stats}


def dimension_sweep(reps: int, warmup: int) -> dict[str, Any]:
    """Cost of the prepared hot path as d grows, against the O(d) floor.

    Section 3.1.1 measures at a single dimension and finds the result dominated
    by NumPy per-call dispatch rather than arithmetic. That makes the headline
    table silent about Proposition 1, whose claim is asymptotic. This sweep
    locates the crossover: the dimension at which issuing the operations stops
    costing more than performing them.

    Exploratory, and labelled as such. It was specified after E2's registered
    run, in response to what that run showed.
    """
    rng = np.random.default_rng(SEED)
    out: dict[str, Any] = {}

    print("[sweep] cost vs dimension — where dispatch stops dominating\n")
    rows = []
    for d in SWEEP_DIMS:
        vectors = np.ascontiguousarray(rng.standard_normal((N_SWEEP, d)))
        vectors /= np.linalg.norm(vectors, axis=1, keepdims=True)
        c_1, c_A, c_B = (np.ascontiguousarray(rng.standard_normal(d)) for _ in range(3))

        projector = PolarProjector()
        frame = projector.prepare(c_1, c_A, c_B)
        rp = np.ascontiguousarray(rng.standard_normal((2, d)) / np.sqrt(d))

        arms: dict[str, Callable[[int], Any]] = {
            "polar_evaluate": lambda i, f=frame, v=vectors, p=projector: p.evaluate(v[i], f, i),
            "random_projection": lambda i, m=rp, v=vectors: m @ v[i],
        }
        stats = interleave(arms, N_SWEEP, reps=reps, warmup=warmup)

        ev = stats["polar_evaluate"]["mean"]
        fl = stats["random_projection"]["mean"]
        out[str(d)] = {"polar_evaluate": ev, "random_projection": fl, "ratio": ev / fl}
        base = out[str(SWEEP_DIMS[0])]["polar_evaluate"]
        rows.append([str(d), f"{ev:.2f}", f"{fl:.2f}", f"{ev / fl:.2f}x", f"{ev / base:.2f}x"])

    print_table(
        ["d", "evaluate us", "floor us", "evaluate/floor", "vs d=16"],
        rows,
        [10, 14, 12, 17, 11],
    )
    print("if cost were dispatch-bound, 'evaluate us' is flat in d; if arithmetic-bound, linear\n")
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=RESULTS_DIR / "latency.json")
    parser.add_argument("--corpus", choices=("spinoza", "synthetic", "both"), default="both")
    parser.add_argument("--reps", type=int, default=REPS)
    parser.add_argument("--warmup", type=int, default=WARMUP)
    parser.add_argument("--smoke", action="store_true",
                        help="tiny run to prove the script executes; not a measurement")
    parser.add_argument("--sweep", action="store_true",
                        help="also measure cost vs dimension (section 3.1.2, exploratory)")
    args = parser.parse_args()

    reps, warmup = (1, 50) if args.smoke else (args.reps, args.warmup)
    n_calls = 200 if args.smoke else 0

    print_header("E2 latency", f"hot path vs O(d) primitives, d={D}, float64")

    corpora = ["spinoza", "synthetic"] if args.corpus == "both" else [args.corpus]
    results: dict[str, Any] = {c: run_corpus(c, n_calls, reps, warmup) for c in corpora}
    if args.sweep:
        results["dimension_sweep"] = dimension_sweep(reps, warmup)

    if args.smoke:
        print("SMOKE RUN — parameters are not the published protocol; no result written")
        return 0

    write_result(
        args.out,
        experiment="E2",
        config={"seed": SEED, "d": D, "window": WINDOW, "k_anchors": K_ANCHORS,
                "reps": reps, "warmup": warmup, "reference_arm": REFERENCE_ARM},
        results=results,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
