# The Polar Projector: A Deterministic O(d) Subspace Operator, and the Trivial Baselines That Bound It

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
> committed artifact** in `bench/results/` (303 figures at present, produced by `bench/latency.py`,
> `bench/drift.py`, `bench/recall.py`, `bench/frame_sensitivity.py`, `bench/reanchor.py`,
> `bench/conditioning.py`, `bench/batched.py` and `tools/decompose_polar_latency.py` against the
> hash-committed corpus in `bench/data/`). The second check is the weaker of the two: it catches a
> manuscript drifting away from its own measurements, not an error inside a benchmark.
>
> No figure in §3 now escapes both checks: the \( O(N^2) \) column and the SQLite deployment numbers
> carried over from the substrate were removed, and §3.5's timing columns are checked against their
> committed artifact like every other timing. `paper/claims.md` registers each claim against its
> checks, and the verifier fails if a checked figure is not printed here.
>
> §4 and §6 are drafted but not reviewed and must not be treated as final. The speculative
> extensions carried by earlier drafts — multi-axis tangent frames and the tripolar model, adaptive
> δ calibration, and active-codebook eviction — have been removed rather than relegated: none is
> implemented in `polar_projector/projector.py`, and none supported a contribution this paper
> claims.

---

## Abstract

A spatial interface over a personal knowledge corpus imposes two constraints that are easy to state
and hard to satisfy together. **Adding one note must not move the others**, because the user's
memory of where things are is the interface. And **each interaction must complete inside a frame
budget**, because the layout is recomputed while the user is moving through it. Global
dimensionality reduction satisfies neither: refitting UMAP or t-SNE as a corpus grows relocates
previously-placed points even with the random seed pinned, and the refit itself costs seconds.

We present the **Polar Projector**, a stateless local subspace operator that derives a planar
position for an incoming vector \( v_n \) from an active contextual frame — a static anchor
\( c_1 \) plus a contrast dipole \( (c_A, c_B) \) — in \( O(d) \) arithmetic and \( O(d) \) memory
per stimulus, independently of corpus size \( N \), and without reading persistent storage. It
returns a projection coefficient \( \lambda \in [-1, 1] \) along the dipole axis and an orthogonal
residual \( d_{esc} \geq 0 \). We prove non-degeneracy for collinear configurations via a
deterministic fallback direction in the anchor's null space (Propositions 1 and 2), and establish an
orthogonal decomposition identity for the residual — exact whenever \( \lambda \) is unsaturated, an
inequality once \( \lambda \) clamps at the dipole boundary (Proposition 3). Per-stimulus latency is
4.57 µs with a prepared frame and 11.75 µs stateless, flat to 1.4% across corpora from 1,000 to
25,000 vectors and to 0.4% across an 11× working set.

**This paper is a measured account of what that construction buys, and it is bounded throughout by
baselines simple enough that a reader may object they are too simple.** That is the point: each one
satisfies every constraint stated above, and each bounds a different claim the operator might
otherwise be read as making. Exact positional stability turns out to be free — any fixed linear map
has it, and three arms hold every previously-placed point still across all seven growth steps of a
2,221-chunk corpus, so stillness is a precondition rather than a result. On fidelity a once-fitted
PCA lands *inside* the operator's own range (trustworthiness 0.6811 against 0.6639 at the frame we
publish and 0.6593–0.6966 across selection rules), and the rule that reaches the fidelity ceiling
does so by aligning with variance — which makes the operator behave like the PCA it was meant to
improve on. Pole selection is therefore a knob, not a detail: it trades manifold preservation
against task-level agreement, and the operator's distinctive behaviour lives at the agreement end,
where it holds 1.17× lift on the smallest corpus while every other stable arm falls to chance.

The one lever that is specific to a local frame is a **movable origin**. Re-anchoring on the query
is worth 29× in local neighbourhood recovery (0.019 to 0.543) for a single \( O(d) \) frame
construction of 42.8 µs, while refitting a linear map's directions on the query's own neighbourhood
is *worse* than not refitting at all — a projection reorients but cannot recentre. Even there the
operator is bounded: a two-line radial coordinate reaches 0.981 on the same instrument at 1.98 µs
per stimulus, faster than the operator and subject to the same constraints. Most of that gap is
units rather than information — rendering \( \lambda \) in multiples of \( \|v_{dipole}\|_2 \)
instead of at unit scale lifts the operator to 0.925 — so the screen mapping's scale ratio is a
design rule, not a free constant.

What remains, and what we claim, is narrower than a dominating result and more useful than one: a
correct and numerically characterized primitive — including an algebraically equivalent form of
\( d_{esc} \) that loses all precision below \( d_{esc}/\|r\|_2 \approx 10^{-6} \) *undetectably* —
together with a map of which parts of its design space are load-bearing and which are free.

## 1. Introduction

A spatial interface over a personal knowledge corpus — a canvas the user navigates to reach their
own notes — is not a corpus visualization that happens to be interactive. It imposes two
constraints that a static layout never has to meet:

1. **Adding one note must not move the others.** The user builds a persistent spatial mental model
   of the interface, and instability in that layout measurably degrades navigation and orientation
   (Boechler, 2001). If positions shift on every write, spatial proximity stops reliably encoding
   semantic proximity and the model the user built is invalidated by their own act of writing.
2. **Each interaction must complete inside a frame budget.** The position of an incoming vector is
   computed while the user is moving, so its cost cannot scale with how much the user has written.

*The premise, and its standing.* Both constraints are **assumptions this paper inherits, not
results it establishes**, and the first one carries the weight. Boechler (2001) measures navigation
and orientation in *hypertext documents* — a linked corpus browsed through a reading interface, not
a continuous canvas over an embedding space — so applying it here is an extrapolation across
interface families. It is a defensible one, and it is the standard motivation in this literature,
but nothing below tests it. No user touched anything in this work: every instrument reported in §3
is numerical, computed on a frozen corpus, and none of them can tell whether a person navigating
actually suffers from layout instability or benefits from its absence.

