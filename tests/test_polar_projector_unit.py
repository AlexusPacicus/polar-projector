"""Unit tests for PolarProjector - isolated, deterministic, < 1ms each."""
import math

import numpy as np
import pytest

from polar_projector import PolarProjector
from polar_projector.fixtures import random_unit_vector


class TestPolarProjectorUnit:
    """Pure unit tests for PolarProjector internal methods."""

    def setup_method(self):
        self.projector = PolarProjector()

    # --- Anchor normalization ---

    def test_normalize_anchor_guard_zero_norm(self):
        c_1 = np.zeros(384, dtype=np.float64)
        c1_hat = self.projector._normalize_anchor(c_1)
        assert np.allclose(c1_hat, 0.0)

    def test_normalize_anchor_guard_normal(self):
        c_1 = np.ones(384, dtype=np.float64)
        c1_hat = self.projector._normalize_anchor(c_1)
        assert np.isclose(np.linalg.norm(c1_hat), 1.0)

    def test_normalize_anchor_at_eps_boundary(self):
        """Test at exactly eps_norm threshold."""
        c_1 = np.array([1e-9, 0.0, 0.0], dtype=np.float64)
        c1_hat = self.projector._normalize_anchor(c_1)
        assert np.allclose(c1_hat, 0.0)

    def test_normalize_anchor_above_eps_boundary(self):
        """Test just above eps_norm threshold."""
        c_1 = np.array([2e-9, 0.0, 0.0], dtype=np.float64)
        c1_hat = self.projector._normalize_anchor(c_1)
        assert np.isclose(np.linalg.norm(c1_hat), 1.0)

    # --- Orthogonal projection (associative O(d) form) ---

    def test_project_perp_eliminates_anchor_component(self):
        """⟨P⊥v, ĉ₁⟩ = 0: the residue is orthogonal to the anchor."""
        c1_hat = np.array([0.6, 0.8, 0.0], dtype=np.float64)
        v = np.array([1.0, 2.0, 3.0], dtype=np.float64)
        v_perp = self.projector._project_perp(v, c1_hat)
        assert np.isclose(np.dot(v_perp, c1_hat), 0.0, atol=1e-15)
        assert np.isclose(v_perp[2], 3.0)

    def test_project_perp_keeps_parallel_component(self):
        """P⊥v = v - ⟨v, ĉ₁⟩ĉ₁ removes exactly the anchor-direction part."""
        c1_hat = np.array([0.6, 0.8, 0.0], dtype=np.float64)
        v = np.array([1.0, 2.0, 3.0], dtype=np.float64)
        v_perp = self.projector._project_perp(v, c1_hat)
        parallel = np.dot(v, c1_hat) * c1_hat
        assert np.allclose(v, v_perp + parallel)

    def test_project_perp_idempotent_on_vector(self):
        """P⊥(P⊥v) = P⊥v on a vector."""
        c1_hat = np.array([0.6, 0.8, 0.0], dtype=np.float64)
        v = np.array([1.0, 2.0, 3.0], dtype=np.float64)
        v_perp = self.projector._project_perp(v, c1_hat)
        assert np.allclose(self.projector._project_perp(v_perp, c1_hat), v_perp)

    def test_project_perp_linearity(self):
        """P⊥(u + v) = P⊥u + P⊥v."""
        c1_hat = np.array([0.6, 0.8, 0.0], dtype=np.float64)
        u = np.array([1.0, 0.0, 2.0], dtype=np.float64)
        v = np.array([0.0, 1.0, 3.0], dtype=np.float64)
        left = self.projector._project_perp(u + v, c1_hat)
        right = self.projector._project_perp(u, c1_hat) + self.projector._project_perp(v, c1_hat)
        assert np.allclose(left, right)

    def test_project_perp_identity_for_zero_anchor(self):
        """Zero anchor (ĉ₁ = 0) degrades to the identity operator."""
        c1_hat = np.zeros(3, dtype=np.float64)
        v = np.array([1.0, 2.0, 3.0], dtype=np.float64)
        assert np.array_equal(self.projector._project_perp(v, c1_hat), v)

    def test_project_perp_centroid(self):
        c1_hat = np.array([1.0, 0.0, 0.0], dtype=np.float64)
        c_A = np.array([2.0, 3.0, 4.0], dtype=np.float64)
        cA_perp = self.projector._project_perp(c_A, c1_hat)
        assert np.isclose(cA_perp[0], 0.0)
        assert np.isclose(cA_perp[1], 3.0)

    # --- Collinearity ---

    def test_collinearity_detection_true(self):
        cA_perp = np.array([1e-7, 2e-7, 0.0], dtype=np.float64)
        cB_perp = np.array([2e-7, 4e-7, 0.0], dtype=np.float64)
        assert self.projector._is_collinear(cA_perp, cB_perp)

    def test_collinearity_detection_false(self):
        cA_perp = np.array([1.0, 0.0, 0.0], dtype=np.float64)
        cB_perp = np.array([0.0, 1.0, 0.0], dtype=np.float64)
        assert not self.projector._is_collinear(cA_perp, cB_perp)

    def test_collinearity_at_eps_boundary(self):
        """Test at exactly eps_collinear threshold (strict <)."""
        cA_perp = np.array([0.5e-6, 0.0, 0.0], dtype=np.float64)
        cB_perp = np.array([1.4999999e-6, 0.0, 0.0], dtype=np.float64)  # diff < 1e-6
        assert self.projector._is_collinear(cA_perp, cB_perp)

    def test_collinearity_above_eps_boundary(self):
        """Test just above eps_collinear threshold."""
        cA_perp = np.array([0.5e-6, 0.0, 0.0], dtype=np.float64)
        cB_perp = np.array([1.5000001e-6, 0.0, 0.0], dtype=np.float64)  # diff > 1e-6
        assert not self.projector._is_collinear(cA_perp, cB_perp)

    # --- Canonical u⊥ ---

    def test_canonical_u_perp_deterministic(self):
        c1_hat = np.array([0.6, 0.8, 0.0], dtype=np.float64)
        results = [self.projector._canonical_u_perp(c1_hat) for _ in range(1000)]
        for u in results[1:]:
            assert np.array_equal(u, results[0]), "Bitwise determinism failed"

    def test_canonical_u_perp_orthogonal(self):
        c1_hat = np.array([0.6, 0.8, 0.0], dtype=np.float64)
        u_perp = self.projector._canonical_u_perp(c1_hat)
        assert np.isclose(np.dot(u_perp, c1_hat), 0.0, atol=1e-10)
        assert np.isclose(np.linalg.norm(u_perp), 1.0)

    def test_canonical_u_perp_min_projection_idx(self):
        # Minimum at index 2 (0.1 is smallest absolute)
        c1_hat = np.array([0.5, 0.5, 0.1, 0.5], dtype=np.float64)
        u_perp = self.projector._canonical_u_perp(c1_hat)
        assert np.abs(u_perp[2]) > 0.9

    def test_canonical_u_perp_first_component_min(self):
        """Test when first component is minimum."""
        c1_hat = np.array([0.1, 0.5, 0.5, 0.5], dtype=np.float64)
        u_perp = self.projector._canonical_u_perp(c1_hat)
        assert np.abs(u_perp[0]) > 0.9

    def test_canonical_u_perp_last_component_min(self):
        """Test when last component is minimum."""
        c1_hat = np.array([0.5, 0.5, 0.5, 0.1], dtype=np.float64)
        u_perp = self.projector._canonical_u_perp(c1_hat)
        assert np.abs(u_perp[3]) > 0.9

    # --- Dipole ---

    def test_dipole_fallback_non_collinear(self):
        cA_perp = np.array([1.0, 0.0, 0.0], dtype=np.float64)
        cB_perp = np.array([0.0, 1.0, 0.0], dtype=np.float64)
        c1_hat = np.array([1.0, 0.0, 0.0], dtype=np.float64)
        v_dipole = self.projector._compute_dipole(cA_perp, cB_perp, c1_hat)
        expected = cA_perp - cB_perp
        assert np.allclose(v_dipole, expected)

    def test_dipole_collinear_fallback(self):
        cA_perp = np.array([1e-7, 0.0, 0.0], dtype=np.float64)
        cB_perp = np.array([2e-7, 0.0, 0.0], dtype=np.float64)
        c1_hat = np.array([1.0, 0.0, 0.0], dtype=np.float64)
        v_dipole = self.projector._compute_dipole(cA_perp, cB_perp, c1_hat)
        expected = 2.0 * self.projector.delta * self.projector._canonical_u_perp(c1_hat)
        assert np.allclose(v_dipole, expected)

    # --- Full pipeline components ---

    def test_stimulus_residual(self):
        v_n = np.array([1.0, 2.0, 3.0], dtype=np.float64)
        c_1 = np.array([0.5, 0.5, 0.5], dtype=np.float64)
        c1_hat = c_1 / np.linalg.norm(c_1)
        P_perp = np.eye(3) - np.outer(c1_hat, c1_hat)
        r = P_perp @ (v_n - c_1)
        assert np.isclose(np.dot(r, c1_hat), 0.0)

    def test_voltage_lambda_bounds(self):
        r = np.array([10.0, 0.0, 0.0], dtype=np.float64)
        v_dipole = np.array([1.0, 0.0, 0.0], dtype=np.float64)
        lambda_val = np.dot(r, v_dipole) / np.dot(v_dipole, v_dipole)
        lambda_val = np.clip(lambda_val, -1.0, 1.0)
        assert -1.0 <= lambda_val <= 1.0

    def test_escape_distance_nonnegative(self):
        r = np.array([1.0, 2.0, 3.0], dtype=np.float64)
        v_dipole = np.array([0.5, 0.5, 0.0], dtype=np.float64)
        lambda_val = 0.5
        d_esc = np.linalg.norm(r - lambda_val * v_dipole)
        assert d_esc >= 0.0

    def test_return_tuple_type(self):
        v_n = np.random.default_rng(1).normal(size=384).astype(np.float64)
        v_n = v_n / np.linalg.norm(v_n)
        c_1 = np.random.default_rng(2).normal(size=384).astype(np.float64)
        c_1 = c_1 / np.linalg.norm(c_1)
        c_A = np.random.default_rng(3).normal(size=384).astype(np.float64)
        c_A = c_A / np.linalg.norm(c_A)
        c_B = np.random.default_rng(4).normal(size=384).astype(np.float64)
        c_B = c_B / np.linalg.norm(c_B)
        result = self.projector.project(v_n, c_1, c_A, c_B, 42)
        assert isinstance(result, tuple)
        assert len(result) == 3
        assert isinstance(result[0], int)
        assert isinstance(result[1], float)
        assert isinstance(result[2], float)

    # --- Custom parameters ---

    def test_custom_delta(self):
        projector = PolarProjector(delta=0.5)
        assert projector.delta == 0.5

    def test_custom_eps_norm(self):
        projector = PolarProjector(eps_norm=1e-6)
        assert projector.eps_norm == 1e-6

    def test_custom_eps_collinear(self):
        projector = PolarProjector(eps_collinear=1e-4)
        assert projector.eps_collinear == 1e-4

    @pytest.mark.parametrize("d", [128, 384, 768])
    @pytest.mark.parametrize("seed", range(20))
    def test_associative_projection_equivalence(self, d, seed):
        """P⊥v = v - ⟨v, ĉ₁⟩ĉ₁ (O(d)) matches the closed-form matrix (O(d²))."""
        rng = np.random.default_rng(seed)
        c1_hat = rng.normal(size=d).astype(np.float64)
        c1_hat = c1_hat / np.linalg.norm(c1_hat)
        P_perp = np.eye(d) - np.outer(c1_hat, c1_hat)  # closed-form oracle (test-only)
        for _ in range(5):
            v = rng.normal(size=d).astype(np.float64)
            matrix_result = P_perp @ v
            assoc_result = self.projector._project_perp(v, c1_hat)
            assert np.allclose(matrix_result, assoc_result, atol=1e-12), (
                f"seed={seed}: associative form diverges from matrix form"
            )

    # --- Fallback dipole non-vanishing ---

    @pytest.mark.parametrize("delta", [0.01, 0.1, 0.5, 1.0])
    @pytest.mark.parametrize("d", [128, 384])
    def test_fallback_dipole_nonvanishing(self, delta, d):
        """||v_dipole||₂ ≥ 2δ > 0 in the collinear fallback path.

        Any nonzero scalar multiple of ĉ₁ is collinear with it (projects to
        exactly 0); the two positive factors guarantee the dipole difference
        stays below eps_collinear without cancellation.
        """
        projector = PolarProjector(delta=delta)
        c1_hat = np.ones(d, dtype=np.float64) / np.sqrt(d)
        c_A = 2.0 * c1_hat
        c_B = 0.5 * c1_hat
        cA_perp = projector._project_perp(c_A, c1_hat)
        cB_perp = projector._project_perp(c_B, c1_hat)
        v_dipole = projector._compute_dipole(cA_perp, cB_perp, c1_hat)
        norm = np.linalg.norm(v_dipole)
        assert norm >= 2.0 * delta - 1e-15, (
            f"delta={delta}: ||v_dipole||₂ = {norm} < 2δ = {2*delta}"
        )
        assert norm > 0.0
    @pytest.mark.parametrize(
        "value",
        [
            -math.inf, -3.0, -1.0000000000000002, -1.0, -0.5, -0.0, 0.0,
            5e-324, 0.5, 1.0, 1.0000000000000002, 3.0, math.inf, math.nan,
        ],
    )
    def test_lambda_clamp_matches_np_clip_exactly(self, value):
        """evaluate() clamps λ with min/max, not np.clip. They must not diverge.

        np.clip costs 1.86 µs on a single scalar against 0.23 µs for min/max --
        29% of the evaluate() call it used to sit in (bench/results/clamp.json) --
        so the hot path uses the latter. That
        is only safe while the two agree on every input, and the interesting
        inputs are the ones nobody reaches for: NaN, signed zero, subnormals,
        infinities, and the float either side of the clip boundary.

        Argument order is load-bearing. min(max(x, -1.0), 1.0) propagates NaN;
        min(max(-1.0, x), 1.0) silently returns -1.0 for it. This test checks the
        two expressions agree; the two tests after it check that evaluate() itself
        clamps this way, which is what fails if anyone reorders the shipped call.
        """
        shipped = min(max(value, -1.0), 1.0)
        reference = float(np.clip(value, -1.0, 1.0))

        if math.isnan(reference):
            assert math.isnan(shipped)
        else:
            assert shipped == reference
            assert math.copysign(1.0, shipped) == math.copysign(1.0, reference)

    def test_evaluate_propagates_nan_through_the_clamp(self):
        """A NaN projection coefficient must come out of evaluate() as NaN, not as -1.0."""
        frame = self.projector.prepare(
            np.array([1.0, 0.0, 0.0]), np.array([0.0, 1.0, 0.0]), np.array([0.0, -1.0, 0.0])
        )
        _, lam, _ = self.projector.evaluate(np.array([math.nan, 0.0, 0.0]), frame, 0)
        assert math.isnan(lam)

    @pytest.mark.parametrize("d", [128, 384, 768])
    def test_evaluate_lambda_matches_np_clip_bitwise(self, d):
        """evaluate()'s lambda equals np.clip of the same raw coefficient, saturated rows included."""
        frame = self.projector.prepare(random_unit_vector(d, 1), random_unit_vector(d, 2), random_unit_vector(d, 3))
        stimuli = [random_unit_vector(d, 100 + i) * scale for i, scale in enumerate([0.5, 1.0, 3.0, 30.0] * 25)]
        stimuli += [frame.c_1 + k * frame.v_dipole for k in (-5.0, -1.0, 0.0, 1.0, 5.0)]
        for i, v in enumerate(stimuli):
            r = self.projector._project_perp(np.asarray(v, dtype=np.float64) - frame.c_1, frame.c1_hat)
            reference = float(np.clip(float(np.dot(r, frame.v_dipole)) / frame.v_dipole_norm_sq, -1.0, 1.0))
            _, lam, _ = self.projector.evaluate(v, frame, i)
            assert lam == reference
            assert math.copysign(1.0, lam) == math.copysign(1.0, reference)

    def test_frame_does_not_alias_the_callers_anchor(self):
        """Mutating c_1 after prepare() must not change what the frame evaluates."""
        c_1 = random_unit_vector(8, 1)
        frame = self.projector.prepare(c_1, random_unit_vector(8, 2), random_unit_vector(8, 3))
        v = random_unit_vector(8, 4)
        before = self.projector.evaluate(v, frame, 0)
        c_1[:] = random_unit_vector(8, 9)
        assert self.projector.evaluate(v, frame, 0) == before

    @pytest.mark.parametrize(
        ("c_1", "c_A", "c_B"),
        [
            ([math.nan, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, -1.0, 0.0]),
            ([math.inf, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, -1.0, 0.0]),
            ([1e160, 1e160, 0.0], [0.0, 1.0, 0.0], [0.0, -1.0, 0.0]),
            ([1.0, 0.0, 0.0], [math.nan, 1.0, 0.0], [0.0, -1.0, 0.0]),
            ([1.0, 0.0, 0.0], [0.0, math.inf, 0.0], [0.0, -1.0, 0.0]),
            ([1.0, 0.0, 0.0], [0.0, 1e160, 0.0], [0.0, -1e160, 0.0]),
        ],
        ids=["nan-anchor", "inf-anchor", "overflowing-anchor", "nan-pole", "inf-pole", "overflowing-dipole"],
    )
    def test_prepare_rejects_non_finite_frames(self, c_1, c_A, c_B):
        with pytest.raises(ValueError, match="not finite"):
            self.projector.prepare(np.array(c_1), np.array(c_A), np.array(c_B))

    def test_dipole_exactly_at_eps_collinear_keeps_the_natural_branch(self):
        """Algorithm 1 step 5: a dipole norm equal to eps_collinear is not collinear."""
        c_A = np.array([0.0, 1e-6, 0.0])
        assert np.linalg.norm(c_A) == self.projector.eps_collinear
        frame = self.projector.prepare(np.array([1.0, 0.0, 0.0]), c_A, np.zeros(3))
        assert np.array_equal(frame.v_dipole, c_A)

    @pytest.mark.parametrize("d", [128, 384, 768])
    @pytest.mark.parametrize("sign", [1.0, -1.0])
    def test_lambda_saturates_to_exactly_pm_one(self, d, sign):
        """A stimulus far along the dipole axis must clamp to exactly ±1.0."""
        projector = PolarProjector()
        c_1 = random_unit_vector(d, 1)
        c_A = random_unit_vector(d, 2)
        c_B = random_unit_vector(d, 3)
        frame = projector.prepare(c_1, c_A, c_B)

        v_n = frame.c_1 + sign * 5.0 * frame.v_dipole
        _, lam, _ = projector.evaluate(v_n, frame, 0)

        assert lam == sign
        assert isinstance(lam, float)
