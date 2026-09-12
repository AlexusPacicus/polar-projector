"""E6 — How much of the operator's fidelity is the operator, and how much is the frame?

Every figure in E1 and E5 is measured against a single contextual frame: one
anchor and one pole pair, chosen once by `_harness.dipole_poles` from the two
most-represented parts of the initial window. That makes trustworthiness 0.6639
and same-part lift 1.57x properties of *that* frame, not of the operator, and
the manuscript's central trade-off number has had no error bar.

This script puts one on it. The anchor stays what `arm_polar_fixed` uses -- the
mean of the initial window -- and the contrast axis is varied over every
unordered pair of the corpus's five part centroids, C(5,2) = 10 frames. For each
frame it reports the same two instruments E1 and E5 use, plus the worst-step
displacement, and aggregates across frames by median and full range.

What this does and does not vary
--------------------------------
Pole centroids here are computed over the whole corpus, not over the initial
window. That uses label information the production selection rule does not have,
and it is deliberate: the question is how much the fidelity figure moves when the
contrast axis moves, and for that the right family to sample is well-separated
semantic axes rather than noisy ones. It is a sensitivity probe on the axis, not
a claim about what a system could have picked at step 0.

The drift measurement is untouched by that choice. A fixed frame is a fixed
frame, so every frame here is exactly still at every step by construction, and
the displacement column exists only to confirm that rather than to discriminate.
The frame chosen by the production rule is reported alongside the distribution so
a reader can see where the manuscript's published number sits in it.

Deterministic, offline. numpy only for the coordinates; trustworthiness needs
scikit-learn and is reported as n/a without it, matching bench/drift.py.

Usage:
    python bench/frame_sensitivity.py
    python bench/frame_sensitivity.py --out bench/results/frame_sensitivity.json
"""

import argparse
import itertools
from pathlib import Path

import numpy as np
from _harness import RESULTS_DIR, SEED, dipole_poles, load_corpus, print_header, write_result
from drift import TRUSTWORTHINESS_K, _polar_coords, displacement_stats, growth_schedule, trustworthiness
from recall import chance_level, recall_at_k

from polar_projector import PolarProjector

K = 15


def part_centroids(vectors: np.ndarray, parts: list[str]) -> dict[str, np.ndarray]:
    """One centroid per part label, over the whole corpus."""
    labels = sorted(set(parts))
    index = {p: [i for i, q in enumerate(parts) if q == p] for p in labels}
    return {p: vectors[index[p]].mean(axis=0) for p in labels}


def evaluate_frame(
    vectors: np.ndarray,
    parts: list[str],
    sizes: list[int],
    c_1: np.ndarray,
    c_A: np.ndarray,
    c_B: np.ndarray,
    chances: list[float],
) -> dict[str, float | None]:
    """Both instruments plus worst-step drift, for one fixed frame."""
    projector = PolarProjector()
    embeddings = [_polar_coords(projector, vectors[:size], c_1, c_A, c_B) for size in sizes]

    worst = max(
        displacement_stats(embeddings[i - 1], embeddings[i])["aligned_p95"]
        for i in range(1, len(sizes))
    )
    lifts = [
        recall_at_k(embeddings[i], parts[: sizes[i]], K) / chances[i] for i in range(len(sizes))
    ]
    return {
        "worst_aligned_p95": worst,
        "trustworthiness": trustworthiness(vectors, embeddings[-1], TRUSTWORTHINESS_K),
        "median_lift": float(np.median(lifts)),
        "final_lift": lifts[-1],
        "worst_lift": min(lifts),
    }


# --- leak-free pole selection rules ---------------------------------------
#
# Every rule below sees only vectors[:sizes[0]] -- the initial window a real
# system would have at step 0 -- so whatever fidelity they reach is actually
# reachable. The bar to clear is pca_fit_once's 0.6811 trustworthiness
# (bench/drift.py arm 7), which is a fixed linear map fitted on that same
# window and is therefore the fairest thing the operator has to beat.


def rule_largest_two_parts(
    window: np.ndarray, window_parts: list[str]
) -> tuple[np.ndarray, np.ndarray]:
    """The production rule: centroids of the two most-represented parts."""
    return dipole_poles(window, window_parts)


def rule_kmeans2(window: np.ndarray, _parts: list[str]) -> tuple[np.ndarray, np.ndarray]:
    """Lloyd with k=2, seeded deterministically by a farthest-point scan.

    Uses no labels at all, which makes it the rule a system could apply to an
    unlabelled corpus -- the common case for a personal knowledge base.
    """
    centre = window.mean(axis=0)
    i = int(np.argmax(((window - centre) ** 2).sum(axis=1)))
    j = int(np.argmax(((window - window[i]) ** 2).sum(axis=1)))
    pole_a, pole_b = window[i].copy(), window[j].copy()
    for _ in range(64):
        mask = ((window - pole_a) ** 2).sum(axis=1) <= ((window - pole_b) ** 2).sum(axis=1)
        if mask.all() or not mask.any():
            break
        next_a, next_b = window[mask].mean(axis=0), window[~mask].mean(axis=0)
        if np.allclose(next_a, pole_a) and np.allclose(next_b, pole_b):
            break
        pole_a, pole_b = next_a, next_b
    return pole_a, pole_b


