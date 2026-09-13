"""E7 — Local fidelity under re-anchoring: the thing only a local frame can do.

E1 and E5 both evaluate a single static layout, which is the one regime where a
fixed linear map competes on equal terms: pca_fit_once matches or beats the
operator there (bench/results/drift.json, frame_sensitivity.json). Neither
instrument touches what separates them. A fixed map has exactly one view of the
corpus, for every query, forever. The operator's coordinates are anchor-relative,
so moving the active context yields a different view -- and re-anchoring costs one
prepare(), O(d), with no corpus access.

This measures whether that buys fidelity where the user is standing.

Instrument
----------
For each of M sampled query chunks q, local recall@15: of q's 15 true nearest
neighbours in the source 384-d space, how many are among q's 15 nearest in the
arm's 2D view, with all 2,221 points placed in that view. Chance is 15/2220 ~
0.007, so these are raw recalls rather than lifts -- "of the fifteen notes really
closest to this one, how many land next to it on screen".

Arms
----
1. pca_global        one PCA fit on the whole corpus. The strongest single-view
                     fixed baseline, and deliberately generous: it sees
                     everything, where the operator sees one frame.
2. polar_published    the single frame §3.2/§3.3 publish, reused for every query.
                     Isolates how much of the operator's result is anchoring
                     rather than the operator.
3. polar_reanchored  c_1 = q itself, poles = the two nearest entries of a bounded
                     codebook built once over the corpus (K = 16, k-means).
4. pca_local         PCA refit on q's 100 true nearest neighbours, per query.
5. radial_plain      (<v - q, e>, ||v - q||) for a fixed random unit e.

Arm 5 is the control that decides how much of arm 3 is the operator. With
c_1 = q, d_esc is the norm of the anchor-projected residual -- close to radial
distance from the query -- so a coordinate system whose vertical axis is simply
||v - q|| might do just as well. If it does, the finding is "use a query-centric
radial coordinate", which is a design insight but not one this construction owns.
If it does not, the difference is what anchor removal and the contrast axis add
on top of distance. Either way it is the same discipline the fixed linear arms of
bench/drift.py apply to the stability claim.

Arm 4 is the honest control and the expensive one. If a locally refitted linear
map matches arm 3, then re-anchoring is not special to this operator -- "use a
local model" is, and a local PCA is one. The difference the paper can claim is
then cost and access, not fidelity, so both are reported: arm 3 needs one
prepare() and a K-way codebook scan, while arm 4 needs q's neighbourhood
materialized, which is a corpus query the operator's O(1)-in-N claim excludes.

Nothing here leaks at query time. The codebook of arm 3 is built once, like
fitting PCA once, and per-query pole selection is the O(K*d) codebook scan
Proposition 1 already accounts for.

Deterministic, offline. numpy only; the PCA arms use numpy's SVD.

Usage:
    python bench/reanchor.py
    python bench/reanchor.py --queries 50 --out bench/results/reanchor.json
"""

import argparse
import time
from pathlib import Path

import numpy as np
from _harness import RESULTS_DIR, SEED, dipole_poles, load_corpus, print_header, write_result

from polar_projector import PolarProjector

K_RECALL = 15
LOCAL_M = 100
CODEBOOK_K = 16
N_INITIAL = 500


def true_neighbours(vectors: np.ndarray, index: int, k: int) -> np.ndarray:
    """Indices of the k nearest vectors to `index` in the source space."""
    d = ((vectors - vectors[index]) ** 2).sum(axis=1)
    d[index] = np.inf
    return np.argpartition(d, k)[:k]


def local_recall(coords: np.ndarray, index: int, truth: np.ndarray, k: int) -> float:
    d = ((coords - coords[index]) ** 2).sum(axis=1)
    d[index] = np.inf
    got = np.argpartition(d, k)[:k]
    return len(set(got.tolist()) & set(truth.tolist())) / k


def pca_project(fit_on: np.ndarray, apply_to: np.ndarray) -> np.ndarray:
    centre = fit_on.mean(axis=0)
    _, _, vt = np.linalg.svd(fit_on - centre, full_matrices=False)
    return (apply_to - centre) @ vt[:2].T