We state this plainly rather than in a limitations paragraph at the end, for two reasons. It is the
premise the whole design rests on, so a reader who rejects it should know by the end of §1 rather
than after §3. And the same gap reappears as this paper's leading open question: §6 asks what a
bounded, interpretable contrast coordinate is worth to a person navigating, which is the
behavioural experiment that would validate constraint 1 and adjudicate §3.5's bound at the same
time. A reader should treat the constraints as a design brief we adopted and then measured against,
not as findings — the findings are in §3, and several of them cut against the design the brief
motivated.

Reusing global dimensionality reduction for this violates both. Stochastic re-optimization alters
existing coordinates on incremental update, and §3.2 measures what survives pinning the random
seed: under refitting, t-SNE (van der Maaten & Hinton, 2008) relocates previously-placed points by
1.03–1.24 times the width of the layout at every growth step and UMAP (McInnes et al., 2018) by
0.31–1.25. Refitting is also not cheap — the same seven growth steps cost 15.7–25.0 s across the
baselines against 0.051 s for the operator, a factor of 307–488×. We make no asymptotic claim about
the baselines here: Barnes-Hut t-SNE is \( O(N \log N) \) and UMAP's graph construction is
sub-quadratic in practice, so the argument against them on this axis is the measured seconds-scale
cost of a refit inside an interaction loop, not a complexity class.

This instability is not news to the visualization community, and the approaches it has taken are
the reason this paper argues for a different primitive rather than a better layout. Dynamic t-SNE
adds a temporal-coherence penalty across a sequence of datasets, trading projection reliability for
stability (Rauber et al., 2016); guided stable dynamic projections make that trade controllable
(Vernier et al., 2021); and incremental techniques evolve a projection without revisiting the data,
buying speed and stability at the cost of global distance preservation (Neves et al., 2020).
Out-of-sample extension takes the complementary route of fitting once and mapping new points
through a learned or interpolated function (Bengio et al., 2003; Sainburg et al., 2021) — §3.2
measures exactly that configuration as one of its arms. Every one of these softens drift by
constraining or amortizing a global optimization. None of them removes the optimization, so none
delivers the *exact* repeatability a spatial interface can rely on per interaction; surveys of the
field treat stability as one quality axis traded against others rather than a guarantee (Espadoto
et al., 2021). Spatial hypertext identified the underlying interface requirement long before
embeddings were the substrate: users encode meaning in where they put things, so the system must
not move them (Marshall & Shipman, 1995).

The Polar Projector meets both constraints by refusing the problem the baselines solve. It is a
per-interaction primitive, not a global layout: a local, deterministic \( O(d) \) operator that
evaluates one incoming vector against one active contextual frame — a static anchor plus a contrast
dipole — deriving a projection coefficient \( \lambda \in [-1, 1] \) and an orthogonal residual
\( d_{esc} \) without reading, modifying or re-evaluating the persistent corpus, with correctness
guarantees proven in §2.

**Contributions.** Three of the four are bounds rather than wins, and the baselines that supply
them are in the paper because a result a two-line baseline matches is not a result.

- **A local \( O(d) \) operator with a characterized numerical failure mode.** A stateless operator
  evaluating one incoming vector against one active contextual frame in \( O(d) \) arithmetic and
  \( O(d) \) memory, with non-degeneracy proven for collinear configurations via a deterministic
  null-space fallback (Propositions 1–2) and an orthogonal decomposition identity for the residual
  (Proposition 3). Proposition 3's algebraically equivalent scalar rearrangement is 1.47× faster and
  must not be used: below \( d_{esc}/\|r\|_2 \approx 10^{-6} \) it returns finite, plausible values
  wrong by factors of \( 10^3 \)–\( 10^5 \), and at two of the sweep's points its radicand stays
  positive so the failure cannot be detected from inside. The identity is a theorem but not an
  algorithm (§2, §B).
- **Exact positional stability is free.** Any fixed linear map has it. A fixed random projection and
  a once-fitted PCA hold every previously-placed point still across all seven growth steps, exactly
  as the operator does, so stillness bounds nothing on its own. What the two baselines do establish
  is that the operator's fidelity figures are not vacuous: the random projection lands near chance
  on both instruments (0.5535 trustworthiness, 1.09× lift), while the PCA lands inside the
  operator's own range (§3.2, §3.3).
- **Pole selection is a knob, not a detail.** Across contrast axes trustworthiness moves over
  0.6593–0.6966 and task-level lift over 1.42–1.57×, in opposite directions. Two leak-free selection
  rules clear the PCA baseline's 0.6811, and the one that reaches the ceiling does it by aligning
  with maximum variance — landing within noise of that PCA on *both* instruments, which is the
  negative result the rule was written to test. The operator's distinctive behaviour lives at the
  other end of the knob, where a part-based rule holds 1.17× lift on the 500-chunk corpus while
  every other stable arm falls to chance (§3.4).
- **A movable origin is the lever; better directions are not.** Re-anchoring on the query is worth
  29× in local neighbourhood recovery (0.019 to 0.543) for one \( O(d) \) frame construction at
  42.8 µs, against 5.2 ms for a locally refitted PCA and 69 ms for a global fit. That refitted PCA
  scores *below* the global one, which supplies the mechanism: a linear projection reorients but
  cannot recentre, and its two local components drop distant points on top of the query. The claim
  is bounded in the same section: a radial coordinate \( (\langle v - q, e \rangle, \|v - q\|) \)
  reaches 0.981 at 1.98 µs per stimulus while satisfying every constraint above. Most of the
  operator's shortfall is a units mismatch in its own screen mapping: with \( \lambda \) rendered in
  multiples of \( \|v_{dipole}\|_2 \) it reaches 0.925, which leaves the two close on this
  instrument and makes the scale ratio of §2.1 a design rule rather than a free constant (§3.5).

