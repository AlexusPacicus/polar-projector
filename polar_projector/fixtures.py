"""Deterministic constructions defining the manuscript's experimental setups.

Shipped with the package rather than kept in the test tree: reproducing the
paper's numerical sections must work from an installed distribution, without
cloning the repository or bootstrapping sys.path. Every function is a pure
function of its seed.
"""

import numpy as np
from numpy.typing import NDArray


def random_unit_vector(d: int, seed: int) -> NDArray[np.float64]:
    """Draw one L2-normalized vector on S^(d-1) from a seeded generator."""
    rng = np.random.default_rng(seed)
    v = rng.normal(size=d).astype(np.float64)
    return v / np.linalg.norm(v)


def collinear_centroids(
    anchor: NDArray[np.float64], d: int
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Build dipole poles collinear with the anchor, so both projections vanish.

    This is the degenerate case Proposition 2's canonical fallback exists for,
    and the setup behind the delta-sweep of manuscript section 3.3.
    """
    c_A = anchor * 1.5
    c_B = anchor * -0.7
    return c_A.astype(np.float64), c_B.astype(np.float64)


def simulate_drift_trajectory(
    steps: int, d: int, drift_rate: float, seed: int = 42
) -> list[NDArray[np.float64]]:
    """Random walk on S^(d-1): additive noise renormalized back onto the sphere."""
    rng = np.random.default_rng(seed)
    trajectory = []
    v = random_unit_vector(d, seed)
    for _ in range(steps):
        trajectory.append(v.copy())
        noise = rng.normal(scale=drift_rate, size=d).astype(np.float64)
        v = v + noise
        v = v / np.linalg.norm(v)
    return trajectory


def near_collinear_stimulus(
    c_1: NDArray[np.float64],
    c1_hat: NDArray[np.float64],
    v_dipole: NDArray[np.float64],
    ratio: float,
    seed: int = 77,
) -> tuple[NDArray[np.float64], float]:
    """Stimulus lying almost entirely along the dipole axis, with a known residual.

    Builds v_n = c_1 + alpha*v_hat + eps*w, where w is orthogonal to both the
    normalized anchor and the dipole direction. The orthogonal residual of the
    result is therefore exactly eps, analytically rather than to within the
    precision of whatever computed it -- which is what lets the two algebraic
    forms of d_esc be scored against a truth instead of against each other.

    alpha is fixed at half the dipole norm, keeping |lambda| = 0.5 and away from
    the clip, so the measurement isolates conditioning from saturation.

    This is the construction behind manuscript section 3.2. It ships with the
    package, rather than living in the benchmark scripts, so that section
    reproduces from an installed distribution.

    Args:
        c_1: Anchor centroid (d,).
        c1_hat: Normalized anchor, as prepare() computes it (d,).
        v_dipole: Dipole vector from a prepared frame (d,).
        ratio: Target d_esc / ||r||, approached from above as ratio -> 0.
        seed: Seed for the orthogonal perturbation direction.

    Returns:
        Tuple (v_n, d_esc_exact).
    """
    d = c_1.shape[0]
    v_norm = float(np.sqrt(np.dot(v_dipole, v_dipole)))
    v_hat = v_dipole / v_norm

    w = random_unit_vector(d, seed)
    w = w - np.dot(w, c1_hat) * c1_hat
    w = w - np.dot(w, v_hat) * v_hat
    w = w / np.linalg.norm(w)

    alpha = 0.5 * v_norm
    eps = alpha * ratio
    return c_1 + alpha * v_hat + eps * w, eps
