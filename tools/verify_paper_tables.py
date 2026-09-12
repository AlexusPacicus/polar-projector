"""Verify the numerical tables published in paper/polar-projector-paper.md.

Two tables are guarded, and the build fails if either moves:

  appendix B   conditioning of the orthogonal residual -- relative error of the
               vector and scalar forms against an analytically known residual.
  appendix C   the delta-sweep.

The two need different tolerances, for a reason worth stating. The delta-sweep
reports sample variances, whose sampling error is known in closed form, so a
tight relative band is the right check. Section 3.2 reports floating-point
cancellation error -- a difference of nearly equal quantities. Its *value* is
stable to a few percent on the host that published it, but the quantity itself
is the residue of cancellation and can shift by more than that under a
different BLAS or a different libm. A tight relative band there would fail on
somebody else's machine for no reason. What the guard must actually catch is a
change of regime: someone swapping the vector form for the scalar one moves
these numbers by four orders of magnitude or more. A half-decade band catches
that with room to spare, and is honest about what it can and cannot detect.

Reproduces the §C collinearity scenario on a controlled corpus of 10,000
stimulus vectors in d=384 with a fixed seed (matching
tools/generate_polar_delta_table.py, which produced the published
table), sweeping the constructor scale factor delta in
{0.001, 0.01, 0.05, 0.1, 0.2, 0.5}, and measures:

    sigma2_lambda = var(lambda)      (sample variance)
    sigma2_esc    = var(d_esc)
    R             = sigma2_lambda / sigma2_esc

against the published values. Reports PASS / MISMATCH per cell.
Read-only, offline (numpy only — no substrate dependency).
"""


import json
import math
import statistics
from pathlib import Path

import numpy as np

from polar_projector import PolarProjector
from polar_projector.fixtures import (
    collinear_centroids,
    near_collinear_stimulus,
    random_unit_vector,
)

D = 384
N_VECTORS = 10_000
DELTAS = (0.001, 0.010, 0.050, 0.100, 0.200, 0.500)
RTOL = 0.03  # ~2.8% 2-sigma sampling bound on the variances at N=10,000

# Section 3.2 is checked to within a half-decade: enough to catch a change of
# formulation (which moves it by 4+ orders of magnitude), loose enough to
# survive a different BLAS computing the same cancellation.
LOG_TOL = 0.5

# Published values from §B of paper/polar-projector-paper.md:
# d_esc/||r|| -> (vector-form rel. error, scalar-form rel. error)
PUBLISHED_CONDITIONING = {
    1e-3: (1.2e-14, 1.1e-10),
    1e-5: (1.1e-12, 4.5e-7),
    1e-7: (9.8e-11, 1.2e-3),
    1e-8: (6.7e-10, 1.0e0),
}

# Published values from §C of paper/polar-projector-paper.md.
PUBLISHED = {
    0.001: (9.782e-1, 3.535e-6, 276747.31),
    0.010: (7.994e-1, 3.886e-6, 205690.72),
    0.050: (2.401e-1, 6.651e-6, 36104.25),
    0.100: (6.594e-2, 6.954e-6, 9482.78),
    0.200: (1.649e-2, 6.954e-6, 2370.69),
    0.500: (2.638e-3, 6.954e-6, 379.31),
}


def _measure(delta: float):
    c_1 = random_unit_vector(D, 1)
    c_A, c_B = collinear_centroids(c_1, D)
    projector = PolarProjector(delta=delta)
    lambdas = np.empty(N_VECTORS, dtype=np.float64)
    d_escs = np.empty(N_VECTORS, dtype=np.float64)
    for i in range(N_VECTORS):
        v_n = random_unit_vector(D, 1000 + i)
        _, lam, d_esc = projector.project(v_n, c_1, c_A, c_B, i)
        lambdas[i] = lam
        d_escs[i] = d_esc
    sigma2_lambda = float(np.var(lambdas))
    sigma2_esc = float(np.var(d_escs))
    r = sigma2_lambda / sigma2_esc
    return sigma2_lambda, sigma2_esc, r


