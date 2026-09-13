# Claims registry

Phase 2 of the manuscript plan. **Nothing enters the manuscript without a row here**, and a row
whose status is `checked` must name at least one check that `tools/verify_paper_tables.py`
actually runs — CI fails otherwise. The registered question this paper answers (phase 1, revised
2026-09-13):

> In a spatial interface over a growing corpus, any fixed map decouples interaction from corpus
> state: what is written does not move what has been placed, and cost does not depend on what is
> stored. What a local frame adds is re-centring the view on the query without re-coupling it —
> which a local refit does not achieve — and a simple radial coordinate exploits that better than
> the operator.

What would refute it, and where it stands:

- **F1** — a method that re-centres by querying the corpus matches the re-anchored operator on local
  recall. Measured, does not hold: 0.023 against 0.543 (C11, C12).
- **F2** — a fixed map, without re-centring, matches it on local recall. Measured, does not hold:
  0.056 (C12).
- **Bound** — the radial coordinate beats the operator. Measured, holds: 0.981 against 0.543 at unit
  scale, and against 0.925 in the exploratory isometric view (C13).

Terms of the question. *Corpus state* is the content and size of the stored corpus, not persistence
on disk, which is out of scope. Whether a method needs the corpus for each view is a fact of its
construction, not a measurement, and the manuscript states it as such; it is not established for
UMAP fitted once. The re-anchoring codebook is built once over the whole corpus, so a growing corpus
re-couples at each rebuild (§4.3). No new experiment is part of this revision: every figure it rests
on is already registered below.

Superseded question (phase 1, approved earlier on 2026-09-13), kept for traceability:

> For placing an incoming vector relative to an active context, exact positional stability does not
> distinguish a local operator, because any fixed linear map has it. What a local frame provides that
> a fixed map does not is re-centring the origin on the query; how much of that shows on screen
> depends on the declared scale; and a simple radial coordinate exploits that lever better than the
> operator at both measured scales.

## Vocabulary

**Status**
- `checked` — every figure the claim quotes has a row in the verifier.
- `not-in-ci` — backed by a committed artifact but deliberately not checked (host timings).
- `mismatch` — the manuscript quotes a figure no committed artifact contains. Must be fixed before
  phase 4 ends.
- `unbacked` — no script or artifact. May not be stated as a measurement.
- `pending` — admissible only if Alexis decides to include it and a script is written.
- `construction` — a fact about how a method is built, read from its code rather than measured. It
  quotes no figure, so it names its source instead of a check, and the manuscript must state it as
  construction, never as a result.
- `remove` — must not appear in the manuscript.

**Pre-registered**
- `yes (commit)` — protocol committed before its results.
- `no` — script and results entered in the same commit. Not wrong, but it may not be described as
  pre-registered.
- `post hoc` — specified after seeing the result it explains, and labelled exploratory in the text.

**CI checks** are prefixes of verifier labels in backticks, or `pytest`, `recompute:§B`,
`recompute:§C`. Every checked string must also be printed in the manuscript. Two exceptions: rows
listed in the verifier's `AWAITING_TEXT` (registered for phase 4, not yet written) and
single-character strings. Known limit: this checks presence, not location. A string that also
occurs elsewhere in the paper passes. Phase 4 is done when `AWAITING_TEXT` is empty.

## Operator

