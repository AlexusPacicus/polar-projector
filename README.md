# Polar Projector

A stateless, deterministic **O(d)** operator that places a vector against a local frame — an anchor
plus a dipole pair — and returns a projection coefficient λ ∈ [−1, 1] along the dipole axis and an
orthogonal residual d_esc ≥ 0. It never reads the stored corpus, so its cost does not depend on
corpus size. It depends on numpy and nothing else.

## The paper

This is the reference implementation for **Decoupling Spatial Interaction from Corpus State:
Re-centring Without Re-coupling** (Alexis Zapico-Fernández, 2026).

- **PDF:** [release `v1.0-paper`](https://github.com/AlexusPacicus/polar-projector/releases/tag/v1.0-paper)
- **Manuscript source:** [`paper/polar-projector-paper.md`](paper/polar-projector-paper.md)
- **Claims registry:** [`paper/claims.md`](paper/claims.md) — every claim, its pre-registration
  status and the check that backs it
- **How to cite:** see [`CITATION.cff`](CITATION.cff), or GitHub's "Cite this repository"

The paper is a measured report, not a case for the operator: on every instrument it uses, a baseline
simple enough to write in a few lines matches or beats the operator, and the paper says so.

## Install

```bash
pip install -e ".[test]"
```

## Quick start

```python
import numpy as np
from polar_projector import PolarProjector

rng = np.random.default_rng(0)
anchor, pole_a, pole_b = rng.standard_normal((3, 384))
stimuli = rng.standard_normal((1000, 384))

projector = PolarProjector()

# Stateless: builds the frame and evaluates one stimulus.
_, lam, d_esc = projector.project(stimuli[0], anchor, pole_a, pole_b, centroid_id=0)

# Prepared: build the frame once, evaluate many stimuli against it.
frame = projector.prepare(anchor, pole_a, pole_b)
coords = [projector.evaluate(v, frame, i)[1:] for i, v in enumerate(stimuli)]
assert coords[0] == (lam, d_esc)  # the two paths are numerically identical

# Batched: same frame, all stimuli at once (agrees to within rounding, not bit for bit).
batch = projector.evaluate_batch(stimuli, frame)
```

The frame depends only on (anchor, pole_a, pole_b), so when the active context outlives a single
stimulus, `prepare()` once and `evaluate()` per stimulus does less than half the work of calling
`project()` each time. Measured costs are in the manuscript's §3.1; they belong to the host they
were measured on, not to the operator.

## Guarantees and failure modes

- **Deterministic.** `project()` and `prepare()` + `evaluate()` return identical values for identical
  inputs; nothing iterates, samples or reads storage.
- **Non-degenerate.** Collinear poles fall back to a canonical direction instead of a zero-length
  dipole (Proposition 2).
- **Fails loudly.** `prepare()` raises `ValueError` for non-1-D inputs, mismatched shapes, d < 2,
  non-finite inputs or norms that overflow float64, and dipoles whose squared norm underflows. The
  load-bearing case is the column vector: a `(d, 1)` input would otherwise broadcast into a `(d, d)`
  matrix and return a wrong answer silently.
- **No aliasing.** The frame keeps its own copy of the anchor, so changing the caller's array after
  `prepare()` does not change the frame.
- **d_esc is computed in vector form.** The algebraically equivalent scalar form is faster but loses
  all precision near collinearity, in places without any detectable sign (manuscript Appendix B).
- **`evaluate_batch()` is not bit-for-bit.** BLAS reorders the reduction for batches of two or more,
  so a row's result depends on its batch. The disagreement in λ scales with ‖r‖/‖v_dipole‖ and grows
  as the poles approach each other (`tests/test_polar_batch.py`). No result in the manuscript uses it.

## Reproducing the paper

Every figure in the manuscript comes from a committed script under `bench/` or `tools/`, run offline
under fixed seeds:

```bash
pip install -e ".[test,repro,bench]"
python tools/verify_paper_tables.py
```

`repro` pins numpy (2.4.1). The `bench` extra — umap-learn and scikit-learn, for the UMAP and t-SNE
baselines and the trustworthiness metric of §3.2–§3.4 — is not pinned. The committed artifacts were
produced with umap-learn 0.5.12, scikit-learn 1.8.0 and numba 0.67.0 on Python 3.11.6, and other
versions can move the baseline rows. Absolute timings are specific to the Apple M1 described in §3.

| Script | Manuscript section |
|---|---|
| `bench/latency.py --sweep --n-sweep` | §3 cost vs. corpus size, §3.1 cost vs. O(d) primitives, §A dimension sweep |
| `tools/decompose_polar_latency.py` | §3.1 `prepare()` row and stateless decomposition (`--out` to avoid overwriting the committed artifact) |
| `bench/conditioning.py` | §B conditioning sweep and scalar- vs. vector-form latency |
| `bench/clamp.py` | §A and §B: the λ clamp substitution, re-measured side by side |
| `tools/generate_polar_delta_table.py` | §C δ-sweep table (N = 10,000) |
| `bench/drift.py` | §3.2 positional stability, 7 arms (baselines need `[bench]`) |
| `bench/recall.py` | §3.3 same-part recall@k (baselines need `[bench]`) |
| `bench/frame_sensitivity.py` | §3.4 pole selection as a trade-off knob |
| `bench/scale.py` | §3.2–§3.4 under a declared screen scale, unit and isometric |
| `bench/reanchor.py` | §3.5 re-anchoring recall and cost columns; `--ablation` for the units decomposition |
| `bench/poles.py` | §2.1: where the published frame's poles land on the λ axis |
| `tools/make_figures.py` | Figures 1–3 |
| `tools/build_arxiv.py` | LaTeX build and upload zip (`paper/build/arxiv-source.zip`) |
| `bench/batched.py` | batched throughput and agreement (not in the manuscript) |

Scripts under `bench/` write JSON to `bench/results/` in a common
`{experiment, config, host, thread_env, results}` envelope; `bench/_harness.py` documents the timing
protocol, including what it does not control. The deterministic constructions they use ship in the
package as `polar_projector.fixtures`.

## What CI checks, and what it doesn't

`tools/verify_paper_tables.py` runs on every push. It:

- recomputes the Appendix B and C tables from the operator and compares the tables printed in the
  manuscript cell by cell;
- checks every other published figure against its committed artifact in `bench/results/`;
- requires each checked figure to be printed in the manuscript, ignoring section references so that
  "§3.2" does not count as printing 3.2;
- fails if a claim in `paper/claims.md` marked checked names a check that does not exist, names a
  whole section instead of a check, or is a malformed row.

It checks consistency between the manuscript and its artifacts. It cannot catch a benchmark that
measures something other than what the paper says it measures.

CI also runs 800 tests on Python 3.11–3.13, ruff, mypy, and a 100% line-coverage gate over the
operator.


## License

- **Code:** [Apache License 2.0](LICENSE). See also [`NOTICE`](NOTICE).
- **Manuscript and figures** (`paper/`): [CC BY 4.0](paper/LICENSE.md).
- **Frozen corpus data** (`bench/data/`): [CC BY 4.0](bench/data/LICENSE.md). The embeddings encode
  R. H. M. Elwes' public-domain translation of Spinoza's *Ethics*; the text is not included.