def _scalar_form_d_esc(projector: PolarProjector, v_n, frame) -> float:
    """Proposition 3's scalar rearrangement — the arm appendix B rejects.

    Deliberately not in the library (see projector.py, where d_esc is
    computed). Reproduced here so the guard measures the same two arms the
    manuscript compares, on the projector's own helpers.
    """
    r = projector._project_perp(v_n - frame.c_1, frame.c1_hat)
    rv = float(np.dot(r, frame.v_dipole))
    lam = min(max(rv / frame.v_dipole_norm_sq, -1.0), 1.0)  # same clamp as evaluate()
    sq = float(np.dot(r, r)) - 2.0 * lam * rv + lam * lam * frame.v_dipole_norm_sq
    return math.sqrt(sq) if sq > 0.0 else 0.0


def _measure_conditioning(ratio: float) -> tuple[float, float]:
    """Relative error of both forms at one d_esc/||r||, against a known truth."""
    projector = PolarProjector()
    frame = projector.prepare(
        random_unit_vector(D, 1), random_unit_vector(D, 2), random_unit_vector(D, 3)
    )
    v_n, exact = near_collinear_stimulus(frame.c_1, frame.c1_hat, frame.v_dipole, ratio)

    _, _, d_vector = projector.evaluate(v_n, frame, 0)
    d_scalar = _scalar_form_d_esc(projector, v_n, frame)
    return abs(d_vector - exact) / exact, abs(d_scalar - exact) / exact


def _log_status(measured: float, published: float) -> str:
    """PASS when the measured error is within half a decade of the published one."""
    if measured <= 0.0:
        return "PASS" if published <= 0.0 else "MISMATCH"
    return "PASS" if abs(math.log10(measured / published)) <= LOG_TOL else "MISMATCH"


def _verify_conditioning() -> int:
    """Section 3.2. Returns the number of mismatched rows."""
    print(f"§B conditioning of the orthogonal residual ({D}D, exact residual by construction)")
    print(f"tolerance: ±{LOG_TOL} decades per cell\n")
    print(f"{'d_esc/||r||':<14}{'vector(meas)':<16}{'vector(pub)':<15}{'S':<10}"
          f"{'scalar(meas)':<16}{'scalar(pub)':<15}{'S':<10}")
    print("-" * 96)

    failures = 0
    for ratio, (pub_v, pub_s) in PUBLISHED_CONDITIONING.items():
        meas_v, meas_s = _measure_conditioning(ratio)
        s_v, s_s = _log_status(meas_v, pub_v), _log_status(meas_s, pub_s)
        failures += int((s_v, s_s) != ("PASS", "PASS"))
        print(f"{ratio:<14.0e}{meas_v:<16.3e}{pub_v:<15.3e}{s_v:<10}"
              f"{meas_s:<16.3e}{pub_s:<15.3e}{s_s:<10}")
    print("-" * 96)
    return failures


def _status(measured: float, published: float) -> str:
    if published == 0.0:
        return "PASS" if abs(measured) < 1e-12 else "MISMATCH"
    return "PASS" if abs(measured - published) / published <= RTOL else "MISMATCH"



# ---------------------------------------------------------------------------
# Artifact consistency: does the manuscript report the committed benchmark
# artifacts correctly?
#
# This is a WEAKER check than the two above and is labelled as such in the
# output. §B and §C are *recomputed* from the operator on every run. The tables
# below cannot be: §3.2/§3.3 need umap-learn, scikit-learn and minutes of
# compute, so what is checked is that the paper's numbers match the JSON in
# bench/results/. That catches a manuscript drifting away from its own
# measurements — the failure mode that put a 189 us figure in a draft while the
# artifact said 11.75 — but it does not re-derive the artifacts themselves.
#
# Each published value is stored as the STRING the paper prints, and the
# measured value is rounded to that same precision before comparing, so a
# transcription error fails and a rounding difference does not.
# ---------------------------------------------------------------------------

RESULTS = Path(__file__).resolve().parent.parent / "bench" / "results"


def _load(name: str) -> dict:
    with (RESULTS / name).open() as fh:
        return json.load(fh)["results"]


def _agree(measured: float, published: str) -> bool:
    nd = len(published.split(".")[1]) if "." in published else 0
    return round(float(measured), nd) == float(published)


def _p95s(arm: dict) -> list[float]:
    return [s["aligned_p95"] for s in arm["steps"]]


