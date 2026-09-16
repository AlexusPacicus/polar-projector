"""Tests for evaluate_batch() — the batched form of Proposition 1's projection.

The load-bearing question is what "agrees with evaluate()" means here, because
it cannot mean bitwise. BLAS uses a blocked reduction order for the
matrix-vector product once B >= 2, so the residual diverges from a sequence of
single-row dot products before any norm is taken. What is asserted instead is a
bound, and the bound is absolute rather than relative on purpose: the error in
d_esc is amplified by ||r||/d_esc, so a relative tolerance passes on generic
vectors and fails in exactly the near-collinear regime section 3.2 exists to
characterize.

The lambda bound is not a constant either. lambda divides <r, v_dipole> by
||v_dipole||^2, so a reduction-order error of order eps*||r||*||v_dipole|| in the
numerator becomes eps*||r||/||v_dipole|| in lambda, which grows without limit as
the poles approach each other. A flat tolerance only held because the fixtures
used well-separated random poles; the close-poles test below would fail it.

Tolerances carry headroom deliberately: the constant is 8*eps, because CI runs
on a different BLAS whose reduction order differs again.
"""
import numpy as np
import pytest

from polar_projector import PolarBatch, PolarProjector

DIMS = (128, 384, 768)
SEEDS = range(10)
BATCHES = (1, 4, 64, 1024)

EPS = float(np.finfo(np.float64).eps)


