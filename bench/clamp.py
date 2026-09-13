"""A9 — Re-measure the lambda clamp substitution, and export what was never exported.

Not pre-registered: a re-measurement of figures first published in c3dfb0b --
np.clip at 1.74 us against min/max at 0.19 us per clamp, evaluate() 6.23 -> 4.56 us
(1.37x), and the scalar form's margin of 1.23x before the substitution -- that no
committed artifact contains. The manuscript takes its clamp figures from this
artifact instead.

Setup
-----
bench/conditioning.py's latency setup, unchanged: d = 384, float64, the frame built
from random_unit_vector seeds 1, 2 and 3, and 25,000 stimuli from seed 1000 onward;
3 repetitions after 1,000 warmup calls, arms interleaved and rotated, median across
repetitions (_harness.interleave). That script's vector_form arm is the evaluate()
figure the manuscript quotes.

Arms
----
clamp_np_clip          float(np.clip(x, -1.0, 1.0)) on the numpy float64 the old
                       evaluate() clamped
clamp_min_max          min(max(x, -1.0), 1.0) on the Python float the shipped
                       evaluate() clamps
evaluate_min_max       PolarProjector.evaluate, as shipped
evaluate_np_clip       the same body with the pre-c3dfb0b clamp restored
scalar_form_min_max    bench/conditioning.py's scalar_form, as it runs today
scalar_form_np_clip    the same with the pre-c3dfb0b clamp restored

Derived: the evaluate() speedup, the old clamp's share of the old call, the
microseconds the substitution removed, and the scalar form's margin over the vector
form, and its share of the hot path, before and after.

Equivalence is recorded alongside: the two evaluate() bodies compared bitwise over
all 25,000 stimuli, and the two clamps compared on the edge values the unit test
pins (NaN, signed zeros, the smallest subnormal, infinities, and the float either
side of each bound).

Usage:
    python bench/clamp.py
    python bench/clamp.py --out bench/results/clamp.json
"""

import argparse
import math
from pathlib import Path
from typing import Any

import numpy as np
from _harness import RESULTS_DIR, SEED, interleave, print_header, print_table, write_result
from conditioning import (
    N_LATENCY,
    REPS,
    SEED_ANCHOR,
    SEED_BASE,
    SEED_POLE_A,
    SEED_POLE_B,
    WARMUP,
    D,
    scalar_form,
)

from polar_projector import PolarFrame, PolarProjector
from polar_projector.fixtures import random_unit_vector

EDGE_VALUES = (
    -math.inf, -3.0, -1.0000000000000002, -1.0, -0.5, -0.0, 0.0,
    5e-324, 0.5, 1.0, 1.0000000000000002, 3.0, math.inf, math.nan,
)


def evaluate_np_clip(
    projector: PolarProjector, v_n: np.ndarray, frame: PolarFrame, centroid_id: int
) -> tuple[int, float, float]:
    """evaluate() with the pre-c3dfb0b clamp restored; every other line identical."""
    v_n = np.asarray(v_n, dtype=np.float64)
    if v_n.shape != frame.c_1.shape:
        raise ValueError(f"v_n shape {v_n.shape} does not match frame dimension {frame.c_1.shape}")
    r = projector._project_perp(v_n - frame.c_1, frame.c1_hat)
    lambda_val = float(np.clip(np.dot(r, frame.v_dipole) / frame.v_dipole_norm_sq, -1.0, 1.0))
    d_esc = float(np.linalg.norm(r - lambda_val * frame.v_dipole))
    return (centroid_id, lambda_val, d_esc)


def scalar_form_np_clip(
    projector: PolarProjector, v_n: np.ndarray, frame: PolarFrame
) -> tuple[float, float, float]:
    """bench/conditioning.py's scalar_form with the pre-c3dfb0b clamp restored."""
    r = projector._project_perp(v_n - frame.c_1, frame.c1_hat)
    rv = float(np.dot(r, frame.v_dipole))
    lam = float(np.clip(rv / frame.v_dipole_norm_sq, -1.0, 1.0))
    sq = float(np.dot(r, r)) - 2.0 * lam * rv + lam * lam * frame.v_dipole_norm_sq
    return lam, (math.sqrt(sq) if sq > 0.0 else 0.0), sq