*What this paper is not.* It is not a demonstration that this operator should be preferred to the
alternatives measured here. On every instrument we could construct, some baseline simple enough to
write in a few lines either matches it or beats it, and those results are reported in the sections
that would otherwise have carried the win. What survives is a primitive with proven guarantees, a
documented failure mode, and a map of which of its design choices are load-bearing — which is the
contribution we can support. The one property no instrument in this paper measures is what
\( \lambda \)'s boundedness and interpretability are worth to a person navigating: it is a bounded
coordinate between two named poles, where the radial baseline's horizontal axis is an arbitrary
direction and its vertical axis is unbounded. §6 records that as the open question it is, rather
than claiming it here.

*System context.* The constraints above are not hypothetical: the operator was extracted from
Traianus, a local-first personal knowledge system the author is building, where it serves as the
navigation primitive the two constraints describe. Traianus as a whole is at proof-of-concept stage,
and this paper deliberately does not depend on it — the operator is packaged standalone with numpy
as its only dependency, the corpus is frozen and hash-committed, and every figure below is either
recomputed or checked against a committed artifact on every push. Reproducing the *operator's* own
figures needs numpy alone; reproducing the baseline arms of §3.2 and §3.3 additionally needs
`umap-learn` and `scikit-learn`, which the package deliberately does not require. What is claimed
here is a property of the operator, not a demonstration that the surrounding system works.

A third bottleneck — synchronous I/O blocking the interaction loop — is addressed at the systems
level within the Traianus substrate, where this operator's output feeds a signal-filtering stage
(a Schmitt Trigger) and an asynchronous batched-write path to SQLite WAL. That architecture is
**out of scope for this paper** and is treated in forthcoming work; the persistence-related numbers
reported in §3 are included only for deployment context, not as a claim proven here.

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
\( c_A, c_B \in \mathbb{R}^d \) secondary pole centroids selected from a bounded active codebook
\( C \) ( \( |C| = K \leq 256 \) ). The anchor is normalized with a zero-guard threshold
\( \epsilon_{norm} > 0 \):

\[ \hat{c}_1 = \begin{cases} c_1 / \|c_1\|_2 & \text{if } \|c_1\|_2 > \epsilon_{norm} \\ 0 & \text{otherwise} \end{cases} \]

The orthogonal projector \( P_\perp: \mathbb{R}^d \to \mathbb{R}^{d-1} \) onto the complement of
\( \hat{c}_1 \) evaluates associatively as \( P_\perp v = v - \langle v, \hat{c}_1 \rangle \hat{c}_1 \),
in \( O(d) \) time and space without materializing the dense \( d \times d \) matrix
\( I - \hat{c}_1\hat{c}_1^T \). Codebook selection over \( K \leq 256 \) (a bounded constant, not
asymptotic in \( d \) or \( N \)) adds \( O(K \cdot d) \); the full evaluation is \( O(d) \),
independent of corpus size \( N \).

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
row.

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

§1 claims that stochastic global projections inherit spatial drift under incremental updates and
that a local deterministic operator does not. That claim was an assertion resting on a citation;
this section measures it, against a corpus with real semantic structure rather than synthetic
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
then violated may be harmed more than one that is never trusted. §6 records it as open.

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

§3.2's trustworthiness column leaves an open question stated directly in §6: whether that
instrument is even the right one for a per-interaction signal. This section gives a second,
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
PCA finds no more signal than chance. The two instruments disagree about that pair, which §3.4
resolves into a property of pole selection rather than of either method. It is also a closer race
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
actually judge relevant. §6 revisits what agreement between the two instruments does and does not
settle about the fidelity gap.

### 3.4 Pole Selection as a Trade-off Knob

Every figure in §3.2 and §3.3 is measured against one contextual frame: the anchor is the mean of
the initial window and the contrast axis comes from the two most-represented parts in it. So
trustworthiness 0.6639 and lift 1.57× are properties of *that* frame, and a single number with no
range beside it understates how much of the result is the operator and how much is the choice.

*Method.* Two sweeps on the frozen corpus and the same growth schedule, `bench/frame_sensitivity.py`.
The first varies the contrast axis over all ten unordered pairs of the corpus's five part centroids,
which bounds how far the figures move when the axis moves. Those centroids use whole-corpus labels
the production rule does not have, so the second sweep evaluates four rules that see only the
initial window — the information a system would actually hold at step 0. The anchor is unchanged
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

*Where the operator is not interchangeable with a PCA* is the other end. The part-based rule is the
only one in the table holding 1.17× on the 500-chunk corpus; the other three rules and the PCA all
sit at 1.01–1.03×, which is chance. Whatever the contrast axis is doing when it is built from
semantic groups rather than from variance, it is the only configuration measured here that finds
signal when there is least of it.

### 3.5 Re-anchoring: A Movable Origin

§3.2 and §3.3 both evaluate a single static layout, and that is the one regime in which a fixed
linear map competes on equal terms — §3.4 ends with the operator and a once-fitted PCA
interchangeable. Neither instrument touches the property that distinguishes them. A fixed map has
one view of the corpus, for every query, permanently. The operator's coordinates are
anchor-relative, so moving the active context yields a different view, and §2.1 shows that moving
it re-places every point by construction. Re-anchoring costs one `prepare()` — \( O(d) \), no
corpus access.