def build_codebook(vectors: np.ndarray, k: int) -> np.ndarray:
    """k-means over the corpus, deterministic farthest-point init. Built once."""
    centre = vectors.mean(axis=0)
    picked = [int(np.argmax(((vectors - centre) ** 2).sum(axis=1)))]
    for _ in range(k - 1):
        d = np.min(
            np.stack([((vectors - vectors[p]) ** 2).sum(axis=1) for p in picked]), axis=0
        )
        picked.append(int(np.argmax(d)))
    book = vectors[picked].copy()
    for _ in range(32):
        assign = np.argmin(
            np.stack([((vectors - c) ** 2).sum(axis=1) for c in book]), axis=0
        )
        nxt = np.stack(
            [vectors[assign == i].mean(axis=0) if (assign == i).any() else book[i] for i in range(k)]
        )
        if np.allclose(nxt, book):
            break
        book = nxt
    return book


def polar_view(
    projector: PolarProjector, vectors: np.ndarray, c_1: np.ndarray, c_A: np.ndarray, c_B: np.ndarray
) -> np.ndarray:
    frame = projector.prepare(c_1, c_A, c_B)
    out = np.empty((vectors.shape[0], 2))
    for i, v in enumerate(vectors):
        _, lam, esc = projector.evaluate(v, frame, i)
        out[i] = (lam, esc)
    return out


X_SCALES = (0.1, 0.25, 0.5, 1.0, 2.0)


