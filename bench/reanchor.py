"""E7 — Local fidelity under re-anchoring: the thing only a local frame can do.

E1 and E5 both evaluate a single static layout, which is the one regime where a
fixed linear map competes on equal terms: pca_fit_once matches or beats the
operator there (bench/results/drift.json, frame_sensitivity.json). Neither
instrument touches what separates them. A fixed map has exactly one view of the
corpus, for every query, forever. The operator's coordinates are anchor-relative,
so moving the active context yields a different view -- and re-anchoring costs a
K-way codebook scan and one prepare(), O(K*d), with no corpus access.

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

Cost columns
------------
Each column times the same operation for every arm, and a structural zero is
written as 0.0 only where the arm does no such work by construction:

  build_us            once over the corpus, before any query: the global PCA's
                      SVD, the published frame's window mean, part centroids and
                      prepare(), the re-anchoring codebook's k-means. Zero for
                      pca_local and radial_plain, which build nothing corpus-wide.
  query_frame_us      once per query, before any point is placed: pca_local's
                      nearest-neighbour scan plus its SVD, polar_reanchored's
                      codebook scan plus prepare(). Zero for the single-view arms,
                      whose view does not depend on the query, and for
                      radial_plain, whose frame is the query vector itself.
  per_stimulus_us     placing one vector in a view that already exists, through
                      each arm's scalar path, returning two Python floats. The
                      stimuli are every corpus vector, against the first query's
                      view for the per-query arms.
  view_vectorized_us  one full view refresh for one query: query_frame_us plus
                      placing all N points as a single array operation
                      (matrix product, evaluate_batch(), or a vectorized norm).
  view_scalar_us      the same refresh placing the N points one at a time
                      through the per_stimulus_us bodies, as the recall loop
                      below does for the operator.

An earlier version of this script mixed these in one frame_us column -- frame plus
full view for the PCA arms and the published frame, frame alone for the
re-anchored arm, the neighbour scan left out of pca_local, and a hand-written 0
for radial_plain -- so ratios read off that column compared different operations.
Timings follow bench/_harness.py: interleaved arms, rotated order, median across
repetitions, peak-to-peak spread recorded.

Deterministic recalls, offline. numpy only; the PCA arms use numpy's SVD.

Usage:
    python bench/reanchor.py
    python bench/reanchor.py --queries 50 --out bench/results/reanchor.json
"""

import argparse
from pathlib import Path

import numpy as np
from _harness import (
    RESULTS_DIR,
    SEED,
    dipole_poles,
    interleave,
    load_corpus,
    print_header,
    write_result,
)

from polar_projector import PolarFrame, PolarProjector

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


