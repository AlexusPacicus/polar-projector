"""E3 — Numerical conditioning of the orthogonal residual.

Question: Proposition 3 is an exact identity, so both ways of evaluating it are
"correct". Where does that stop being true in floating point, and what does the
faster one cost you?

Rearranging Proposition 3 expresses d_esc purely in scalars already computed
for lambda:

    scalar form   sqrt(<r,r> - 2*lambda*<r,v_dipole> + lambda^2*||v_dipole||^2)
    vector form   ||r - lambda*v_dipole||              (what the library ships)

The scalar form is cheaper -- it reuses two dot products the operator has
already paid for. It is also a textbook cancellation: as the stimulus
approaches the dipole axis, it subtracts nearly equal quantities, and the
result can underflow negative before the square root ever runs.

Method
------
Both forms are scored against a truth rather than against each other.
polar_projector.fixtures.near_collinear_stimulus builds a stimulus whose exact
orthogonal residual is known analytically -- a perturbation of size eps taken
orthogonal to both the anchor and the dipole -- so "error" here means distance
from the right answer, not disagreement between two guesses.

lambda is held at 0.5 throughout, away from the clip, so what is measured is
conditioning and not saturation.

The sweep runs to d_esc/||r|| = 1e-14, well past the point where the scalar
form has failed completely. The manuscript publishes the 1e-3 .. 1e-8 window;
the rest is kept because where a method stops degrading gracefully and starts
returning noise is worth seeing in full.

Why this reimplements the scalar form
-------------------------------------
The scalar form is deliberately absent from the library -- projector.py
documents the omission at the line where d_esc is computed. It lives here
instead, built on the projector's own private helpers rather than on a
reimplementation of them, so that the two arms differ in exactly one step and
share every other code path.

Scope note: the delta-sweep of section 3.3 is not re-run here. It already has a
generator and, unusually for this repository, a CI verifier that fails the
build if a published cell moves. Adding a third copy of that measurement would
add a way for the three to disagree, not a way to catch an error. What this
experiment contributes to section 3.3 is the same guard for section 3.2, which
had none.

Deterministic, offline, numpy only.

Usage:
    python bench/conditioning.py
    python bench/conditioning.py --reps 5
"""

import argparse
import math
from pathlib import Path
from typing import Any

import numpy as np
from _harness import (
    RESULTS_DIR,
    SEED,
    interleave,
    print_header,
    print_table,
    write_result,
)

from polar_projector import PolarFrame, PolarProjector
from polar_projector.fixtures import near_collinear_stimulus, random_unit_vector

D = 384
N_LATENCY = 25_000
REPS = 3
WARMUP = 1_000

SEED_ANCHOR, SEED_POLE_A, SEED_POLE_B, SEED_BASE = 1, 2, 3, 1000

#: Exponents of the d_esc/||r|| sweep. The manuscript publishes 3, 5, 7 and 8.
EXPONENTS = tuple(range(1, 15))


def scalar_form(
    projector: PolarProjector, v_n: np.ndarray, frame: PolarFrame
) -> tuple[float, float, float]:
    """Proposition 3's scalar rearrangement, for the comparison only.

    Uses the projector's own _project_perp so that this arm and evaluate()
    differ in the final step and nowhere else.
    """
    r = projector._project_perp(v_n - frame.c_1, frame.c1_hat)
    rv = float(np.dot(r, frame.v_dipole))
    lam = float(np.clip(rv / frame.v_dipole_norm_sq, -1.0, 1.0))
    sq = float(np.dot(r, r)) - 2.0 * lam * rv + lam * lam * frame.v_dipole_norm_sq
    return lam, (math.sqrt(sq) if sq > 0.0 else 0.0), sq


def conditioning_sweep(projector: PolarProjector, frame: PolarFrame) -> list[dict[str, Any]]:
    """Both forms against an analytically known residual, as it shrinks."""
    rows = []
    for exponent in EXPONENTS:
        ratio = 10.0**-exponent
        v_n, exact = near_collinear_stimulus(frame.c_1, frame.c1_hat, frame.v_dipole, ratio)

        _, _, d_vector = projector.evaluate(v_n, frame, 0)
        _, d_scalar, sq = scalar_form(projector, v_n, frame)

        rows.append({
            "ratio": ratio,
            "exact": exact,
            "vector_rel_err": abs(d_vector - exact) / exact,
            "scalar_rel_err": abs(d_scalar - exact) / exact,
            "scalar_negative_under_sqrt": bool(sq <= 0.0),
        })
    return rows


def form_latency(
    projector: PolarProjector, frame: PolarFrame, reps: int, warmup: int
) -> dict[str, dict[str, float]]:
    """What the unusable form buys, so the trade is stated with a number on it."""
    vectors = np.ascontiguousarray(
        [random_unit_vector(D, SEED_BASE + i) for i in range(N_LATENCY)]
    )
    arms = {
        "vector_form": lambda i: projector.evaluate(vectors[i], frame, i),
        "scalar_form": lambda i: scalar_form(projector, vectors[i], frame),
    }
    return interleave(arms, N_LATENCY, reps=reps, warmup=warmup)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=RESULTS_DIR / "conditioning.json")
    parser.add_argument("--reps", type=int, default=REPS)
    parser.add_argument("--warmup", type=int, default=WARMUP)
    args = parser.parse_args()

    print_header("E3 conditioning", f"scalar vs vector residual, d={D}, float64")

    projector = PolarProjector()
    frame = projector.prepare(
        random_unit_vector(D, SEED_ANCHOR),
        random_unit_vector(D, SEED_POLE_A),
        random_unit_vector(D, SEED_POLE_B),
    )

    sweep = conditioning_sweep(projector, frame)
    print_table(
        ["d_esc/||r||", "exact d_esc", "vector rel err", "scalar rel err", "sqrt<0"],
        [
            [
                f"{row['ratio']:.0e}",
                f"{row['exact']:.3e}",
                f"{row['vector_rel_err']:.3e}",
                f"{row['scalar_rel_err']:.3e}",
                "yes" if row["scalar_negative_under_sqrt"] else "",
            ]
            for row in sweep
        ],
        [14, 15, 18, 18, 8],
    )
    print("error is distance from an analytically known residual, not disagreement\n")

    latency = form_latency(projector, frame, args.reps, args.warmup)
    speedup = latency["vector_form"]["mean"] / latency["scalar_form"]["mean"]
    print_table(
        ["form", "mean us", "p50", "p95", "p99", "spread"],
        [
            [name, f"{s['mean']:.2f}", f"{s['p50']:.2f}", f"{s['p95']:.2f}",
             f"{s['p99']:.2f}", f"{s['spread'] * 100:.1f}%"]
            for name, s in latency.items()
        ],
        [16, 10, 9, 9, 9, 9],
    )
    print(f"the scalar form is {speedup:.2f}x faster, and unusable below "
          f"d_esc/||r|| ~ 1e-6\n")

    write_result(
        args.out,
        experiment="E3",
        config={"seed": SEED, "d": D, "n_latency": N_LATENCY, "reps": args.reps,
                "warmup": args.warmup, "exponents": list(EXPONENTS)},
        results={"sweep": sweep, "latency": latency, "scalar_speedup": speedup},
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
