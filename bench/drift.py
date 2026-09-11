"""E1 — Positional drift under incremental corpus growth.

Question: when a corpus grows, how far do the points that did NOT change move?

A user navigating a semantic space builds a spatial mental model of it; layout
instability under incremental updates measurably degrades navigation (Boechler,
2001). Section 1 of the manuscript asserts that stochastic global projections
inherit this problem and that a local deterministic operator does not. This
script measures that claim instead of asserting it.

Arms
----
1. umap_fit_once   fit on the initial window, then transform() new points only.
2. umap_refit      refit from scratch at every step (what keeping fidelity costs).
3. tsne_refit      sklearn TSNE has no transform(); refitting is the only option.
4. polar_fixed     PolarProjector with the anchor held fixed.
5. polar_moving    PolarProjector with the anchor following the newest batch.

Arm 5 is not optional. The operator's output is anchor-relative, so reporting
only arm 4 would claim a stability the operator does not have. The defensible
claim is narrower and stronger: drift is a deterministic function of one
explicit, caller-controlled variable, not of hidden stochastic state or of
corpus size.

Method notes
------------
UMAP and t-SNE layouts are defined only up to a similarity transform, so raw
displacement largely measures global rotation — which a UI could absorb by
re-anchoring its camera. Both raw and Procrustes-aligned displacement are
reported; the aligned figure is the one that matters, and it is the reading
charitable to the baselines.

Displacements are normalized by each embedding's own RMS radius, since the
coordinate spaces are not commensurable (UMAP's units are arbitrary; the
operator's are (lambda, d_esc) with lambda in [-1, 1]).

Both baselines run with a fixed random_state. Demonstrating that an unseeded
stochastic method is unstable would prove nothing; the drift shown here is what
survives seeding, and comes from refitting rather than from randomness.

Deterministic, offline, CPU-only. Requires the [bench] extra.

Usage:
    python bench/drift.py
    python bench/drift.py --out bench/results/drift.json
"""

import argparse
import json
import platform
import sys
import time
from pathlib import Path

import numpy as np

from polar_projector import PolarProjector

BENCH_DIR = Path(__file__).resolve().parent
DATA_DIR = BENCH_DIR / "data"

SEED = 42
N_INITIAL = 500
BATCH = 250
UMAP_NEIGHBORS = 15
UMAP_MIN_DIST = 0.1
TRUSTWORTHINESS_K = 15


def load_corpus() -> tuple[np.ndarray, list[str]]:
    """Frozen Spinoza embeddings in reading order, with their part labels."""
    vectors = np.load(DATA_DIR / "embeddings.npy").astype(np.float64)
    labels = json.loads((DATA_DIR / "labels.json").read_text(encoding="utf-8"))
    if len(labels) != vectors.shape[0]:
        raise SystemExit(
            f"ERR: {vectors.shape[0]} vectors but {len(labels)} labels — "
            "the frozen artifact is inconsistent; re-run the freezer."
        )
    return vectors, [entry["part"] for entry in labels]


def growth_schedule(n_total: int) -> list[int]:
    """Corpus sizes at each step: reading order, so parts arrive in sequence."""
    sizes = list(range(N_INITIAL, n_total, BATCH))
    sizes.append(n_total)
    return sizes


def rms_radius(coords: np.ndarray) -> float:
    """Scale of an embedding: RMS distance of its points from their centroid."""
    centered = coords - coords.mean(axis=0)
    return float(np.sqrt(np.mean(np.sum(centered**2, axis=1))))


def align_similarity(source: np.ndarray, target: np.ndarray) -> np.ndarray:
    """Map `source` onto `target` by the best translation + rotation + scale.

    Full Procrustes. Removes exactly the degrees of freedom a layout algorithm
    leaves undetermined, so what remains is displacement the algorithm actually
    chose rather than an arbitrary global reorientation.
    """
    src_c = source - source.mean(axis=0)
    tgt_c = target - target.mean(axis=0)

    u, s, vt = np.linalg.svd(src_c.T @ tgt_c)
    rotation = u @ vt

    src_norm = float(np.sum(src_c**2))
    scale = float(np.sum(s)) / src_norm if src_norm > 0.0 else 1.0

    return scale * (src_c @ rotation) + target.mean(axis=0)


