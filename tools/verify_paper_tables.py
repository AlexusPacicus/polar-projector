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


import math

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
    total = failures + cond_failures
    if total == 0:
        print("Verdict: ALL PASS")
    else:
        print(f"Verdict: {cond_failures} §B row(s) and {failures} §C row(s) mismatched")
    return 0 if total == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
