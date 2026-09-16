# Decoupling Spatial Interaction from Corpus State: Re-centring Without Re-coupling

**Author:** Alexis Zapico
**Affiliation:** Independent researcher
**Date:** September 2026

> **Editorial note — strip this block before submission.** It is repository scaffolding, not part
> of the manuscript.
>
> This file is canonical for the manuscript. An earlier draft was mirrored by hand into a Corca
> document (https://corca.app/doc/er5CXGbjDUaGnbFE45Hse); that copy has since diverged substantially
> and is superseded, not synchronized. Edits belong here, where CI checks the figures.
>
> Provenance: this operator and its test suite were extracted, with git history, from the
> Traianus substrate (https://github.com/AlexusPacicus/Traianus), where the design record lives
> in `docs/LEDGER.md` seq 40-43. The extraction exists so this manuscript can be reproduced with
> numpy alone, without the substrate's fastapi/torch dependency stack.
>
> Status: DRAFT. Sections 1–3, §5 and the appendices are grounded, and
> `tools/verify_paper_tables.py` — which CI runs on every push — checks them two different ways.
> The tables in §B and §C are **recomputed** from `polar_projector/projector.py` on every run and
> compared cell by cell. Every other published figure is checked for **consistency with its
> committed artifact** in `bench/results/` (figures produced by `bench/latency.py`,
> `bench/drift.py`, `bench/recall.py`, `bench/frame_sensitivity.py`, `bench/reanchor.py`,
> `bench/conditioning.py` and `tools/decompose_polar_latency.py` against the
> hash-committed corpus in `bench/data/`). The second check is the weaker of the two: it catches a
> manuscript drifting away from its own measurements, not an error inside a benchmark.
>
> No figure in §3 now escapes both checks: the \( O(N^2) \) column and the SQLite deployment numbers
> carried over from the substrate were removed, and §3.5's timing columns are checked against their
> committed artifact like every other timing. `paper/claims.md` registers each claim against its
> checks, and the verifier fails if a checked figure is not printed here.
>
> §4 is drafted but not reviewed and must not be treated as final. The speculative
> extensions carried by earlier drafts — multi-axis tangent frames and the tripolar model, adaptive
> δ calibration, and active-codebook eviction — have been removed rather than relegated: none is
> implemented in `polar_projector/projector.py`, and none supported a contribution this paper
> claims.

---

## Abstract

Spatial interfaces place a personal knowledge corpus of embeddings on a canvas, commonly using
global dimensionality reduction such as UMAP or t-SNE. Refitting these projections to keep the
canvas current relocates placed points, even with a fixed seed, at a cost of seconds per refit, and
stable or incremental projections soften that drift rather than remove it. Writing a note requires
decoupling the interaction from the state of the corpus: new notes must not move placed ones, and
placing one must not read what is stored.
Navigating also requires re-centring the view on the note being consulted. Any fixed linear map
meets the first requirement; the second is where methods differ. We present the Polar Projector, a
local \( O(d) \) operator that places an incoming vector against an active frame, an anchor plus a
contrast dipole, without reading the corpus, returning a clamped projection coefficient \( \lambda
\in [-1, 1] \) and an orthogonal residual \( d_{esc} \geq 0 \). Its collinear configurations do not
degenerate (Proposition 2), its residual decomposition is exact when \( \lambda \) is unsaturated
(Proposition 3), and an algebraically equivalent scalar form of \( d_{esc} \) loses all precision
below \( d_{esc}/\|r\|_2 \approx 10^{-6} \), at two points undetectably. Re-anchoring the frame on
the query re-centres the view without re-coupling it, beyond a codebook built once. Per-stimulus
cost is 4.57 µs with a prepared frame, and a stateless call stays flat to 1.4% across corpora of
1,000 to 25,000 vectors. On 2,221 chunks of Spinoza's *Ethics*, re-anchoring raises the recall of a
query's 15 nearest neighbours 29×, from 0.019 to 0.543, while a local PCA refit reads the corpus again
and recovers 0.023. A radial coordinate centred on the query bounds the operator at 0.981 on this
instrument, which rewards any view ordered by distance from the query; rendering \( \lambda \) in
length units lifts the operator to 0.925 in an exploratory ablation. No user took part, so whether any of this helps a person
navigate remains open.

## 1. Introduction

**The interaction must be decoupled from the state of the corpus** — its content and its size. A
spatial interface over a personal knowledge corpus — a canvas on which the user reaches their own
notes — encounters that requirement at two moments. The first is *introducing a vector*: writing a
note adds its embedding to the corpus and gives it a place on the canvas. The second is
*navigating*: the user consults a note already in the corpus, and the view is organized around it.
Each moment makes its own demands, and a static layout meets neither, because it never has to.

Introducing a vector imposes two constraints:

1. **Writing one note must not move the others.** Users encode meaning in where things are
   (Marshall & Shipman, 1995), and instability in a layout degrades navigation and orientation
   (Boechler, 2001). If positions shift on every write, spatial proximity stops reliably encoding
   semantic proximity, and the user's own act of writing invalidates the map they built.
2. **Placing a note must not depend on what is stored.** The position is computed while the user
   works, so its cost cannot scale with how much the user has written, and computing it should not
   require reading the stored corpus. The constraint concerns placing one vector: refreshing a whole
   view still touches every placed point, for every method measured in §3.5.

*The premise, and its standing.* Both constraints are **assumptions this paper inherits, not
results it establishes**, and the first one carries the weight. Boechler (2001) measures navigation
and orientation in *hypertext documents* — a linked corpus browsed through a reading interface, not
a continuous canvas over an embedding space — so applying it here is an extrapolation across
interface families. It is a defensible one, and it is the standard motivation in this literature,
but nothing below tests it. No user touched anything in this work: every instrument reported in §3
is numerical, computed on a frozen corpus, and none of them can tell whether a person navigating
actually suffers from layout instability or benefits from its absence. A reader who rejects the
premise should know it by the end of this section rather than after §3.

*What existing approaches do with the two constraints.* Reusing global dimensionality reduction
violates both. Refitting alters existing coordinates as the corpus grows, and §3.2 measures what
survives pinning the random seed: t-SNE (van der Maaten & Hinton, 2008) relocates previously placed
points by 1.03–1.24 times the width of the layout at every growth step, and UMAP (McInnes et al.,
2018) by 0.31–1.25. Refitting is also not cheap — the same seven growth steps cost 15.7–25.0 s across
the baselines against 0.051 s for the operator, a factor of 307–488×. We make no asymptotic claim
about the baselines: Barnes-Hut t-SNE is \( O(N \log N) \) and UMAP's graph construction is
sub-quadratic in practice, so the argument on this axis is the measured seconds-scale cost of a refit
inside an interaction loop, not a complexity class.

The visualization community has long treated this instability as a trade-off. Dynamic t-SNE adds a
temporal-coherence penalty across a sequence of datasets, trading projection reliability for
stability (Rauber et al., 2016); guided stable dynamic projections make that trade controllable
(Vernier et al., 2021); and incremental techniques evolve a projection without revisiting the data,
buying speed and stability at the cost of global distance preservation (Neves et al., 2020).
Out-of-sample extension fits once and maps new points through a learned or interpolated function
(Bengio et al., 2003; Sainburg et al., 2021); §3.2 measures that configuration as one of its arms and
finds it still at 5 of 7 growth steps and relocating at the other 2. Surveys of the field treat
stability as one quality axis traded against others rather than a guarantee (Espadoto et al., 2021).

Decoupling itself, however, is cheap. A fixed linear map — a random projection drawn once, or a PCA
fitted once — places a vector without reading the corpus and never moves a placed point, and §3.2
confirms that both hold exactly; §4.1 tabulates both couplings for every method measured. The
constraints of introducing a vector do not, on their own, call for a new primitive.

*Navigating is where they stop being enough.* Moving through one's own notes calls for a view
organized around the note being consulted, which means re-centring the view on it. A fixed map has
one view of the corpus for every query, and on a local neighbourhood-recovery instrument it scores
0.056 (§3.5). Refitting a projection on the consulted note's neighbourhood does re-centre the view,
but by construction it reads the corpus again for every view — re-coupling what the constraints
decoupled — and it still scores only 0.023, at 238× the operator's cost per query.
What is missing is a way to **re-centre the view on the query without re-coupling it to the
corpus**.

The Polar Projector is a local primitive for that. It evaluates one incoming vector against one
active contextual frame — an anchor \( c_1 \) plus a contrast dipole \( (c_A, c_B) \) — in \( O(d) \)
arithmetic and memory, returning a projection coefficient \( \lambda \in [-1, 1] \) and an orthogonal
residual \( d_{esc} \geq 0 \) without reading the stored corpus: 4.57 µs per stimulus with a prepared
frame and 11.75 µs stateless, with correctness guarantees proven in §2. Re-anchoring the frame on the
consulted note re-centres the view without re-coupling it — the poles come from a codebook built once
over the corpus (§3.5, §4.3) — and raises local neighbourhood recovery 29×, from 0.019 to 0.543, for
16.3 µs per query. The result is bounded from the start: a two-line radial coordinate
centred on the query reaches 0.981 on the same instrument, under the same constraints, and most of
the operator's remaining gap is the units of its screen mapping — with \( \lambda \) rendered in length
units it reaches 0.925, in an exploratory ablation (§3.5).

**Contributions.**

- **A local \( O(d) \) operator with a characterized numerical failure mode.** Non-degeneracy is
  proven for collinear poles via a deterministic null-space fallback (Proposition 2), and the residual
  satisfies an orthogonal decomposition identity (Proposition 3). The identity's algebraically
  equivalent scalar form is 1.47× faster and must not be used: below
  \( d_{esc}/\|r\|_2 \approx 10^{-6} \) it returns finite, plausible values wrong by factors of
  \( 10^3 \)–\( 10^5 \), and at two points of the sweep its radicand stays positive, so the failure
  cannot be detected from inside (§2, §B).
- **Decoupling from corpus state is cheap.** A fixed random projection and a once-fitted PCA hold
  every placed point still across all seven growth steps without reading the corpus, exactly as the
  operator does with a fixed frame, so stillness distinguishes nothing on its own. That the random
  projection lands near chance on both fidelity instruments (0.5535 trustworthiness, 1.09× lift)
  shows the instruments are not vacuous (§3.2, §3.3).
- **Re-centring without re-coupling is what a local frame adds, and a radial coordinate does it
  better.** Re-anchoring is worth 29× in local recovery, while a locally refitted PCA re-couples the
  view and recovers less than a global one: moving a linear projection's origin changes no distance,
  and what recovers the neighbourhood is a norm measured from the query (§3.5, §4.1). The radial
  baseline bounds the operator, and the scale ratio of §2.1 is a design rule rather than a free
  constant: in an exploratory ablation it moves local recall across most of its range, while the
  global instruments of §3.2–§3.4 barely change (§3.4, §3.5).

*What this paper is not.* It is not a demonstration that this operator should be preferred to the
alternatives measured here — on every instrument we could construct, some baseline simple enough to
write in a few lines either matches it or beats it (§5) — nor does it establish what \( \lambda \)
is worth as a control signal to a person navigating (§4.3).

*System context.* The requirements above are not hypothetical: the operator was extracted from
Traianus, a local-first engine the author is building at proof-of-concept stage, on which a personal
knowledge management application is built. It is packaged standalone with numpy as its only
dependency, so every figure below can be recomputed or checked against a committed artifact on every
push. *Persistence* — how the system stores and indexes its corpus on disk — is addressed within
Traianus and is out of scope here: *corpus state* in this paper means the content and size of the
stored corpus, not its storage.

## Notation

| Symbol | Meaning |
|---|---|
| \( v_n \in \mathbb{R}^d \) | incoming input vector |
| \( c_1 \in \mathbb{R}^d \) | local anchor centroid (reference vector) |
| \( \hat{c}_1 \) | normalized anchor, \( c_1 / \|c_1\|_2 \), with a zero-guard |
| \( P_\perp \) | rank-1 orthogonal projector \( I - \hat{c}_1\hat{c}_1^T \), applied associatively |
| \( c_A, c_B \in \mathbb{R}^d \) | secondary pole centroids (difference of projected centroids) |
| \( v_{dipole} \) | contrast axis: local basis direction \( P_\perp c_A - P_\perp c_B \) |
| \( u_\perp \) | deterministic null-space fallback direction (perpendicular to \( \hat{c}_1 \)) |
| \( r \) | residual \( P_\perp(v_n - c_1) \) |
| \( \lambda \) | clipped least-squares projection coefficient of \( r \) onto \( v_{dipole} \) |
| \( d_{esc} \) | orthogonal residual norm after regressing out \( v_{dipole} \) |
| \( E_\lambda \) | aligned energy \( \lambda^2 \|v_{dipole}\|_2^2 \) |
| \( E_{esc} \) | residual energy \( d_{esc}^2 \) |

## 2. Main Result

*Proposition 1 (Complexity and Associative Equivalence).* Let \( v_n \in \mathbb{R}^d \) be an
input vector, \( c_1 \in \mathbb{R}^d \) the local anchor centroid, and
\( c_A, c_B \in \mathbb{R}^d \) secondary pole centroids. The anchor is normalized with a zero-guard
threshold \( \epsilon_{norm} > 0 \):

\[ \hat{c}_1 = \begin{cases} c_1 / \|c_1\|_2 & \text{if } \|c_1\|_2 > \epsilon_{norm} \\ 0 & \text{otherwise} \end{cases} \]

The orthogonal projector \( P_\perp: \mathbb{R}^d \to \mathbb{R}^d \), onto the \( (d-1) \)-dimensional
complement of \( \hat{c}_1 \), evaluates associatively as
\( P_\perp v = v - \langle v, \hat{c}_1 \rangle \hat{c}_1 \), in \( O(d) \) time and space without
materializing the dense \( d \times d \) matrix \( I - \hat{c}_1\hat{c}_1^T \). The full evaluation is
\( O(d) \), independent of corpus size \( N \); §3.5 adds the \( O(K \cdot d) \) cost of selecting
poles from a codebook when one is used.

*The null-anchor branch, and what it costs.* When \( \|c_1\|_2 \leq \epsilon_{norm} \) the guard
above sets \( \hat{c}_1 = 0 \), and the implementation proceeds rather than raising. In that branch
\( P_\perp \) is the identity, not a rank-\( (d-1) \) projector, so the signature stated here does
not hold and no anchor component is removed from either pole. Propositions 2 and 3 survive
unchanged — the fallback yields \( \sigma = 1 \) and \( u_\perp = e_k \), still a unit vector, and
the decomposition remains a valid least-squares split of \( r \) onto \( v_{dipole} \) in the full
space — so the operator returns well-defined, non-degenerate values. What is lost is the
*interpretation*: \( \lambda \) and \( d_{esc} \) are then measured against an unanchored dipole,
and the local-frame reading the rest of this paper relies on does not apply. A caller that cannot
guarantee a non-null anchor should treat this branch as a distinct mode, not as a graceful
degradation of the same one.

*Proposition 2 (Guaranteed Dipole Non-Degeneracy).* Assume \( \delta > 0 \),
\( \epsilon_{collinear} > 0 \) and \( d \geq 2 \). Let \( c_A^\perp = P_\perp c_A \),
\( c_B^\perp = P_\perp c_B \). The dipole vector

\[ v_{dipole} = \begin{cases} c_A^\perp - c_B^\perp & \text{if } \|c_A^\perp - c_B^\perp\|_2 \geq \epsilon_{collinear} \\ 2\delta \cdot u_\perp & \text{otherwise} \end{cases} \]

satisfies \( \|v_{dipole}\|_2 \geq \min(\epsilon_{collinear}, 2\delta) > 0 \) for every
configuration. In the degenerate case, \( k = \arg\min_i |\hat{c}_1[i]| \) satisfies
\( |\hat{c}_1[k]| \leq 1/\sqrt{d} \) (RMS bound on a unit vector), so
\( u_\perp = \text{normalize}(e_k - \langle e_k, \hat{c}_1 \rangle \hat{c}_1) \) is well-defined for
\( d \geq 2 \), since \( \|u_\perp^{raw}\|_2^2 \geq 1 - 1/d > 0 \).

*Remark.* Deterministically constructing a vector orthogonal to a single reference vector, without
an arbitrary sign or branch choice, is a well-studied problem in computer graphics for per-pixel
tangent-frame construction (Duff et al., 2017). That work optimizes a branchless, sign-based
construction for GPU evaluation at every shading point; the \( \arg\min \) + Gram-Schmidt
construction here instead targets a single CPU-resident fallback triggered only on the collinear
branch of Proposition 2, where per-call branch cost is irrelevant and analytical simplicity is the
only requirement. The broader principle — resolving geometric degeneracies by a consistent
deterministic rule fixed in advance, rather than by an ad-hoc branch per special case — is the one
*Simulation of Simplicity* establishes (Edelsbrunner & Mücke, 1990). The mechanism here is not
theirs: SoS resolves degeneracies by symbolic infinitesimal perturbation of the inputs, whereas
Proposition 2 substitutes a canonical fallback direction and leaves the inputs untouched. What is
shared is the discipline of making the degenerate case a defined branch with a reproducible answer
instead of an error.

The fallback vector also admits a closed scalar form, since \( e_k \) is one-hot:
\( \langle e_k, \hat{c}_1 \rangle = \hat{c}_1[k] \), and because \( \|\hat{c}_1\|_2 = 1 \),

\[ \|e_k - \hat{c}_1[k]\hat{c}_1\|_2 = \sqrt{1 - \hat{c}_1[k]^2} \]

— an exact identity, not an approximation (expand the square: the cross-term collapses using
\( \sum_{i\neq k}\hat{c}_1[i]^2 = 1-\hat{c}_1[k]^2 \)). This lets \( u_\perp \) be built directly as
\( u_\perp[k] = \sqrt{1-\hat{c}_1[k]^2} \), \( u_\perp[i] = \alpha\hat{c}_1[i] \) for \( i \neq k \),
with \( \alpha = -\hat{c}_1[k]/\sqrt{1-\hat{c}_1[k]^2} \), replacing the \( e_k \) allocation, dot
product, and vector-norm reduction with one scalar square root and a single scaled pass over
\( \hat{c}_1 \). This affects only the rare collinear-fallback branch inside `prepare()` — not the
per-stimulus `evaluate()` hot loop the §3 latency figures characterize — so its benefit is
implementation simplicity for that one branch, not a change to the paper's headline latency claims.

*Proposition 3 (Orthogonal Decomposition).* Let \( r = P_\perp(v_n - c_1) \),
\( \lambda^* = \langle r, v_{dipole} \rangle / \|v_{dipole}\|_2^2 \),
\( \lambda = \text{clip}(\lambda^*, -1, 1) \) (the projection coefficient), and
\( d_{esc} = \|r - \lambda \cdot v_{dipole}\|_2 \) (the orthogonal residual). Decomposing
\( r = \lambda v_{dipole} + (r - \lambda v_{dipole}) \):

\[ \|r\|_2^2 = \|\lambda v_{dipole}\|_2^2 + d_{esc}^2 + 2\lambda(\lambda^* - \lambda)\|v_{dipole}\|_2^2 \]

When \( |\lambda^*| \leq 1 \), \( \lambda = \lambda^* \) and the cross-term vanishes: exact
Pythagorean equality. When \( |\lambda^*| > 1 \) (saturation), \( \lambda = \operatorname{sgn}(\lambda^*) \),
so \( \lambda \) and \( (\lambda^* - \lambda) \) carry the same sign and the cross-term is strictly
positive. The equality therefore weakens to a one-sided bound rather than breaking:

\[ \|r\|_2^2 \;\geq\; \|\lambda v_{dipole}\|_2^2 + d_{esc}^2 \]

with equality exactly when \( |\lambda^*| \leq 1 \). The clipped components never over-account for
the residual's energy; they under-account for it by the cross-term. ∎

*Corollary (Energy Form).* The decomposition above is native to squared (energy) units. Writing
\( E_\lambda = \lambda^2 \|v_{dipole}\|_2^2 \) (aligned energy — computable from \( \lambda \) and
the frame's already-stored \( \|v_{dipole}\|_2^2 \), at no extra cost) and
\( E_{esc} = d_{esc}^2 \) (residual energy), the exact case reads
\( \|r\|_2^2 = E_\lambda + E_{esc} \): a direct sum of energies — the squared-unit form of the same
orthogonal split as the linear quantities \( \lambda, d_{esc} \).
This is an exposition device, not an implementation instruction: \( E_{esc} \) must still be
computed by squaring the numerically stable vector-form residual of §B
(\( \|r - \lambda v_{dipole}\|_2^2 \)), never via the algebraically expanded
\( \langle r,r\rangle - 2\lambda\langle r,v_{dipole}\rangle + \lambda^2\|v_{dipole}\|_2^2 \) — that
expansion is exactly the *scalar form* §B measured losing all precision below
\( d_{esc}/\|r\|_2 \approx 10^{-6} \), which is precisely the near-collinear regime where an energy
reading would most need to be trustworthy.

*Algorithm 1* states the two halves separately, because the split is what the implementation and
§3.1's measurement both turn on: steps 1–12 depend only on the frame \( (c_1, c_A, c_B) \) and run
once per active context, while steps 13–17 are the only work a new stimulus costs.

```
────────────────────────────────────────────────────────────────────────────
 Algorithm 1   Polar Projector — frame preparation and per-stimulus evaluation
────────────────────────────────────────────────────────────────────────────
 PREPARE(c₁, c_A, c_B)                            ▷ once per active context
     require  d ≥ 2,  δ > 0,  ε_norm > 0,  ε_collinear > 0
  1  if ‖c₁‖₂ > ε_norm  then  ĉ₁ ← c₁/‖c₁‖₂   else  ĉ₁ ← 0
  2  c_A⊥ ← c_A − ⟨c_A, ĉ₁⟩·ĉ₁                                      ▷ O(d)
  3  c_B⊥ ← c_B − ⟨c_B, ĉ₁⟩·ĉ₁                                      ▷ O(d)
  4  d_raw ← c_A⊥ − c_B⊥
  5  if ‖d_raw‖₂ ≥ ε_collinear then
  6      v_dipole ← d_raw
  7  else                                    ▷ collinear fallback, Prop. 2
  8      k ← argmin_i |ĉ₁[i]|                ▷ canonical; ties break by index
  9      σ ← √(1 − ĉ₁[k]²)                   ▷ closed form, Remark above
 10      u⊥ ← (−ĉ₁[k]/σ)·ĉ₁ ;   u⊥[k] ← σ    ▷ no e_k, no dot, no norm pass
 11      v_dipole ← 2δ·u⊥
 12  return frame ← (c₁, ĉ₁, v_dipole, ‖v_dipole‖₂²)

 EVALUATE(vₙ, frame)                              ▷ per stimulus, hot path
 13  r ← (vₙ − c₁) − ⟨vₙ − c₁, ĉ₁⟩·ĉ₁                                ▷ O(d)
 14  λ* ← ⟨r, v_dipole⟩ / ‖v_dipole‖₂²          ▷ norm cached in the frame
 15  λ  ← min(max(λ*, −1), 1)                   ▷ scalar clamp, not np.clip
 16  d_esc ← ‖r − λ·v_dipole‖₂                  ▷ vector form, never scalar
 17  return (λ, d_esc)
────────────────────────────────────────────────────────────────────────────
```

Nothing in either half iterates to convergence, draws a random number, or reads persistent storage,
which is what makes Propositions 1–3 hold per call rather than in expectation. Two steps encode
findings reported later rather than obvious choices: step 15 clamps with `min`/`max` instead of
`np.clip` (§A: bit-for-bit identical, 1.40× faster), and step 16 computes the residual in vector
space rather than via the algebraically equivalent scalar rearrangement (§B: the scalar form loses
all precision in the near-collinear regime, undetectably).

### 2.1 Screen Mapping: From \( (\lambda, d_{esc}) \) to a Planar Position

The operator outputs a pair of scalar signals \( (\lambda, d_{esc}) \) per stimulus. To consume them
directly in a spatial interface without a global solver, the pair maps to screen coordinates
\( (X_n, Y_n) \) relative to the anchor's position \( (X_{c_1}, Y_{c_1}) \), using viewport scales
\( S_x, S_y > 0 \):

\[ X_n = X_{c_1} + \lambda \cdot S_x, \qquad Y_n = Y_{c_1} + d_{esc} \cdot S_y \]

With the frame and both scales held fixed, this mapping is affine, so positional stability transfers
directly to screen space. That stability is not a proposition of §2: it follows from the
construction — each position is a pure function of its own vector and the fixed frame — and §3.2
measures it. Trustworthiness is invariant to translation and to uniform scaling, so evaluating it on
\( (\lambda, d_{esc}) \) at a declared ratio \( S_x / S_y \) is the same as evaluating it on
\( (X_n, Y_n) \), the layout this mapping produces.

The coefficient \( \lambda \) measures relative displacement along \( v_{dipole} \). Clamping enforces
\( \lambda \in [-1, 1] \), where \( \pm 1 \) marks the boundary of the domain rather than the pole
locations. In the published frame the initial 500-chunk window holds 409 chunks of P1_GOD and 91 of
P2_MIND, so the anchor \( c_1 \) is a convex combination of the two poles, and the projected poles sit
at \( \lambda = +0.182 \) (\( +91/500 \)) and \( \lambda = -0.818 \) (\( -409/500 \)).

We evaluate two viewport scaling ratios: unit scale (\( S_x = S_y \)), where \( \lambda \) remains an
unscaled coefficient, and isometric scale (\( S_x = \|v_{dipole}\|_2 \cdot S_y \)), which renders both
axes in length units. Whenever \( \lambda \) is unsaturated (\( |\lambda^*| \leq 1 \)), the isometric
scale preserves the scaled anchor-residual distance exactly, as a corollary of Proposition 3:

\[ (X_n - X_{c_1})^2 + (Y_n - Y_{c_1})^2 = S_y^2 \left( \lambda^2 \|v_{dipole}\|_2^2 + d_{esc}^2 \right) = S_y^2 \|r\|_2^2 \]

It preserves the distance to the anchor within its complement, \( \|r\|_2 \), which is at most
\( \|v_n - c_1\|_2 \). Under the isometric scale, pairwise screen distances also contract — never more
than \( S_y \|v_i - v_j\|_2 \) — for every pair of points, saturated ones included:
\( (\lambda \|v_{dipole}\|_2, d_{esc}) \) forms a cylindrical coordinate system in the image of
\( P_\perp \), collapsing the remaining \( d - 2 \) orthogonal dimensions (\( d - 1 \) in the
null-anchor branch of Proposition 1) into the radial distance \( d_{esc} \geq 0 \), and clamping does
not break the bound. At unit scale the horizontal axis is stretched by \( 1 / \|v_{dipole}\|_2 \), and
screen distances can exceed both bounds. The fold forces points to fan upward into the upper
half-plane \( Y_n \geq Y_{c_1} \).

When \( |\lambda^*| > 1 \), stimuli collapse onto the boundary lines \( X_{c_1} \pm S_x \), and under the
isometric scale their screen distance to the anchor strictly underestimates \( S_y \|r\|_2 \).
Throughout, \( d_{esc} \) is the distance from \( r \) to the segment \( [-v_{dipole}, +v_{dipole}] \):
for an unsaturated stimulus the nearest point is interior and \( d_{esc} \) is its distance to the
dipole axis; for a saturated one it is the distance to the nearer endpoint. Saturation affects 11.39%
of the corpus in the static published frame and ranges from 7.7% to 18.8% per step under a moving
anchor (§3.2); across the re-anchored frames of §3.5 its median is 0.68%, an exploratory figure
measured after that section's table existed. Re-anchoring does not translate the viewport: the
anchor's screen position stays at \( (X_{c_1}, Y_{c_1}) \), but moving \( c_1 \) in the embedding space
changes \( \hat{c}_1 \), \( v_{dipole} \) and every stimulus's \( (\lambda, d_{esc}) \), so every point is
re-placed. Finally, \( d_{esc} \) is unbounded above while a viewport is not, so \( S_y \) requires a
clipping policy that this paper does not specify.

When re-anchoring sets \( c_1 = q \) on a unit-normalized corpus, \( \|r\|_2 \) is not monotone in the
angle to the query: \( \|r\|_2 = \sin\theta \), rising to 1 at \( \theta = 90° \) and falling back
toward 0 as \( \theta \to 180° \). A stimulus diametrically opposed to the query lands on the anchor
itself, on screen indistinguishable from the query's own nearest neighbours.

![The published frame's 2,221 chunks placed on screen. Left, unit scale (\( S_x = S_y \)): \( \lambda \) spans the full width and the saturated stimuli, 11.39% of the corpus, collapse onto the clamp lines \( \lambda = \pm 1 \). Right, isometric scale (\( S_x = \|v_{dipole}\|_2 \cdot S_y \)), same data and equal aspect: both axes are lengths and the horizontal spread shrinks accordingly. The poles sit at \( \lambda = +0.182 \) and \( \lambda = -0.818 \), not at \( \pm 1 \).](figures/fig1_screen_mapping.png)

## 3. Numerical Behavior

All figures in this section were measured on one machine: Apple M1 (8 cores), 8 GB RAM, macOS
15.6, Python 3.11.6, NumPy 2.4.1. The machine is passively cooled, so sustained runs are subject to
thermal throttling; the run-to-run spreads reported below are what that variability amounts to in
practice. Absolute microsecond figures are properties of this host, not of the operator — the
claims that do not depend on the host are the *scaling* behaviour and the *ratios* between arms.

Stateless cost against corpus size, on synthetic unit vectors at \( d = 384 \), float64:

| Corpus size (N) | Mean (µs) | p95 (µs) |
|---|---|---|
| 1,000 | 11.46 | 11.92 |
| 2,221 | 11.61 | 11.79 |
| 4,000 | 11.61 | 12.21 |
| 25,000 | 11.58 | 12.00 |

Latency stays flat as \( N \) grows — 1.4% across a 25× corpus and a 25× working set, consistent
with Proposition 1's independence from corpus size. `bench/latency.py --n-sweep`, 3 repetitions per
row. Spreads and ratios throughout this manuscript are computed on unrounded measurements; reading
them off the two-decimal figures printed in a table — 11.46 to 11.61 here — gives 1.3%, not 1.4%.

### 3.1 Frame Preparation vs. Per-Stimulus Cost

The anchor normalization, dipole-pole projections and dipole construction of Proposition 1 depend
only on \( (c_1, c_A, c_B) \) — not on \( v_n \) — so they are invariant across every stimulus
evaluated under one active context. Splitting the operator into `prepare()` (frame construction)
and `evaluate()` (per-stimulus) separates the two costs; bracketing the result between the least
and the most work a planar local coordinate could require places it in its complexity class:

| Arm | Mean (µs) | p95 (µs) | Relative cost |
|---|---|---|---|
| Random projection, \( (2 \times d) \) matrix-vector | 1.03 | 1.08 | 0.23× |
| Multi-anchor cosine, \( K = 3 \) | 1.14 | 1.21 | 0.25× |
| **`evaluate()` — per stimulus, prepared frame** | **4.57** | 4.79 | **1.00×** |
| `prepare()` — invariant frame, once per context † | 6.87 | 7.21 | 1.50× |
| `project()` — full stateless call | 11.75 | 12.50 | 2.57× |
| Sliding-window PCA, \( W = 32 \) | 292.55 | 316.67 | 64.02× |

Frozen Spinoza corpus (\( N = 2{,}221 \), \( d = 384 \), float64), 3 repetitions of 2,221 calls
after 1,000 warmup iterations, arms interleaved round-robin; `bench/latency.py`. Run-to-run spread
is 2.5–2.8% on the polar arms and 0.5–2.5% elsewhere; `bench/_harness.py` reports the median across
repetitions and the peak-to-peak spread alongside it, and rotates arm order so that no arm is
permanently measured on the coolest machine.

† The `prepare()` row and the stateless decomposition come from an independent script on a
different frame (`tools/decompose_polar_latency.py`, artifact `bench/results/decompose.json`):
11.51 µs stateless
against the 11.75 measured here, with `prepare()` accounting for 59.7% of it. That script reports
the median of 3 repetitions rather than a single pass, because on this passively cooled host single
passes were observed inflated by thermal throttling; the per-repetition means are recorded in the
artifact, and their spread on `evaluate()` is 0.5%.

Two things follow, in opposite directions. Hoisting the frame out of the loop leaves **2.57× less
work per interaction** whenever the active context outlives a single stimulus — which, for an
interface where one anchor serves a whole navigation gesture, is the common case rather than the
optimization. But the operator is **not at the floor**: it costs 4.4× a random projection and 4.0× a
three-anchor cosine, and that gap is the price of what it additionally computes — anchor isolation, a
contrast axis, and a residual orthogonal to it. What it buys against the other end of the table is
larger: a locally adaptive frame by sliding-window SVD costs **64.0×** the prepared evaluation,
which is the comparison that matters for a hot path.

*The prepared path is flat in the working set, not just in \( N \).* The table above is the frozen
Spinoza corpus at 6.8 MB, largely cache-resident on this host. Repeating the whole experiment on the
synthetic corpus at \( N = 25{,}000 \) — 76.8 MB, which is not — moves `evaluate()` from 4.57 to
4.59 µs: **0.4% for 11× the working set.** The per-call cost is not memory-bound at these sizes, so
the \( N \)-sweep above and the figures here are comparable, and the flatness claim covers the
prepared path and not only the stateless one.

*What these figures do not establish is that the gap is arithmetic.* At \( d = 384 \) roughly 90% of
the per-call cost is fixed NumPy dispatch overhead independent of dimension, and only about 0.4 µs of
it is the \( O(d) \) work Proposition 1 describes; the crossover where the asymptotic claim becomes
visible sits between \( d = 1{,}024 \) and \( d = 4{,}096 \). §A measures this and states what it
narrows. Every latency figure in this paper also reflects one substitution — clamping \( \lambda \)
with `min`/`max` rather than `np.clip`, bit-for-bit identical on every input and 1.40× faster — also
documented in §A; no table of *values* anywhere in this paper is affected by it.

### 3.2 Positional Stability Under Incremental Growth

§1 states that refitting a global projection relocates placed points as the corpus grows, and that a
fixed map does not. This section measures both, against a corpus with real semantic structure rather than synthetic
blobs: 2,221 sentence-chunks of Spinoza's *Ethics* embedded at \( d = 384 \) with
`all-MiniLM-L6-v2` (Reimers & Gurevych, 2019) at a pinned revision and L2-normalized; the
embeddings, labels and their SHA-256 digests are committed in `bench/data/`. The corpus grows in reading order from 500 chunks in batches of 250, and at each of
the 7 transitions we measure how far the points **already present and unchanged** moved.

*Method.* Layouts produced by UMAP and t-SNE are defined only up to a similarity transform, so raw
displacement largely measures global reorientation — which an interface could absorb by
re-anchoring its camera, and which the baselines should not be charged for. Displacement is
therefore reported after full Procrustes alignment (translation, rotation, scale; Gower, 1975), and
normalized
by each embedding's own RMS radius, since the coordinate spaces are not commensurable (UMAP's units
are arbitrary; the operator's are \( (\lambda, d_{esc}) \) with \( \lambda \in [-1,1] \)). A value
of 1.0 means points moved as far as the layout is wide. Both baselines run with a fixed
`random_state`: demonstrating that an unseeded stochastic method is unstable would prove nothing,
so what is reported is the drift that *survives* seeding. Alignment is not a cosmetic correction —
for UMAP under refitting it reduces the median p95 from 5.81 to 1.16, so roughly 80% of the
apparent movement is global reorientation that the charitable reading forgives.

| Arm | Median step | Worst step | Still steps | Trustworthiness | Worst step (isometric) | Trustworthiness (isometric) |
|---|---|---|---|---|---|---|
| Fixed random projection, \( 2 \times d \) | **0.0000** | 0.0000 | **7/7** | 0.5535 | — | — |
| PCA, fit once on the initial window | **0.0000** | 0.0000 | **7/7** | 0.6811 | — | — |
| Polar Projector, fixed anchor | **0.0000** | 0.0000 | **7/7** | 0.6639 | 0.0000 | 0.6666 |
| Polar Projector, moving anchor | 0.2984 | 0.6138 | 0/7 | 0.6208 | 0.8144 | 0.6235 |
| UMAP, fit once + `transform()` | 0.0000 | 1.0725 | 5/7 | 0.7681 | — | — |
| UMAP, refit per step | 1.1607 | 1.2527 | 0/7 | 0.9049 | — | — |
| t-SNE, refit per step | 1.1408 | 1.2439 | 0/7 | **0.9197** | — | — |

Aligned p95 displacement per growth step; "still" counts steps under \( 10^{-9} \).
Trustworthiness (\( k = 15 \); Venna & Kaski, 2001) of the final layout against the source 384D
space measures neighborhood preservation. Apple M1, 8 GB, macOS 15.6, Python 3.11.6, NumPy 2.4.1;
`bench/drift.py`, deterministic under a fixed seed and reproduced bit-for-bit across runs.
Unmarked columns render the operator at \( S_x = S_y \) (§2.1). The isometric columns render its
\( \lambda \) in multiples of its frame's \( \|v_{dipole}\|_2 \), so both of its axes are lengths, as
the other arms' already are; they apply to the operator's rows only, since no other arm has a
\( \lambda \) axis (`bench/scale.py`, whose unit scale reproduces the unmarked columns exactly).

![Aligned p95 displacement of previously placed points at each growth step, at unit scale (§3.2). The seed-pinned refits relocate points at every step; UMAP fitted once is still except at two steps, where it relocates by 0.39 and 1.07; the moving-anchor operator drifts by 0.13–0.61; the fixed random projection, the once-fitted PCA and the fixed-anchor operator stay at 0.0000.](figures/fig2_displacement.png)

*What the stability column does not show.* Three arms are still at 7 of 7 steps, and two of them
are a Gaussian matrix and an SVD. A fixed linear map's coordinates are a pure function of the
vector, so no amount of new data can move a placed point — in \( O(d) \), deterministically, with
no guard needed. The operator's stillness is therefore not a finding, and the first two rows exist
so that it cannot be read as one. What the two rows do establish is that the fidelity column is not
vacuous: a random projection is the cheapest thing that is exactly stable and it lands at 0.5535,
so the numbers above it are measuring something. A once-fitted PCA lands at 0.6811, above the
operator's 0.6639 (0.6666 with \( \lambda \) in length units) — the comparison §3.4 takes up, since it
depends on how the operator's poles are chosen.

*What the displacement column does show.* Under refitting — the path required to keep a global
layout faithful as a corpus grows — both global baselines relocate previously-placed points at
every single step, with the seed pinned.
This is not seed noise; it is what refitting does. t-SNE moves them by 1.03–1.24 times the layout
width on all 7 transitions; UMAP's per-step range is wider and reaches lower, 0.31–1.25 with a
median of 1.16, so "roughly the full width, always" overstates UMAP specifically even though it
never reaches stillness. The operator with a fixed anchor is still at all 7 steps to float64
rounding — aligned p95 between \( 4.3 \times 10^{-16} \) and \( 5.0 \times 10^{-15} \), which is
zero at the resolution the arithmetic affords, not an exact algebraic zero.

*What does not.* Three results cut against the simple reading.

First, UMAP fitted once and extended by `transform()` — the out-of-sample configuration §1 names
(Bengio et al., 2003) — is not steadily unstable; it is intermittent. It is exactly still for 5 of 7
steps and relocates at the other two, by 0.39 and then 1.07. Averaging across steps yields 0.21, a
figure that describes none of the steps that actually happen; the aggregation here is
median-and-worst for that reason. Whether intermittent relocation is better or worse than steady
drift is not settled by this measurement: a spatial mental model that is confirmed several times and
then violated may be harmed more than one that is never trusted. §4.3 records it as open.

Second: **the operator is the least faithful arm in the table.** Its trustworthiness (0.6639 fixed,
0.6208 moving; 0.6666 and 0.6235 with \( \lambda \) in length units) sits below the refit baselines
(0.9049–0.9197) and below fit-once UMAP (0.7681). Part of that gap is a category difference — the
operator never constructs a global layout, and trustworthiness scores exactly the thing it does not
attempt. It is not purely a category error: §2.1 maps \( (\lambda, d_{esc}) \) to a planar position,
and under that reading the metric is a fair question. What this section supports is a trade, not a
win: **exact positional stability and a growth schedule more than two orders of magnitude cheaper,
paid for in neighborhood fidelity** — and the first two rows of the table show that the stability
half of that trade is available without the operator.

Third, the moving-anchor arm drifts. It must: the operator's output is anchor-relative by
construction, so \( \lambda \) and \( d_{esc} \) change when \( c_1 \) does, and a paper reporting
only the fixed-anchor row would be claiming a stability the operator does not have. What the
measurement shows is that this drift stays bounded — 0.13–0.61 across steps at unit scale, worst
step 0.8144 with \( \lambda \) in length units, which includes the per-step change of aspect ratio
declared before that measurement — and never exhibits the relocation spikes of fit-once UMAP. The defensible claim is accordingly narrower than "no drift",
and stronger: **drift is a deterministic function of one explicit, caller-controlled variable, not
of hidden stochastic state and not of corpus size.**

*Scope.* Comparing a per-interaction local operator against global layout algorithms is a
task-level comparison, not an algorithm-level one: these methods do not compute the same object.
It is included because §1 names them as what practitioners reach for, and a claim about displacing
them should be measured rather than asserted. The mismatch is a limitation of the comparison, and
the trustworthiness column is where it shows.

### 3.3 Task-Level Neighborhood Preservation: Same-Part Retrieval

§3.2's trustworthiness column leaves open whether that instrument is even the right one for a
per-interaction signal. This section gives a second,
task-shaped instrument on the same corpus and the same growth schedule, and lets a reader judge the
fidelity gap against something more concrete than a manifold-preservation score: if a reader asked
"what else is like this point," what fraction of the answer would come from the same part of the
*Ethics* the point itself belongs to?

*Method.* At each of the same eight growth steps as §3.2, and for every arm's 2D output at that
step — \((\lambda, d_{esc})\) for the operator, an arbitrary 2D layout for the baselines —
recall@15 measures, for every point, what fraction of its 15 nearest neighbours in that 2D space
share its `part` label (P1_GOD .. P5_POWER; `bench/data/PROVENANCE.json`). The frozen corpus is read
in part order, so the prefix at size 500 is far more lopsided across parts than the full
2,221-chunk corpus, and a uniformly-random neighbour already matches by chance far more often early
(chance ≈ 0.70) than late (chance ≈ 0.22). What is reported is *lift* — recall@15 divided by that
step's own chance level — the same kind of correction §3.2 already applies when it normalizes
displacement by RMS radius rather than comparing raw coordinates. `bench/recall.py`; deterministic
under the same fixed seed as §3.2, reusing its embeddings rather than recomputing UMAP/t-SNE/polar
coordinates a third way.

| Arm | Median lift | Final-step lift | Worst-step lift | Median lift (isometric) | Worst-step lift (isometric) |
|---|---:|---:|---:|---:|---:|
| Fixed random projection, \( 2 \times d \) | 1.09× | 1.10× | 0.99× | — | — |
| PCA, fit once on the initial window | 1.47× | 1.48× | 1.01× | — | — |
| Polar Projector, fixed anchor | 1.57× | 1.59× | **1.17×** | 1.59× | **1.17×** |
| Polar Projector, moving anchor | 1.39× | 1.34× | 1.17× | 1.41× | 1.17× |
| UMAP, fit once + `transform()` | 1.57× | 1.57× | 1.12× | — | — |
| UMAP, refit per step | 2.05× | 2.41× | 1.12× | — | — |
| t-SNE, refit per step | **2.12×** | **2.47×** | 1.10× | — | — |

1× = no better than a uniformly random neighbour at that step's part composition. Worst-step is the
first step (size=500) for every arm, without exception — a property of the corpus at that size, not
of any arm; see below. Isometric columns as in §3.2.

*The instrument discriminates.* A fixed random projection scores 1.09× median and 0.99× at its
worst step — chance, to within measurement. Whatever the arms above it are doing, it is not an
artifact of projecting 384 dimensions onto two. That is the check §3.2's stability column could not
provide, and it is why this instrument carries more of the paper's weight than trustworthiness does.

*What holds.* Against this instrument the fixed-anchor operator is level with fit-once UMAP to two
decimals — 1.57× median lift for both, 1.59× against 1.57× at the final step; no significance test
was run. It also leads the once-fitted PCA that beat it on trustworthiness — 1.57× against 1.47×
(1.59× with \( \lambda \) in length units), and 1.17× against 1.01× at the smallest corpus, where the
PCA finds no more signal than chance. That lead has a caveat: the published frame's contrast axis is
built from the `part` labels of the initial window, the same labels this instrument scores, while the
PCA sees no labels; §3.4 shows the label-free rules landing level with the PCA. The two instruments
disagree about that pair, which §3.4 resolves into a property of pole selection rather than of either
method. It is also a closer race
with fit-once UMAP than §3.2's trustworthiness column shows (0.6639 against 0.7681): the two arms
that never fully re-account for new data land in the same place on a task a reader can interpret
directly.

*What does not.* The refit baselines pull ahead as the corpus grows rather than staying level: both
t-SNE and UMAP-refit cross 2× lift by the middle of the growth schedule and reach 2.41–2.47× by the
final step, while the operator and fit-once UMAP stay within 1.40–1.62× after the first step. That
is the same story §3.2 already tells about trustworthiness (0.9049–0.9197 for the refit arms against
0.6208–0.7681 for the operator and fit-once UMAP) — refitting buys measurably more locally-coherent neighbourhoods, on this task as on that
one, and it buys it at exactly the cost §3.2 measures: relocating previously-placed points at
every step — t-SNE by 1.03–1.24 times the layout width, UMAP by 0.31–1.25.

*The worst-step column does not discriminate.* Every
arm's lowest lift is its first step, where the 500-chunk prefix is almost entirely one or two parts
and chance is already 0.70 — there is little headroom above chance for any method to demonstrate
anything. A table reporting only worst-case lift would flatten a real difference between arms into
a number that is mostly measuring the corpus at that size, not the arm; median and final-step lift
are reported alongside it for that reason.

*Scope.* This instrument answers a narrower question than trustworthiness — same-part agreement
among 15 neighbours, not preservation of the full 384-dimensional neighborhood structure — and
`part` is a coarse five-way proxy for semantic relevance, not a ground truth of what a reader would
actually judge relevant (§4.3).

### 3.4 Pole Selection as a Trade-off Knob

Every figure in §3.2 and §3.3 is measured against one contextual frame: the anchor is the mean of
the initial window and the contrast axis comes from the two most-represented parts in it. So
trustworthiness 0.6639 and lift 1.57× are properties of *that* frame, and a single number with no
range beside it understates how much of the result is the operator and how much is the choice.

*Method.* Two sweeps on the frozen corpus and the same growth schedule, `bench/frame_sensitivity.py`.
The first varies the contrast axis over all ten unordered pairs of the corpus's five part centroids,
which bounds how far the figures move when the axis moves. Those centroids use whole-corpus labels
the production rule does not have, so the second sweep evaluates four rules that see only the
initial window — the information a system would actually hold at step 0. Three of them use no labels;
the published rule uses the window's `part` labels, which are also what same-part lift scores. The anchor is unchanged
throughout. Drift is not reported per rule: a fixed frame cannot drift, and every frame here is
still at every step to float64 resolution, which confirms the construction rather than
discriminating between choices.

| Selection rule (initial window only) | Trustworthiness | Median lift | Worst-step lift | Trustworthiness (isometric) | Median lift (isometric) | Worst-step lift (isometric) |
|---|---:|---:|---:|---:|---:|---:|
| `farthest_neighbourhoods` | 0.6593 | 1.42× | 1.03× | 0.6623 | 1.42× | 1.03× |
| Two largest parts — **the rule §3.2 and §3.3 publish** | 0.6639 | **1.57×** | **1.17×** | 0.6666 | **1.59×** | **1.17×** |
| *PCA, fit once — the baseline to clear* | *0.6811* | *1.47×* | *1.01×* | *0.6811* | *1.47×* | *1.01×* |
| `kmeans2`, label-free | 0.6858 | 1.46× | 1.01× | 0.6863 | 1.46× | 1.01× |
| First-PC deciles | **0.6966** | 1.46× | 1.01× | **0.6968** | 1.45× | 1.01× |

Isometric columns as in §3.2; the PCA row has no \( \lambda \) axis and is repeated unchanged.

Varying the axis over whole-corpus part centroids instead gives trustworthiness 0.6950 in
\( [0.6664, 0.7029] \) and median lift 1.6830 in \( [1.4273, 1.7258] \) across the ten pairs.

*The declared scale does not move this section.* Rendering \( \lambda \) in length units changes
trustworthiness by at most 0.003 and median lift by at most 0.02 across the operator's arms and the
four rules, and none of the orderings the rest of this section reads changes: the operator stays
below the PCA on trustworthiness and above it on lift, the part-based rule keeps 1.17× at 500 chunks,
and the rules keep their order on both metrics. That comparison was registered before it was run
(`bench/scale.py`); the paragraphs below read the unit-scale columns, and their conclusions hold at
both scales.

*The figures we publish are the pessimistic end of one axis and the optimistic end of the other.*
At unit scale the published frame's 0.6639 sits below the minimum of the ten-pair trustworthiness
range, and its
1.57× above their median lift. Neither was chosen for that; the rule was fixed before either sweep
existed. But it means a reader taking 0.6639 as "the operator's fidelity" is taking the worst axis
we measured, and one taking 1.57× as "the operator's task performance" is taking close to the best.

*No leak is needed to clear the PCA baseline.* Two rules that see only the initial window pass
0.6811, and the first-PC rule reaches 0.6966 — the top of the leaked range. The rule, not the
operator, was leaving fidelity on the table.

*But nothing is gained.* Read the two right-hand columns against the first: every rule that gains
trustworthiness loses task-level lift, and the first-PC rule lands within noise of the once-fitted
PCA on *both* instruments (0.6966 against 0.6811; 1.46× against 1.47×). That rule was written to
test a specific hypothesis — that the PCA's fidelity advantage is variance alignment — and the
result confirms it in the least flattering way available: pointing the dipole down the axis of
maximum variance makes the operator behave like the fixed linear map it was supposed to improve on.
Pole selection is a position on a trade-off, and a fixed PCA occupies one end of it.

*Where the operator appears not interchangeable with a PCA* is the other end, and this sweep cannot
settle it. The part-based rule is the only one in the table holding 1.17× on the 500-chunk corpus;
the other three rules and the PCA all sit at 1.01–1.03×, which is chance. But it is also the only rule
that reads labels, and at 500 chunks the labels it reads are exactly the ones lift is scored against.
Whether that 1.17× comes from building the axis out of semantic groups or from supervision on the
evaluated labels is not separable here; no label-free rule measured beats the PCA on lift.

### 3.5 Re-anchoring: A Movable Origin

§3.2 and §3.3 both evaluate a single static layout, and that is the one regime in which a fixed
linear map competes on equal terms — §3.4 ends with the operator and a once-fitted PCA
interchangeable. Neither instrument touches the property that distinguishes them. A fixed map has
one view of the corpus, for every query, permanently. The operator's coordinates are
anchor-relative, so moving the active context yields a different view, and §2.1 shows that moving
it re-places every point by construction. Re-anchoring costs a codebook scan and one `prepare()` —
\( O(K \cdot d) \), no corpus access at query time. In the terms of the question this paper answers,
it re-centres the view on the query without re-coupling the view to the corpus; the refit below
re-centres only by reading the corpus again.

*Method.* 50 query chunks sampled under a fixed seed. For each query \( q \), local recall@15: of
\( q \)'s 15 true nearest neighbours in the source 384-dimensional space, how many are among its 15
nearest in the arm's two-dimensional view, with all 2,221 points placed in that view. Chance is
\( 15/2220 \approx 0.0068 \), so these are raw recalls — *of the fifteen notes really closest to
this one, how many land next to it on screen*. `bench/reanchor.py`.

| Arm | Mean | Median | Min | Max |
|---|---:|---:|---:|---:|
| PCA fit on the whole corpus, one view | 0.056 | 0.033 | 0.000 | 0.267 |
| Polar, the frame §3.2 publishes, one view | 0.019 | 0.000 | 0.000 | 0.133 |
| PCA refit per query on its 100 neighbours | 0.023 | 0.000 | 0.000 | 0.533 |
| **Polar, re-anchored on the query** | **0.543** | **0.567** | 0.133 | 0.867 |
| Radial \( (\langle v-q, e\rangle, \|v-q\|) \) | **0.981** | **1.000** | 0.933 | 1.000 |

The arms do different work at different moments, so cost is reported per operation rather than as
one figure, with each column timing the same operation for every arm:

| Arm | Once (ms) | Query (µs) | Stimulus (µs) | View (ms) | Loop (ms) |
|---|---:|---:|---:|---:|---:|
| PCA, whole corpus | 63.7 | — | 1.56 | 1.75 | 3.2 |
| Polar, published frame | 0.24 | — | 4.58 | 3.71 | 10.1 |
| PCA, local refit | — | 3,889 | 1.52 | 5.81 | 7.2 |
| **Polar, re-anchored** | 581 | **16.3** | 4.64 | 3.67 | 10.4 |
| Radial | — | — | 1.97 | **1.99** | **4.3** |

*Once* is paid over the whole corpus before any query: the global PCA's fit, the published frame's
centroids and `prepare()`, the re-anchoring codebook. *Query* is paid each time the view re-centres,
before any point is placed: the local PCA's neighbour scan and refit, the re-anchored arm's codebook
scan and `prepare()`. *Stimulus* places one further vector in a view that already exists, through each
arm's scalar path. *View* and *Loop* are one full refresh for one query — the per-query step plus all
2,221 points, placed as a single array operation or one at a time. A dash marks a step the arm does
not have by construction. Timings are medians of five interleaved repetitions on the host of §3; the
artifact records each column's spread.

Poles for the re-anchored arm come from a 16-entry codebook built once over the corpus by k-means;
per-query selection is the \( O(K \cdot d) \) codebook scan Proposition 1 already accounts for, so
nothing here consults the corpus at query time. The build is not free: at 581 ms it is the most
expensive single step in the table, 9.1× the global PCA's fit, and a growing corpus would require
repeating it (§4.3).

*Re-centring is cheap; refreshing the view is not specific to it.* The per-query column isolates the
step that re-centring adds, and there the operator's 16.3 µs is 238× less than the local PCA's scan
and refit. A full refresh still places every stored point, which is \( O(N \cdot d) \) for every arm
in the table. Vectorized, the re-anchored view costs 3.67 ms against 5.81 ms for the local PCA and
1.99 ms for the radial coordinate. One point at a time the operator is the most expensive of the
three — 10.4 ms against 7.2 and 4.3 ms — because its per-stimulus path (4.64 µs) outweighs its cheaper
frame. At this corpus size every refresh in the table is shorter than one frame of a 60 Hz display,
so cost does not separate the arms here; the ordering that holds at both granularities is that the
radial coordinate is cheaper than the operator.

*The movable origin is the lever, and it is large.* The same operator goes from 0.019 to 0.543
purely by moving the anchor to the query — a factor of 29. This is the first measurement in this
paper where a property specific to a local frame produces a difference of that size.

*Better directions are not the lever, and they re-couple the view.* The refitted PCA scores 0.023,
*below* the global fit's 0.056, and the reason is visible in the construction. Moving a linear
projection's origin changes none of the distances in its view, and its two locally fitted components
discard all but two of the 384 dimensions, so points far from \( q \) in the discarded ones land on
top of it. Refitting the directions on the query's own neighbourhood — paying 238× the re-anchored
arm's per-query cost and, by construction, scanning the corpus for that neighbourhood before every
view — buys less than not refitting at all. Whatever value the local frame has here comes from where
it measures *from*, not from which directions it measures *along*.

*The radial baseline leads, but most of the gap is the screen mapping's units.* A coordinate system
whose vertical axis is simply \( \|v - q\| \) and whose horizontal axis is the projection onto an
arbitrary fixed unit vector reaches 0.981 — median 1.000, minimum 0.933 — at 1.97 µs per stimulus
against the operator's 4.64, and with nothing to build once or per query. It satisfies every
constraint §1 states: \( O(d) \) per stimulus, no corpus access, exactly stable for a fixed \( q \),
fully deterministic.
Decomposing the operator's view on the same queries and frames locates its 0.543
(`bench/reanchor.py --ablation`; exploratory, specified after the table above existed):

| View of the re-anchored frame | Mean | Median |
|---|---:|---:|
| \( (\lambda, d_{esc}) \) — the operator at \( S_x = S_y \) | 0.543 | 0.567 |
| \( (\lambda^*, \|r - \lambda^* v_{dipole}\|_2) \) — clamp removed | 0.543 | 0.567 |
| \( (0, d_{esc}) \) | 0.485 | 0.467 |
| \( (0, \|r\|_2) \) | 1.000 | 1.000 |
| \( (\|v_{dipole}\|_2 \cdot \lambda,\ d_{esc}) \) — \( \lambda \) in length units | **0.925** | **1.000** |

Removing the clamp changes nothing. \( d_{esc} \) read alone does lose the neighbourhood, but the
residual it is split from loses none of it: \( \|r\|_2 \) by itself recovers every neighbour of every
query, so the information is intact in the pair. What the view gets wrong is its **units**.
\( \lambda \) is a coefficient in multiples of \( \|v_{dipole}\|_2 \) — median 0.463 across these
frames, range 0.313–0.647 — while \( d_{esc} \) is a length, so rendering both at \( S_x = S_y \)
stretches the horizontal axis roughly twofold against the vertical. The scale ratio alone moves the
result across most of its range: \( (s\lambda, d_{esc}) \) scores 0.511, 0.628, 0.857, 0.543 and
0.344 at \( s = 0.1, 0.25, 0.5, 1, 2 \). At \( s = \|v_{dipole}\|_2 \), Proposition 3 makes the
view's distance from the query exactly \( \|r\|_2 \) wherever \( \lambda \) is unsaturated, and the
operator reaches 0.925 with a median of 1.000. Because \( \|r\|_2 \) alone scores 1.000, what
remains between 0.925 and \( \|r\|_2 \) alone can only come from saturated stimuli, where
Proposition 3 is an inequality and the view places them closer to the query than they are; the
gap to the radial baseline's 0.981 is not established to have the same cause.

![Local recall@15 of the re-anchored operator as the screen ratio \( s = S_x / S_y \) varies, from the exploratory ablation. The unit scale (\( s = 1 \)) gives 0.543. Rendering \( \lambda \) in length units sets \( s = \|v_{dipole}\|_2 \) frame by frame, plotted at its median 0.463, and gives 0.925. The radial coordinate reaches 0.981 and \( \|r\|_2 \) alone 1.000.](figures/fig3_scale_ratio.png)

*What that leaves the instrument able to settle.* Local recall@15 rewards any view whose distance
from the query is monotone in true distance. The radial baseline's vertical axis is exactly that, for
every stimulus. The operator's is not: with \( c_1 = q \), \( \|r\|_2 = \sin\theta \) is monotone only
up to \( \theta = 90° \) and folds back toward the anchor beyond it (§2.1). The fold costs recall only
if some chunk lies far enough past 90° to land among a query's nearest on screen, and on this corpus
none does for the queries measured: \( \|r\|_2 \) alone scores 1.000. That is a property of this
corpus, not of the instrument — a corpus holding near-opposite notes would expose the fold — and it is
why the two views are close on this instrument — 0.981 against 0.925 — rather than separated by the
factor the unscaled row suggests. The defensible conclusions are the two above —
re-anchoring matters, refitting directions does not — plus a design rule for §2.1: the scale ratio
is not a free viewport constant, and \( S_x = \|v_{dipole}\|_2\, S_y \) is the ratio that preserves
distance from the anchor. What the instrument cannot do is distinguish the two arms on what the
construction was built for, a contrast coordinate between two chosen poles; §4.3 records what a test
of that would have to measure.

## 4. Discussion

### 4.1 What the Results Answer

The question this paper answers concerns two ways the interaction can be coupled to the state of the
corpus: placed points moving as the corpus grows, and the corpus being read to place a point. The
table arranges every measured method along both. Its middle column is a fact of each method's
construction, not a measurement.

| Method | Moves placed points as the corpus grows (§3.2) | Reads the stored corpus to place a point (construction) | Local recall@15 (§3.5) |
|---|---|---|---:|
| UMAP or t-SNE, refit per step | yes, at every step | yes | — |
| UMAP, fit once + `transform()` | at 2 of 7 steps | yes, its own training set | — |
| Fixed random projection | no | no | — |
| PCA, fit once | no | no, after fitting | 0.056 |
| PCA, refit on the query's neighbourhood | not measured | yes | 0.023 |
| Operator, the published frame | no | no | 0.019 |
| Operator, re-anchored on the query | not measured | no, beyond a codebook built once | 0.543 |
| Radial coordinate centred on the query | not measured | no | 0.981 |

"—": not measured on that instrument. The PCA of §3.2 is fitted on the initial window and that of
§3.5 on the whole corpus; both stay fixed after fitting. Local recall is at unit scale; with
\( \lambda \) rendered in length units the re-anchored operator reaches 0.925 (exploratory, §3.5).

*Positional stability does not distinguish the operator.* Any map whose output is a pure function
of the vector and of parameters that do not change is exactly still — a Gaussian projection, a PCA
frozen after the initial window, and the operator with a fixed frame all hold placed points at
0.0000 (§3.2), while UMAP fitted once and merely *avoiding* re-optimization still relocates points
twice. Stability is a precondition this design meets, not a property that sets it apart.

*Re-centring the origin, not reorienting the axes, is the lever for local navigation.* Moving the
anchor to the query raises local neighbourhood recovery 29×, while refitting the projection's
directions on the query's own neighbourhood recovers less than not refitting at all (§3.5):
translation changes no pairwise distance in a linear view, so a two-axis refit still discards the
382 dimensions it never measured. What re-anchoring adds instead is a coordinate that is a norm
measured from the query, but not the radial baseline's norm — removing \( \hat{c}_1 \) discards
exactly the component that would disambiguate near from far, so \( \|r\|_2 = \sin\theta \) folds
back past \( \theta = 90° \) while the radial baseline's \( \|v - q\|_2 = 2\sin(\theta/2) \) does not
(§2.1), a fold recall@15 does not register on this corpus, where \( \|r\|_2 \) alone scores 1.000 (§3.5). What
local exploration needs is an origin that moves with the query; whether a bounded contrast axis adds
anything beyond that is a separate, open question (§4.3).

*The operator's remaining gap to the radial baseline was mostly a unit mismatch.* Rendering
\( \lambda \) under the isometric rule (\( S_x = \|v_{dipole}\|_2 \cdot S_y \)) makes the screen
distance to the query equal \( \|r\|_2 \) for unsaturated stimuli (Proposition 3), raising recall
from 0.543 to 0.925 (§3.5). What separates 0.925 from \( \|r\|_2 \) alone can only come from saturated
stimuli; the gap to the radial baseline's 0.981 is not established to have the same cause. The fix is free everywhere else: on the global evaluations of §3.2–§3.4 it moves
trustworthiness by at most 0.003 and lift by at most 0.02, changing no ordering.

### 4.2 Relation to Prior Work

The Polar Projector combines known linear-algebra identities into a volatile primitive oriented to
human-computer interaction:

- **Rank-1 orthogonal complement and Gram-Schmidt.** \( P_\perp v = v - \langle v, \hat{c}_1 \rangle
  \hat{c}_1 \) (§2) is the classical projection onto the orthogonal complement of the anchor — the
  same identity as a single Gram-Schmidt step, evaluated associatively to avoid the dense
  \( d \times d \) matrix.
- **Embedding debiasing.** Removing a subspace with \( P_\perp \) is the same projection used to
  debias word embeddings (Bolukbasi et al., 2016) when the removed bias subspace is one-dimensional;
  the difference is when and where it is applied. Bolukbasi et al. use it as a global, static,
  one-time preprocessing step that permanently alters the stored embeddings, while the Polar
  Projector applies it per interaction against an active anchor, without touching persisted
  representations.
- **Centroid-difference and semantic axes.** Projecting onto the difference of two group centroids,
  \( c_A - c_B \), is established practice for visualizing semantic relationships (Liu et al., 2018;
  Bandyopadhyay et al., 2022) and for contrast axes (SemAxis, An et al., 2018; semantic projection,
  Grand et al., 2022). The Polar Projector removes the anchor's component from both poles first — by
  linearity, \( P_\perp c_A - P_\perp c_B = P_\perp(c_A - c_B) \), confining the dipole to the
  anchor's complement — and returns the residual \( d_{esc} \) alongside the scalar those methods
  stop at, reconstructing \( \|r\|_2 \) at the isometric scale (§4.1).
- **Locality-sensitive hashing.** As in random-hyperplane LSH (Charikar, 2002), evaluating the
  projection reduces to an inner product — but LSH is stochastic and targets approximate retrieval
  over a global corpus, while the Polar Projector is deterministic, uses chosen rather than random
  references, and evaluates direction against a local active state.
- **Anchor-based placement in visualization.** Positioning items relative to a small set of
  reference points is established practice in information visualization: VIBE (Olsen et al., 1993)
  places documents by similarity to user-chosen points of interest, Dust & Magnet (Yi et al., 2005)
  uses reference points that pull items by attribute value, and Landmark Isomap (de Silva &
  Tenenbaum, 2002) fits a small landmark subset once and triangulates the rest of the corpus from
  it. LAMP (Joia et al., 2011) is closest in spirit — a local affine mapping from control points,
  chosen for the same reasons this paper chooses a local operator: accuracy and a cost low enough
  for interactive use. None of the four states a non-degeneracy guarantee comparable to
  Proposition 2, or accounts for what clamping does to a residual as Proposition 3 does.

### 4.3 Limitations and Open Questions

The experimental body and the formal characterization of the operator have explicit boundaries; each
item below states what was not tested and, where it applies, what would need to be measured to close
the gap:

- **Scope of corpus, encoder and platform — untested beyond one of each.** All quantitative
  evaluation runs on a single corpus (2,221 chunks of Spinoza's *Ethics*), a single embedding model
  (`all-MiniLM-L6-v2`) and a single passively cooled host (Apple M1). Absolute timings reflect this
  specific platform; the ratios between arms and the flatness in \( N \) should depend on it less,
  but neither was measured on another host. Whether the trade-off of §3.4 — every rule that gained
  trustworthiness lost task-level lift — belongs to the construction or to this corpus's structure,
  and whether the re-centring gain and the radial bound of §3.5 reappear on corpora of a different
  shape and under other encoders, are open. The dimension sweep of Appendix A is the same limitation
  from the implementation side: every real figure in this paper comes from that one 384-dimensional
  encoder, so whether the operator's behaviour past the dispatch/arithmetic crossover holds on real
  embeddings from a higher-dimensional model, rather than the synthetic vectors swept there, is
  untested.
- **Proxy for semantic relevance.** The division of the text into five parts (`part`) serves as a
  coarse proxy for semantic coherence when computing same-part lift. It is not equivalent to a
  fine-grained evaluation of topical relevance or to a human judgement of usefulness.
- **Pre-registration status and post hoc analysis.** The protocols of §3.2, Appendices A–C, and the
  isometric-scale rerun of §3.2–§3.4 were committed before their results, with two exceptions inside
  them: §3.2's two fixed linear baselines were committed together with their results, and Appendix
  A's dimension sweep was specified after its own results. §3.3, §3.4 and §3.5, the clamp
  re-measurement and the pole positions of §2.1 were likewise committed together with their results,
  and the scale ablation on re-anchoring is post hoc; `paper/claims.md` records the status of every
  figure. The manuscript includes no formal hypothesis tests and no bootstrap confidence intervals.
- **Asymmetry of the published frame (P1).** In the static published frame (§3.2), the initial
  500-chunk window contains 409 chunks of P1_GOD and 91 of P2_MIND. As a consequence, the anchor
  \( c_1 \) is a convex combination of the two poles that places the projected poles at
  \( \lambda = +0.182 \) and \( \lambda = -0.818 \), making clear that \( \lambda = \pm 1 \) is the bound
  of the clamp and not the position of the poles.
- **If re-centring helps, what does a bounded contrast axis add?** On local neighbourhood recovery
  the radial coordinate bounds the operator — 0.981 on the same instrument, under the same
  constraints (§3.5). The two views share an unbounded vertical axis and differ only in the
  horizontal one: \( \lambda \), bounded by its clamp and built from two chosen poles, against a
  projection onto an arbitrary direction. No instrument in this paper can tell whether that
  difference matters to a person; a fair test is behavioural, and would first have to settle what the
  ends of \( \lambda \) mean, since the poles sit at \( +0.182 \) and \( -0.818 \) rather than at
  \( \pm 1 \) in the published frame.
- **Fixed codebook for re-anchoring, and how often it must be rebuilt.** In the re-anchoring
  evaluation (§3.5), the contrast poles are selected from a static codebook of \( K = 16 \) centroids
  precomputed globally by k-means; the scan costs \( O(K \cdot d) \) without consulting the corpus at
  query time, but the view depends on how representative those \( K \) fixed centroids are, and
  \( K \) was not varied. A growing corpus eventually requires rebuilding that codebook, which reads
  the corpus again — how often a rebuild is needed, how much it changes views a user has already
  seen, and whether it can be done incrementally, are all unmeasured.
- **Anchor degeneracy in bimodal distributions, with no internal detector.** If the active context
  spans a bimodal distribution, a centroid anchor \( c_1 \) can fall in the gap between the two
  clusters and represent neither; Proposition 2 resolves the collapse of the dipole but not a badly
  placed origin, and every norm in Propositions 1–3 stays well-conditioned, so the operator returns
  confident values whose interpretation has stopped holding, with nothing here that detects it. The
  risk applies to the published frame's anchor and to the centroids that serve as poles — part
  centroids in the published frame, codebook centroids once re-anchored — and a re-anchored frame's
  origin is itself a real note. What a cheap per-frame test would look like, and whether the
  distribution of \( d_{esc} \) already carries the signal, is unexamined.
- **Is relocating in jumps worse than drifting a little?** UMAP fitted once and extended by
  `transform()` is still at 5 of 7 growth steps and relocates at the other two, by 0.39 and 1.07;
  the operator's moving-anchor arm moves at every step, by 0.13–0.61 at unit scale (§3.2). Which
  profile does more damage to a user's spatial model is an empirical HCI question these measurements
  cannot answer, and Boechler (2001), which establishes that instability degrades navigation, does
  not distinguish the two.
- **No behavioural tests with users — the question the whole design rests on.** The design
  requirement of positional stability is an extrapolation from the hypertext-navigation literature
  (§1), and nothing here tests it, or whether a bounded contrast coordinate \( \lambda \in [-1, 1] \)
  is more useful as a control signal than a pure radial distance. A behavioural study would have to
  test both against baselines as simple as the ones §3 uses — a fixed map for stability, a radial
  coordinate for re-centring — before any question about the operator's own coordinates is worth
  asking.

## 5. Conclusion

This work began as a search for a way to decouple the interaction from the state of the corpus in a
spatial interface, and the results support a narrower account: decoupling is trivial for any fixed
linear map, and what a local frame adds is re-centring the view on the query without re-coupling it
to the corpus — a lever a two-line radial coordinate still bounds (§3.5, §4.1).

The operator itself is correct: its collinear configurations do not degenerate (Proposition 2), its
residual decomposition is exact when \( \lambda \) does not saturate (Proposition 3), and its
per-stimulus latency is flat across a 25× range of corpus sizes. The scalar form of the residual
loses all precision below \( d_{esc}/\|r\|_2 \approx 10^{-6} \), undetectably at two points of the
sweep, while the vector form stays stable — these are the properties that can be handed to whoever
implements the system.

What the evidence cannot hand them is a reason to prefer the operator on numerical metrics alone
(§4.1): stability, manifold preservation and re-centring are each matched or beaten by a baseline
simple enough to write in a few lines.

For whoever implements this primitive, the results mark explicit design decisions:

- **Declare the screen scale ratio \( S_x / S_y \).** Rendering \( \lambda \) under the isometric rule
  (\( S_x = \|v_{dipole}\|_2 \cdot S_y \)) preserves the on-screen distance to the anchor for
  unsaturated points; the unit scale exaggerates the \( \lambda \) axis. The choice moves local recall
  (an exploratory figure) but barely moves the global instruments — at most 0.003 in trustworthiness
  and 0.02 in lift, with no ordering changed.
- **Re-anchor rather than refit directions to re-centre.** Moving the anchor to the query re-centres
  the view without reading stored vectors, whereas refitting local directions re-couples the
  interaction to the corpus. With a growing corpus, the codebook of \( K \) centroids should be
  rebuilt periodically, outside the active loop.
- **Always compute \( d_{esc} \) in vector form,** as \( \|r - \lambda v_{dipole}\|_2 \). The scalar
  rearrangement is 1.47× faster but loses all precision in near-collinear regimes, at two points of the
  sweep without any detectable sign.
- **Choose the pole-selection rule deliberately.** It is a knob between manifold preservation and
  task-level agreement: rules aligned with variance match the fidelity of a fixed PCA, and no
  label-free rule measured beats that PCA on task-level agreement.
- **Check the frame's saturation.** \( \lambda = \pm 1 \) is the clamp's domain boundary, not the
  location of the poles; check what share of points saturates for the frames in use.

We report these negative bounds because they clarify the design space in a way positive results
would not: that a fixed random projection lands near chance shows the fidelity instruments are not
vacuous, that a locally refitted PCA fails despite being centred on the neighbourhood shows neither
moving nor reorienting a linear projection recovers it, and that pole selection trades preservation
against lift tells an implementer which knob they are actually turning.

The question this numerical analysis cannot answer, and the one that will ultimately decide the
operator's practical usefulness, is behavioural rather than numerical (§4.3) — a contact with reality
this work does not make.

## Code and Data Availability

The operator, every benchmark script, the frozen corpus embeddings with their SHA-256 digests and
encoder revision, the committed result artifacts and the figure scripts are available at
<https://github.com/AlexusPacicus/polar-projector> under the GNU AGPL v3. The tables of Appendices B
and C are recomputed, and every other figure in this manuscript is checked against the committed
artifacts, by `tools/verify_paper_tables.py`.

## Use of Generative AI

AI assistants were used throughout this work. Claude (Anthropic) drafted parts of the text, including
the abstract and several sections, translated sections the author wrote in Spanish, reviewed the
analysis, and wrote and corrected benchmark and verification code. Free versions of other AI
assistants were used to audit earlier drafts. The author decided the scope of the work and what it
claims, reviewed every passage, and takes full responsibility for the content.

## References

1. An, J., Kwak, H., & Ahn, Y.-Y. (2018). SemAxis: A Lightweight Framework to Characterize
   Domain-Specific Word Semantics Beyond Sentiment. *Proceedings of the 56th Annual Meeting of the
   Association for Computational Linguistics (Volume 1: Long Papers)*, 2450–2461.
   DOI:10.18653/v1/P18-1228.
2. Bandyopadhyay, S., Xu, J., Pawar, N., & Touretzky, D. (2022). Interactive Visualizations of Word
   Embeddings for K-12 Students. *Proceedings of the AAAI Conference on Artificial Intelligence*,
   36(11), 12713–12720.
3. Bengio, Y., Paiement, J.-F., Vincent, P., Delalleau, O., Le Roux, N., & Ouimet, M. (2003).
   Out-of-Sample Extensions for LLE, Isomap, MDS, Eigenmaps, and Spectral Clustering. *Advances in
   Neural Information Processing Systems 16 (NIPS 2003)*.
4. Boechler, P. M. (2001). How Spatial Is Hyperspace? Interacting with Hypertext Documents:
   Cognitive Processes and Concepts. *CyberPsychology & Behavior*, 4(1), 23–46.
5. Bolukbasi, T., Chang, K.-W., Zou, J., Saligrama, V., & Kalai, A. T. (2016). Man is to Computer
   Programmer as Woman is to Homemaker? Debiasing Word Embeddings. *Advances in Neural Information
   Processing Systems 29 (NeurIPS 2016)*. arXiv:1607.06520.
6. Charikar, M. S. (2002). Similarity Estimation Techniques from Rounding Algorithms. *Proceedings
   of the 34th Annual ACM Symposium on Theory of Computing (STOC 2002)*, 380–388.
7. de Silva, V., & Tenenbaum, J. B. (2002). Global Versus Local Methods in Nonlinear Dimensionality
   Reduction. *Advances in Neural Information Processing Systems 15 (NeurIPS 2002)*, 721–728.
8. Duff, T., Burgess, J., Christensen, P., Hery, C., Kensler, A., Liani, M., & Villemin, R. (2017).
   Building an Orthonormal Basis, Revisited. *Journal of Computer Graphics Techniques*, 6(1), 1–8.
9. Edelsbrunner, H., & Mücke, E. P. (1990). Simulation of Simplicity: A Technique to Cope with
   Degenerate Cases in Geometric Algorithms. *ACM Transactions on Graphics*, 9(1), 66–104.
   DOI:10.1145/77635.77639.
10. Espadoto, M., Martins, R. M., Kerren, A., Hirata, N. S. T., & Telea, A. C. (2021). Toward a
    Quantitative Survey of Dimension Reduction Techniques. *IEEE Transactions on Visualization and
    Computer Graphics*, 27(3), 2153–2173.
11. Gower, J. C. (1975). Generalized Procrustes Analysis. *Psychometrika*, 40(1), 33–51.
    DOI:10.1007/BF02291478.
12. Grand, G., Blank, I. A., Pereira, F., & Fedorenko, E. (2022). Semantic projection recovers rich
    human knowledge of multiple object features from word embeddings. *Nature Human Behaviour*, 6(7),
    975–987. DOI:10.1038/s41562-022-01316-8.
13. Joia, P., Paulovich, F. V., Coimbra, D., Cuminato, J. A., & Nonato, L. G. (2011). Local Affine
    Multidimensional Projection. *IEEE Transactions on Visualization and Computer Graphics*, 17(12),
    2563–2571. DOI:10.1109/TVCG.2011.220.
14. Liu, S., Bremer, P.-T., Thiagarajan, J. J., Srikumar, V., Wang, B., Livnat, Y., & Pascucci, V.
    (2018). Visual Exploration of Semantic Relationships in Neural Word Embeddings. *IEEE
    Transactions on Visualization and Computer Graphics*, 24(1), 553–562.
    DOI:10.1109/TVCG.2017.2745141.
15. Marshall, C. C., & Shipman, F. M. (1995). Spatial Hypertext: Designing for Change.
    *Communications of the ACM*, 38(8), 88–97. DOI:10.1145/208344.208350.
16. McInnes, L., Healy, J., & Melville, J. (2018). UMAP: Uniform Manifold Approximation and
    Projection for Dimension Reduction. arXiv:1802.03426.
17. Neves, T. T. A. T., Martins, R. M., Coimbra, D. B., Kucher, K., Kerren, A., & Paulovich, F. V.
    (2020). Xtreaming: An Incremental Multidimensional Projection Technique and Its Application to
    Streaming Data. arXiv:2003.09017.
18. Olsen, K. A., Korfhage, R. R., Sochats, K. M., Spring, M. B., & Williams, J. G. (1993).
    Visualization of a Document Collection: The VIBE System. *Information Processing & Management*,
    29(1), 69–81.
19. Rauber, P. E., Falcão, A. X., & Telea, A. C. (2016). Visualizing Time-Dependent Data Using
    Dynamic t-SNE. *EuroVis 2016 — Short Papers*. DOI:10.2312/eurovisshort.20161164.
20. Reimers, N., & Gurevych, I. (2019). Sentence-BERT: Sentence Embeddings using Siamese
    BERT-Networks. *Proceedings of EMNLP-IJCNLP 2019*, 3982–3992.
21. Sainburg, T., McInnes, L., & Gentner, T. Q. (2021). Parametric UMAP Embeddings for
    Representation and Semisupervised Learning. *Neural Computation*, 33(11), 2881–2907.
22. van der Maaten, L., & Hinton, G. (2008). Visualizing Data using t-SNE. *Journal of Machine
    Learning Research*, 9, 2579–2605.
23. Venna, J., & Kaski, S. (2001). Neighborhood Preservation in Nonlinear Projection Methods: An
    Experimental Study. *Artificial Neural Networks — ICANN 2001*, 485–491.
    DOI:10.1007/3-540-44668-0_68.
24. Vernier, E. F., Comba, J. L. D., & Telea, A. C. (2021). Guided Stable Dynamic Projections.
    *Computer Graphics Forum*, 40(3), 87–98. DOI:10.1111/cgf.14291.
25. Yi, J. S., Melton, R., Stasko, J., & Jacko, J. A. (2005). Dust & Magnet: Multivariate
    Information Visualization Using a Magnet Metaphor. *Information Visualization*, 4(4), 239–256.
    DOI:10.1057/palgrave.ivs.9500099.

## Appendix

The three appendices below answer a narrower question than §3 does, and
`tools/verify_paper_tables.py` covers their tables as well: whether the implementation is numerically sound, rather than whether the operator works as
a navigation substrate.

### Appendix A — Dimension Sweep and Where Dispatch Stops Dominating

§3.1 closes by saying the operator's per-call gap to the floor is dispatch rather than arithmetic.
That caveat is testable: if it holds, per-call latency should be flat in \( d \) until the arithmetic
becomes large enough to matter.
Sweeping the prepared hot path and the random-projection floor across dimension, on synthetic unit
vectors — no encoder used in this paper produces vectors above \( d = 384 \) (§4.3):

| \( d \) | `evaluate()` (µs) | Floor (µs) | Ratio | vs. \( d = 16 \) |
|---|---|---|---|---|
| 16 | 4.18 | 0.72 | 5.78× | 1.00× |
| 64 | 4.12 | 0.74 | 5.58× | 0.99× |
| 256 | 4.54 | 0.90 | 5.07× | 1.09× |
| 384 | 4.58 | 1.08 | 4.25× | 1.10× |
| 1024 | 5.64 | 1.64 | 3.43× | 1.35× |
| 4096 | 11.00 | 4.62 | 2.38× | 2.63× |
| 8192 | 25.18 | 8.63 | 2.92× | 6.03× |

1,000 vectors per dimension, 3 repetitions, 1,000 warmup iterations, arms interleaved;
`bench/latency.py --sweep`. Exploratory: this sweep was specified after §3.1's registered run, in
response to what it showed, and is not covered by that experiment's pre-registration.

The prediction holds. Per-call cost is nearly flat from \( d = 16 \) to \( d = 384 \) — the output
dimension of the sentence-transformer encoder used throughout this paper (`all-MiniLM-L6-v2`,
§3.2) — costing only 1.10× more despite 24× the floating-point work, because **roughly 90% of the
per-call cost at that dimension is fixed dispatch overhead**, not the \( O(d) \) arithmetic
Proposition 1 describes. The crossover into arithmetic-dominated cost sits between
\( d = 1{,}024 \) and \( d = 4{,}096 \) — well above \( d = 384 \) — where the ratio to the floor
collapses from 5.78× to 2.38×; the further rise at \( d = 8{,}192 \) (2.92×) is a memory effect, a
65 MB working set no longer fitting in cache, not an arithmetic one.

Two consequences follow, both narrowing this paper's claims rather than widening them. First, the
microsecond figures in §3 and §3.1 are not a measurement of Proposition 1's asymptotic claim, and
whether the operator's behaviour past the crossover holds on real embeddings rather than the
synthetic vectors swept here is untested (§4.3). Second, the lever that would most reduce cost at
\( d = 384 \) is **issuing fewer array operations**, not doing less arithmetic; a fused or compiled
implementation of the same mathematics would close most of the gap to the floor without changing a
single flop.

That second claim is not left as an inference — it was tested by removing exactly one array
operation. `evaluate()` clamps \( \lambda \) into \( [-1, 1] \), and clamping a single scalar
through `np.clip` enters NumPy's ufunc machinery for 1.88 µs — 30% of the whole call — where
`min(max(x, -1), 1)` does it in 0.23 µs. The two are bit-for-bit identical on every input, including
NaN, signed zero, subnormals, infinities and the float either side of the boundary, so the
substitution changes no value this paper reports. It made `evaluate()` **1.40× faster**, from 6.34
to 4.54 µs, for zero change in arithmetic (`bench/clamp.py`, which restores the old clamp and measures
both bodies side by side). Every latency figure in §3 reflects the substitution;
every table of *values* — §B, §C, §3.2 — is unchanged by it, which is the check that the two
forms really are equivalent.

### Appendix B — Conditioning of the Orthogonal Residual

Proposition 3's decomposition is an exact identity, and rearranging it expresses \( d_{esc} \)
purely in scalars already computed for \( \lambda \):
\( d_{esc}^2 = \langle r,r \rangle - 2\lambda\langle r, v_{dipole} \rangle + \lambda^2\|v_{dipole}\|_2^2 \),
which is 1.47× faster than evaluating \( \|r - \lambda v_{dipole}\|_2 \) directly. It is, however,
not a usable substitute: it subtracts nearly equal quantities as \( d_{esc} \) shrinks relative to
\( \|r\|_2 \). Against a construction whose exact residual is known analytically:

| \( d_{esc}/\|r\|_2 \) | Vector-form rel. error | Scalar-form rel. error |
|---|---|---|
| \( 10^{-3} \) | \( 1.2 \times 10^{-14} \) | \( 1.1 \times 10^{-10} \) |
| \( 10^{-5} \) | \( 1.1 \times 10^{-12} \) | \( 4.5 \times 10^{-7} \) |
| \( 10^{-7} \) | \( 9.8 \times 10^{-11} \) | \( 1.2 \times 10^{-3} \) |
| \( 10^{-8} \) | \( 6.7 \times 10^{-10} \) | \( 1.0 \times 10^{0} \) |

Generated by `bench/conditioning.py`; both forms scored against a residual known analytically by
construction (`polar_projector.fixtures.near_collinear_stimulus`), with \( \lambda \) pinned at 0.5
so conditioning is measured without saturation confounding it. CI re-derives these four rows on
every push (`tools/verify_paper_tables.py`).

Below \( d_{esc}/\|r\|_2 \approx 10^{-6} \) the scalar form returns values uncorrelated with the
true distance, while the vector form degrades gracefully across the full sweep. This is not a
property of the corpus or of \( d \): the scalar form subtracts terms of order \( \|r\|_2^2 \) to
recover a quantity of order \( d_{esc}^2 \), so float64's rounding noise
(\( \sim\varepsilon\|r\|_2^2 \)) overtakes the true signal once \( d_{esc}/\|r\|_2 \) drops below
\( \sqrt{\varepsilon} \approx 1.49 \times 10^{-8} \) — matching where the table's failure sits.
The identity of Proposition 3 therefore stands as a theorem but not as an algorithm: the residual is
computed in vector space before the norm is taken. This regime — a stimulus lying almost entirely
along the dipole axis — is not a saturation regime: the fixture pins \( \lambda \) at 0.5
specifically to isolate conditioning from saturation as a confound. Precision failing here is a
property of the ratio \( d_{esc}/\|r\|_2 \) alone, not of clipping, so it is not incidental.

Continuing the sweep past the published window, to \( d_{esc}/\|r\|_2 = 10^{-14} \), shows the
failure is worse than a loss of accuracy — it is a loss of accuracy that does not announce itself.
At \( 10^{-8} \), \( 10^{-9} \), \( 10^{-10} \), \( 10^{-12} \) and \( 10^{-14} \) the
scalar form's radicand goes negative and the computation can at least detect its own failure. At
\( 10^{-11} \) and \( 10^{-13} \) it does not: the radicand stays positive and the form returns a
finite, plausible-looking distance that is too large by factors of \( 1.4 \times 10^{3} \) and
\( 1.4 \times 10^{5} \) respectively. A caller checking for a negative radicand — the obvious
defensive measure, and the one the arithmetic suggests — would pass those two cases through. The
argument against the scalar form is therefore not that it is inaccurate near collinearity but that
its inaccuracy is undetectable from inside.

The cost of refusing it is real, and it grew. Measured over 25,000 stimuli at \( d = 384 \), the
vector form runs at 4.56 µs against the scalar form's 3.10 µs — the scalar rearrangement is
**1.47× faster**, up from 1.24× under the old clamp: §A's clamp substitution removed nearly the
same fixed overhead (1.8–2.0 µs) from both arms, so the residual computation is now a larger share
of a leaner call. Refusing the scalar form costs about a third of the hot path rather than a fifth
— the argument is unchanged, a third of the hot path is not worth a silently wrong answer, but the
price is stated at its current value.

### Appendix C — δ-Sweep Behavior

Varying the fallback scale \( \delta \) (Proposition 2) under the controlled collinearity scenario
(\( d = 384 \), fixed seed) traces the sensitivity of \( \lambda \) and \( d_{esc} \) to the
fallback direction:

| \( \delta \) | \( \sigma^2_\lambda \) | \( \sigma^2_{d_{esc}} \) | \( R = \sigma^2_\lambda / \sigma^2_{d_{esc}} \) |
|---|---|---|---|
| 0.001 | 9.782e-1 | 3.535e-6 | 276747.31 |
| 0.010 | 7.994e-1 | 3.886e-6 | 205690.72 |
| 0.050 | 2.401e-1 | 6.651e-6 | 36104.25 |
| 0.100 | 6.594e-2 | 6.954e-6 | 9482.78 |
| 0.200 | 1.649e-2 | 6.954e-6 | 2370.69 |
| 0.500 | 2.638e-3 | 6.954e-6 | 379.31 |

Generated by `tools/generate_polar_delta_table.py` at \( N = 10{,}000 \) samples per
row (2-sigma sampling bound ≈ 2.8% on the reported variances) — fully deterministic under the
fixed seed, so any reader can regenerate this exact table. \( \sigma^2_{d_{esc}} \) saturates at a
constant floor for \( \delta \geq 0.1 \): no trial saturates in that range, so \( d_{esc} \) equals
\( r \)'s component orthogonal to \( u_\perp \) exactly — a concrete instance of §2.1's collapse of
the orthogonal dimensions into a single radial distance. Below \( \delta = 0.1 \) an increasing
share of trials saturate, which reintroduces Proposition 3's cross-term into \( d_{esc} \) and is
why \( R \) inflates by orders of magnitude as the dipole norm collapses toward its \( 2\delta \)
floor.
