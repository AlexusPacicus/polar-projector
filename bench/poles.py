"""P1 — Where the named poles land on the lambda axis in the published frame.

Post hoc, and not pre-registered: these positions were first computed ad hoc
during a review of the manuscript, and this script exists so they can be
committed and checked rather than quoted from a scratch session.

The published frame (bench/drift.py, arm_polar_fixed) anchors on the mean of the
initial window and takes its poles from the two most-represented parts of that
same window (_harness.dipole_poles). When the window holds exactly two parts the
anchor is a convex combination of the poles, c_1 = (n_A c_A + n_B c_B) / N, so
c_A - c_1 = (n_B / N)(c_A - c_B) and, by linearity of P_perp, both poles lie on
the dipole axis at lambda = +n_B / N and -n_A / N, with d_esc = 0. lambda = +-1
then corresponds to neither pole.

This records the measured positions, the algebraic prediction and its residual,
and the window composition the prediction depends on.

Deterministic, offline, numpy only.

Usage:
    python bench/poles.py
    python bench/poles.py --out bench/results/poles.json
"""

import argparse
from collections import Counter
from pathlib import Path

from _harness import RESULTS_DIR, dipole_poles, load_corpus, print_header, write_result
from drift import N_INITIAL

from polar_projector import PolarProjector


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=RESULTS_DIR / "poles.json")
    args = parser.parse_args()

    vectors, parts = load_corpus()
    window, window_parts = vectors[:N_INITIAL], parts[:N_INITIAL]
    counts = Counter(window_parts)
    ranked = sorted(counts.items(), key=lambda item: -item[1])

    c_1 = window.mean(axis=0)
    c_A, c_B = dipole_poles(window, window_parts)
    projector = PolarProjector()
    frame = projector.prepare(c_1, c_A, c_B)

    positions = {}
    for name, vector in (("c_A", c_A), ("c_B", c_B), ("c_1", c_1)):
        _, lam, d_esc = projector.evaluate(vector, frame, 0)
        positions[name] = {"lambda": lam, "d_esc": d_esc}

    prediction = None
    if len(counts) == 2:
        (_, n_a), (_, n_b) = ranked
        prediction = {"c_A": n_b / N_INITIAL, "c_B": -n_a / N_INITIAL}
        residual = max(abs(positions[p]["lambda"] - prediction[p]) for p in ("c_A", "c_B"))
    else:
        residual = None

    print_header("P1 pole positions", f"published frame, initial window of {N_INITIAL}")
    print(f"window parts: {dict(ranked)}  (pole A = {ranked[0][0]}, pole B = {ranked[1][0]})")
    for name, pos in positions.items():
        print(f"  {name}: lambda = {pos['lambda']:+.6f}   d_esc = {pos['d_esc']:.3e}")
    if prediction is not None:
        print(f"two-part prediction: c_A {prediction['c_A']:+.6f}, c_B {prediction['c_B']:+.6f}; "
              f"max residual {residual:.2e}")
    else:
        print("window holds more than two parts: no two-part prediction applies")

    write_result(
        args.out,
        experiment="P1",
        config={"n_initial": N_INITIAL, "anchor": "initial-window mean",
                "poles": "_harness.dipole_poles on the initial window"},
        results={
            "window_part_counts": dict(ranked),
            "n_window_parts": len(counts),
            "pole_parts": [ranked[0][0], ranked[1][0]],
            "positions": positions,
            "dipole_norm": float(frame.v_dipole_norm_sq**0.5),
            "two_part_prediction": prediction,
            "max_prediction_residual": residual,
        },
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
