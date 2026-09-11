"""E4 — Batched subspace evaluation.

Question: what does batching the projection actually buy, and is the answer the
one section 4.2 assumes?

Section 4.2 proposes evaluating B stimuli against one frame as
V P⊥ = V - (V ĉ₁) ĉ₁ᵀ, and separately proposes returning the squared residual
energy E_esc to skip a square root in hot loops. Both are claims about cost.
Neither had been measured.

Arms
----
1. scalar_loop      a Python loop over evaluate(), the thing being replaced.
2. evaluate_batch   the shipped batched path.

Both are run at every batch size, so the speedup is a ratio of two measurements
taken under the same protocol on the same machine minutes apart, not a
comparison against a published figure.

What is measured
----------------
Throughput, as microseconds per vector and vectors per second, across
B in {1, 4, 16, 64, 256, 1024, 4096}. A batch of 1 is included because it is
where batching can only lose: it pays the setup and gets no amortization.

Agreement against the scalar loop, reported as the deviation actually observed
and normalized by machine epsilon, not as a pass/fail against a tolerance. The
batched path is not bitwise identical to the loop -- BLAS reorders the
reduction once B >= 2 -- so quoting "parity" would be wrong. What is quoted is
|dlambda|/eps and |d_esc|/(eps*||r||), which is the shape the error actually
has.

The square-root claim, separately: einsum with and without the trailing
np.sqrt, at each batch size. Section 4.2 argues that skipping the root is worth
something. This measures whether it is.

Row-order sensitivity, because it is a property of this implementation a user
could be bitten by: the same rows evaluated in a permuted batch, then
un-permuted, compared against the unpermuted result.

Deterministic, offline, numpy only. BLAS thread settings are recorded in the
result file; on the publishing host they were measured not to matter at these
shapes (see bench/_harness.py).

Usage:
    python bench/batched.py
    python bench/batched.py --smoke
"""

import argparse
from pathlib import Path
from typing import Any

import numpy as np
from _harness import (
    EPS,
    RESULTS_DIR,
    SEED,
    interleave,
    print_header,
    print_table,
    write_result,
)

from polar_projector import PolarProjector
from polar_projector.fixtures import random_unit_vector

D = 384
N_CORPUS = 16_384
BATCH_SIZES = (1, 4, 16, 64, 256, 1024, 4096)
REPS = 3
WARMUP_BATCH = 50

SEED_ANCHOR, SEED_POLE_A, SEED_POLE_B, SEED_BASE = 1, 2, 3, 1000


def corpus() -> np.ndarray:
    return np.ascontiguousarray(
        [random_unit_vector(D, SEED_BASE + i) for i in range(N_CORPUS)]
    )


def residual_norms(projector: PolarProjector, V: np.ndarray, frame) -> np.ndarray:
    """||r||_2 per row: the scale the d_esc deviation is meaningful against."""
    r = V - frame.c_1
    r = r - (r @ frame.c1_hat)[:, None] * frame.c1_hat
    return np.linalg.norm(r, axis=1)