def displacement_stats(previous: np.ndarray, current: np.ndarray) -> dict[str, float]:
    """Per-point movement of the shared prefix, raw and Procrustes-aligned.

    Both are normalized by the current embedding's RMS radius, so a value of
    1.0 means points moved as far as the layout is wide.
    """
    n = previous.shape[0]
    shared_now = current[:n]
    scale = rms_radius(current)
    if scale <= 0.0:
        raise ValueError("degenerate embedding: zero radius")

    raw = np.linalg.norm(shared_now - previous, axis=1) / scale
    aligned_prev = align_similarity(previous, shared_now)
    aligned = np.linalg.norm(shared_now - aligned_prev, axis=1) / scale

    return {
        "n_shared": n,
        "raw_p50": float(np.percentile(raw, 50)),
        "raw_p95": float(np.percentile(raw, 95)),
        "raw_max": float(np.max(raw)),
        "aligned_p50": float(np.percentile(aligned, 50)),
        "aligned_p95": float(np.percentile(aligned, 95)),
        "aligned_max": float(np.max(aligned)),
    }


def trustworthiness(high: np.ndarray, low: np.ndarray, k: int) -> float:
    """How well a 2D layout preserves high-dimensional neighborhoods (0..1).

    Quantifies the cost of arm 1's stability: a fit-once model stays perfectly
    still precisely because it stops accounting for what arrived after it.
    """
    from sklearn.manifold import trustworthiness as sk_trustworthiness

    return float(sk_trustworthiness(high, low, n_neighbors=k))


# --- arms -------------------------------------------------------------------


def arm_umap_fit_once(vectors: np.ndarray, sizes: list[int]) -> list[np.ndarray]:
    import umap

    reducer = umap.UMAP(
        n_neighbors=UMAP_NEIGHBORS,
        min_dist=UMAP_MIN_DIST,
        n_components=2,
        random_state=SEED,
    )
    base = reducer.fit_transform(vectors[: sizes[0]])

    out = [np.asarray(base, dtype=np.float64)]
    for size in sizes[1:]:
        new = reducer.transform(vectors[sizes[0] : size])
        out.append(np.vstack([base, np.asarray(new, dtype=np.float64)]))
    return out


def arm_umap_refit(vectors: np.ndarray, sizes: list[int]) -> list[np.ndarray]:
    import umap

    out = []
    for size in sizes:
        reducer = umap.UMAP(
            n_neighbors=UMAP_NEIGHBORS,
            min_dist=UMAP_MIN_DIST,
            n_components=2,
            random_state=SEED,
        )
        out.append(np.asarray(reducer.fit_transform(vectors[:size]), dtype=np.float64))
    return out


def arm_tsne_refit(vectors: np.ndarray, sizes: list[int]) -> list[np.ndarray]:
    from sklearn.manifold import TSNE

    out = []
    for size in sizes:
        tsne = TSNE(n_components=2, random_state=SEED, init="pca")
        out.append(np.asarray(tsne.fit_transform(vectors[:size]), dtype=np.float64))
    return out


def _polar_coords(
    projector: PolarProjector,
    vectors: np.ndarray,
    c_1: np.ndarray,
    c_A: np.ndarray,
    c_B: np.ndarray,
) -> np.ndarray:
    """(lambda, d_esc) for every vector against one prepared frame."""
    frame = projector.prepare(c_1, c_A, c_B)
    coords = np.empty((vectors.shape[0], 2), dtype=np.float64)
    for i, v in enumerate(vectors):
        _, lam, d_esc = projector.evaluate(v, frame, i)
        coords[i] = (lam, d_esc)
    return coords


def _initial_frame(
    vectors: np.ndarray, parts: list[str], size: int
) -> tuple[np.ndarray, np.ndarray]:
    """Dipole poles from the two largest parts present in the initial window."""
    window = parts[:size]
    present = sorted(set(window), key=lambda p: -window.count(p))
    if len(present) < 2:
        raise SystemExit("ERR: initial window spans fewer than two parts")

    pole_a = vectors[:size][[i for i, p in enumerate(window) if p == present[0]]].mean(axis=0)
    pole_b = vectors[:size][[i for i, p in enumerate(window) if p == present[1]]].mean(axis=0)
    return pole_a, pole_b


