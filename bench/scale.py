"""E8 — Declared screen scale: which of §3.2-§3.4's figures depend on S_x / S_y?

Protocol committed before any results, as E1-E7 were. A --smoke run on a
synthetic corpus verifies execution, prints no metric and writes nothing.

Why this exists
---------------
The manuscript's registered question says that how much of a local frame's
re-centring shows on screen depends on the declared scale. E1, E5 and E6 never
declared one: bench/drift.py's _polar_coords hands the operator's (lambda, d_esc)
to trustworthiness and to recall@k as they are, which is the screen mapping of
§2.1 at S_x = S_y. Both instruments are invariant to a uniform rescaling of a
layout but not to stretching one axis against the other, so every polar figure in
those three experiments -- trustworthiness 0.6639, the lifts, the moving anchor's
0.13-0.61 per-step displacement -- is a property of that undeclared ratio as much
as of the operator. The stillness counts are not: a fixed frame stays exactly
still under any affine map of its output.

This is robustness check F3 of the registered question, not a refutation
criterion. Whatever it shows is reported, and it does not change the question.

Scales
------
unit        (lambda, d_esc), S_x = S_y: what E1, E5 and E6 measured. lambda is a
            fraction of the current frame's dipole and d_esc a length, so the two
            axes are in different units.
isometric   (||v_dipole|| * lambda, d_esc), with ||v_dipole|| taken from the frame
            the point is evaluated against. Both axes are lengths in the embedding
            space -- the units PCA and the random projection already produce -- so
            this is the comparison on equal terms against the fixed linear
            baselines. By the Corollary of Proposition 3 the two coordinates square
            to E_lambda and E_esc wherever lambda is unsaturated.

No third scale. lambda is the operator's output as returned, clamp included: the
experiment characterizes the operator as shipped, not a variant of it.

Declared before running
-----------------------
1. Moving anchor under isometric. ||v_dipole|| = ||P_perp(c_A - c_B)|| depends on
   the anchor, so it changes at every growth step and the aspect ratio changes
   with it. Full Procrustes alignment removes a uniform scale, not a change of
   aspect ratio, so part of that arm's measured displacement will be the ratio
   change itself. It is a real displacement in length units and is reported as
   one; ||v_dipole|| per step is stored so a reader can separate the two.
2. Saturation. Where lambda clamps, Proposition 3 is an inequality and the
   isometric coordinates under-account for the residual's energy. The fraction of
   points with |lambda| == 1.0 is recorded per frame (per step for the moving
   anchor) as a descriptive column, not as a claim.
3. Validity. The unit scale must reproduce the committed E1, E5 and E6 figures for
   the polar arms, the four pole-selection rules and the ten axis pairs to within
   1e-12. If it does not, this run measures something other than what was
   published: the artifact records the failure and the script exits non-zero.
4. What F3 compares. Under each scale: the sign of polar_fixed minus pca_fit_once,
   and minus random_fixed, on trustworthiness, median lift and worst-step lift; and
   the order of the four leak-free pole-selection rules by trustworthiness and by
   median lift. Whether each of those changes between scales is stored explicitly.
5. Manuscript sentences resting on the unit scale. They are rewritten to report
   both scales, whichever direction the result goes: the abstract's PCA-inside-
   the-range and 1.17x-where-other-stable-arms-fall-to-chance claims; the third
   contribution bullet; §3.2's 0.6811-above-0.6639 comparison and the moving
   anchor's 0.13-0.61; §3.3's lead over the once-fitted PCA (1.57x against 1.47x,
   1.17x against 1.01x); §3.4's rule table, its pessimistic/optimistic reading and
   the part-based rule's 1.17x; and §2.1, §4 and §6 where they repeat 0.13-0.61.
   Neither scale is promoted to headline after seeing results: isometric is the
   declared comparison against the linear baselines, unit is continuity with what
   was published.

Out of scope: an energy analysis, other instruments, UMAP and t-SNE (their layouts
have no lambda axis to rescale), and any scale not listed above. Figures from this
script enter the manuscript only through rows in tools/verify_paper_tables.py.

Deterministic, offline. numpy for the coordinates; trustworthiness needs
scikit-learn and is n/a without it, as in bench/drift.py.

Usage:
    python bench/scale.py --smoke
    python bench/scale.py --out bench/results/scale.json
"""

import argparse
import contextlib
import io
import itertools
import json
from pathlib import Path

