"""E5 — Task-level neighborhood preservation: same-part retrieval.

Question: section 3.4 measures fidelity with trustworthiness (0.66 against
0.90-0.92) and leaves open whether that instrument is the right one for a
per-interaction signal. This experiment gives a second, task-shaped instrument
on the same corpus and the same growth schedule: at each step, if a reader
asked "what else is like this point," what fraction of the answer would come
from the same section of the Ethics as the point itself?

Method
------
The frozen Spinoza corpus (bench/data/) is already labelled by `part` -- five
sections, P1_GOD through P5_POWER. For each arm's 2D coordinates at each
growth step (UMAP, t-SNE and the two polar arms all produce an (n, 2) array --
(lambda, d_esc) for the operator, an arbitrary 2D layout for the baselines),
recall@k measures, for every point, what fraction of its k nearest neighbours
in that 2D space share its `part`. Averaged over points, that is recall@k for
one arm at one step.

A chance level is reported alongside it: the expected recall@k if neighbours
were drawn uniformly at random, which is (c_p - 1)/(n - 1) for a point in a
part of size c_p, averaged over points. This does not depend on k -- a
uniformly random k-subset has the same expected same-part fraction as a
uniformly random 1-subset, by linearity of expectation -- so it is not
reported once per k. It is, however, reported once *per growth step*, not
once per corpus: the frozen corpus is ordered by part (bench/data/, reading
order), so the composition of the size-500 prefix is far more lopsided than
the full 2,221-chunk corpus, and chance itself falls from about 0.70 to about
0.22 across the growth schedule. Comparing every step's raw recall@k against
one global chance level would blame the arms for a shift in the task itself.
What is aggregated across steps is therefore lift = recall@k / chance, the
same kind of correction bench/drift.py already applies when it normalizes
displacement by RMS radius rather than comparing raw coordinates.

Reuse, not reimplementation
----------------------------
drift.py already produces exactly the embeddings this experiment needs: its
ARMS dict and growth_schedule() are imported directly rather than
reimplementing UMAP/t-SNE/polar-coordinate construction a third time.
Recomputing them here is unavoidable -- drift.json stores only aggregated
displacement statistics, not the per-step coordinate arrays -- so this script
pays the same cost drift.py already pays, once more.

Aggregation across steps follows drift.py's rule: median and worst case,
never mean. "Worst" here means lowest lift, the opposite direction from
drift.py's "worst" (largest displacement) -- both mean "the step that argues
against the arm." Every arm's worst step turns out to be the first one
(size=500): a small, part-skewed prefix leaves little headroom above its own
already-high chance level, which is a property of the corpus at that size,
not a property of any arm. The steps that actually discriminate between arms
are the later ones, reported alongside the aggregate rather than in place of
it.

Deterministic, offline. The baseline arms need the [bench] extra; the two
polar arms need numpy alone, matching the numpy-only guarantee bench/drift.py
already gives its own arms.

Usage:
    python bench/recall.py
    python bench/recall.py --arms polar_fixed polar_moving   # numpy only
    python bench/recall.py --k 15 --out bench/results/recall.json
"""

import argparse
import time
from pathlib import Path

import numpy as np
from _harness import RESULTS_DIR, load_corpus, print_header, print_table, write_result
from drift import ARMS, growth_schedule

K_DEFAULT = 15  # matches TRUSTWORTHINESS_K in drift.py, for direct comparability


def recall_at_k(coords: np.ndarray, parts: list[str], k: int) -> float:
    """Mean fraction of each point's k nearest 2D neighbours sharing its part.

    Brute force via the Gram matrix (n squared distances, not n squared
    (n, d) differences): n is at most 2,221 here, so exactness is cheaper to
    reason about than an approximate index would be to validate.
    """
    n = coords.shape[0]
    if k >= n:
        raise ValueError(f"k={k} must be smaller than the number of points ({n})")

    parts_arr = np.asarray(parts)
    sq_norms = np.sum(coords * coords, axis=1)
    dist_sq = sq_norms[:, None] + sq_norms[None, :] - 2.0 * (coords @ coords.T)
    np.fill_diagonal(dist_sq, np.inf)  # exclude self as its own neighbour

    neighbor_idx = np.argpartition(dist_sq, k, axis=1)[:, :k]
    same_part = parts_arr[neighbor_idx] == parts_arr[:, None]
    return float(np.mean(same_part))


def chance_level(parts: list[str]) -> float:
    """Expected recall@k under uniformly random neighbours; independent of k.

    For a point in a part of size c_p, a uniformly random neighbour matches
    with probability (c_p - 1)/(n - 1). Averaged over points, not over parts,
    so a large part is weighted the same way recall_at_k weights it.
    """
    parts_arr = np.asarray(parts)
    n = len(parts_arr)
    sizes = {p: int(np.sum(parts_arr == p)) for p in set(parts)}
    per_point = np.array([(sizes[p] - 1) / (n - 1) for p in parts_arr])
    return float(np.mean(per_point))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=RESULTS_DIR / "recall.json")
    parser.add_argument("--arms", nargs="*", choices=sorted(ARMS), default=sorted(ARMS))
    parser.add_argument("--k", type=int, default=K_DEFAULT)
    args = parser.parse_args()

    vectors, parts = load_corpus()
    sizes = growth_schedule(vectors.shape[0])
    chances = [chance_level(parts[:size]) for size in sizes]

    print_header("E5 recall", f"same-part k={args.k} retrieval, {vectors.shape[0]} chunks")
    print(f"growth: {sizes[0]} then steps to {sizes[-1]} ({len(sizes)} steps)")
    print("chance level per step (corpus is part-ordered, so this is not constant):")
    print("  " + ", ".join(f"{c:.3f}" for c in chances) + "\n")

    results: dict[str, dict] = {}
    for name in args.arms:
        print(f"[{name}] running...", flush=True)
        started = time.perf_counter()
        fn = ARMS[name]
        embeddings = (
            fn(vectors, parts, sizes)  # type: ignore[operator]
            if name.startswith("polar")
            else fn(vectors, sizes)  # type: ignore[operator]
        )
        elapsed = time.perf_counter() - started

        steps = []
        for i, size in enumerate(sizes):
            recall = recall_at_k(embeddings[i], parts[:size], args.k)
            chance = chances[i]
            steps.append({"size": size, "recall_at_k": recall, "chance": chance, "lift": recall / chance})
        results[name] = {"seconds": elapsed, "steps": steps}
        lifts = [s["lift"] for s in steps]
        print(
            f"[{name}] {elapsed:6.1f}s | median lift {np.median(lifts):.2f}x "
            f"| final-step lift {lifts[-1]:.2f}x | worst-step lift {min(lifts):.2f}x"
        )

    rows = []
    for name, res in results.items():
        lifts = [s["lift"] for s in res["steps"]]
        rows.append(
            [
                name,
                f"{float(np.median(lifts)):.2f}x",
                f"{lifts[-1]:.2f}x",
                f"{min(lifts):.2f}x",
            ]
        )
    print()
    print_table(["arm", "median lift", "final-step lift", "worst-step lift"], rows, [16, 14, 18, 17])
    print("lift = recall@k / chance for that step's part composition; 1.0x = no better than random.")
    print("worst-step is always the first step (size=500) -- see module docstring.")

    write_result(
        args.out,
        experiment="E5",
        config={
            "k": args.k,
            "sizes": sizes,
            "chance_level_per_step": chances,
        },
        results=results,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