| ID | Claim | Status | Pre-registered | Source | CI checks |
|---|---|---|---|---|---|
| A1 | Propositions 1–3: the dipole is non-degenerate for collinear poles, and the residual decomposition is exact when λ is unsaturated and an inequality when it saturates | checked | n/a (proof) | tests/test_polar_projector_properties.py | `pytest` |
| A2 | The scalar form of d_esc loses all precision below d_esc/‖r‖ ≈ 1e-6 | checked | yes (06c0d5c) | bench/conditioning.py → conditioning.json | `recompute:§B` |
| A3 | That failure is undetectable at 1e-11 and 1e-13: the radicand stays positive and the error is 1.4e3 and 1.4e5 | checked | yes (06c0d5c) | conditioning.json | `§B  undetectable` |
| A4 | The scalar form is 1.47× faster (3.10 against 4.56 µs). Re-measured side by side, its margin is 1.24× under the old clamp and 1.45× under the new one, which removed 1.8 µs from the vector form and 2.0 µs from the scalar one | checked | 1.47× yes (06c0d5c); side by side no (bench/clamp.py) | conditioning.json; clamp.json | `§B  scalar`; `§B  vector-form`; `§B  clamp` |
| A5 | The stateless call is flat in N: 11.46–11.61 µs for N = 1,000–25,000, a 1.4% spread | checked | yes (c21024c) | bench/latency.py → latency.json | `§3  sweep` |
| A6 | prepare/evaluate split: evaluate 4.57 µs, project 11.75 µs, prepare 6.87 µs, 59.7% of a stateless call; the prepared split does 2.57× less work per interaction, costs 4.4× and 4.0× the two floor arms and 64.0× less than sliding-window PCA, and moves 0.4% across an 11× working set | checked | yes for latency (c21024c); no for decompose | latency.json; decompose.json | `§3.1` |
| A7 | About 90% of per-call cost at d = 384 is dispatch; the crossover sits between d = 1,024 and 4,096 | checked | post hoc (protocol 21e8e45, specified after E2) | latency.json | `§A  d=`; `§3.1 dispatch`; `§3.1 O(d)` |
| A8 | Clamping with min/max is bit-identical to np.clip | checked | no (c3dfb0b) | tests/test_polar_projector_unit.py | `pytest` |
| A9 | The clamp substitution makes evaluate() 1.40× faster (6.34 → 4.54 µs). np.clip costs 1.88 µs per clamp against 0.23 µs, 30% of the old call, and outputs are bitwise identical on all 25,000 stimuli and 14 edge values | checked | no (re-measurement of figures c3dfb0b never exported) | bench/clamp.py → clamp.json | `§A  clamp` |
| A10 | Batching peaks at 5.16× (B = 256), is 0.39× at B = 1, and is non-monotone | checked | yes (4b159d0) | bench/batched.py → batched.json | `§D  B=` |
| A11 | Batched agreement is ≤ 0.19 ε in λ and ≤ 2.02 ε‖r‖ in d_esc; a permuted batch is not bitwise stable (≤ 0.12 ε in λ, ≤ 2.2e-16 in d_esc) | checked | yes (4b159d0) | batched.json | `§D  agreement`; `§D  row order` |
| A12 | The square root costs 1.0–1.6%, so the energy form is not worth shipping | checked | yes (4b159d0) | batched.json | `§D  sqrt saving` |
| A13 | δ-sweep of the collinear fallback (§C) | checked | n/a (recomputed) | tools/generate_polar_delta_table.py | `recompute:§C` |
| A14 | Under the isometric scale the screen distance to the anchor is S_y‖r‖₂ when λ is unsaturated and strictly less when it saturates; pairwise screen distances never exceed ‖r_i − r_j‖₂ ≤ ‖v_i − v_j‖₂, saturated points included; and d_esc is always the distance from r to the segment [−v_dipole, +v_dipole] | checked | n/a (derivation) | tests/test_polar_projector_properties.py | `pytest` |

## Registered question