*Method.* 50 query chunks sampled under a fixed seed. For each query \( q \), local recall@15: of
\( q \)'s 15 true nearest neighbours in the source 384-dimensional space, how many are among its 15
nearest in the arm's two-dimensional view, with all 2,221 points placed in that view. Chance is
\( 15/2220 \approx 0.0068 \), so these are raw recalls — *of the fifteen notes really closest to
this one, how many land next to it on screen*. `bench/reanchor.py`.

| Arm | Mean | Median | Min | Max | Frame (µs) | Per stimulus (µs) |
|---|---:|---:|---:|---:|---:|---:|
| PCA fit on the whole corpus, one view | 0.056 | 0.033 | 0.000 | 0.267 | 69,178 | 1.34 |
| Polar, the frame §3.2 publishes, one view | 0.019 | 0.000 | 0.000 | 0.133 | 10,690 | 4.51 |
| PCA refit per query on its 100 neighbours | 0.023 | 0.000 | 0.000 | 0.533 | 5,156 | 1.23 |
| **Polar, re-anchored on the query** | **0.543** | **0.567** | 0.133 | 0.867 | **42.8** | 4.53 |
| Radial \( (\langle v-q, e\rangle, \|v-q\|) \) | **0.981** | **1.000** | 0.933 | 1.000 | 0 | **1.98** |

Per-stimulus cost is the same operation for every arm — placing one further vector in a view that
already exists — because comparing frame-construction times would compare a one-off global fit
against a per-query re-prepare. Poles for the re-anchored arm come from a 16-entry codebook built
once over the corpus by k-means; per-query selection is the \( O(K \cdot d) \) codebook scan
Proposition 1 already accounts for, so nothing here consults the corpus at query time.

*The movable origin is the lever, and it is large.* The same operator goes from 0.019 to 0.543
purely by moving the anchor to the query — a factor of 29 — for a frame construction 121× cheaper
than the local PCA fit and 1,618× cheaper than the global one. This is the first measurement in this paper where a property
specific to a local frame produces a difference of that size.

*Better directions are not the lever.* The refitted PCA scores 0.023, *below* the global fit's
0.056, and the mechanism is visible in the construction: a linear projection reorients but cannot
recentre. Its two locally-fitted components span two of 384 dimensions, so points arbitrarily far
from \( q \) can share a projection with it and land on top of it. Refitting the directions on the
query's own neighbourhood — and paying 121× the frame cost, plus a corpus query to materialize that
neighbourhood — buys less than not refitting at all. Whatever value the local frame has here comes
from where it measures *from*, not from which directions it measures *along*.

*The radial baseline leads, but most of the gap is the screen mapping's units.* A coordinate system
whose vertical axis is simply \( \|v - q\| \) and whose horizontal axis is the projection onto an
arbitrary fixed unit vector reaches 0.981 — median 1.000, minimum 0.933 — at 1.98 µs per stimulus,
faster than the operator's 4.53. It satisfies every constraint §1 states: \( O(d) \) per stimulus,
no frame to build, no corpus access, exactly stable for a fixed \( q \), fully deterministic.
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
remains of the gap to the radial baseline can only come from saturated stimuli, where Proposition 3
is an inequality and the view places them closer to the query than they are.

*What that leaves the instrument able to settle.* Local recall@15 rewards any view whose distance
from the query is monotone in true distance. At matched units both the radial baseline and the
operator nearly are, so on this instrument they are close — 0.981 against 0.925 — rather than
separated by the factor the unscaled row suggests. The defensible conclusions are the two above —
re-anchoring matters, refitting directions does not — plus a design rule for §2.1: the scale ratio
is not a free viewport constant, and \( S_x = \|v_{dipole}\|_2\, S_y \) is the ratio that preserves
distance from the anchor. What the instrument cannot do is distinguish the two arms on what the
construction was built for, a contrast coordinate between two chosen poles; §6 records what a test
of that would have to measure.

## 4. Discussion

### 4.1 What the Results Answer

*Positional stability does not distinguish the operator.* A fixed linear map has zero drift
trivially: a Gaussian projection drawn once and a PCA frozen after the initial window hold every
placed point still at 0.0000, exactly as the operator does with a fixed frame (§3.2). The class that
has this property is not "methods that avoid stochastic re-optimization" — UMAP fitted once and
extended by `transform()` avoids it and still relocates points twice (§3.2) — but maps whose output
is a pure function of the vector and of parameters that do not change. The operator belongs to that
class only while its frame is fixed; when the anchor moves, its output moves with it,
deterministically (§3.2). Stability is a precondition this design meets, not a property that sets it
apart.

*Re-centring the origin, not reorienting the axes, is the lever for local navigation.* Moving the
anchor to the query (\( c_1 = q \)) raises local neighbourhood recovery 29×, from 0.019 to 0.543 at
unit scale, for a frame construction of 42.8 µs (§3.5). Reorienting the view instead — refitting a
linear projection on the query's own neighbourhood — fails to recover the local structure (0.023)
and costs 121× more per frame. Re-centring alone would not rescue that projection: translation leaves
every pairwise distance in a linear view unchanged, and a two-axis projection discards all but two of
the 384 dimensions, so points far from the query in the discarded ones land on top of it. What
re-anchoring adds is a coordinate that is a norm measured from the query — in the exploratory
ablation of §3.5, \( \|r\|_2 \) alone recovers every neighbour of every query — and that coordinate
measures distance from the query only once the origin sits there. What local exploration needs is an
origin that moves with the query.