import numpy as np
from _harness import RESULTS_DIR, SEED, dipole_poles, load_corpus, print_header, write_result
from drift import (
    TRUSTWORTHINESS_K,
    _fmt_trust,
    arm_pca_fit_once,
    arm_random_fixed,
    displacement_stats,
    growth_schedule,
    trustworthiness,
)
from frame_sensitivity import RULES, part_centroids
from recall import chance_level, recall_at_k

from polar_projector import PolarFrame, PolarProjector

K = 15  # matches bench/recall.py and bench/frame_sensitivity.py
SCALES = ("unit", "isometric")
STILL = 1e-9  # a step counts as still below this, as in bench/drift.py
REPRODUCE_ATOL = 1e-12
F3_METRICS = ("trustworthiness", "median_lift", "worst_lift")


def raw_view(projector: PolarProjector, vectors: np.ndarray, frame: PolarFrame) -> np.ndarray:
    """(lambda, d_esc) for every vector, exactly as bench/drift.py's _polar_coords."""
    coords = np.empty((vectors.shape[0], 2), dtype=np.float64)
    for i, v in enumerate(vectors):
        _, lam, d_esc = projector.evaluate(v, frame, i)
        coords[i] = (lam, d_esc)
    return coords


def scaled(coords: np.ndarray, frame: PolarFrame, scale: str) -> np.ndarray:
    """Apply one declared screen scale. unit returns the operator's output untouched."""
    if scale == "unit":
        return coords
    out = coords.copy()
    out[:, 0] *= float(np.sqrt(frame.v_dipole_norm_sq))
    return out


def saturated_fraction(coords: np.ndarray) -> float:
    """Share of points whose lambda was clamped: the clamp returns exactly +-1.0."""
    return float(np.mean(np.abs(coords[:, 0]) == 1.0))


def series_metrics(
    vectors: np.ndarray, parts: list[str], sizes: list[int], chances: list[float], embeddings: list[np.ndarray]
) -> dict:
    """E1's displacement and trustworthiness, and E5's lift, over one growth series."""
    p95 = [
        displacement_stats(embeddings[i - 1], embeddings[i])["aligned_p95"] for i in range(1, len(sizes))
    ]
    lifts = [recall_at_k(embeddings[i], parts[: sizes[i]], K) / chances[i] for i in range(len(sizes))]
    return {
        "median_step": float(np.median(p95)),
        "worst_step": float(max(p95)),
        "still_steps": sum(1 for x in p95 if x < STILL),
        "aligned_p95_per_step": p95,
        "trustworthiness": trustworthiness(vectors, embeddings[-1], TRUSTWORTHINESS_K),
        "median_lift": float(np.median(lifts)),
        "final_lift": lifts[-1],
        "worst_lift": float(min(lifts)),
        "lift_per_step": lifts,
    }


def fixed_frame(
    projector: PolarProjector,
    vectors: np.ndarray,
    parts: list[str],
    sizes: list[int],
    chances: list[float],
    c_1: np.ndarray,
    c_A: np.ndarray,
    c_B: np.ndarray,
) -> dict:
    """One frame for the whole series, under both scales.

    A point's coordinates are a pure function of that point and the frame, so the
    view at each growth step is a prefix of the full-corpus view -- bitwise what
    bench/drift.py obtains by re-evaluating every prefix.
    """
    frame = projector.prepare(c_1, c_A, c_B)
    coords = raw_view(projector, vectors, frame)
    out: dict = {
        "dipole_norm": float(np.sqrt(frame.v_dipole_norm_sq)),
        "saturated_fraction": saturated_fraction(coords),
    }
    for scale in SCALES:
        view = scaled(coords, frame, scale)
        out[scale] = series_metrics(vectors, parts, sizes, chances, [view[:size] for size in sizes])
    return out


def moving_anchor(
    projector: PolarProjector, vectors: np.ndarray, parts: list[str], sizes: list[int], chances: list[float]
) -> dict:
    """bench/drift.py's polar_moving: poles fixed at step 0, anchor = newest batch mean."""
    c_A, c_B = dipole_poles(vectors[: sizes[0]], parts[: sizes[0]])
    views: dict[str, list[np.ndarray]] = {scale: [] for scale in SCALES}
    norms, saturation = [], []
    previous = 0
    for size in sizes:
        frame = projector.prepare(vectors[previous:size].mean(axis=0), c_A, c_B)
        coords = raw_view(projector, vectors[:size], frame)
        norms.append(float(np.sqrt(frame.v_dipole_norm_sq)))
        saturation.append(saturated_fraction(coords))
        for scale in SCALES:
            views[scale].append(scaled(coords, frame, scale))
        previous = size
    out: dict = {"dipole_norm_per_step": norms, "saturated_fraction_per_step": saturation}
    for scale in SCALES:
        out[scale] = series_metrics(vectors, parts, sizes, chances, views[scale])
    return out