| ID | Claim | Status | Pre-registered | Source | CI checks |
|---|---|---|---|---|---|
| C1 | Exact stability is free: a fixed random projection, a once-fitted PCA and the operator with a fixed anchor are all still at 7 of 7 steps | checked | operator yes (1c363bb); linear arms no (c560801) | bench/drift.py → drift.json | `§3.2 random_fixed still`; `§3.2 pca_fit_once still`; `§3.2 polar_fixed still`; `§3.2 isometric polar_fixed still`; `§3.2 still range` |
| C2 | The fidelity instruments are not vacuous: the random projection lands at chance on both (trustworthiness 0.5535, lift 1.09×) | checked | no (c560801) | drift.json; recall.json | `§3.2 random_fixed trustworthiness`; `§3.3 random_fixed` |
| C3 | Seed-pinned refits relocate points at every step: t-SNE 1.03–1.24, UMAP 0.31–1.25 (median 1.16 aligned, 5.81 unaligned) | checked | yes (1c363bb) | drift.json | `§3.2 range`; `§3.2 umap_refit`; `§3.2 tsne_refit`; `§3.2 alignment` |
| C4 | Running the three global baselines over the seven growth steps costs 15.7–25.0 s, against 0.051 s for the operator (307–488×) | checked | yes (1c363bb); timings from the c560801 rerun | drift.json | `§1  refit` |
| C5 | The moving anchor drifts 0.13–0.61 per step at unit scale, worst step 0.8144 when λ is in length units; the latter includes the declared aspect-ratio effect | checked | unit yes (1c363bb); isometric yes (498d0ab) | drift.json; bench/scale.py → scale.json | `§3.2 range polar_moving`; `§3.2 isometric polar_moving` |
| C6 | Against the once-fitted PCA the fixed-anchor operator is below on trustworthiness (0.6639 unit, 0.6666 isometric, against 0.6811) and above on lift (1.57× / 1.59× against 1.47×; worst step 1.17× against 1.01×) at both scales | checked | unit: operator yes, PCA arm no, E5 no; isometric yes (498d0ab) | drift.json; recall.json; scale.json | `§3.2 polar_fixed trustworthiness`; `§3.2 pca_fit_once trustworthiness`; `§3.3 polar_fixed`; `§3.3 pca_fit_once`; `§3.2 isometric`; `§3.3 isometric` |
| C7 | Pole selection trades trustworthiness against lift across four leak-free rules, at both scales; the ten-axis sweep bounds how far either moves | checked | unit no (87d72cc); isometric yes (498d0ab) | bench/frame_sensitivity.py → frame_sensitivity.json; scale.json | `§3.4 farthest`; `§3.4 kmeans2`; `§3.4 pc1_extremes`; `§3.4 largest_two_parts`; `§3.4 axis-sweep`; `§3.4 isometric` |
| C8 | The declared scale changes none of the F3 orderings; trustworthiness moves at most 0.003 and median lift at most 0.02 | checked | yes (498d0ab) | scale.json | `§3.4 F3` |
| C9 | The unit scale in E8 reproduces the committed E1, E5 and E6 figures | checked | yes (498d0ab) | scale.json | `§3.2 E8 unit reproduces` |
| C10 | λ saturates for 11.39% of the corpus in the published frame, and 7.7–18.8% per step under the moving anchor | checked | yes (498d0ab, descriptive) | scale.json | `§2.1 saturation` |
| C11 | Re-centring on the query is worth 29×: local recall 0.019 → 0.543, the factor taken on the unrounded means | checked | no (d12e03f) | bench/reanchor.py → reanchor.json | `§3.5 polar_published`; `§3.5 polar_reanchored`; `§3.5 re-anchoring factor` |
| C12 | Better directions are not the lever: a locally refitted PCA (0.023) scores below a global one (0.056) | checked | no (d12e03f) | reanchor.json | `§3.5 pca_local`; `§3.5 pca_global` |
| C13 | A radial coordinate beats the operator: 0.981 against 0.543 at unit scale and against 0.925 with λ in length units | checked | unit no (d12e03f); isometric post hoc (07255f7) | reanchor.json; reanchor_ablation.json | `§3.5 radial_plain`; `§3.5 ablation isometric` |
| C14 | The visible effect of re-centring depends on the scale: recall 0.344–0.857 across S_x/S_y, the clamp has no effect, and ‖r‖ alone recovers 1.000 | checked | post hoc (07255f7) | reanchor_ablation.json | `§3.5 ablation` |
| C15 | A re-anchored frame costs 42.8 µs, against 5,156 µs for a local PCA (121×) and 69,178 µs for a global one (1,618×); per stimulus the operator costs 4.53 µs against 1.98 µs for the radial coordinate | checked | no (d12e03f) | reanchor.json | `§3.5 frame`; `§3.5 per-stimulus` |
| C16 | UMAP fitted once and extended by transform() is intermittent: still at 5 of 7 steps and relocating by 0.39 and 1.07 at the other two, so its mean step (0.21) describes none of them | checked | yes (1c363bb) | drift.json | `§3.2 fit-once`; `§3.2 umap_fit_once` |
| C17 | The refit baselines pull ahead on same-part lift as the corpus grows (2.41× and 2.47× at the final step) while the operator and fit-once UMAP stay within 1.40–1.62× after the first step; chance falls from 0.70 to 0.22 across the schedule | checked | no (52ab929) | recall.json | `§3.3 umap_refit`; `§3.3 tsne_refit`; `§3.3 umap_fit_once`; `§3.3 later-step`; `§3.3 chance` |
| C18 | Across the re-anchored frames of §3.5 the median share of saturated stimuli is 0.68% | checked | post hoc (07255f7) | reanchor_ablation.json | `§2.1 re-anchored saturation` |
| C19 | Some methods need the stored corpus for each view: the refitted UMAP and t-SNE refit on every point present at each growth step, and the local PCA of §3.5 scans the corpus for the query's nearest neighbours before every view | construction | n/a | bench/drift.py `arm_umap_refit`, `arm_tsne_refit`; bench/reanchor.py `true_neighbours` before `pca_project` | — |
| C20 | Some place a vector without reading the corpus: a fixed random projection, a once-fitted PCA after its fit, the operator's `evaluate()` against a fixed frame, and the radial coordinate. The re-anchored operator reads the corpus only through a codebook built once over all of it, so a growing corpus re-couples it at each rebuild | construction | n/a | bench/drift.py `arm_random_fixed`, `arm_pca_fit_once`; polar_projector/projector.py `evaluate`; bench/reanchor.py `build_codebook` and the radial arm | — |