def throughput(projector: PolarProjector, V: np.ndarray, frame, reps: int) -> dict[str, Any]:
    """Per-vector cost of both paths, at every batch size."""
    out: dict[str, Any] = {}
    rows = []

    for b in BATCH_SIZES:
        n_batches = max(1, min(64, N_CORPUS // b))
        batches = [np.ascontiguousarray(V[i * b : (i + 1) * b]) for i in range(n_batches)]

        def batched(i: int, _bs=batches, _n=n_batches) -> Any:
            return projector.evaluate_batch(_bs[i % _n], frame)

        def looped(i: int, _bs=batches, _n=n_batches) -> Any:
            chunk = _bs[i % _n]
            return [projector.evaluate(chunk[j], frame, j) for j in range(chunk.shape[0])]

        stats = interleave(
            {"scalar_loop": looped, "evaluate_batch": batched},
            n_batches,
            reps=reps,
            warmup=WARMUP_BATCH,
        )
        per_vec_loop = stats["scalar_loop"]["mean"] / b
        per_vec_batch = stats["evaluate_batch"]["mean"] / b

        out[str(b)] = {
            "scalar_loop_us_per_vec": per_vec_loop,
            "evaluate_batch_us_per_vec": per_vec_batch,
            "speedup": per_vec_loop / per_vec_batch,
            "vectors_per_second": 1e6 / per_vec_batch,
        }
        rows.append([
            str(b), f"{per_vec_loop:.3f}", f"{per_vec_batch:.3f}",
            f"{per_vec_loop / per_vec_batch:.2f}x", f"{1e6 / per_vec_batch:,.0f}",
        ])

    print_table(
        ["B", "loop us/vec", "batch us/vec", "speedup", "vec/s"],
        rows, [8, 14, 15, 11, 14],
    )
    print("B=1 is included because it is where batching can only lose\n")
    return out


def agreement(projector: PolarProjector, V: np.ndarray, frame) -> dict[str, Any]:
    """Observed deviation from the scalar loop, normalized by epsilon."""
    out: dict[str, Any] = {}
    rows = []

    for b in BATCH_SIZES:
        chunk = np.ascontiguousarray(V[:b])
        batch = projector.evaluate_batch(chunk, frame)
        scalar = [projector.evaluate(v, frame, i) for i, v in enumerate(chunk)]

        d_lam = np.abs(batch.lambdas - np.array([s[1] for s in scalar]))
        d_esc = np.abs(batch.d_esc - np.array([s[2] for s in scalar]))
        norms = residual_norms(projector, chunk, frame)

        lam_ulp = float(np.max(d_lam) / EPS)
        esc_ulp = float(np.max(d_esc / (EPS * norms)))
        out[str(b)] = {"max_dlambda_over_eps": lam_ulp, "max_desc_over_eps_r": esc_ulp}
        rows.append([str(b), f"{lam_ulp:.2f}", f"{esc_ulp:.2f}"])

    print_table(["B", "max |dlam|/eps", "max |dd_esc|/(eps*||r||)"], rows, [8, 18, 26])
    print("not parity: BLAS reorders the reduction at B>=2, so these are bounds\n")
    return out


def sqrt_cost(V: np.ndarray, reps: int) -> dict[str, Any]:
    """What section 4.2's E_esc proposal would actually save."""
    out: dict[str, Any] = {}
    rows = []

    for b in (64, 1024, 4096):
        chunk = np.ascontiguousarray(V[:b])
        arms = {
            "with_sqrt": lambda i, c=chunk: np.sqrt(np.einsum("ij,ij->i", c, c)),
            "without_sqrt": lambda i, c=chunk: np.einsum("ij,ij->i", c, c),
        }
        stats = interleave(arms, 200, reps=reps, warmup=WARMUP_BATCH)
        saving = 1.0 - stats["without_sqrt"]["mean"] / stats["with_sqrt"]["mean"]
        out[str(b)] = {
            "with_sqrt_us": stats["with_sqrt"]["mean"],
            "without_sqrt_us": stats["without_sqrt"]["mean"],
            "saving": saving,
        }
        rows.append([str(b), f"{stats['with_sqrt']['mean']:.2f}",
                     f"{stats['without_sqrt']['mean']:.2f}", f"{saving * 100:+.1f}%"])

    print_table(["B", "with sqrt us", "without us", "saving"], rows, [8, 15, 13, 10])
    print("section 4.2 proposes returning E_esc to skip this square root\n")
    return out


def row_order_sensitivity(projector: PolarProjector, V: np.ndarray, frame) -> dict[str, Any]:
    """Is a row's result a pure function of that row? Measured, not assumed."""
    out: dict[str, Any] = {}
    rng = np.random.default_rng(SEED)
    rows = []

    for b in (64, 1024, 4096):
        chunk = np.ascontiguousarray(V[:b])
        perm = rng.permutation(b)
        inverse = np.argsort(perm)

        direct = projector.evaluate_batch(chunk, frame)
        shuffled = projector.evaluate_batch(np.ascontiguousarray(chunk[perm]), frame)

        d_lam = np.abs(direct.lambdas - shuffled.lambdas[inverse])
        d_esc = np.abs(direct.d_esc - shuffled.d_esc[inverse])
        identical = bool(np.array_equal(direct.lambdas, shuffled.lambdas[inverse])
                         and np.array_equal(direct.d_esc, shuffled.d_esc[inverse]))

        out[str(b)] = {
            "bitwise_identical": identical,
            "max_dlambda_over_eps": float(np.max(d_lam) / EPS),
            "max_ddesc_abs": float(np.max(d_esc)),
        }
        rows.append([str(b), "yes" if identical else "no",
                     f"{np.max(d_lam) / EPS:.2f}", f"{np.max(d_esc):.3e}"])

    print_table(["B", "bitwise stable", "max |dlam|/eps", "max |dd_esc|"], rows,
                [8, 17, 18, 15])
    print("permuted then un-permuted, against the unpermuted result\n")
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=RESULTS_DIR / "batched.json")
    parser.add_argument("--reps", type=int, default=REPS)
    parser.add_argument("--smoke", action="store_true",
                        help="tiny run to prove the script executes; not a measurement")
    args = parser.parse_args()

    reps = 1 if args.smoke else args.reps

    print_header("E4 batched", f"V P⊥ vs a scalar loop, d={D}, N={N_CORPUS}, float64")

    V = corpus()
    projector = PolarProjector()
    frame = projector.prepare(
        random_unit_vector(D, SEED_ANCHOR),
        random_unit_vector(D, SEED_POLE_A),
        random_unit_vector(D, SEED_POLE_B),
    )
    results = {
        "throughput": throughput(projector, V, frame, reps),
        "agreement": agreement(projector, V, frame),
        "sqrt_cost": sqrt_cost(V, reps),
        "row_order": row_order_sensitivity(projector, V, frame),
    }

    if args.smoke:
        print("SMOKE RUN — parameters are not the published protocol; no result written")
        return 0

    write_result(
        args.out,
        experiment="E4",
        config={"seed": SEED, "d": D, "n_corpus": N_CORPUS,
                "batch_sizes": list(BATCH_SIZES), "reps": reps, "warmup": WARMUP_BATCH},
        results=results,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