def pca_fit(fit_on: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Centre and the (d, 2) matrix of the first two principal directions."""
    centre = fit_on.mean(axis=0)
    _, _, vt = np.linalg.svd(fit_on - centre, full_matrices=False)
    return centre, vt[:2].T


def pca_project(fit_on: np.ndarray, apply_to: np.ndarray) -> np.ndarray:
    centre, comps = pca_fit(fit_on)
    return (apply_to - centre) @ comps


def radial_direction(d: int) -> np.ndarray:
    """The fixed arbitrary unit vector of radial_plain's horizontal axis."""
    e = np.random.default_rng(SEED + 1).standard_normal(d)
    return e / np.linalg.norm(e)


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


STRUCTURAL_ZERO = {
    "build_us": ("pca_local", "radial_plain"),
    "query_frame_us": ("pca_global", "polar_published", "radial_plain"),
}
ARMS = ("pca_global", "polar_published", "pca_local", "polar_reanchored", "radial_plain")
COLUMNS = ("build_us", "query_frame_us", "per_stimulus_us", "view_vectorized_us", "view_scalar_us")


def measure_costs(
    vectors: np.ndarray, parts: list[str], queries: list[int], reps: int
) -> dict[str, dict[str, dict[str, float]]]:
    """Every cost column of the module docstring, per arm: {column: aggregate}."""
    n = vectors.shape[0]
    projector = PolarProjector()
    window, window_parts = vectors[:N_INITIAL], parts[:N_INITIAL]
    e = radial_direction(vectors.shape[1])

    # --- what each arm holds once built ------------------------------------
    centre_g, comps_g = pca_fit(vectors)
    frame_pub = projector.prepare(window.mean(axis=0), *dipole_poles(window, window_parts))
    codebook = build_codebook(vectors, CODEBOOK_K)

    def frame_pca_local(i: int) -> tuple[np.ndarray, np.ndarray]:
        return pca_fit(vectors[true_neighbours(vectors, queries[i], LOCAL_M)])

    def frame_reanchored(i: int) -> PolarFrame:
        v = vectors[queries[i]]
        order = np.argsort(((codebook - v) ** 2).sum(axis=1))
        return projector.prepare(v, codebook[order[0]], codebook[order[1]])

    # --- per-stimulus bodies, shared by per_stimulus_us and view_scalar_us --
    def place_pca(v: np.ndarray, centre: np.ndarray, comps: np.ndarray) -> tuple[float, float]:
        x = (v - centre) @ comps
        return float(x[0]), float(x[1])

    def place_polar(v: np.ndarray, frame: PolarFrame) -> tuple[float, float]:
        _, lam, d_esc = projector.evaluate(v, frame, 0)
        return lam, d_esc

    def place_radial(v: np.ndarray, q: np.ndarray) -> tuple[float, float]:
        delta = v - q
        return float(delta @ e), float(np.linalg.norm(delta))

    costs: dict[str, dict[str, dict[str, float]]] = {arm: {} for arm in ARMS}
    zero = {"mean": 0.0, "p50": 0.0, "p95": 0.0, "p99": 0.0, "min": 0.0, "spread": 0.0,
            "reps": 0.0}

    print("timing build_us")
    built = interleave(
        {
            "pca_global": lambda _i: pca_fit(vectors),
            "polar_published": lambda _i: projector.prepare(
                window.mean(axis=0), *dipole_poles(window, window_parts)
            ),
            "polar_reanchored": lambda _i: build_codebook(vectors, CODEBOOK_K),
        },
        1, reps=reps, warmup=1,
    )

    print("timing query_frame_us")
    framed = interleave(
        {"pca_local": frame_pca_local, "polar_reanchored": frame_reanchored},
        len(queries), reps=reps, warmup=len(queries),
    )

    print("timing per_stimulus_us")
    q0 = vectors[queries[0]]
    centre_l0, comps_l0 = frame_pca_local(0)
    frame_re0 = frame_reanchored(0)
    placed = interleave(
        {
            "pca_global": lambda i: place_pca(vectors[i], centre_g, comps_g),
            "polar_published": lambda i: place_polar(vectors[i], frame_pub),
            "pca_local": lambda i: place_pca(vectors[i], centre_l0, comps_l0),
            "polar_reanchored": lambda i: place_polar(vectors[i], frame_re0),
            "radial_plain": lambda i: place_radial(vectors[i], q0),
        },
        n, reps=reps, warmup=1000,
    )

    print("timing view_vectorized_us")

    def view_pca_local(i: int) -> np.ndarray:
        centre, comps = frame_pca_local(i)
        return (vectors - centre) @ comps

    def view_radial(i: int) -> np.ndarray:
        delta = vectors - vectors[queries[i]]
        return np.stack([delta @ e, np.linalg.norm(delta, axis=1)], axis=1)

    vectorized = interleave(
        {
            "pca_global": lambda _i: (vectors - centre_g) @ comps_g,
            "polar_published": lambda _i: projector.evaluate_batch(vectors, frame_pub),
            "pca_local": view_pca_local,
            "polar_reanchored": lambda i: projector.evaluate_batch(vectors, frame_reanchored(i)),
            "radial_plain": view_radial,
        },
        len(queries), reps=reps, warmup=len(queries),
    )

    print("timing view_scalar_us")

    def scalar_pca_local(i: int) -> list[tuple[float, float]]:
        centre, comps = frame_pca_local(i)
        return [place_pca(v, centre, comps) for v in vectors]

    def scalar_reanchored(i: int) -> list[tuple[float, float]]:
        frame = frame_reanchored(i)
        return [place_polar(v, frame) for v in vectors]

    def scalar_radial(i: int) -> list[tuple[float, float]]:
        q = vectors[queries[i]]
        return [place_radial(v, q) for v in vectors]

    scalar = interleave(
        {
            "pca_global": lambda _i: [place_pca(v, centre_g, comps_g) for v in vectors],
            "polar_published": lambda _i: [place_polar(v, frame_pub) for v in vectors],
            "pca_local": scalar_pca_local,
            "polar_reanchored": scalar_reanchored,
            "radial_plain": scalar_radial,
        },
        len(queries), reps=reps, warmup=5,
    )

    for arm in ARMS:
        costs[arm]["build_us"] = built.get(arm, zero)
        costs[arm]["query_frame_us"] = framed.get(arm, zero)
        costs[arm]["per_stimulus_us"] = placed[arm]
        costs[arm]["view_vectorized_us"] = vectorized[arm]
        costs[arm]["view_scalar_us"] = scalar[arm]
    return costs


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--queries", type=int, default=50)
    parser.add_argument("--reps", type=int, default=5)
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

    # --- recalls: single-view arms, one layout serves every query ----------
    coords_pca_global = pca_project(vectors, vectors)
    pole_a, pole_b = dipole_poles(vectors[:N_INITIAL], parts[:N_INITIAL])
    coords_polar_pub = polar_view(
        projector, vectors, vectors[:N_INITIAL].mean(axis=0), pole_a, pole_b
    )
    scores: dict[str, list[float]] = {
        "pca_global": [local_recall(coords_pca_global, q, truths[q], K_RECALL) for q in queries],
        "polar_published": [local_recall(coords_polar_pub, q, truths[q], K_RECALL) for q in queries],
    }

    # --- recalls: per-query arms --------------------------------------------
    codebook = build_codebook(vectors, CODEBOOK_K)
    radial_dir = radial_direction(vectors.shape[1])
    reanchored, pca_local_scores, radial_scores = [], [], []
    for q in queries:
        # arm 3: anchor on the note itself, poles from the bounded codebook
        order = np.argsort(((codebook - vectors[q]) ** 2).sum(axis=1))
        frame_poles = (codebook[order[0]], codebook[order[1]])
        reanchored.append(
            local_recall(
                polar_view(projector, vectors, vectors[q], *frame_poles), q, truths[q], K_RECALL
            )
        )
        # arm 4: a linear map refit on the query's own neighbourhood
        nb = true_neighbours(vectors, q, LOCAL_M)
        pca_local_scores.append(local_recall(pca_project(vectors[nb], vectors), q, truths[q], K_RECALL))
        # arm 5: radial distance from the query plus one arbitrary angle
        delta = vectors - vectors[q]
        radial = np.stack([delta @ radial_dir, np.linalg.norm(delta, axis=1)], axis=1)
        radial_scores.append(local_recall(radial, q, truths[q], K_RECALL))

    scores["polar_reanchored"] = reanchored
    scores["pca_local"] = pca_local_scores
    scores["radial_plain"] = radial_scores

    results: dict[str, dict[str, object]] = {
        name: {
            "mean_recall": float(np.mean(v)),
            "median_recall": float(np.median(v)),
            "min_recall": float(np.min(v)),
            "max_recall": float(np.max(v)),
        }
        for name, v in scores.items()
    }

    # --- costs: one operation per column, identical across arms -------------
    costs = measure_costs(vectors, parts, queries, args.reps)
    for arm in ARMS:
        for column in COLUMNS:
            results[arm][column] = costs[arm][column]["mean"]
        results[arm]["timing"] = costs[arm]

    print(f"\n{'arm':<18}{'mean':>7}{'build us':>11}{'query us':>10}{'stim us':>9}"
          f"{'view vec us':>13}{'view scalar us':>16}")
    print("-" * 84)
    for name in ARMS:
        r = results[name]
        print(
            f"{name:<18}{r['mean_recall']:>7.3f}{r['build_us']:>11.1f}{r['query_frame_us']:>10.1f}"
            f"{r['per_stimulus_us']:>9.2f}{r['view_vectorized_us']:>13.1f}{r['view_scalar_us']:>16.1f}"
        )
    print("-" * 84)
    print(f"local recall@{K_RECALL} of the source-space neighbourhood; chance "
          f"{K_RECALL / (n - 1):.4f}. Columns: see the module docstring.")

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
            "timing_reps": args.reps,
            "structural_zero": {k: list(v) for k, v in STRUCTURAL_ZERO.items()},
        },
        results=results,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
