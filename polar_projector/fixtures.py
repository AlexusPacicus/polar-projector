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