def _unit_rows(b: int, d: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    v = rng.normal(size=(b, d)).astype(np.float64)
    return np.ascontiguousarray(v / np.linalg.norm(v, axis=1, keepdims=True))


def _frame(projector: PolarProjector, d: int, seed: int = 0):
    c_1, c_A, c_B = _unit_rows(3, d, seed + 991)
    return projector.prepare(c_1, c_A, c_B)


def _residual_norms(projector: PolarProjector, V: np.ndarray, frame) -> np.ndarray:
    """||r||_2 per row — the scale the d_esc tolerance is measured against."""
    r = V - frame.c_1
    r = r - (r @ frame.c1_hat)[:, None] * frame.c1_hat
    return np.linalg.norm(r, axis=1)


def _assert_agrees(batch, scalar, norms: np.ndarray, frame) -> None:
    """|dlambda| <= 8 eps max(1, ||r||/||v_dipole||) and |dd_esc| <= 8 eps ||r||, per row."""
    lambda_scale = np.maximum(1.0, norms / np.sqrt(frame.v_dipole_norm_sq))
    assert np.all(np.abs(batch.lambdas - [s[1] for s in scalar]) <= 8 * EPS * lambda_scale)
    assert np.all(np.abs(batch.d_esc - [s[2] for s in scalar]) <= 8 * EPS * norms)


class TestBatchAgreesWithScalar:
    def setup_method(self):
        self.projector = PolarProjector()

    @pytest.mark.parametrize("d", DIMS)
    @pytest.mark.parametrize("seed", SEEDS)
    def test_matches_evaluate_within_the_measured_bound(self, d, seed):
        frame = _frame(self.projector, d, seed)
        V = _unit_rows(8, d, seed)

        batch = self.projector.evaluate_batch(V, frame)
        scalar = [self.projector.evaluate(v, frame, i) for i, v in enumerate(V)]

        norms = _residual_norms(self.projector, V, frame)
        _assert_agrees(batch, scalar, norms, frame)

    @pytest.mark.parametrize("b", BATCHES)
    def test_agreement_does_not_degrade_with_batch_size(self, b):
        d = 384  # b != d in every case, so both width-error branches stay reachable
        frame = _frame(self.projector, d)
        V = _unit_rows(b, d, 5)

        batch = self.projector.evaluate_batch(V, frame)
        scalar = [self.projector.evaluate(v, frame, i) for i, v in enumerate(V)]
        norms = _residual_norms(self.projector, V, frame)

        _assert_agrees(batch, scalar, norms, frame)

    @pytest.mark.parametrize("d", DIMS)
    def test_near_collinear_needs_absolute_not_relative_tolerance(self, d):
        """The regime section 3.2 characterizes, and the one rtol would fail in.

        Error in d_esc is amplified by ||r||/d_esc. This pins the absolute bound
        and documents that a tight rtol is not a stricter version of it but a
        different, wrong assertion.
        """
        from polar_projector.fixtures import near_collinear_stimulus

        frame = _frame(self.projector, d)
        rows = [near_collinear_stimulus(frame.c_1, frame.c1_hat, frame.v_dipole, 10.0**-e)[0]
                for e in (3, 6, 9, 12)]
        V = np.ascontiguousarray(np.vstack(rows))

        batch = self.projector.evaluate_batch(V, frame)
        scalar = [self.projector.evaluate(v, frame, i) for i, v in enumerate(V)]
        norms = _residual_norms(self.projector, V, frame)

        assert np.all(np.abs(batch.d_esc - [s[2] for s in scalar]) <= 8 * EPS * norms)

    @pytest.mark.parametrize("d", (384, 768))
    @pytest.mark.parametrize("gap", (1e-2, 1e-4))
    @pytest.mark.parametrize("seed", range(10))
    def test_close_poles_scale_the_lambda_bound(self, d, gap, seed):
        """Nearly coincident poles amplify lambda's disagreement by ||r||/||v_dipole||.

        Stimuli are scaled up and poles pulled together, so ||r||/||v_dipole|| reaches
        the range where a flat 8*eps bound on lambda does not hold.
        """
        c_1, c_A, w = _unit_rows(3, d, seed + 311)
        frame = self.projector.prepare(c_1, c_A, c_A + gap * w)
        V = np.ascontiguousarray(_unit_rows(256, d, seed) * 10.0)

        batch = self.projector.evaluate_batch(V, frame)
        scalar = [self.projector.evaluate(v, frame, i) for i, v in enumerate(V)]
        norms = _residual_norms(self.projector, V, frame)

        _assert_agrees(batch, scalar, norms, frame)

    @pytest.mark.parametrize("d", DIMS)
    @pytest.mark.parametrize("sign", (1.0, -1.0))
    def test_saturated_lambda_matches_bitwise(self, d, sign):
        """Where the clip is total, upstream reduction noise is erased entirely."""
        frame = _frame(self.projector, d)
        V = np.ascontiguousarray(
            np.vstack([frame.c_1 + sign * k * frame.v_dipole for k in (5.0, 9.0, 17.0)])
        )

        batch = self.projector.evaluate_batch(V, frame)
        assert np.array_equal(batch.lambdas, np.full(3, sign))

    @pytest.mark.parametrize("d", DIMS)
    def test_collinear_poles_fallback_frame(self, d):
        """The Proposition 2 fallback dipole must batch like any other."""
        c_1 = _unit_rows(1, d, 3)[0]
        frame = self.projector.prepare(c_1, c_1 * 2.0, c_1 * 0.5)
        V = _unit_rows(16, d, 4)

        batch = self.projector.evaluate_batch(V, frame)
        scalar = [self.projector.evaluate(v, frame, i) for i, v in enumerate(V)]
        norms = _residual_norms(self.projector, V, frame)

        _assert_agrees(batch, scalar, norms, frame)


class TestBatchContract:
    def setup_method(self):
        self.projector = PolarProjector()

    @pytest.mark.parametrize("d", DIMS)
    def test_empty_batch_returns_empty_float64_arrays(self, d):
        frame = _frame(self.projector, d)
        batch = self.projector.evaluate_batch(np.zeros((0, d)), frame)

        assert batch.lambdas.shape == (0,)
        assert batch.d_esc.shape == (0,)
        assert batch.lambdas.dtype == np.float64
        assert batch.d_esc.dtype == np.float64

    @pytest.mark.parametrize("d", DIMS)
    def test_does_not_mutate_the_callers_buffer(self, d):
        """First method in this package to do in-place arithmetic. It must not leak."""
        frame = _frame(self.projector, d)
        V = _unit_rows(32, d, 7)
        before = V.copy()

        self.projector.evaluate_batch(V, frame)
        assert np.array_equal(V, before)

    @pytest.mark.parametrize("d", DIMS)
    def test_accepts_a_non_contiguous_view(self, d):
        frame = _frame(self.projector, d)
        V = _unit_rows(32, d, 8)
        view = V[::2]
        before = V.copy()

        strided = self.projector.evaluate_batch(view, frame)
        packed = self.projector.evaluate_batch(np.ascontiguousarray(view), frame)

        assert np.array_equal(V, before)
        assert np.array_equal(strided.lambdas, packed.lambdas)
        assert np.array_equal(strided.d_esc, packed.d_esc)

    @pytest.mark.parametrize("d", DIMS)
    def test_accepts_float32_and_returns_float64(self, d):
        frame = _frame(self.projector, d)
        V = _unit_rows(8, d, 9)
        batch = self.projector.evaluate_batch(V.astype(np.float32), frame)

        assert batch.lambdas.dtype == np.float64
        assert batch.d_esc.dtype == np.float64

        upcast = np.ascontiguousarray(V.astype(np.float32).astype(np.float64))
        scalar = [self.projector.evaluate(v, frame, i) for i, v in enumerate(upcast)]
        norms = _residual_norms(self.projector, upcast, frame)
        _assert_agrees(batch, scalar, norms, frame)

    @pytest.mark.parametrize("d", DIMS)
    def test_result_is_an_immutable_namedtuple(self, d):
        frame = _frame(self.projector, d)
        batch = self.projector.evaluate_batch(_unit_rows(4, d, 10), frame)

        assert isinstance(batch, PolarBatch)
        lambdas, d_esc = batch
        assert lambdas is batch.lambdas
        assert d_esc is batch.d_esc
        with pytest.raises(AttributeError):
            batch.lambdas = np.zeros(4)

    @pytest.mark.parametrize("d", DIMS)
    def test_bounds_hold_for_every_row(self, d):
        frame = _frame(self.projector, d)
        batch = self.projector.evaluate_batch(_unit_rows(256, d, 11), frame)

        assert np.all(batch.lambdas >= -1.0)
        assert np.all(batch.lambdas <= 1.0)
        assert np.all(batch.d_esc >= 0.0)
        assert np.all(np.isfinite(batch.lambdas))
        assert np.all(np.isfinite(batch.d_esc))

    @pytest.mark.parametrize("d", DIMS)
    def test_frame_is_unchanged_by_a_batch_call(self, d):
        frame = _frame(self.projector, d)
        snapshot = [frame.c_1.copy(), frame.c1_hat.copy(), frame.v_dipole.copy()]

        self.projector.evaluate_batch(_unit_rows(16, d, 12), frame)

        assert np.array_equal(frame.c_1, snapshot[0])
        assert np.array_equal(frame.c1_hat, snapshot[1])
        assert np.array_equal(frame.v_dipole, snapshot[2])


class TestBatchRejects:
    def setup_method(self):
        self.projector = PolarProjector()
        self.d = 384
        self.frame = _frame(self.projector, self.d)

    def test_rejects_a_1d_stimulus(self):
        with pytest.raises(ValueError, match="2-D"):
            self.projector.evaluate_batch(np.ones(self.d), self.frame)

    def test_rejects_a_3d_array(self):
        with pytest.raises(ValueError, match="2-D"):
            self.projector.evaluate_batch(np.ones((4, self.d, 1)), self.frame)

    def test_rejects_a_column_vector(self):
        """(d, 1) is a legal batch shape but the wrong one, caught by width."""
        with pytest.raises(ValueError, match="does not match frame dimension"):
            self.projector.evaluate_batch(np.ones((self.d, 1)), self.frame)

    def test_rejects_a_transposed_batch_and_says_so(self):
        with pytest.raises(ValueError, match=r"did you pass V\.T"):
            self.projector.evaluate_batch(_unit_rows(8, self.d, 13).T, self.frame)

    def test_rejects_a_dimension_mismatch(self):
        with pytest.raises(ValueError, match="does not match frame dimension"):
            self.projector.evaluate_batch(np.ones((4, 128)), self.frame)

    def test_square_input_is_accepted_as_b_equals_d(self):
        """(d, d) is ambiguous by shape and has no numerical tell.

        Pinned rather than guessed at: a heuristic here would be the convenience
        broadcast prepare() already refuses to make.
        """
        batch = self.projector.evaluate_batch(_unit_rows(self.d, self.d, 14), self.frame)
        assert batch.lambdas.shape == (self.d,)