*The radial baseline exploits the origin better, but the operator's gap was a unit mismatch that
leaves the global instruments untouched.* The `radial_plain` baseline reaches 0.981 local recall because
its vertical axis directly measures the exact Euclidean distance to the query. Most of the operator's
initial gap came from expressing the dimensionless coefficient \( \lambda \) alongside the length
\( d_{esc} \) at the same scale. Under the isometric rule (\( S_x = \|v_{dipole}\|_2 \cdot S_y \)),
Proposition 3 makes the screen distance to the query equal to \( \|r\|_2 \) for every unsaturated
stimulus, raising recall to 0.925 (median 1.000) in the exploratory ablation of §3.5, and what
remains between that figure and \( \|r\|_2 \) alone is confined to saturation at the boundaries.
Likewise, while this scale corrects the local metric distance, on the global evaluations
(§3.2–§3.4) it barely matters — at most 0.003 in trustworthiness and 0.02 in lift — and it leaves
intact all four orderings of baselines and rules that F3 defined.

### 4.2 Relation to Prior Work

> TODO — the author writes this subsection. Agreed content: the rank-1 complement and Gram-Schmidt;
> embedding debiasing (Bolukbasi et al., 2016); centroid-difference axes (Liu et al., 2018;
> Bandyopadhyay et al., 2022); semantic-axis methods — SemAxis (An et al., 2018) and semantic
> projection (Grand et al., 2022), both verified against their publisher records and to be added to
> the references when cited — and what the operator adds to them, removing the anchor's component
> before forming the axis; LSH (Charikar, 2002) in one sentence. The paragraphs below are retained
> from the previous draft as material.

The projector \( P_\perp \) itself is not new: it is the standard rank-1 orthogonal complement, and
its associative form \( P_\perp v = v - \langle v, \hat{c}_1\rangle\hat{c}_1 \) is the same identity
underlying classical Gram-Schmidt orthogonalization — it is what lets Proposition 1 avoid
materializing the dense \( d \times d \) matrix, not a new mathematical object. The honest question
is not whether \( P_\perp \) is novel, but what this paper does with it that a reader already
familiar with that identity would not expect.

The closest structural precedent is debiasing word embeddings (Bolukbasi et al., 2016), which
learns a bias subspace from paired difference vectors and projects it out of the remaining
embeddings with the same rank-1 orthogonal complement used here. The distinction is *where and
when* \( P_\perp \) is applied: Bolukbasi et al. use it as a static, global, one-time preprocessing
pass over the whole corpus, permanently altering stored embeddings; the Polar Projector applies the
identical primitive as a volatile, per-interaction \( O(d) \) operator against one active anchor,
never touching persisted embeddings. This contrast pre-empts the most direct version of "this is
just embedding debiasing."

The dipole construction fares similarly under scrutiny. Projecting embeddings onto an axis defined
by the difference of two centroids, \( c_A - c_B \), is an established visualization technique (Liu
et al., 2018; Bandyopadhyay et al., 2022), so a pair-of-centroids dipole is not itself a
contribution. What those methods do not do, and what this operator does by construction, is remove
the anchor's own component from both poles *before* forming the axis: by linearity of \( P_\perp \),
\( P_\perp c_A - P_\perp c_B = P_\perp(c_A - c_B) \), so the dipole is anchored to the local
complement, not to the raw embedding space those visualization tools project onto directly.

The structurally closest prior art to the *shape* of this computation, rather than to its purpose,
is random-hyperplane locality-sensitive hashing (Charikar, 2002): both reduce to an inner product
against a reference direction. The two solve different problems. LSH is stochastic by design and
targets approximate similarity search over an entire corpus; the Polar Projector is deterministic,
uses one semantically-chosen anchor rather than a random one, and answers a local directional
question against an active state, not a retrieval question over the whole dataset. This is the most
likely reviewer objection, so it is stated here directly rather than left implicit.

### 4.3 Limitations