def _artifact_checks() -> list[tuple[str, str, float]]:
    """(label, published-as-printed, measured-from-artifact)."""
    lat = _load("latency.json")
    dec = _load("decompose.json")
    dri = _load("drift.json")
    rec = _load("recall.json")
    out: list[tuple[str, str, float]] = []

    # §3 corpus sweep — the flatness claim
    for n, mean, p95 in [("1000", "11.46", "11.92"), ("2221", "11.61", "11.79"),
                         ("4000", "11.61", "12.21"), ("25000", "11.58", "12.00")]:
        out.append((f"§3  sweep N={n} mean", mean, lat["corpus_size_sweep"][n]["mean"]))
        out.append((f"§3  sweep N={n} p95", p95, lat["corpus_size_sweep"][n]["p95"]))

    # §3.1 cost bracketing
    for arm, mean, p95 in [("random_projection", "1.03", "1.08"),
                           ("multi_anchor_cosine", "1.14", "1.21"),
                           ("polar_evaluate", "4.57", "4.79"),
                           ("polar_project", "11.75", "12.50"),
                           ("sliding_window_pca", "292.55", "316.67")]:
        a = lat["spinoza"]["arms"][arm]
        out.append((f"§3.1 {arm} mean", mean, a["mean"]))
        out.append((f"§3.1 {arm} p95", p95, a["p95"]))
    out.append(("§3.1 prepare() mean", "6.87", dec["prepare_only"]["mean"]))
    out.append(("§3.1 prepare() p95", "7.21", dec["prepare_only"]["p95"]))
    out.append(("§3.1 stateless (decompose)", "11.51", dec["project_stateless"]["mean"]))
    out.append(("§3.1 frame share %", "59.7", dec["frame_share_pct"]))

    # §3.2 positional stability
    for arm, med, worst, still, trust in [
        ("polar_fixed", "0.0000", "0.0000", 7, "0.6639"),
        ("polar_moving", "0.2984", "0.6138", 0, "0.6208"),
        ("umap_fit_once", "0.0000", "1.0725", 5, "0.7681"),
        ("umap_refit", "1.1607", "1.2527", 0, "0.9049"),
        ("tsne_refit", "1.1408", "1.2439", 0, "0.9197"),
    ]:
        p = _p95s(dri[arm])
        out.append((f"§3.2 {arm} median step", med, statistics.median(p)))
        out.append((f"§3.2 {arm} worst step", worst, max(p)))
        out.append((f"§3.2 {arm} still steps", str(still), sum(1 for x in p if x < 1e-9)))
        out.append((f"§3.2 {arm} trustworthiness", trust, dri[arm]["final_trustworthiness"]))

    # §3.3 same-part retrieval
    for arm, med, final, worst in [("polar_fixed", "1.57", "1.59", "1.17"),
                                   ("polar_moving", "1.39", "1.34", "1.17"),
                                   ("umap_fit_once", "1.57", "1.57", "1.12"),
                                   ("umap_refit", "2.05", "2.41", "1.12"),
                                   ("tsne_refit", "2.12", "2.47", "1.10")]:
        L = [s["lift"] for s in rec[arm]["steps"]]
        out.append((f"§3.3 {arm} median lift", med, statistics.median(L)))
        out.append((f"§3.3 {arm} final lift", final, L[-1]))
        out.append((f"§3.3 {arm} worst lift", worst, min(L)))

    # Appendix B extra claims: the cost of refusing the scalar form
    con = _load("conditioning.json")
    out.append(("§B  vector-form mean", "4.56", con["latency"]["vector_form"]["mean"]))
    out.append(("§B  scalar-form mean", "3.10", con["latency"]["scalar_form"]["mean"]))
    out.append(("§B  scalar speedup", "1.47", con["scalar_speedup"]))

    # Appendix D batched throughput
    bat = _load("batched.json")
    for b, loop, batch, speed, vps in [("1", "5.380", "13.874", "0.39", "72075"),
                                       ("4", "5.464", "3.649", "1.50", "274064"),
                                       ("16", "4.689", "1.568", "2.99", "637692"),
                                       ("64", "4.904", "1.102", "4.45", "907198"),
                                       ("256", "4.610", "0.893", "5.16", "1119291"),
                                       ("1024", "4.468", "1.283", "3.48", "779626"),
                                       ("4096", "4.481", "1.624", "2.76", "615720")]:
        s = bat["throughput"][b]
        out.append((f"§D  B={b} scalar loop", loop, s["scalar_loop_us_per_vec"]))
        out.append((f"§D  B={b} evaluate_batch", batch, s["evaluate_batch_us_per_vec"]))
        out.append((f"§D  B={b} speedup", speed, s["speedup"]))
        out.append((f"§D  B={b} vectors/s", vps, s["vectors_per_second"]))
    # the sqrt is free: every measured saving rounds to <= 2%
    for b in ("64", "1024", "4096"):
        out.append((f"§D  sqrt saving B={b} <2%", "0.0",
                    round(bat["sqrt_cost"][b]["saving"], 1)))

    # Appendix A dimension sweep
    for d, ev, floor, ratio in [("16", "4.18", "0.72", "5.78"), ("64", "4.12", "0.74", "5.58"),
                                ("256", "4.54", "0.90", "5.07"), ("384", "4.58", "1.08", "4.25"),
                                ("1024", "5.64", "1.64", "3.43"), ("4096", "11.00", "4.62", "2.38"),
                                ("8192", "25.18", "8.63", "2.92")]:
        s = lat["dimension_sweep"][d]
        out.append((f"§A  d={d} evaluate", ev, s["polar_evaluate"]))
        out.append((f"§A  d={d} floor", floor, s["random_projection"]))
        out.append((f"§A  d={d} ratio", ratio, s["ratio"]))
    return out