## Post hoc

| ID | Claim | Status | Pre-registered | Source | CI checks |
|---|---|---|---|---|---|
| P1 | In the published frame the named poles sit at λ = +0.182 and −0.818, exactly the two-part prediction +91/500 and −409/500, because the initial window holds only two parts (409 + 91) | checked | post hoc (computed during review before bench/poles.py existed) | bench/poles.py → poles.json | `§2.1 poles` |

## Must not appear

| ID | Claim | Status | Pre-registered | Source | CI checks |
|---|---|---|---|---|---|
| R1 | λ is a bounded coordinate between two named poles | remove | — | contradicted by P1; currently in §1 (What this paper is not), §5 and §6 | — |
| R2 | (λ, d_esc) is consumed as a planar position by at least one system | remove | — | the system this operator came from renders (λ, ⟨v, ĉ₁⟩); currently in §2.1 and §3.2 | — |
| R3 | The O(N²) force-simulation column and the SQLite deployment figures | remove | — | reproduced by no code in this repository; removed from §3 in phase 4 | — |
| R4 | Determinism is the paper's contribution | remove | — | removed from §4 in bd4de9b | — |
| R5 | UMAP fitted once and extended by transform() does, or does not, need the stored corpus to place a new point | remove | — | not established by any code or measurement here; the revised question leaves it open | — |

## Exploration notebook

Figures computed ad hoc during review, with no committed script. None is admissible as a measurement.
Each needs a registered row and a check before it can appear anywhere in the manuscript.

- Bootstrap 95% CI [+0.097, +0.138] for the 1.17× against 1.01× gap at 500 chunks.
- Share of ‖v − c₁‖² removed along the anchor direction: 2.2% (published frame), 38.4% (re-anchored).
  For a unit anchor this is exactly (1 − cos θ)/2, which is algebra rather than measurement.
- Share of ‖r‖² on the contrast axis: 0.77% and 0.94%; no random-direction reference was measured.
- Spread ratios ρ/‖v_dipole‖ 4.08 / 2.09 and abs(a)/‖v_dipole‖ 0.36 / 0.21; re-anchored pole heights.

Out of scope for this paper: the render frames of the system the operator came from, option B
(encoding a weak contrast on screen), and any energy analysis.