def _sign(value: float | None, reference: float | None) -> str | None:
    if value is None or reference is None:
        return None
    return "above" if value > reference else "below" if value < reference else "equal"


def orderings(fixed: dict, rules: dict, references: dict, scale: str) -> dict:
    """The comparisons F3 is defined over (module docstring, item 4)."""
    out: dict = {}
    for ref in ("pca_fit_once", "random_fixed"):
        out[f"polar_fixed_vs_{ref}"] = {
            m: _sign(fixed[scale][m], references[ref][m]) for m in F3_METRICS
        }
    for m in ("trustworthiness", "median_lift"):
        values = {name: r[scale][m] for name, r in rules.items()}
        if all(v is not None for v in values.values()):
            out[f"rules_by_{m}"] = sorted(values, key=lambda k: values[k], reverse=True)
    return out


def reproduces_published(fixed: dict, moving: dict, rules: dict, axis_pairs: dict) -> dict:
    """Item 3: the unit scale must be E1, E5 and E6 as committed."""

    def load(name: str) -> dict:
        return json.loads((RESULTS_DIR / name).read_text(encoding="utf-8"))["results"]

    def close(a: object, b: object) -> bool:
        if a is None or b is None or np.shape(a) != np.shape(b):
            return False
        return bool(np.allclose(a, b, rtol=0.0, atol=REPRODUCE_ATOL))  # type: ignore[arg-type]

    drift, recall, sensitivity = load("drift.json"), load("recall.json"), load("frame_sensitivity.json")
    checks: dict[str, bool] = {}
    for name, arm in (("polar_fixed", fixed), ("polar_moving", moving)):
        unit = arm["unit"]
        checks[f"E1 {name} aligned_p95"] = close(
            unit["aligned_p95_per_step"], [s["aligned_p95"] for s in drift[name]["steps"]]
        )
        checks[f"E1 {name} trustworthiness"] = close(
            unit["trustworthiness"], drift[name]["final_trustworthiness"]
        )
        checks[f"E5 {name} lift"] = close(unit["lift_per_step"], [s["lift"] for s in recall[name]["steps"]])
    for name, r in rules.items():
        for m in F3_METRICS:
            checks[f"E6 rule {name} {m}"] = close(r["unit"][m], sensitivity["rules"][name][m])
    for name, f in axis_pairs.items():
        for m in ("trustworthiness", "median_lift"):
            checks[f"E6 axis {name} {m}"] = close(f["unit"][m], sensitivity["frames"][name][m])
    return {"all": all(checks.values()), "checks": checks}


def synthetic_corpus() -> tuple[np.ndarray, list[str]]:
    """Smoke-only stand-in: unit Gaussian vectors, part-ordered labels, no real data.

    Label names match the real corpus so the reproduction check's lookups run end
    to end; its comparisons fail on this data, as they must.
    """
    rng = np.random.default_rng(SEED)
    vectors = rng.standard_normal((800, 384))
    vectors /= np.linalg.norm(vectors, axis=1, keepdims=True)
    labels = (["P1_GOD"] * 350 + ["P2_MIND"] * 250 + ["P3_AFFECTS"] * 80
              + ["P4_BONDAGE"] * 70 + ["P5_POWER"] * 50)
    return vectors, labels