> TODO — the author writes this subsection. Agreed content: one corpus, one encoder and one host;
> `part` as a coarse proxy for relevance; E5, E6 and E7 were not pre-registered and the E7 ablation is
> post hoc (`paper/claims.md` records each figure's status); no significance tests; the reading of
> \( \lambda \) in the published frame depends on the composition of the initial window (§2.1); an
> unrepresentative anchor — a centroid of a bimodal neighbourhood falling between its modes — leaves
> every norm well-conditioned and is detected by nothing here (§6 refers to this); and no user took
> part.

## 5. Conclusion

We set out to show that a local, deterministic \( O(d) \) operator is the right primitive for
placing an incoming vector in a spatial interface over a growing corpus, and we can report a
narrower result than that. The operator is correct, its degenerate cases are proven non-degenerate,
one of its two algebraically equivalent forms fails silently and must not be used, and its cost is
flat in corpus size across a 25× range. Those are properties we can hand to someone building on it.

What we cannot hand them is a reason to prefer it on the evidence assembled here. Exact positional
stability, which motivated the work, is a property of any fixed linear map and three arms have it.
On manifold preservation a once-fitted PCA sits inside the operator's own range, and the pole
selection rule that reaches the top of that range does so by aligning with variance, at which point
the operator and the PCA are interchangeable on both instruments. Re-anchoring — the one lever
genuinely specific to a local frame, and worth a factor of 29 at a frame cost 121× below
that of a local refit — still trails a two-line radial coordinate subject to the same
constraints: narrowly once \( \lambda \) is rendered in the same units as \( d_{esc} \) (0.925
against 0.981), and by a wide margin when it is not.

We report this as the outcome rather than restructuring around a comparison that survives, because
the negative results are the part a reader cannot easily reconstruct. That a fixed random projection
lands at chance on both fidelity instruments is what makes every figure above it meaningful. That a
locally refitted PCA scores below a globally fitted one identifies a whole family of approaches —
refit the directions near the query — as the wrong lever, and says why: a projection reorients but
cannot recentre. That pole selection trades manifold preservation against task-level agreement
rather than improving both tells an implementer which knob they are actually turning. None of these
would have appeared in a paper organized around a win.

The property that remains unmeasured is the one the construction was designed for: \( \lambda \) is
a bounded coordinate between two named poles, and the baselines that beat it on numerical fidelity
offer nothing comparable as an interface control signal. Whether that is worth anything to a person
navigating is a behavioural question, and answering it is the work this paper makes possible rather
than the work it does.

## 6. Open Questions

> TODO — draft, not reviewed. Four items, kept as a list rather than prose: each is an independent
> open problem, and forcing transitions between unrelated questions would manufacture connections
> that are not there. Earlier drafts carried eight; the four dropped were narrow numerical
> questions about \( \epsilon_{collinear} \) tightness, sample size near collinearity, further
> stabilization of the vector-form residual, and adversarial anchor dynamics. They remain open and
> are recorded in the repository's issue history rather than padding this section.

- **What is a bounded, interpretable contrast coordinate worth?** This is the question the paper
  cannot answer and the one everything else now rests on. §3.5's radial baseline beats the operator
  at local neighbourhood recovery while meeting every constraint of §1, but its horizontal axis is
  the projection onto an arbitrary direction and its vertical axis is unbounded. The operator's
  \( \lambda \in [-1, 1] \) is a bounded coordinate between two *named* poles, which is what makes
  it usable as an interface control signal rather than only as a position — and no instrument in
  this paper measures that. A fair test is behavioural, not numerical: whether a person navigating
  a corpus locates material faster, or builds a more durable spatial model, under a bounded named
  axis than under an unbounded arbitrary one. Until that exists, §3.5's bound stands unqualified.
- **Is intermittent relocation better or worse than steady drift?** §3.2 found UMAP fitted once and
  extended by `transform()` to be bimodal — exactly still for 5 of 7 growth steps, then relocating
  by 1.07. Our own moving-anchor arm does the opposite: it always moves a little (0.13–0.61) and
  never spikes. Which profile damages a user's spatial mental model more is an empirical HCI
  question that this paper's measurements cannot answer, and we decline to assume the answer
  favours us. Boechler (2001) establishes that instability degrades navigation; it does not
  distinguish these two shapes of instability.
- **Is the trade-off of §3.4 a frontier or an artifact of one corpus?** Every rule that gained
  trustworthiness lost task-level lift, on 2,221 chunks of one text with a five-way part label. That
  the trade is real here does not establish that it is a property of the construction rather than of
  this corpus's structure, and the part labels are a coarse proxy for relevance in any case. Open:
  whether the same opposition appears on a corpus of a different shape, and whether a rule exists
  that sits strictly above the line rather than on it.
- **Detecting an unrepresentative anchor.** §4 notes that a centroid summarizing a bimodal
  neighborhood can fall in the gap between its two modes, making it the least representative point
  of both. Proposition 2 does not cover this — it handles a collapsed contrast axis, not a badly
  placed origin — and every norm in Propositions 1–3 stays well-conditioned throughout, so the
  operator returns confident values whose interpretation has quietly stopped holding. That is the
  more dangerous of the two degeneracies and the one with no guard: what a cheap per-frame test for
  it would look like, and whether \( d_{esc} \)'s own distribution across a context already carries
  the signal, is unexamined. §3.5 sharpens this rather than resolving it: re-anchoring makes the
  origin the most consequential choice in the construction, and nothing validates it.

## Acknowledgements

> TODO.

## References

> Status: each entry is cited at least once above, and each was verified against its publisher or
> preprint record rather than reconstructed from memory. None is a claim of prior art over this
> work — §4 states how the closest ones relate to and differ from the Polar Projector.

1. Bandyopadhyay, S., Xu, J., Pawar, N., & Touretzky, D. (2022). Interactive Visualizations of Word
   Embeddings for K-12 Students. *Proceedings of the AAAI Conference on Artificial Intelligence*,
   36(11), 12713–12720.
2. Bengio, Y., Paiement, J.-F., Vincent, P., Delalleau, O., Le Roux, N., & Ouimet, M. (2003).
   Out-of-Sample Extensions for LLE, Isomap, MDS, Eigenmaps, and Spectral Clustering. *Advances in
   Neural Information Processing Systems 16 (NIPS 2003)*.
3. Boechler, P. M. (2001). How Spatial Is Hyperspace? Interacting with Hypertext Documents:
   Cognitive Processes and Concepts. *CyberPsychology & Behavior*, 4(1), 23–46.
4. Bolukbasi, T., Chang, K.-W., Zou, J., Saligrama, V., & Kalai, A. T. (2016). Man is to Computer
   Programmer as Woman is to Homemaker? Debiasing Word Embeddings. *Advances in Neural Information
   Processing Systems 29 (NeurIPS 2016)*. arXiv:1607.06520.
5. Charikar, M. S. (2002). Similarity Estimation Techniques from Rounding Algorithms. *Proceedings
   of the 34th Annual ACM Symposium on Theory of Computing (STOC 2002)*, 380–388.
6. Duff, T., Burgess, J., Christensen, P., Hery, C., Kensler, A., Liani, M., & Villemin, R. (2017).
   Building an Orthonormal Basis, Revisited. *Journal of Computer Graphics Techniques*, 6(1), 1–8.
7. Edelsbrunner, H., & Mücke, E. P. (1990). Simulation of Simplicity: A Technique to Cope with
   Degenerate Cases in Geometric Algorithms. *ACM Transactions on Graphics*, 9(1), 66–104.
   DOI:10.1145/77635.77639.
8. Espadoto, M., Martins, R. M., Hirata, N. S. T., Kerren, A., & Telea, A. C. (2021). Toward a
   Quantitative Survey of Dimension Reduction Techniques. *IEEE Transactions on Visualization and
   Computer Graphics*, 27(3), 2153–2173.
9. Gower, J. C. (1975). Generalized Procrustes Analysis. *Psychometrika*, 40(1), 33–51.
   DOI:10.1007/BF02291478.
10. Liu, S., Bremer, P.-T., Thiagarajan, J. J., Srikumar, V., Wang, B., Livnat, Y., & Pascucci, V.
    (2018). Visual Exploration of Semantic Relationships in Neural Word Embeddings. *IEEE
    Transactions on Visualization and Computer Graphics*, 24(1), 553–562.
    DOI:10.1109/TVCG.2017.2745141.
11. Marshall, C. C., & Shipman, F. M. (1995). Spatial Hypertext: Designing for Change.
    *Communications of the ACM*, 38(8), 88–97. DOI:10.1145/208344.208350.
12. McInnes, L., Healy, J., & Melville, J. (2018). UMAP: Uniform Manifold Approximation and
    Projection for Dimension Reduction. arXiv:1802.03426.
13. Neves, T. T. A. T., Martins, R. M., Coimbra, D. B., Kucher, K., Kerren, A., & Paulovich, F. V.
    (2020). Xtreaming: An Incremental Multidimensional Projection Technique and Its Application to
    Streaming Data. arXiv:2003.09017.
14. Rauber, P. E., Falcão, A. X., & Telea, A. C. (2016). Visualizing Time-Dependent Data Using
    Dynamic t-SNE. *EuroVis 2016 — Short Papers*. DOI:10.2312/eurovisshort.20161164.
15. Reimers, N., & Gurevych, I. (2019). Sentence-BERT: Sentence Embeddings using Siamese
    BERT-Networks. *Proceedings of EMNLP-IJCNLP 2019*, 3982–3992.
16. Sainburg, T., McInnes, L., & Gentner, T. Q. (2021). Parametric UMAP Embeddings for
    Representation and Semisupervised Learning. *Neural Computation*, 33(11), 2881–2907.
17. van der Maaten, L., & Hinton, G. (2008). Visualizing Data using t-SNE. *Journal of Machine
    Learning Research*, 9, 2579–2605.
18. Venna, J., & Kaski, S. (2001). Neighborhood Preservation in Nonlinear Projection Methods: An
    Experimental Study. *Artificial Neural Networks — ICANN 2001*, 485–491.
    DOI:10.1007/3-540-44668-0_68.
19. Vernier, E. F., Comba, J. L. D., & Telea, A. C. (2021). Guided Stable Dynamic Projections.
    *Computer Graphics Forum*, 40(3), 87–98. DOI:10.1111/cgf.14291.

## Appendix

The four sections below were body sections of earlier drafts. They are retained in full — every
figure still reproduces, and `tools/verify_paper_tables.py` still covers the tables CI checks — but
each answers a narrower question than §3 does: whether the implementation is numerically sound and
how it behaves off the single-stimulus path, rather than whether the operator works as a navigation
substrate.

### Appendix A — Dimension Sweep and Where Dispatch Stops Dominating

§3.1 closes by saying the operator's per-call gap to the floor is dispatch rather than arithmetic.
That caveat is testable: if it holds, per-call latency should be flat in \( d \) until the arithmetic
becomes large enough to matter.
Sweeping the prepared hot path and the random-projection floor across dimension:

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

The prediction holds. From \( d = 16 \) to \( d = 64 \) — four times the arithmetic — per-call cost
*falls* slightly, from 4.18 to 4.12 µs. At \( d = 384 \), the dimension every published figure in
this paper is measured at, `evaluate()` costs 1.10× what it costs at \( d = 16 \) despite doing 24×
the floating-point work. **Roughly 90% of the operator's per-call cost at \( d = 384 \) is fixed
overhead independent of dimension**, and about 0.4 µs of it is the \( O(d) \) work Proposition 1
describes.

The crossover sits between \( d = 1{,}024 \) and \( d = 4{,}096 \). Above it the curve turns linear
and the gap to the floor collapses — from 5.78× at \( d = 16 \) to 2.38× at \( d = 4{,}096 \),
approaching the ratio of vector passes the two methods actually make. The widening at
\( d = 8{,}192 \) (2.92×) is a memory effect, not an arithmetic one: a 65 MB working set at that
dimension no longer sits in cache.

Two consequences, both of which narrow this paper's claims rather than widening them. First, the
microsecond figures in §3 and §3.1 characterize a NumPy implementation at a dimension where NumPy
overhead dominates — they are not a measurement of Proposition 1's asymptotic claim, and the
crossover dimension is where a reader should expect that claim to become visible. Second, the
lever that would most reduce cost at \( d = 384 \) is **issuing fewer array operations**, not doing
less arithmetic; a fused or compiled implementation of the same mathematics would close most of the
gap to the floor without changing a single flop.

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
true distance, while the vector form degrades gracefully across the full sweep. The identity of
Proposition 3 therefore stands as a theorem but not as an algorithm: the residual is computed in
vector space before the norm is taken. This regime — a stimulus lying almost entirely along the
dipole axis — is precisely the one where \( \lambda \) saturates, so precision there is not
incidental.

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
**1.47× faster**. Restoring the old clamp and re-measuring both forms side by side puts that margin
at 1.24× before §A's substitution and 1.45× after it, which removed 1.8 µs from the vector form and
2.0 µs from the scalar one — nearly the same fixed overhead from both arms; subtracting a constant from both sides of a ratio moves it, and the honest
reading is that the residual computation is a larger share of a leaner call than it was of a fatter
one. Refusing the scalar form now costs about a third of the hot path rather than a fifth. The
argument is unchanged — a third of the hot path is not worth a silently wrong answer — but the
price is stated at its current value, not its more flattering old one.

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
constant floor for \( \delta \geq 0.1 \), where the fallback branch stops dominating the residual;
below that, shrinking \( \delta \) inflates \( R \) by orders of magnitude as the dipole norm
collapses toward its \( 2\delta \) floor (Proposition 2).

*Methodological note:* an earlier pass of this table at \( N = 1{,}000 \) reproduced only 4 of 6
rows within a 5% tolerance band — the two small-\( \delta \) rows deviated by 9–12%, consistent
with the theoretical ≈4.5% sampling error at that N in the near-collinear regime. This table
supersedes it.

### Appendix D — Batched Subspace Evaluation

*`evaluate_batch()` ships in `polar_projector/projector.py` and the figures below are measured by
`bench/batched.py`. It is in the appendix because it sits off the single-stimulus path §3 measures,
not because it is unimplemented — and because the determinism claims of §2 and §4 are stated for
the scalar entry points, which is the distinction this section exists to make precise.*

The associative projection \( P^\perp v = v - \langle v, \hat{c}_1 \rangle \hat{c}_1 \) extends
directly to batched inputs \( V \in \mathbb{R}^{B \times d} \):

\[ V P^\perp = V - (V \hat{c}_1) \hat{c}_1^T \]

which evaluates \( B \) stimuli against a fixed frame in \( \mathcal{O}(B \cdot d) \) without
instantiating a dense \( d \times d \) intermediate — Proposition 1's identity applied row-wise.
Against a Python loop over `evaluate()`, both arms measured under the same protocol
(\( d = 384 \), float64, \( N = 16{,}384 \)):

| \( B \) | Loop (µs/vec) | Batched (µs/vec) | Speedup | Vectors/s | Temporaries (MB) |
|---|---|---|---|---|---|
| 1 | 5.380 | 13.874 | **0.39×** | 72,075 | 0.01 |
| 4 | 5.464 | 3.649 | 1.50× | 274,064 | 0.04 |
| 16 | 4.689 | 1.568 | 2.99× | 637,692 | 0.15 |
| 64 | 4.904 | 1.102 | 4.45× | 907,198 | 0.59 |
| 256 | 4.610 | 0.893 | **5.16×** | 1,119,291 | 2.36 |
| 1,024 | 4.468 | 1.283 | 3.48× | 779,626 | 9.44 |
| 4,096 | 4.481 | 1.624 | 2.76× | 615,720 | 37.75 |

*The gain is bounded and non-monotone.* Speedup peaks at \( B = 256 \) and **falls thereafter**,
to 2.76× by \( B = 4{,}096 \) — the opposite of the "larger batches are better" reading the
identity invites. The last column explains it: the implementation holds three \( (B \times d) \)
temporaries, and at \( B = 256 \) they occupy 2.36 MB, while at \( B = 1{,}024 \) they occupy
9.44 MB and stop fitting alongside the input in this host's shared L2. Past that point the routine
is memory-bandwidth bound and batching buys less, not more. A caller choosing a batch size should
choose one that keeps \( 3Bd \) floats in cache, not the largest one available.

*At \( B = 1 \) batching is 2.6× slower than not batching.* This is reported because omitting it
would be choosing the range that flatters the result: a batch of one pays the setup and receives no
amortization. `evaluate()` remains the right entry point for a single stimulus.

*What the speedup is made of.* §A established that at \( d = 384 \) per-call cost is dominated
by the number of array operations issued, not by arithmetic. The batched path issues a fixed number
of NumPy calls regardless of \( B \), so what it amortizes is dispatch overhead — roughly 4.5 µs per
vector in the loop — rather than floating-point work. The flop count is unchanged. This is why the
ceiling is around 5× and not an order of magnitude, and why the ceiling is set by memory traffic
once dispatch has been amortized away.

*Agreement is bounded, not exact.* The batched path is **not** bitwise identical to a loop over
`evaluate()`, and the divergence begins at the matrix-vector product rather than at the norm: BLAS
switches to a blocked reduction order once \( B \geq 2 \), which a sequence of single-row dot
products does not use. Measured across all batch sizes above, the deviation is at most
\( 0.19\,\varepsilon \) in \( \lambda \) and \( 2.02\,\varepsilon\|r\|_2 \) in \( d_{esc} \). The
normalization by \( \|r\|_2 \) is not cosmetic: the error in \( d_{esc} \) is amplified by
\( \|r\|_2/d_{esc} \), so a *relative* tolerance would pass on generic stimuli and fail in exactly
the near-collinear regime of §B.

Two consequences follow, and the implementation documents both rather than leaving them to be
discovered. First, \( \texttt{evaluate\_batch}(V)_i \) **is not a pure function of** \( V_i \) and
the frame: permuting a batch and un-permuting the result is not bitwise stable at \( B = 64 \),
\( 1{,}024 \) or \( 4{,}096 \), though the magnitude is last-bit
(\( \leq 0.12\,\varepsilon \) in \( \lambda \), \( \leq 2.2 \times 10^{-16} \) in \( d_{esc} \)).
This qualifies the "deterministic execution for fixed inputs" claim §2 makes for the scalar path:
it holds there, and holds for the batched path only at fixed batch composition and order. Second,
the API exposes **no chunk size parameter**, because splitting a batch is a reduction-order change
and would silently alter results.

*The square root is free, so the energy form is not implemented.* An earlier draft of this section
proposed returning \( E_{esc} = \|r_{esc}\|_2^2 \) instead of \( d_{esc} \) to skip the square-root
instruction in hot loops. Measured, that saving is **1.0–1.6%** across \( B \in \{64, 1{,}024,
4{,}096\} \) — one square root against \( d = 384 \) multiply-accumulates, which is within the
run-to-run spread of the measurement itself. The proposal is therefore withdrawn rather than
shipped: adding a second return shape to the API to save nothing measurable would be a cost with no
corresponding benefit. The Corollary of §2 stands as an exposition device, which is all it claimed
to be, and \( E_{esc} \) remains available to any caller as `d_esc ** 2` — which is precisely the
"square the numerically stable vector-form residual" the Corollary requires, and never the expanded
form §B measured losing all precision near collinearity.
