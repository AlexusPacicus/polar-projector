"""Generate the Polar Projector delta-sweep table for the manuscript.

Reproduces the same construction as `verify_paper_tables.py` (Appendix C
collinearity scenario, d=384, anchor seed 1, stimulus seeds 1000 + i) at
N = 10,000 stimuli.

The table is exact under those seeds; it is not a population estimate with a
stated error bar. An earlier version quoted a 2-sigma sampling bound of ~2.8%
from the normal-theory formula SE(sigma2) ~= sigma2 * sqrt(2/(N-1)), which does
not hold here: d_esc is heavy-tailed (kurtosis roughly 8-14 across the rows), and
the general formula sqrt((kappa - 1)/N) roughly doubles that bound. This script
prints the excess-kurtosis-aware bound per row so the size of the sampling error
is visible, but the manuscript does not rely on it.
"""


import numpy as np

from polar_projector import PolarProjector
from polar_projector.fixtures import collinear_centroids, random_unit_vector

D = 384
N_VECTORS = 10_000
DELTAS = (0.001, 0.010, 0.050, 0.100, 0.200, 0.500)


def _measure(delta: float) -> tuple[float, float, float, float]:
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
    return sigma2_lambda, sigma2_esc, sigma2_lambda / sigma2_esc, _variance_bound(d_escs)


def _variance_bound(x: np.ndarray) -> float:
    """2-sigma relative sampling bound on var(x) without assuming normality: 2*sqrt((kappa-1)/N)."""
    centred = x - x.mean()
    kurtosis = float(np.mean(centred**4) / np.mean(centred**2) ** 2)
    return 2.0 * ((kurtosis - 1.0) / x.size) ** 0.5


def main() -> int:
    print(f"Polar Projector delta-sweep table ({D}D, N={N_VECTORS}, anchor seed 1, stimulus seeds 1000+i)\n")
    print(f"{'delta':<8}{'sigma2_lambda':<16}{'sigma2_esc':<16}{'R':<12}{'2-sigma bound on sigma2_esc':<12}")
    print("-" * 80)
    for delta in DELTAS:
        s_l, s_e, r, bound = _measure(delta)
        print(f"{delta:<8.3f}{s_l:<16.6e}{s_e:<16.6e}{r:<12.2f}{bound:.1%}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