def arm_polar_fixed(
    vectors: np.ndarray, parts: list[str], sizes: list[int]
) -> list[np.ndarray]:
    projector = PolarProjector()
    c_1 = vectors[: sizes[0]].mean(axis=0)
    c_A, c_B = _initial_frame(vectors, parts, sizes[0])
    return [_polar_coords(projector, vectors[:size], c_1, c_A, c_B) for size in sizes]


def arm_polar_moving(
    vectors: np.ndarray, parts: list[str], sizes: list[int]
) -> list[np.ndarray]:
    """Anchor follows the newest batch: the active context moves as you read."""
    projector = PolarProjector()
    c_A, c_B = _initial_frame(vectors, parts, sizes[0])

    out = []
    previous = 0
    for size in sizes:
        c_1 = vectors[previous:size].mean(axis=0)
        out.append(_polar_coords(projector, vectors[:size], c_1, c_A, c_B))
        previous = size
    return out


ARMS = {
    "umap_fit_once": arm_umap_fit_once,
    "umap_refit": arm_umap_refit,
    "tsne_refit": arm_tsne_refit,
    "polar_fixed": arm_polar_fixed,
    "polar_moving": arm_polar_moving,
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=BENCH_DIR / "results" / "drift.json")
    parser.add_argument("--arms", nargs="*", choices=sorted(ARMS), default=sorted(ARMS))
    args = parser.parse_args()

    vectors, parts = load_corpus()
    sizes = growth_schedule(vectors.shape[0])

    print(f"E1 drift — {vectors.shape[0]} chunks, d={vectors.shape[1]}")
    print(f"growth: {sizes[0]} then +{BATCH} to {sizes[-1]} ({len(sizes)} steps)")
    print(f"host: {platform.platform()} | python {sys.version.split()[0]} | numpy {np.__version__}\n")

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

        steps = [
            {"size": sizes[i], **displacement_stats(embeddings[i - 1], embeddings[i])}
            for i in range(1, len(sizes))
        ]
        fidelity = trustworthiness(vectors, embeddings[-1], TRUSTWORTHINESS_K)

        results[name] = {
            "seconds": elapsed,
            "steps": steps,
            "final_trustworthiness": fidelity,
        }
        worst = max(s["aligned_p95"] for s in steps)
        print(
            f"[{name}] {elapsed:6.1f}s | worst aligned p95 drift {worst:.4f} "
            f"| final trustworthiness {fidelity:.4f}"
        )

    # Aggregated ACROSS steps by median and worst case, never by mean: at least
    # one arm is bimodal over steps (exactly still, then a large relocation),
    # and a mean reports neither of the two things that actually happen.
    print(
        f"\n{'arm':<16}{'median step':>13}{'worst step':>12}{'still steps':>13}{'trust':>9}"
    )
    print("-" * 63)
    for name, res in results.items():
        per_step = [s["aligned_p95"] for s in res["steps"]]
        still = sum(1 for v in per_step if v < 1e-9)
        print(
            f"{name:<16}{float(np.median(per_step)):>13.4f}{max(per_step):>12.4f}"
            f"{still:>8}/{len(per_step):<4}{res['final_trustworthiness']:>9.4f}"
        )
    print("-" * 63)
    print("aligned p95 displacement per growth step, normalized by the embedding's RMS radius")
    print("1.0 = points moved as far as the layout is wide; 'still' = steps under 1e-9")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(
            {
                "config": {
                    "seed": SEED,
                    "n_initial": N_INITIAL,
                    "batch": BATCH,
                    "sizes": sizes,
                    "umap_n_neighbors": UMAP_NEIGHBORS,
                    "umap_min_dist": UMAP_MIN_DIST,
                    "trustworthiness_k": TRUSTWORTHINESS_K,
                },
                "host": {
                    "platform": platform.platform(),
                    "processor": platform.processor(),
                    "python": sys.version.split()[0],
                    "numpy": np.__version__,
                },
                "results": results,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"\nwrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