def rule_pc1_extremes(window: np.ndarray, _parts: list[str]) -> tuple[np.ndarray, np.ndarray]:
    """Centroids of the top and bottom deciles along the window's first PC.

    This is the rule that tests a specific hypothesis: that pca_fit_once's
    fidelity edge comes from aligning with maximum variance. If so, pointing the
    dipole down the same axis should recover most of it.
    """
    centre = window.mean(axis=0)
    _, _, vt = np.linalg.svd(window - centre, full_matrices=False)
    scores = (window - centre) @ vt[0]
    order = np.argsort(scores)
    edge = max(1, len(window) // 10)
    return window[order[-edge:]].mean(axis=0), window[order[:edge]].mean(axis=0)


def rule_farthest_neighbourhoods(
    window: np.ndarray, _parts: list[str]
) -> tuple[np.ndarray, np.ndarray]:
    """Two farthest-apart points, each replaced by its decile neighbourhood mean.

    Maximizes pole separation without labels. The neighbourhood averaging is the
    point: two single farthest vectors are outliers, and a dipole built from
    outliers describes the corpus edge rather than its contrast.
    """
    centre = window.mean(axis=0)
    i = int(np.argmax(((window - centre) ** 2).sum(axis=1)))
    j = int(np.argmax(((window - window[i]) ** 2).sum(axis=1)))
    edge = max(1, len(window) // 10)

    def neighbourhood(index: int) -> np.ndarray:
        order = np.argsort(((window - window[index]) ** 2).sum(axis=1))
        return window[order[:edge]].mean(axis=0)

    return neighbourhood(i), neighbourhood(j)


RULES = {
    "largest_two_parts": rule_largest_two_parts,
    "kmeans2": rule_kmeans2,
    "pc1_extremes": rule_pc1_extremes,
    "farthest_neighbourhoods": rule_farthest_neighbourhoods,
}

PCA_FIT_ONCE_TRUST = 0.6811  # bench/results/drift.json, arm pca_fit_once


def _spread(values: list[float], fmt: str = ".4f") -> str:
    return f"{np.median(values):{fmt}}  [{min(values):{fmt}}, {max(values):{fmt}}]"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=RESULTS_DIR / "frame_sensitivity.json")
    args = parser.parse_args()

    vectors, parts = load_corpus()
    sizes = growth_schedule(vectors.shape[0])
    chances = [chance_level(parts[:size]) for size in sizes]
    c_1 = vectors[: sizes[0]].mean(axis=0)

    centroids = part_centroids(vectors, parts)
    pairs = list(itertools.combinations(sorted(centroids), 2))

    print_header("E6 frame sensitivity", f"{vectors.shape[0]} chunks, d={vectors.shape[1]}")
    print(f"anchor: initial-window mean (as arm_polar_fixed) | {len(pairs)} pole pairs\n")

    frames: dict[str, dict] = {}
    for a, b in pairs:
        name = f"{a}|{b}"
        frames[name] = evaluate_frame(
            vectors, parts, sizes, c_1, centroids[a], centroids[b], chances
        )
        f = frames[name]
        trust = f["trustworthiness"]
        print(
            f"  {name:<20} trust {trust:.4f}   lift {f['median_lift']:.2f}x   "
            f"worst drift {f['worst_aligned_p95']:.2e}"
            if trust is not None
            else f"  {name:<20} trust    n/a   lift {f['median_lift']:.2f}x"
        )

    # Leak-free selection rules: what a system could actually reach at step 0.
    window, window_parts = vectors[: sizes[0]], parts[: sizes[0]]
    rules: dict[str, dict] = {}
    print("\nleak-free pole selection (initial window only):")
    for rule_name, rule in RULES.items():
        pole_a, pole_b = rule(window, window_parts)
        rules[rule_name] = evaluate_frame(vectors, parts, sizes, c_1, pole_a, pole_b, chances)
        r = rules[rule_name]
        beats = "" if r["trustworthiness"] is None else (
            "  BEATS pca_fit_once" if r["trustworthiness"] > PCA_FIT_ONCE_TRUST else ""
        )
        print(
            f"  {rule_name:<24} trust {r['trustworthiness']:.4f}   "
            f"lift {r['median_lift']:.2f}x{beats}"
            if r["trustworthiness"] is not None
            else f"  {rule_name:<24} trust    n/a   lift {r['median_lift']:.2f}x"
        )

    published = rules["largest_two_parts"]

    trusts = [f["trustworthiness"] for f in frames.values() if f["trustworthiness"] is not None]
    med_lifts = [f["median_lift"] for f in frames.values()]
    drifts = [f["worst_aligned_p95"] for f in frames.values()]

    print(f"\n{'metric':<22}{'median  [min, max] across frames':<40}{'published frame':>18}")
    print("-" * 80)
    if trusts:
        print(f"{'trustworthiness':<22}{_spread(trusts):<40}{published['trustworthiness']:>18.4f}")
    print(f"{'median same-part lift':<22}{_spread(med_lifts):<40}{published['median_lift']:>18.4f}")
    print(f"{'worst-step drift':<22}{_spread(drifts, '.2e'):<40}"
          f"{published['worst_aligned_p95']:>18.2e}")
    print("-" * 80)
    print("every frame is exactly still at every step: a fixed frame cannot drift, so the")
    print("drift row confirms the construction rather than discriminating between frames.")
    print(f"bar to clear on trustworthiness: {PCA_FIT_ONCE_TRUST:.4f} (pca_fit_once, a fixed")
    print("linear map fitted on the same initial window)")

    write_result(
        args.out,
        experiment="E6",
        config={
            "seed": SEED,
            "sizes": sizes,
            "k": K,
            "trustworthiness_k": TRUSTWORTHINESS_K,
            "anchor": "initial-window mean",
            "pole_source": "whole-corpus part centroids, all C(5,2) pairs",
            "chance_level_per_step": chances,
        },
        results={"frames": frames, "rules": rules, "published_frame": published,
                 "pca_fit_once_trust": PCA_FIT_ONCE_TRUST},
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
