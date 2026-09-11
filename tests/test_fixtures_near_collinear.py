"""Tests for the near-collinear construction behind manuscript section 3.2.

The construction's whole value is that it knows the answer analytically. These
tests check that claim directly -- the returned residual must be the geometry
the constructor promises, not merely whatever the operator happens to compute
from it. A silent break here would not fail any other test; it would just make
section 3.2's conditioning table measure something else.
"""
import numpy as np
import pytest

from polar_projector import PolarProjector
from polar_projector.fixtures import near_collinear_stimulus, random_unit_vector

DIMS = (128, 384, 768)
RATIOS = (1e-1, 1e-3, 1e-6, 1e-9)


def _frame(d: int, projector: PolarProjector):
    c_1 = random_unit_vector(d, 1)
    c_A = random_unit_vector(d, 2)
    c_B = random_unit_vector(d, 3)
    return projector.prepare(c_1, c_A, c_B)


class TestNearCollinearStimulus:
    def setup_method(self):
        self.projector = PolarProjector()

    @pytest.mark.parametrize("d", DIMS)
    @pytest.mark.parametrize("ratio", RATIOS)
    def test_returned_residual_is_the_true_residual(self, d, ratio):
        """The exact d_esc is a geometric fact, checkable without the operator."""
        frame = _frame(d, self.projector)
        v_n, exact = near_collinear_stimulus(frame.c_1, frame.c1_hat, frame.v_dipole, ratio)

        r = (v_n - frame.c_1) - np.dot(v_n - frame.c_1, frame.c1_hat) * frame.c1_hat
        lam = np.dot(r, frame.v_dipole) / frame.v_dipole_norm_sq
        residual = np.linalg.norm(r - lam * frame.v_dipole)

        assert residual == pytest.approx(exact, rel=1e-6)

    @pytest.mark.parametrize("d", DIMS)
    @pytest.mark.parametrize("ratio", RATIOS)
    def test_lambda_sits_at_one_half_away_from_the_clip(self, d, ratio):
        """Conditioning must be measured without saturation confounding it."""
        frame = _frame(d, self.projector)
        v_n, _ = near_collinear_stimulus(frame.c_1, frame.c1_hat, frame.v_dipole, ratio)

        _, lam, _ = self.projector.evaluate(v_n, frame, 0)
        assert lam == pytest.approx(0.5, abs=1e-9)

    @pytest.mark.parametrize("d", DIMS)
    def test_ratio_scales_the_residual_proportionally(self, d):
        """Sweeping the ratio must sweep d_esc, or the table's x-axis is a lie."""
        frame = _frame(d, self.projector)
        _, big = near_collinear_stimulus(frame.c_1, frame.c1_hat, frame.v_dipole, 1e-3)
        _, small = near_collinear_stimulus(frame.c_1, frame.c1_hat, frame.v_dipole, 1e-6)

        assert big / small == pytest.approx(1e3, rel=1e-9)

    @pytest.mark.parametrize("d", DIMS)
    def test_perturbation_is_orthogonal_to_anchor_and_dipole(self, d):
        """What makes the residual exactly eps: w lies outside both directions."""
        frame = _frame(d, self.projector)
        ratio = 1e-4
        v_n, exact = near_collinear_stimulus(frame.c_1, frame.c1_hat, frame.v_dipole, ratio)

        v_hat = frame.v_dipole / np.linalg.norm(frame.v_dipole)
        w = (v_n - frame.c_1 - 0.5 * np.linalg.norm(frame.v_dipole) * v_hat) / exact

        assert np.dot(w, frame.c1_hat) == pytest.approx(0.0, abs=1e-9)
        assert np.dot(w, v_hat) == pytest.approx(0.0, abs=1e-9)
        assert np.linalg.norm(w) == pytest.approx(1.0, rel=1e-9)

    @pytest.mark.parametrize("d", DIMS)
    def test_is_deterministic_under_its_seed(self, d):
        frame = _frame(d, self.projector)
        a, ea = near_collinear_stimulus(frame.c_1, frame.c1_hat, frame.v_dipole, 1e-5)
        b, eb = near_collinear_stimulus(frame.c_1, frame.c1_hat, frame.v_dipole, 1e-5)

        assert np.array_equal(a, b)
        assert ea == eb

    @pytest.mark.parametrize("d", DIMS)
    def test_distinct_seeds_give_distinct_perturbations(self, d):
        frame = _frame(d, self.projector)
        a, ea = near_collinear_stimulus(frame.c_1, frame.c1_hat, frame.v_dipole, 1e-5, seed=77)
        b, eb = near_collinear_stimulus(frame.c_1, frame.c1_hat, frame.v_dipole, 1e-5, seed=78)

        assert not np.array_equal(a, b)
        assert ea == eb  # the residual is a property of the ratio, not the seed