def report(fixed: dict, moving: dict, rules: dict, references: dict, changed: dict, reproduced: dict) -> None:
    print(f"\n{'arm':<34}{'scale':<11}{'trust':>8}{'med lift':>10}{'worst lift':>12}"
          f"{'worst step':>12}{'still':>7}")
    print("-" * 94)

    def row(name: str, scale: str, m: dict) -> None:
        print(f"{name:<34}{scale:<11}{_fmt_trust(m['trustworthiness'], 8)}{m['median_lift']:>9.2f}x"
              f"{m['worst_lift']:>11.2f}x{m['worst_step']:>12.4f}{m['still_steps']:>5}/{len(m['aligned_p95_per_step'])}")

    for scale in SCALES:
        row("polar_fixed", scale, fixed[scale])
    for scale in SCALES:
        row("polar_moving", scale, moving[scale])
    for name, r in rules.items():
        for scale in SCALES:
            row(f"rule {name}", scale, r[scale])
    for name, m in references.items():
        row(name, "native", m)
    print("-" * 94)
    print(f"polar_fixed ||v_dipole|| {fixed['dipole_norm']:.4f}, saturated {fixed['saturated_fraction']:.4f}")
    print(f"polar_moving ||v_dipole|| per step {min(moving['dipole_norm_per_step']):.4f}-"
          f"{max(moving['dipole_norm_per_step']):.4f}, saturated per step "
          f"{min(moving['saturated_fraction_per_step']):.4f}-{max(moving['saturated_fraction_per_step']):.4f}")
    for name, r in rules.items():
        print(f"rule {name:<24} ||v_dipole|| {r['dipole_norm']:.4f}, saturated {r['saturated_fraction']:.4f}")
    print("\nF3 — does the ordering change between unit and isometric?")
    for key, flag in changed.items():
        print(f"  {key:<40} {'CHANGED' if flag else 'unchanged'}")
    print(f"\nunit reproduces committed E1/E5/E6: {'yes' if reproduced['all'] else 'NO — run invalid'}")
    for label, ok in reproduced["checks"].items():
        if not ok:
            print(f"  MISMATCH {label}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=RESULTS_DIR / "scale.json")
    parser.add_argument(
        "--smoke", action="store_true",
        help="synthetic corpus: verifies execution, prints no metric, writes nothing",
    )
    args = parser.parse_args()

    vectors, parts = synthetic_corpus() if args.smoke else load_corpus()
    sizes = growth_schedule(vectors.shape[0])
    chances = [chance_level(parts[:size]) for size in sizes]
    projector = PolarProjector()
    window, window_parts = vectors[: sizes[0]], parts[: sizes[0]]
    c_1 = window.mean(axis=0)

    print_header("E8 declared scale", f"{vectors.shape[0]} vectors, d={vectors.shape[1]}"
                 + (" (SMOKE: synthetic)" if args.smoke else ""))

    fixed = fixed_frame(projector, vectors, parts, sizes, chances, c_1, *dipole_poles(window, window_parts))
    moving = moving_anchor(projector, vectors, parts, sizes, chances)
    rules = {
        name: fixed_frame(projector, vectors, parts, sizes, chances, c_1, *rule(window, window_parts))
        for name, rule in RULES.items()
    }
    centroids = part_centroids(vectors, parts)
    axis_pairs = {
        f"{a}|{b}": fixed_frame(projector, vectors, parts, sizes, chances, c_1, centroids[a], centroids[b])
        for a, b in itertools.combinations(sorted(centroids), 2)
    }
    references = {
        "pca_fit_once": series_metrics(vectors, parts, sizes, chances, arm_pca_fit_once(vectors, sizes)),
        "random_fixed": series_metrics(vectors, parts, sizes, chances, arm_random_fixed(vectors, sizes)),
    }
    order = {scale: orderings(fixed, rules, references, scale) for scale in SCALES}
    changed = {key: order["unit"][key] != order["isometric"][key] for key in order["unit"]}

    reproduced = reproduces_published(fixed, moving, rules, axis_pairs)

    if args.smoke:
        # Exercise the report path too, so a crash in it cannot surface only in
        # the registered run -- but swallow its output: no metric is shown.
        with contextlib.redirect_stdout(io.StringIO()):
            report(fixed, moving, rules, references, changed, reproduced)
        n_frames = 2 + len(rules) + len(axis_pairs)
        print(f"smoke ok: {n_frames} polar series x {len(SCALES)} scales, 2 references, "
              f"{len(changed)} F3 comparisons, reproduction check ({len(reproduced['checks'])} lookups) "
              "and report executed; no metric printed, nothing written")
        return 0

    report(fixed, moving, rules, references, changed, reproduced)

    write_result(
        args.out,
        experiment="E8",
        config={
            "seed": SEED,
            "sizes": sizes,
            "k": K,
            "trustworthiness_k": TRUSTWORTHINESS_K,
            "scales": list(SCALES),
            "still_threshold": STILL,
            "reproduce_atol": REPRODUCE_ATOL,
            "anchor": "initial-window mean (fixed arms); newest-batch mean (moving arm)",
            "chance_level_per_step": chances,
        },
        results={
            "polar_fixed": fixed,
            "polar_moving": moving,
            "rules": rules,
            "axis_pairs": axis_pairs,
            "references": references,
            "orderings": order,
            "ordering_changed": changed,
            "unit_reproduces_published": reproduced,
        },
    )
    return 0 if reproduced["all"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