def _bitwise_equal(a: float, b: float) -> bool:
    if math.isnan(a) or math.isnan(b):
        return math.isnan(a) and math.isnan(b)
    return a == b and math.copysign(1.0, a) == math.copysign(1.0, b)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=RESULTS_DIR / "clamp.json")
    parser.add_argument("--reps", type=int, default=REPS)
    parser.add_argument("--warmup", type=int, default=WARMUP)
    args = parser.parse_args()

    print_header("A9 clamp", f"np.clip against min/max, d={D}, float64, {N_LATENCY:,} stimuli")

    projector = PolarProjector()
    frame = projector.prepare(
        random_unit_vector(D, SEED_ANCHOR), random_unit_vector(D, SEED_POLE_A), random_unit_vector(D, SEED_POLE_B)
    )
    vectors = np.ascontiguousarray([random_unit_vector(D, SEED_BASE + i) for i in range(N_LATENCY)])

    # The value each clamp receives in its own evaluate(): a numpy float64 for the
    # old body, a Python float for the shipped one.
    raw = [np.dot(projector._project_perp(v - frame.c_1, frame.c1_hat), frame.v_dipole) / frame.v_dipole_norm_sq
           for v in vectors]
    as_python = [float(x) for x in raw]

    equal_stimuli = sum(
        1
        for i, v in enumerate(vectors)
        if all(_bitwise_equal(a, b) for a, b in zip(projector.evaluate(v, frame, i)[1:],
                                                     evaluate_np_clip(projector, v, frame, i)[1:]))
    )
    equal_edges = sum(
        1
        for x in EDGE_VALUES
        if _bitwise_equal(min(max(x, -1.0), 1.0), float(np.clip(np.float64(x), -1.0, 1.0)))
    )

    arms: dict[str, Any] = {
        "clamp_np_clip": lambda i: float(np.clip(raw[i], -1.0, 1.0)),
        "clamp_min_max": lambda i: min(max(as_python[i], -1.0), 1.0),
        "evaluate_min_max": lambda i: projector.evaluate(vectors[i], frame, i),
        "evaluate_np_clip": lambda i: evaluate_np_clip(projector, vectors[i], frame, i),
        "scalar_form_min_max": lambda i: scalar_form(projector, vectors[i], frame),
        "scalar_form_np_clip": lambda i: scalar_form_np_clip(projector, vectors[i], frame),
    }
    latency = interleave(arms, N_LATENCY, reps=args.reps, warmup=args.warmup)
    mean = {name: s["mean"] for name, s in latency.items()}

    derived = {
        "evaluate_speedup": mean["evaluate_np_clip"] / mean["evaluate_min_max"],
        "removed_us": mean["evaluate_np_clip"] - mean["evaluate_min_max"],
        "np_clip_share_of_old_call": mean["clamp_np_clip"] / mean["evaluate_np_clip"],
        "scalar_margin_before": mean["evaluate_np_clip"] / mean["scalar_form_np_clip"],
        "scalar_margin_after": mean["evaluate_min_max"] / mean["scalar_form_min_max"],
        "refusal_share_before": 1.0 - mean["scalar_form_np_clip"] / mean["evaluate_np_clip"],
        "refusal_share_after": 1.0 - mean["scalar_form_min_max"] / mean["evaluate_min_max"],
    }

    print_table(
        ["arm", "mean us", "p50", "p95", "spread"],
        [[name, f"{s['mean']:.2f}", f"{s['p50']:.2f}", f"{s['p95']:.2f}", f"{s['spread'] * 100:.1f}%"]
         for name, s in latency.items()],
        [22, 10, 9, 9, 9],
    )
    for key, value in derived.items():
        print(f"  {key:<28} {value:.4f}")
    print(f"  bitwise-identical evaluate() outputs: {equal_stimuli}/{N_LATENCY}; "
          f"edge values: {equal_edges}/{len(EDGE_VALUES)}")

    write_result(
        args.out,
        experiment="A9",
        config={"seed": SEED, "d": D, "n_latency": N_LATENCY, "reps": args.reps, "warmup": args.warmup,
                "setup": "bench/conditioning.py form_latency", "edge_values": [repr(x) for x in EDGE_VALUES]},
        results={
            "latency": latency,
            "derived": derived,
            "equivalence": {
                "stimuli_bitwise_equal": equal_stimuli,
                "stimuli": N_LATENCY,
                "edge_values_bitwise_equal": equal_edges,
                "edge_values": len(EDGE_VALUES),
            },
        },
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