def ablate(vectors: np.ndarray, queries: list[int], out: Path) -> int:
    """Which part of the re-anchored operator costs local recall?

    Exploratory, specified after the E7 table existed. The manuscript first
    attributed the gap to radial_plain to d_esc discarding distance and to the
    clamp on lambda; this removes one piece at a time, on the same queries and the
    same codebook frames, to test that. Recalls only -- no timings -- so it writes
    its own artifact and leaves reanchor.json's measured latencies untouched.

    Views, all from the frame polar_reanchored uses:
      operator                (lambda, d_esc)               the arm itself
      unclamped               (lambda*, ||r - lambda* v||)  clamp removed
      lambda_residual_norm    (lambda, ||r||)               dipole not regressed out
      residual_norm_only      (0, ||r||)                    horizontal axis removed
      d_esc_only              (0, d_esc)
      x_scale_<s>             (s * lambda, d_esc)           the S_x / S_y ratio of §2.1
      isometric               (||v_dipole|| * lambda, d_esc)
                              lambda back in length units, so by Proposition 3 the
                              view distance from q is ||r|| wherever lambda is
                              unsaturated
    """
    projector = PolarProjector()
    codebook = build_codebook(vectors, CODEBOOK_K)
    n = vectors.shape[0]
    names = ["operator", "unclamped", "lambda_residual_norm", "residual_norm_only", "d_esc_only"]
    names += [f"x_scale_{s}" for s in X_SCALES] + ["isometric"]
    scores: dict[str, list[float]] = {name: [] for name in names}
    dipole_norms: list[float] = []
    saturated: list[float] = []

    for q in queries:
        truth = true_neighbours(vectors, q, K_RECALL)
        order = np.argsort(((codebook - vectors[q]) ** 2).sum(axis=1))
        frame = projector.prepare(vectors[q], codebook[order[0]], codebook[order[1]])
        view = polar_view(projector, vectors, vectors[q], codebook[order[0]], codebook[order[1]])
        lam, d_esc = view[:, 0], view[:, 1]

        r = vectors - frame.c_1
        r -= (r @ frame.c1_hat)[:, None] * frame.c1_hat
        lam_star = (r @ frame.v_dipole) / frame.v_dipole_norm_sq
        r_norm = np.linalg.norm(r, axis=1)
        zeros = np.zeros(n)

        views = {
            "operator": view,
            "unclamped": np.c_[
                lam_star, np.linalg.norm(r - lam_star[:, None] * frame.v_dipole, axis=1)
            ],
            "lambda_residual_norm": np.c_[lam, r_norm],
            "residual_norm_only": np.c_[zeros, r_norm],
            "d_esc_only": np.c_[zeros, d_esc],
        }
        views.update({f"x_scale_{s}": np.c_[s * lam, d_esc] for s in X_SCALES})
        dipole_norm = float(np.sqrt(frame.v_dipole_norm_sq))
        views["isometric"] = np.c_[dipole_norm * lam, d_esc]
        dipole_norms.append(dipole_norm)
        saturated.append(float(np.mean(np.abs(lam_star) > 1.0)))
        for name, coords in views.items():
            scores[name].append(local_recall(coords, q, truth, K_RECALL))

    results: dict[str, dict[str, float]] = {
        name: {"mean_recall": float(np.mean(v)), "median_recall": float(np.median(v))}
        for name, v in scores.items()
    }
    results["frame"] = {
        "dipole_norm_median": float(np.median(dipole_norms)),
        "dipole_norm_min": float(np.min(dipole_norms)),
        "dipole_norm_max": float(np.max(dipole_norms)),
        "saturated_fraction_median": float(np.median(saturated)),
    }
    print(f"{'view':<24}{'mean':>8}{'median':>9}")
    print("-" * 41)
    for name in names:
        r_ = results[name]
        print(f"{name:<24}{r_['mean_recall']:>8.3f}{r_['median_recall']:>9.3f}")
    print(f"\n||v_dipole|| median {results['frame']['dipole_norm_median']:.3f} "
          f"[{results['frame']['dipole_norm_min']:.3f}, {results['frame']['dipole_norm_max']:.3f}]"
          f" | saturated fraction median {results['frame']['saturated_fraction_median']:.3f}")

    write_result(
        out,
        experiment="E7-ablation",
        config={"seed": SEED, "queries": queries, "k_recall": K_RECALL,
                "codebook_k": CODEBOOK_K, "x_scales": list(X_SCALES)},
        results=results,
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--queries", type=int, default=50)
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument(
        "--ablation", action="store_true",
        help="decompose the re-anchored arm instead of running the five-arm table",
    )
    args = parser.parse_args()

    vectors, parts = load_corpus()
    n = vectors.shape[0]
    rng = np.random.default_rng(SEED)
    queries = sorted(rng.choice(n, size=args.queries, replace=False).tolist())

    if args.ablation:
        print_header("E7 ablation", f"{n} chunks, d={vectors.shape[1]}")
        return ablate(vectors, queries, args.out or RESULTS_DIR / "reanchor_ablation.json")
    args.out = args.out or RESULTS_DIR / "reanchor.json"

    print_header("E7 re-anchoring", f"{n} chunks, d={vectors.shape[1]}")
    print(f"{len(queries)} queries | local recall@{K_RECALL} | chance {K_RECALL / (n - 1):.4f}\n")

    projector = PolarProjector()
    truths = {q: true_neighbours(vectors, q, K_RECALL) for q in queries}

    # --- single-view arms: one layout serves every query -------------------
    t0 = time.perf_counter()
    coords_pca_global = pca_project(vectors, vectors)
    cost_pca_global = time.perf_counter() - t0

    pole_a, pole_b = dipole_poles(vectors[:N_INITIAL], parts[:N_INITIAL])
    t0 = time.perf_counter()
    coords_polar_pub = polar_view(
        projector, vectors, vectors[:N_INITIAL].mean(axis=0), pole_a, pole_b
    )
    cost_polar_pub = time.perf_counter() - t0

    scores: dict[str, list[float]] = {
        "pca_global": [local_recall(coords_pca_global, q, truths[q], K_RECALL) for q in queries],
        "polar_published": [local_recall(coords_polar_pub, q, truths[q], K_RECALL) for q in queries],
    }

    # --- per-query arms ----------------------------------------------------
    codebook = build_codebook(vectors, CODEBOOK_K)
    reanchored, pca_local_scores, radial_scores = [], [], []
    setup_polar, setup_pca, setup_radial = [], [], []
    radial_dir = np.random.default_rng(SEED + 1).standard_normal(vectors.shape[1])
    radial_dir /= np.linalg.norm(radial_dir)
    for q in queries:
        # arm 3: anchor on the note itself, poles from the bounded codebook
        t0 = time.perf_counter()
        order = np.argsort(((codebook - vectors[q]) ** 2).sum(axis=1))
        frame_poles = (codebook[order[0]], codebook[order[1]])
        projector.prepare(vectors[q], *frame_poles)
        setup_polar.append(time.perf_counter() - t0)
        reanchored.append(
            local_recall(
                polar_view(projector, vectors, vectors[q], *frame_poles), q, truths[q], K_RECALL
            )
        )
        # arm 4: a linear map refit on the query's own neighbourhood
        nb = true_neighbours(vectors, q, LOCAL_M)
        t0 = time.perf_counter()
        coords = pca_project(vectors[nb], vectors)
        setup_pca.append(time.perf_counter() - t0)
        pca_local_scores.append(local_recall(coords, q, truths[q], K_RECALL))
        # arm 5: radial distance from the query plus one arbitrary angle
        t0 = time.perf_counter()
        delta = vectors - vectors[q]
        radial = np.stack([delta @ radial_dir, np.linalg.norm(delta, axis=1)], axis=1)
        setup_radial.append(time.perf_counter() - t0)
        radial_scores.append(local_recall(radial, q, truths[q], K_RECALL))

    scores["polar_reanchored"] = reanchored
    scores["pca_local"] = pca_local_scores
    scores["radial_plain"] = radial_scores

    results = {
        name: {
            "mean_recall": float(np.mean(v)),
            "median_recall": float(np.median(v)),
            "min_recall": float(np.min(v)),
            "max_recall": float(np.max(v)),
        }
        for name, v in scores.items()
    }
    results["polar_reanchored"]["frame_us"] = float(np.median(setup_polar)) * 1e6
    results["pca_local"]["frame_us"] = float(np.median(setup_pca)) * 1e6
    results["radial_plain"]["frame_us"] = 0.0  # no frame to build
    results["pca_global"]["frame_us"] = cost_pca_global * 1e6
    results["polar_published"]["frame_us"] = cost_polar_pub * 1e6

    # Per-stimulus cost, measured identically for every arm: place one further
    # vector given a frame that already exists. Comparing frame-construction
    # times would compare different operations -- a one-off global fit against a
    # per-query re-prepare -- and would flatter whichever arm was asked to do less.
    q0 = queries[0]
    probe = vectors[q0]
    frame_pub = projector.prepare(vectors[:N_INITIAL].mean(axis=0), pole_a, pole_b)
    book_order = np.argsort(((codebook - probe) ** 2).sum(axis=1))
    frame_re = projector.prepare(probe, codebook[book_order[0]], codebook[book_order[1]])
    centre_g = vectors.mean(axis=0)
    _, _, vt_g = np.linalg.svd(vectors - centre_g, full_matrices=False)
    comps = vt_g[:2].T

    def _time(fn, reps: int = 2000) -> float:
        fn()
        t_start = time.perf_counter()
        for _ in range(reps):
            fn()
        return (time.perf_counter() - t_start) / reps * 1e6

    per_stimulus = {
        "pca_global": _time(lambda: (probe - centre_g) @ comps),
        "polar_published": _time(lambda: projector.evaluate(probe, frame_pub, 0)),
        "polar_reanchored": _time(lambda: projector.evaluate(probe, frame_re, 0)),
        "pca_local": _time(lambda: (probe - centre_g) @ comps),
        "radial_plain": _time(
            lambda: (float(np.dot(probe - probe, radial_dir)), float(np.linalg.norm(probe - probe)))
        ),
    }
    for name, us in per_stimulus.items():
        results[name]["per_stimulus_us"] = us

    print(f"{'arm':<20}{'mean':>8}{'median':>9}{'min':>8}{'max':>8}"
          f"{'frame us':>11}{'per-stim us':>13}")
    print("-" * 79)
    for name in ("pca_global", "polar_published", "pca_local", "polar_reanchored",
                 "radial_plain"):
        r = results[name]
        print(
            f"{name:<20}{r['mean_recall']:>8.3f}{r['median_recall']:>9.3f}"
            f"{r['min_recall']:>8.3f}{r['max_recall']:>8.3f}"
            f"{r['frame_us']:>11.1f}{r['per_stimulus_us']:>13.2f}"
        )
    print("-" * 79)
    print(f"local recall@{K_RECALL} of the source-space neighbourhood; chance "
          f"{K_RECALL / (n - 1):.4f}")
    print("frame us: building one view. per-stim us: placing one further vector in a view that")
    print("already exists -- the same operation for every arm, which is the comparison the")
    print("paper's O(d) claim is about. pca_local additionally needs the query's neighbourhood")
    print("materialized, a corpus query none of the other arms makes.")

    write_result(
        args.out,
        experiment="E7",
        config={
            "seed": SEED,
            "queries": queries,
            "k_recall": K_RECALL,
            "local_m": LOCAL_M,
            "codebook_k": CODEBOOK_K,
            "chance": K_RECALL / (n - 1),
        },
        results=results,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