def _verify_artifacts() -> int:
    print("\nartifact consistency — manuscript vs committed bench/results/*.json")
    print("(compares reported figures against the stored artifacts; does NOT re-derive them)\n")
    checks = _artifact_checks()
    failures = 0
    for label, published, measured in checks:
        ok = _agree(measured, published)
        failures += int(not ok)
        if not ok:
            print(f"  MISMATCH  {label:34} paper={published:>10}  artifact={measured!r}")
    print(f"  {len(checks) - failures}/{len(checks)} figures agree with their artifact")
    return failures


def main() -> int:
    print("Polar Projector — published table verification\n")
    cond_failures = _verify_conditioning()

    print(f"\n§C delta-sweep ({D}D, {N_VECTORS} vectors, seed=42)")
    print(f"tolerance: {RTOL:.0%} relative per cell\n")
    print(f"{'delta':<7}{'sig2_lam(meas)':<16}{'sig2_lam(pub)':<15}{'S':<9}"
          f"{'sig2_esc(meas)':<15}{'sig2_esc(pub)':<14}{'S':<9}"
          f"{'R(meas)':<12}{'R(pub)':<12}{'S':<9}")
    print("-" * 115)

    failures = 0
    for delta in DELTAS:
        m_l, m_e, m_r = _measure(delta)
        p_l, p_e, p_r = PUBLISHED[delta]
        s_l, s_e, s_r = _status(m_l, p_l), _status(m_e, p_e), _status(m_r, p_r)
        row_fail = (s_l, s_e, s_r) != ("PASS", "PASS", "PASS")
        failures += int(row_fail)
        print(f"{delta:<7.3f}{m_l:<16.6e}{p_l:<15.6e}{s_l:<9}"
              f"{m_e:<15.6e}{p_e:<14.6e}{s_e:<9}"
              f"{m_r:<12.2f}{p_r:<12.2f}{s_r:<9}")

    print("-" * 115)
    print("\nScaling law check: sigma2_esc(0.5)/sigma2_esc(0.1) "
          f"= {_measure(0.5)[1]:.6e}/{_measure(0.1)[1]:.6e} "
          "(paper: 6.954e-6 constant for delta >= 0.100)")
    art_failures = _verify_artifacts()

    total = failures + cond_failures + art_failures
    if total == 0:
        print("\nVerdict: ALL PASS")
    else:
        print(f"\nVerdict: {cond_failures} §B row(s), {failures} §C row(s) and "
              f"{art_failures} artifact figure(s) mismatched")
    return 0 if total == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
