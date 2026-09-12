# The Polar Projector: A Deterministic O(d) Operator for Interaction State, Decoupled from Persistent Storage

**Author:**
**Affiliation:**
**Date:**

> Working mirror of the manuscript authored in Corca (https://corca.app/doc/er5CXGbjDUaGnbFE45Hse).
> Corca has no external read/write access from this repo and keeps no git-style history reachable
> from here, so this file is the version-controlled source of truth between sync passes — edit here,
> paste into Corca, or vice versa, and keep both in sync by hand.
>
> Provenance: this operator and its test suite were extracted, with git history, from the
> Traianus substrate (https://github.com/AlexusPacicus/Traianus), where the design record lives
> in `docs/LEDGER.md` seq 40-43. The extraction exists so this manuscript can be reproduced with
> numpy alone, without the substrate's fastapi/torch dependency stack.
>
> Status: DRAFT. Sections 1–3 and §4.2 are grounded (verified against
> `polar_projector/projector.py`, reproduced by `tools/verify_paper_tables.py` which CI runs on
> every push, and — for §3.4, §3.5 and §4.2 — by `bench/drift.py`, `bench/recall.py` and
> `bench/batched.py` against the frozen corpus in `bench/data/`). The rest of §4, and §5–6, are
> scaffolding only — see the TODO notes — and must not be treated as final until reviewed.

---

## Abstract

Embedding-based information architectures suffer from scalability problems caused by coupling
persistent corpus storage with hot-path interaction state. Existing systems rely either on
quadratic-cost spatial simulations (\( O(N^2) \)) or on non-linear stochastic projections (t-SNE,
UMAP) that introduce spatial drift under incremental updates. While global projections excel at
static corpus visualization, they are ill-suited for hot-path control, where local spatial
continuity and deterministic repeatability are required.

To address this, we present the **Polar Projector**: a local subspace operator that acts as a
deterministic \( O(d) \) projection layer for managing interaction state in volatile memory — a
guarantee scoped to its single-stimulus entry points, `project()` and `evaluate()`; §4.2 measures
how much of it a batched throughput mode trades away. The operator evaluates an incoming vector
(\( v_n \)) against an active local anchor, operating completely isolated from persistent disk
storage and independently of global corpus size (\( N \)). It is a per-interaction primitive, not a
substitute for a global layout: it never constructs the corpus-wide coordinate system UMAP or t-SNE
do, and §3.4 measures what that costs in neighborhood fidelity. We show that the projection is
governed by an orthogonal decomposition identity — the squared norm of the projected residual
splits exactly into the aligned and residual components along a local contrast axis — and that
collinearity singularities in the tangent plane are mitigated by a deterministic fallback direction
in the anchor's orthogonal complement.

The benchmark suite measured projection latency at \( \approx 11.6\,\mu\text{s} \) with the
stateless entry point and \( \approx 4.6\,\mu\text{s} \) once the local frame is prepared once per
active context — flat across corpus sizes from 1,000 to 25,000 vectors, consistent with the
operator's proven independence from \( N \).

Against a growing corpus of 2,221 embedded text chunks, the operator holds previously-placed points
exactly fixed across every incremental step, while seed-pinned UMAP and t-SNE refits relocate them
by roughly the full width of the layout at each step. That stability is not free: on the same
corpus the operator preserves high-dimensional neighborhoods measurably worse than either baseline
(trustworthiness 0.66 against 0.90–0.92). We report this as a trade — exact positional stability
and a step roughly two orders of magnitude cheaper, paid for in fidelity — rather than as a
dominating result.

## 1. Introduction

Representing information via continuous vector embeddings rigidly couples two independent
operational dimensions:

1. **Interaction state:** volatile, short-lived trajectory dynamics in hot memory.
2. **Persistence state:** immutable, corpus-wide data structures stored on disk.

Reusing global visualization techniques (such as t-SNE or UMAP) to manage local interaction state
introduces two fundamental limitations. First, stochastic re-optimization alters existing
coordinates upon incremental updates, producing spatial drift that disrupts the user's spatial
mental model (Boechler, 2001); §3.4 measures this directly, and finds that under refitting both
methods relocate previously-placed points by roughly the full width of the layout at every
incremental step even with their random seed pinned. Second, global graph-layout algorithms scale
quadratically (\( O(N^2) \)), saturating the execution thread as corpus size grows.

That measurement does not run one way. §3.4 also finds that the operator pays for its stability in
neighborhood fidelity, and that one configuration of UMAP — fitted once, extended by
`transform()` — is stable across most incremental steps. The contribution argued here is a
different point on that trade-off, not a dominating one.

The Polar Projector resolves these bottlenecks by formulating a distinct computational primitive: a
local, deterministic \( O(d) \) hot loop that operates exclusively on the active contextual
complement, deriving a projection coefficient (\( \lambda \in [-1.0, 1.0] \)) and an orthogonal
residual (\( d_{esc} \)) without modifying or re-evaluating the global persistent corpus, with
correctness guarantees proven in §2.

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
only requirement.

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
Pythagorean equality. When \( |\lambda^*| > 1 \) (saturation), the cross-term is strictly positive:
the clip leaves the components no longer summing to \( \|r\|_2^2 \). ∎

*Corollary (Energy Form).* The decomposition above is native to squared (energy) units. Writing
\( E_\lambda = \lambda^2 \|v_{dipole}\|_2^2 \) (aligned energy — computable from \( \lambda \) and
the frame's already-stored \( \|v_{dipole}\|_2^2 \), at no extra cost) and
\( E_{esc} = d_{esc}^2 \) (residual energy), the exact case reads
\( \|r\|_2^2 = E_\lambda + E_{esc} \): a direct sum of energies — the squared-unit form of the same
orthogonal split as the linear quantities \( \lambda, d_{esc} \).
This is an exposition device, not an implementation instruction: \( E_{esc} \) must still be
computed by squaring the numerically stable vector-form residual of §3.2
(\( \|r - \lambda v_{dipole}\|_2^2 \)), never via the algebraically expanded
\( \langle r,r\rangle - 2\lambda\langle r,v_{dipole}\rangle + \lambda^2\|v_{dipole}\|_2^2 \) — that
expansion is exactly the *scalar form* §3.2 measured losing all precision below
\( d_{esc}/\|r\|_2 \approx 10^{-6} \), which is precisely the near-collinear regime where an energy
reading would most need to be trustworthy.

## 3. Numerical Behavior

All figures in this section were measured on one machine: Apple M1 (8 cores), 8 GB RAM, macOS
15.6, Python 3.11.6, NumPy 2.4.1. The machine is passively cooled, so sustained runs are subject to
thermal throttling; the run-to-run spreads reported below are what that variability amounts to in
practice. Absolute microsecond figures are properties of this host, not of the operator — the
claims that do not depend on the host are the *scaling* behaviour and the *ratios* between arms.

Benchmarked over \( N = 25{,}000 \) vectors ( \( d = 384 \), float64):

| Corpus Size (N) | Polar Projector Mean (µs) | Polar Projector p95 (µs) | \( O(N^2) \) Force Simulation |
|---|---|---|---|
| 1,000 | 11.46 | 11.92 | 0.955 s |
| 2,221 | 11.61 | 11.79 | 5.595 s |
| 4,000 | 11.61 | 12.21 | 19.800 s |
| 25,000 | 11.58 | 12.00 | 767.2 s (least-squares fit \( 1.228 \times 10^{-6} N^2 \), extrapolated) |

Projection latency stays flat as \( N \) grows — 1.3% across a 25× corpus and a 25× working set,
consistent with Proposition 1's independence from corpus size — while the \( O(N^2) \) force
baseline it replaces grows quadratically. The polar column is `bench/latency.py --n-sweep`, 3
repetitions per row; the \( O(N^2) \) column is the substrate measurement it was originally
compared against and is reproduced unchanged.

*Deployment context (not a claim of this paper — see §1 scope note):* within the Traianus
substrate, the persistence layer consuming this operator's output measured 25,000 embeddings
(76.8 MB) ingested in 1.38 s, async re-indexing in 66 ms, and 0 `SQLITE_BUSY` lock events across
191 concurrent readers (4.33–5.19 ms read latency). These numbers characterize the substrate the
benchmarks above were run in, not the operator itself.

### 3.1 Frame Preparation vs. Per-Stimulus Cost

The anchor normalization, dipole-pole projections and dipole construction of Proposition 1 depend
only on \( (c_1, c_A, c_B) \) — not on \( v_n \) — so they are invariant across every stimulus
evaluated under one active context. Splitting the operator into `prepare()` (frame construction)
and `evaluate()` (per-stimulus) separates the two costs:

| Stage | Mean (µs) | p95 (µs) |
|---|---|---|
| Full stateless call | 11.64 | 12.39 |
| `prepare()` — invariant frame | 6.90 | 7.18 |
| `evaluate()` — per stimulus | 4.56 | 4.81 |

Means over three runs of 25,000 stimuli each at \( d = 384 \), float64, fixed seeds
(`tools/decompose_polar_latency.py`); run-to-run spread is under 2%. Frame construction
accounts for 59.3% of a stateless call, so hoisting it out of the loop leaves **2.55× less work per
interaction** whenever the active context outlives a single stimulus. The stateless baseline here
(11.64 µs) is consistent with the 11.46–11.61 µs range measured independently in the table above.

#### 3.1.1 Cost Relative to Primitives of the Same Complexity Class

§3.1 compares the operator only against itself, so it establishes that the frame can be hoisted but
not whether what remains is cheap. Bracketing the prepared hot path between the least and most work
a planar local coordinate could require:

| Arm | Mean (µs) | p50 | p95 | p99 | Relative cost |
|---|---|---|---|---|---|
| Random projection, \( (2 \times d) \) matrix-vector | 1.03 | 1.04 | 1.08 | 1.12 | 0.23× |
| Multi-anchor cosine, \( K = 3 \) | 1.14 | 1.12 | 1.21 | 1.29 | 0.25× |
| **`evaluate()` — prepared frame** | **4.57** | 4.50 | 4.79 | 5.03 | **1.00×** |
| `project()` — stateless | 11.75 | 11.54 | 12.50 | 13.32 | 2.57× |
| Sliding-window PCA, \( W = 32 \) | 292.55 | 287.75 | 316.67 | 360.40 | 64.02× |

Frozen Spinoza corpus (\( N = 2{,}221 \), \( d = 384 \), float64), 3 repetitions of 2,221 calls
after 1,000 warmup iterations, arms interleaved round-robin; `bench/latency.py`. Run-to-run spread
is 2.4–2.8% on the polar arms and under 3% elsewhere.

Three things this establishes, and one it does not.

*The §3.1 figures reproduce from an independent script.* `project()` measures 11.75 µs here against
11.64 µs there, `evaluate()` 4.57 against 4.56, and their ratio 2.57× against 2.55× — on a different
corpus, with a different harness and a different frame.

*Working set is not the confound it appeared to be.* The Spinoza corpus is 6.8 MB and largely
cache-resident on this host; the synthetic corpus of §3.1 is 76.8 MB and is not. Repeating the
whole experiment at \( N = 25{,}000 \) moves `evaluate()` from 4.57 to 4.59 µs — **0.4% for 11× the
working set.** The operator's per-call cost is not memory-bound at these sizes, so figures from the
two corpora are comparable after all.

*The operator is not at the floor.* It costs **4.4× a random projection** and 4.0× a three-anchor
cosine. That gap is the price of what it additionally computes — anchor isolation, a contrast axis,
and a residual orthogonal to it — and it is a real cost, not a rounding error. What the operator
buys against the other end of the table is larger: a locally adaptive frame by sliding-window SVD
costs **64.0×** the prepared evaluation, which is the comparison that matters for a hot path.

*What this does not establish is that the gap is arithmetic.* At \( d = 384 \), NumPy's per-call
dispatch dominates: `np.dot` costs 0.433 µs on a 2-element input and 0.460 µs on a 384-element one
— 192× the floating-point work for 6% of the time. Per-call latency at this dimension therefore
tracks the **number of array operations** a method issues, not its flop count, and the 4.4× gap to
the floor is close to the ratio of NumPy calls the two arms make. The \( O(d) \) claim of
Proposition 1 is an asymptotic statement about the operator; these microseconds do not test it at
this dimension, and a reader should not read the table as if they did. §3.1.2 measures where
dispatch stops dominating.

#### 3.1.2 Where Dispatch Stops Dominating

The caveat above is testable: if the cost at \( d = 384 \) is dispatch rather than arithmetic, then
per-call latency should be flat in \( d \) until the arithmetic becomes large enough to matter.
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
`bench/latency.py --sweep`. Exploratory: this sweep was specified after §3.1.1's registered run, in
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
microsecond figures in §3 and §3.1.1 characterize a NumPy implementation at a dimension where NumPy
overhead dominates — they are not a measurement of Proposition 1's asymptotic claim, and the
crossover dimension is where a reader should expect that claim to become visible. Second, the
lever that would most reduce cost at \( d = 384 \) is **issuing fewer array operations**, not doing
less arithmetic; a fused or compiled implementation of the same mathematics would close most of the
gap to the floor without changing a single flop.

That second claim is not left as an inference — it was tested by removing exactly one array
operation. `evaluate()` clamps \( \lambda \) into \( [-1, 1] \), and clamping a single scalar
through `np.clip` enters NumPy's ufunc machinery for 1.74 µs — 29% of the whole call — where
`min(max(x, -1), 1)` does it in 0.19 µs. The two are bit-for-bit identical on every input, including
NaN, signed zero, subnormals, infinities and the float either side of the boundary, so the
substitution changes no value this paper reports. It made `evaluate()` **1.37× faster**, from 6.23
to 4.56 µs, for zero change in arithmetic. Every latency figure in §3 reflects the substitution;
every table of *values* — §3.2, §3.3, §3.4 — is unchanged by it, which is the check that the two
forms really are equivalent.

### 3.2 Conditioning of the Orthogonal Residual

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
**1.47× faster**. That margin was 1.23× before §3.1.2's clamp substitution removed 1.7 µs of fixed
overhead from both arms; subtracting a constant from both sides of a ratio moves it, and the honest
reading is that the residual computation is a larger share of a leaner call than it was of a fatter
one. Refusing the scalar form now costs about a third of the hot path rather than a fifth. The
argument is unchanged — a third of the hot path is not worth a silently wrong answer — but the
price is stated at its current value, not its more flattering old one.

### 3.3 δ-Sweep Behavior

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

### 3.4 Positional Stability Under Incremental Growth

§1 claims that stochastic global projections inherit spatial drift under incremental updates and
that a local deterministic operator does not. That claim was an assertion resting on a citation;
this section measures it, against a corpus with real semantic structure rather than synthetic
blobs: 2,221 sentence-chunks of Spinoza's *Ethics* embedded at \( d = 384 \) and
L2-normalized. The corpus grows in reading order from 500 chunks in batches of 250, and at each of
the 7 transitions we measure how far the points **already present and unchanged** moved.

*Method.* Layouts produced by UMAP and t-SNE are defined only up to a similarity transform, so raw
displacement largely measures global reorientation — which an interface could absorb by
re-anchoring its camera, and which the baselines should not be charged for. Displacement is
therefore reported after full Procrustes alignment (translation, rotation, scale), and normalized
by each embedding's own RMS radius, since the coordinate spaces are not commensurable (UMAP's units
are arbitrary; the operator's are \( (\lambda, d_{esc}) \) with \( \lambda \in [-1,1] \)). A value
of 1.0 means points moved as far as the layout is wide. Both baselines run with a fixed
`random_state`: demonstrating that an unseeded stochastic method is unstable would prove nothing,
so what is reported is the drift that *survives* seeding. Alignment is not a cosmetic correction —
for UMAP under refitting it reduces the median p95 from 5.81 to 1.16, so roughly 80% of the
apparent movement is global reorientation that the charitable reading forgives.

| Arm | Median step | Worst step | Still steps | Trustworthiness |
|---|---|---|---|---|
| Polar Projector, fixed anchor | **0.0000** | 0.0000 | 7/7 | 0.6639 |
| Polar Projector, moving anchor | 0.2984 | 0.6138 | 0/7 | 0.6208 |
| UMAP, fit once + `transform()` | 0.0000 | 1.0725 | 5/7 | 0.7681 |
| UMAP, refit per step | 1.1607 | 1.2527 | 0/7 | 0.9049 |
| t-SNE, refit per step | 1.1408 | 1.2439 | 0/7 | **0.9197** |

Aligned p95 displacement per growth step; "still" counts steps under \( 10^{-9} \).
Trustworthiness (\( k = 15 \)) of the final layout against the source 384D space measures
neighborhood preservation. Apple M1, 8 GB, macOS 15.6, Python 3.11.6, NumPy 2.4.1;
`bench/drift.py`, deterministic under a fixed seed and reproduced bit-for-bit across runs.

*What holds.* Under refitting — the path required to keep a global layout faithful as a corpus
grows — both baselines relocate previously-placed points by roughly the full width of the layout,
at every single step, with the seed pinned. This is not seed noise; it is what refitting does. The
operator with a fixed anchor is exactly still at all 7 steps, to float64 rounding.

*What does not.* Three results cut against the simple reading, and are stated here rather than
left for a reader to find.

First, UMAP fitted once and extended by `transform()` is **not** the unstable arm §1 implies — it
is bimodal. It is exactly still for 5 of 7 steps and then relocates by 1.07. Averaging across
steps yields 0.21, a figure that describes neither of the two things that actually happen; the
aggregation here is median-and-worst for that reason. Whether intermittent relocation is better or
worse than steady drift is not settled by this measurement: a spatial mental model that is
confirmed five times and then violated may be harmed more than one that is never trusted. We flag
this as a question (§6), not as a result in our favour.

Second, and most directly against us: **the operator is the least faithful arm in the table.** Its
trustworthiness (0.66 fixed, 0.62 moving) sits well below the refit baselines (0.90–0.92) and
below fit-once (0.77). Part of that gap is a category difference — the operator never constructs a
global layout, and trustworthiness scores exactly the thing it does not attempt. But it is not
purely a category error: \( (\lambda, d_{esc}) \) is consumed as a planar position by at least one
system built on this operator, and under that use the metric is a fair question. The conclusion
this section supports is therefore a trade, not a victory: **exact positional stability and a step
roughly two orders of magnitude cheaper, paid for in neighborhood fidelity.**

Third, the moving-anchor arm drifts. It must: the operator's output is anchor-relative by
construction, so \( \lambda \) and \( d_{esc} \) change when \( c_1 \) does, and a paper reporting
only the fixed-anchor row would be claiming a stability the operator does not have. What the
measurement shows is that this drift stays bounded (0.13–0.61 across steps) and never exhibits the
relocation spikes of fit-once UMAP. The defensible claim is accordingly narrower than "no drift",
and stronger: **drift is a deterministic function of one explicit, caller-controlled variable, not
of hidden stochastic state and not of corpus size.**

*Scope.* Comparing a per-interaction local operator against global layout algorithms is a
task-level comparison, not an algorithm-level one: these methods do not compute the same object.
It is included because §1 names them as what practitioners reach for, and a claim about displacing
them should be measured rather than asserted. The mismatch is a limitation of the comparison, and
the trustworthiness column is where it shows.

### 3.5 Task-Level Neighborhood Preservation: Same-Part Retrieval

§3.4's trustworthiness column leaves an open question stated directly in §6: whether that
instrument is even the right one for a per-interaction signal. This section gives a second,
task-shaped instrument on the same corpus and the same growth schedule, and lets a reader judge the
fidelity gap against something more concrete than a manifold-preservation score: if a reader asked
"what else is like this point," what fraction of the answer would come from the same part of the
*Ethics* the point itself belongs to?

*Method.* At each of the same eight growth steps as §3.4, and for every arm's 2D output at that
step — \((\lambda, d_{esc})\) for the operator, an arbitrary 2D layout for the baselines —
recall@15 measures, for every point, what fraction of its 15 nearest neighbours in that 2D space
share its `part` label (P1_GOD .. P5_POWER; `bench/data/PROVENANCE.json`). The frozen corpus is read
in part order, so the prefix at size 500 is far more lopsided across parts than the full
2,221-chunk corpus, and a uniformly-random neighbour already matches by chance far more often early
(chance ≈ 0.70) than late (chance ≈ 0.22). What is reported is *lift* — recall@15 divided by that
step's own chance level — the same kind of correction §3.4 already applies when it normalizes
displacement by RMS radius rather than comparing raw coordinates. `bench/recall.py`; deterministic
under the same fixed seed as §3.4, reusing its embeddings rather than recomputing UMAP/t-SNE/polar
coordinates a third way.

| Arm | Median lift | Final-step lift | Worst-step lift |
|---|---:|---:|---:|
| Polar Projector, fixed anchor | 1.57× | 1.59× | **1.17×** |
| Polar Projector, moving anchor | 1.39× | 1.34× | 1.17× |
| UMAP, fit once + `transform()` | 1.57× | 1.57× | 1.12× |
| UMAP, refit per step | 2.05× | 2.41× | 1.12× |
| t-SNE, refit per step | **2.12×** | **2.47×** | 1.10× |

1× = no better than a uniformly random neighbour at that step's part composition. Worst-step is the
first step (size=500) for every arm, without exception — a property of the corpus at that size, not
of any arm; see below.

*What holds.* Against this instrument the fixed-anchor operator is statistically indistinguishable
from fit-once UMAP: 1.57× median lift for both, 1.59× against 1.57× at the final step. That is a
closer race than §3.4's trustworthiness column shows (0.66 against 0.77) — the two arms that never
fully re-account for new data land in the same place on a task a reader can interpret directly, not
only on a manifold-preservation score neither of them was optimizing for.

*What does not.* The refit baselines pull ahead as the corpus grows rather than staying level: both
t-SNE and UMAP-refit cross 2× lift by the middle of the growth schedule and reach 2.41–2.47× by the
final step, while the operator and fit-once UMAP plateau around 1.3–1.6×. That is the same story
§3.4 already tells about trustworthiness (0.90–0.92 for the refit arms against 0.66–0.77 for the
others) — refitting buys measurably more locally-coherent neighbourhoods, on this task as on that
one, and it buys it at exactly the cost §3.4 measures: relocating previously-placed points by
roughly the full width of the layout at every step.

*The worst-step column does not discriminate, and that is disclosed rather than hidden.* Every
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

## 4. Extensions

> TODO — draft, not reviewed. Candidate directions, scoped strictly to the Polar Projector itself
> (not the broader Ulpia/Traianus system). §4.2 is the exception and is no longer a proposal:
> `evaluate_batch()` ships, and that subsection reports measurements. §4.1, §4.3 and §4.4 do not
> exist in `polar_projector/projector.py` — each is a proposed direction, not a description of
> current code.

### 4.1 Multi-Axis Tangent Frames and the Tripolar Model

The core Polar Projector derives a 1D scalar signal \( \lambda \) from a single projected dipole
\( v_{dipole} = P_\perp(c_A - c_B) \). This construction extends natively to \( m \)-dimensional
local tangent frames (\( m \ll d \)). Selecting additional secondary centroids
\( \{c_C, c_D, \dots\} \) and applying Gram-Schmidt orthogonalization within the null space of
\( \hat{c}_1 \) constructs an orthonormal basis \( \{u_1^\perp, u_2^\perp, \dots, u_m^\perp\} \).
Evaluating \( r \) across \( m \) orthogonal dipoles yields a multi-axis coordinate vector
\( \boldsymbol{\lambda} \in [-1.0, 1.0]^m \), resolving directional ambiguity in multi-faceted
local manifolds while preserving the \( \mathcal{O}(m \cdot d) \approx \mathcal{O}(d) \)
associative projection property (for \( m \) treated as a small bounded constant, not asymptotic
in \( d \) or \( N \) — same status as \( K \) in Proposition 1).

As a limiting 3-anchor case, a **Tripolar Model** would evaluate interactions against three key
anchors (\( c_1, c_{near}, c_{far} \)) instead of one. This could resolve directional ambiguity
across distant manifold regions without losing the \( \mathcal{O}(d) \) linear-time execution
guarantee. Nothing about this extension is concurrent or timing-related — it is a purely geometric
generalization of the single-anchor construction to multiple simultaneous anchors.

### 4.2 Batched Subspace Evaluation

*This subsection is not scaffolding: `evaluate_batch()` ships in
`polar_projector/projector.py` and the figures below are measured by `bench/batched.py`.*

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

*What the speedup is made of.* §3.1.2 established that at \( d = 384 \) per-call cost is dominated
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
the near-collinear regime of §3.2.

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
form §3.2 measured losing all precision near collinearity.

### 4.3 Adaptive Scale Calibration

In the core formulation, the fallback scale factor \( \delta \) is a static hyperparameter
(\( \delta = 0.100 \)). An adaptive calibration rule could instead scale \( v_{dipole} \)
dynamically relative to local manifold dispersion:

\[ \delta_{local} = \eta \cdot \frac{1}{|\mathcal{C}|} \sum_{i \in \mathcal{C}} \|c_i - c_1\|_2 \]

where \( \eta > 0 \) is a global scaling constant and \( \mathcal{C} \subset \mathcal{C}_{active} \)
is the active local neighborhood. Scaling the synthetic dipole diameter dynamically could prevent
artificial voltage saturation in dense subspaces. Proposition 2's non-degeneracy bound
\( \|v_{dipole}\|_2 \geq \min(\epsilon_{collinear}, 2\delta_{local}) > 0 \) would still hold under
this substitution, but only conditionally: it requires \( \delta_{local} > 0 \), i.e. \( \eta > 0 \)
and \( \mathcal{C} \) not entirely coincident with \( c_1 \) (every \( c_i = c_1 \) drives
\( \delta_{local} \to 0 \), degrading the bound along with it — see §6 for this edge case).

### 4.4 Active Codebook Capacity

Proposition 1 assumes secondary dipole centroids are selected from "a bounded active codebook
\( C \) (\( |C| = K \leq 256 \))" — this is a modeling assumption about an external caller, not
something implemented inside `polar_projector/projector.py` today: no codebook data
structure, capacity bound, or eviction policy exists anywhere in the current codebase (`centroid_id`
is a bare, unbounded external identifier). Any discussion of behavior beyond \( K = 256 \) is
therefore conditional future work, not a description of an existing capacity story. *If* such a
codebook is implemented, keeping \( K \) small enough that centroid indices fit compact
representations and active-frame construction (\( \mathcal{O}(K \cdot d) \approx \mathcal{O}(d) \))
stays cache-resident would matter; an LRU eviction policy or a hierarchical Product Quantization
(PQ) index are two candidate mechanisms for bounding \( K \) as active contexts grow past that
point — but confirming whether a codebook needs to exist at all, and at what layer, comes first.

## 5. Discussion

> TODO — draft, not reviewed.

*Scope guard.* This section argues determinism as a property of the **operator itself** — canonical
`argmin` tie-breaking, fixed-threshold clipping, no iterative optimization or random seed anywhere
in `project()` (Props 1–3) — not as a claim about the rest of whatever system consumes it. Whatever
else Traianus/Ulpia does architecturally is out of scope here and belongs to later, separate papers.

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

One naming collision is worth flagging explicitly rather than leaving for a reader to discover
independently: at least one existing system (`chronos-vector`,
github.com/manucouto1/chronos-vector) uses the name "Anchor Projection" for
`project_to_anchors(traj, anchors, metric='cosine')` — cosine distance from a trajectory to
*multiple* anchors, producing a multi-anchor coordinate summary. This is a different mechanism from
the single-anchor rank-1 decomposition used here; the shared vocabulary is coincidental, not
structural.

None of the above is where this paper's claim to a contribution rests. That claim is determinism
itself, as a property of the operator, not as a slogan. Any system that reaches for a stochastic
method — t-SNE, UMAP, randomly-initialized force layout — to answer this specific question (how
does an incoming vector relate to one active local state) inherits spatial drift: identical
underlying data can render at different apparent positions across runs or incremental updates, so
spatial proximity stops reliably encoding semantic proximity. The Polar Projector does not inherit
this, by construction (Props 1–3, and the canonical `argmin` tie-break of Proposition 2's fallback
in particular), independent of anything else about the system that adopts it. This construction
argument covers the scalar entry points — `project()`, `prepare()` and `evaluate()` — where every
proposition above holds without qualification; §4.2 ships a separate batched entry point for
throughput and measures the bounded amount of per-row determinism it trades away, so the claim in
this paragraph is stated for the path it actually holds for. §3.4 turns the scalar-path
construction argument into a measurement: across seven incremental growth steps the operator is
exactly still while seed-pinned refits of both baselines relocate points by about the width of the
layout each time. This matters beyond raw correctness: HCI research on hypertext navigation shows
users build a persistent spatial mental model of the interface they interact with, and that
instability in that layout measurably degrades navigation and orientation (Boechler, 2001) — a
stable, reproducible operator is valuable for the signal it produces (\( \lambda, d_{esc} \)),
independent of any claim about how a downstream system renders or persists positions.

Two qualifications belong here rather than in a footnote, because both weaken the paragraph above.
The stability is *conditional on the anchor*: \( \lambda \) and \( d_{esc} \) are anchor-relative,
so a system that moves \( c_1 \) moves its output too (§3.4 measures that arm at 0.13–0.61 per
step). What the operator removes is not change but *unattributable* change — drift becomes a
deterministic function of a variable the caller sets, rather than of hidden optimizer state. And
the stability is *paid for*: §3.4 finds the operator preserves high-dimensional neighborhoods
worse than either baseline (0.66 against 0.90–0.92). A reader weighing this operator against UMAP
should weigh that number too; determinism is the contribution being argued, not a claim of
across-the-board superiority.

The structurally closest prior art to the *shape* of this computation, rather than to its purpose,
is random-hyperplane locality-sensitive hashing (Charikar, 2002): both reduce to an inner product
against a reference direction. The two solve different problems. LSH is stochastic by design and
targets approximate similarity search over an entire corpus; the Polar Projector is deterministic,
uses one semantically-chosen anchor rather than a random one, and answers a local directional
question against an active state, not a retrieval question over the whole dataset. This is the most
likely reviewer objection, so it is stated here directly rather than left implicit.

*A reading in terms of known and unknown.* Proposition 3's energy split (§2, Corollary) admits a
plain epistemic gloss worth stating once, explicitly, rather than left implicit in the energy
decomposition: \( E_\lambda \) is the portion of an incoming stimulus's energy that the
active local frame already explains — it lies along an axis built from two previously-observed
centroids — while \( E_{esc} \) is the portion that frame cannot account for. This reading has a
boundary worth stating alongside it, not hiding: a centroid is, by the defining property of the
arithmetic mean, the point that minimizes total squared distance to the group it summarizes — in
that precise sense it *is* the most "known" point of a unimodal neighborhood. But the same
construction can mislead for a bimodal one, where the mean falls in the gap between two clusters
rather than inside either — the least representative point of both. That is not a hypothetical
concern; it is the exact configuration Proposition 2's collinearity fallback exists to handle, so
the known/unknown reading and the paper's own non-degeneracy guarantee describe the same failure
mode from two directions.

## 6. Open Questions

> TODO — draft, not reviewed. Kept as a list rather than prose: each item below is an independent
> open problem, not a connected argument, and forcing narrative transitions between unrelated
> questions would manufacture connections that aren't there.

- **Is intermittent relocation better or worse than steady drift?** §3.4 found UMAP fitted once and
  extended by `transform()` to be bimodal — exactly still for 5 of 7 growth steps, then relocating
  by 1.07. Our own moving-anchor arm does the opposite: it always moves a little (0.13–0.61) and
  never spikes. Which profile damages a user's spatial mental model more is an empirical HCI
  question that this paper's measurements cannot answer, and we decline to assume the answer
  favours us. Boechler (2001) establishes that instability degrades navigation; it does not
  distinguish these two shapes of instability.
- **The fidelity gap, and whether it is reducible.** §3.4 measures the operator at 0.66
  trustworthiness against 0.90–0.92 for the global baselines. §3.5 answers this bullet's previous
  question of whether trustworthiness is even the right instrument by building a second,
  task-shaped one (same-part recall@15) — and finds the same shape of result on it: the
  fixed-anchor operator ties fit-once UMAP (1.57× lift, both) and both trail the refit baselines
  (2.05–2.12×). Two instruments agreeing is weaker evidence than it first looks, since both measure
  neighbourhood coherence on the same one corpus — it rules out an instrument-specific artifact, not
  a corpus-specific one. Genuinely still open: what is the achievable ceiling for a local,
  deterministic, \( O(d) \) operator on either instrument, whether the multi-axis extension of §4.1
  raises it by giving the frame more than one degree of freedom, and whether `part` (or a
  `part`-like semantic proxy) generalizes as a relevance signal beyond one five-part corpus this
  small.
- **Tightness of the \( \epsilon_{collinear} \) vs. \( \delta \) bound in Proposition 2.** The
  guarantee \( \|v_{dipole}\|_2 \geq \min(\epsilon_{collinear}, 2\delta) \) is a worst-case bound;
  whether it is ever loose enough in practice to matter — whether real collinear configurations
  approach it — hasn't been measured. The δ-sweep in §3.3 varies \( \delta \) but doesn't
  specifically probe the tightness of this particular inequality.
- **Behavior under adversarial or fast-drifting anchors.** Every proposition here treats
  \( (c_1, c_A, c_B) \) as fixed for the duration of one `prepare()`/`evaluate()` cycle. What
  happens to \( \lambda \) and \( d_{esc} \) continuity if \( c_1 \) itself changes between calls
  faster than the interaction loop consumes them — is there a meaningful notion of Lipschitz
  continuity in the anchor, or does an anchor change simply invalidate the frame outright (the
  current `PolarFrame` design's implicit assumption)?
- **Required sample size for variance-sensitive metrics near the collinear regime.** §3.3's
  methodological note already found that \( N = 1{,}000 \) undersamples by 9–12% in the two
  smallest-\( \delta \) rows while \( N = 10{,}000 \) does not; this was resolved empirically for
  that one table, but the general relationship between \( \delta \), dimension \( d \), and the
  sample size needed for a trustworthy variance estimate near collinearity hasn't been turned into
  a guideline a reader could apply to a different sweep.
- **Further stabilization of the §3.2 vector-form residual.** The vector form degrades gracefully
  rather than catastrophically, but "gracefully" is not "exactly" — whether re-orthogonalization or
  another correction could tighten the vector-form error further in the regime where \( P_\perp \)
  suffers cancellation for stimuli nearly parallel to the anchor has been measured (§3.2's table)
  but not addressed algorithmically.
- **§4.3's adaptive \( \delta_{local} \) under a degenerate neighborhood.** If the active
  neighborhood \( \mathcal{C} \) collapses to points coincident with \( c_1 \) (or \( \eta \to 0 \)),
  \( \delta_{local} \to 0 \) and Proposition 2's non-degeneracy bound degrades along with it. §4.3
  states \( \delta_{local} > 0 \) as a precondition; what's missing is an explicit lower bound on
  \( \delta_{local} \) itself, analogous to how \( \delta \) is required `> 0` at construction time
  for the static case.

## Acknowledgements

> TODO.

## References

> Status: found via the Browser tool (per the option below) and user-verified prior to inclusion.
> Each entry is cited at least once above; none is a claim of direct novelty over this work — see
> §5 for how each relates to (and differs from) the Polar Projector.

1. Bandyopadhyay, S., Xu, J., Pawar, N., & Touretzky, D. (2022). Interactive Visualizations of Word
   Embeddings for K-12 Students. *Proceedings of the AAAI Conference on Artificial Intelligence*,
   36(11), 12713–12720.
2. Boechler, P. M. (2001). How Spatial Is Hyperspace? Interacting with Hypertext Documents:
   Cognitive Processes and Concepts. *CyberPsychology & Behavior*, 4(1).
3. Bolukbasi, T., Chang, K.-W., Zou, J., Saligrama, V., & Kalai, A. T. (2016). Man is to Computer
   Programmer as Woman is to Homemaker? Debiasing Word Embeddings. *Advances in Neural Information
   Processing Systems 29 (NeurIPS 2016)*. arXiv:1607.06520.
4. Charikar, M. S. (2002). Similarity Estimation Techniques from Rounding Algorithms. *Proceedings
   of the 34th Annual ACM Symposium on Theory of Computing (STOC 2002)*.
5. Duff, T., Burgess, J., Christensen, P., Hery, C., Kensler, A., Liani, M., & Villemin, R. (2017).
   Building an Orthonormal Basis, Revisited. *Journal of Computer Graphics Techniques*, 6(1).
6. Liu, S., Bremer, P.-T., Thiagarajan, J. J., Srikumar, V., Wang, B., Livnat, Y., & Pascucci, V.
   (2018). Visual Exploration of Semantic Relationships in Neural Word Embeddings. *IEEE
   Transactions on Visualization and Computer Graphics*, 24(1), 553–562.
   DOI:10.1109/TVCG.2017.2745141.
7. `chronos-vector` (manucouto1). Temporal vector database; "Anchor Projection" tutorial and
   `project_to_anchors()` API. https://github.com/manucouto1/chronos-vector — software, cited in
   §5 for terminology disambiguation only, not as academic prior art.
