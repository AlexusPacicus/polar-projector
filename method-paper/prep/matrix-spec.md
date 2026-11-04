# Matrix: specification, for the author's approval

Phase 0 (`method-paper/BRIEF.md:30-32`). Drafted on 2026-11-04 by an AI agent (Claude) in a cloud session, outside the
governed channel. It is the specification that `outline.md` decision 3 asks for. The author approves it first, and the
Phase 1 code is then written to it.

- The exploratory v0 in `matrix/` stays as it is; the paper declares that it was run.
- Line numbers of the form `:N` refer to `matrix/build_matrix.py`.
- Counts marked *exploratory* were made in this session while drafting. They are planning facts, not results.

## 1. What the matrix answers

**H1** (`outline.md`, Hypotheses): every result figure printed in the manuscript has a root in code output, reached
through a declared interaction and confirmed by recomputation at the printed precision.

- **Refuter:** a result figure without a checked root.
- **Edges:** text → code on the case, plus the registry column for text → registry (`outline.md`, Table 1). This
  paper's own figures are governed by references (`references-spec.md`), so the matrix reads only the case.

**It measures the case as released: `f59430a` (`v1.0-paper`).** That is the version that was published.

- Between `f59430a` and `501c67f`, only the manuscript changed: `3ca439c` and `0b15002` (the editorial note,
  Algorithm 1, the byline). The operator, the artifacts and the verifier are identical; checked in this session with
  `git diff --stat`.
- The case is read through a snapshot, `method-paper/case-history/f59430a/` (`references-spec.md` §10, item 6).
  Because the operator is unchanged, the snapshot's recomputation of Appendices B and C is exact.
- The case-registry and case-verifier producers read the same snapshot (`references-spec.md` §4), so the whole case
  is read at one commit.

## 2. Kept from v0, and decided again

Decision 3 keeps the mechanical parts after review and tests, and decides the judgment parts again.

| Part | v0 | v1 | Kind |
|---|---|---|---|
| Reader: numerals, line, context, region, table cell, math, code and link spans | `scan_manuscript`, `TOKEN` (:291-480) | Kept. Adds each token's offsets and its rank on its line | Mechanical |
| The verifier's checks | `_artifact_checks()` run, not read (:53) | Kept. Imported through `sys.path`, not `importlib` (§3) | Mechanical |
| Each check's artifact | Perturbation (:105) | Kept | Mechanical |
| Appendix B and C cells | Cell, verifier constant, recomputation (:648) | Kept | Mechanical |
| Artifact writers and script dependencies | :147, :156 | Kept for H2. Not used for H1 | Mechanical |
| Registry rows of each check | The verifier's prefix rule (:280) | Kept | Mechanical |
| Categories | Context rules and evidence rules (:501) | Context only (§4) | Judgment |
| Matching an occurrence to a check | Same section; in tables, row or column; short strings doubtful (:613, :781) | Kept; statuses renamed (§5) | Judgment |
| Derivations | Not mapped | Roots and interactions, declared (§5) | Judgment |
| Output | `matrix.csv` and `summary.md`, written by the script | One artifact, printed to stdout (§3) | — |

## 3. Under Actuarii

The v0 code cannot become the Phase 1 code as it stands. It imports `importlib` (:53) and `subprocess` (:865), and
`test_matrix.py` runs processes. Actuarii denies both primitives in a governed Python file (`references-spec.md` §4).

v1 is `method-paper/producers/matrix.py`:

- it imports the snapshot's verifier by putting the snapshot's `tools/` on `sys.path`;
- it takes the measured commit from the snapshot's path, not from git;
- perturbation stays in process: it swaps the verifier's JSON loader, which uses no primitive;
- it prints one artifact, the rows and the counts, to stdout, and the agent writes it to
  `method-paper/results/matrix.json`.

Its tests call it in process, on temporary copies, through `pytest`.

## 4. Categories

**Principle: context decides the category; evidence decides only the status.**

- **Why.** In v0, an occurrence could become a result or a parameter because a check, a config value or an artifact
  datum matched its string (:534, :542, :544, :552).
  - The truth used to judge was also an input to what was judged. That is question 2 of step 2(a) in
    `docs/METHODOLOGY.md`.
  - A wrong figure stops matching, so it can fall out of the population H1 counts. v0 patched one case of this
    (`decimal-en-texto`, :560), found by `test_altered_occurrence`. v1 removes evidence from every category rule.
- **What it costs.** *Exploratory:* v0's `categorize` was run with its evidence arguments off, on `f59430a`, outside
  the References section.
  - Results go from 479 to 451, math from 75 to 110, and unclassified from 27 to 44.
  - Of the 105 numbers the formula rule takes, 36 are decimals or in scientific notation. Those can be results
    (`λ = +0.182`) or mathematics (`1.49 × 10⁻⁸`).
- **Hence one new rule.** Inside math, a decimal or a number in scientific notation is unclassified; an integer stays
  math. That leaves about 80 unclassified occurrences, and the author decides each one before the run (§5).

| Category | v0 name | What it is | What its status needs |
|---|---|---|---|
| result | `resultado` | Produced by running code, measured or derived from what code produced | A root (§5) |
| parameter | `parametro` | A setting of an experiment: N, d, K, seeds, grids, sizes | Recorded in an artifact's `config` (strong), or a literal in code (weak) |
| math | `derivacion` | A mathematical fact: a bound, an identity, a constant of a proposition | A test (`pytest`); outside H1 |
| environment | `entorno` | Machine and versions | Recorded in an artifact's `host` |
| citation | `referencia` | Years and volumes, in the text or the References section | None; outside H1 |
| structure | `texto` | Numbering: sections, propositions, steps, list items, headings, the front matter | None |
| notation | `notacion` | Digits inside names and notation: `c_1`, ‖·‖₂, `float64`, `P1_GOD` | None |
| unclassified | `sin-clasificar` | No rule applies | The author decides, before the run |

"Math" replaces v0's `derivacion`, so that "derivation" means only the interaction column of decision 7.

**Rules.**

- v0's context rules are kept, in order, with one test each.
- Four evidence rules are removed: `coincide-con-chequeo`, `coincide-con-chequeo-un-caracter`, `coincide-con-config`
  and `coincide-con-datos`.
- One rule is added: a decimal or scientific number inside math is unclassified.

## 5. Roots, interactions and statuses

**Roots.** A result occurrence has a root when code output reaches it by one of two routes.

- **A check.** A verifier check whose printed string equals the occurrence. It counts if it belongs to the same
  section or, in a table, names the cell's row or column (:781). The cells of Appendices B and C are matched cell by
  cell, as the verifier already does.
- **A declaration** in `method-paper/producers/matrix_declarations.toml`. It gives the occurrence's key, its roots
  (artifact fields or check labels), its interaction and its printed format. The matrix recomputes the value and
  compares it at the printed precision.

The same file records the author's category for each unclassified occurrence.

**Interactions** form a closed list. A new kind is added to the list before the run, never after.

- identity;
- ratio, and difference;
- share: a/b printed as a percentage;
- range: the minimum and maximum over a declared set;
- order of magnitude: 10^k of a value;
- threshold: the first value of a declared sweep at which a declared condition on a declared field holds.

**Statuses.**

| Status | Means | Row of Table 2 (`outline.md`) |
|---|---|---|
| tied-located | An Appendix B or C cell, matched cell by cell | Tied directly |
| tied-check | Reached by a check | Tied directly |
| tied-check-1c | A single-character figure matched by a same-section check that shares words with its context (v0) | Tied directly, counted apart |
| tied-derivation | Reached by a declaration, and the recomputation matches | Tied by a checked derivation |
| string-elsewhere | Only a check of another section, row or column has the string | Passing only because the string matches another figure |
| check-fails | A check or declaration exists and disagrees | Untied |
| untied | No root | Untied |

**Two cautions.**

- **A value found in some artifact without a check** (v0's `datos-sin-prueba`) is a hint for writing a declaration,
  not a status. The occurrence stays untied until it is declared.
- **The declarations are written after v0 was seen.** That is why the interactions form a closed list and why the
  recomputation must match at the printed precision: a wrong root fails. Every declaration is listed in the artifact,
  Table 2 shows how many figures are tied only by one, and the H1 keys carry a weakened label (`references-spec.md`
  §10, item 5).

## 6. H1's verdict

- **H1 holds on the case** if no result occurrence is string-elsewhere, check-fails or untied.
- **Reported:** Table 2's counts, every occurrence that refutes H1, and the calibration of §8 next to them.
- **The verdict is not revised** after the blind sample is compared.

## 7. Validating the instrument

- **One test per rule:** each category rule, each matching rule and each interaction, with a positive and a negative
  case, taken from pinned lines of the manuscript or from synthetic lines.
- **Planted errors:**
  - v0's six (`matrix/README.md`, "Qué demuestran las pruebas negativas");
  - an integer result in prose, changed: it stays a result and becomes untied, which tests the principle of §4;
  - a declared root changed: check-fails;
  - a declaration with an interaction outside the list: refused;
  - a snapshot file changed: CI fails (`references-spec.md` §10, item 6).
- **Coverage:** every verifier check longer than one character matches at least one occurrence, as v0 already checks.
- **Frozen on day 1** with the protocol. There is one definitive run, and its artifact feeds the paper. A later change
  to the matrix marks its keys post hoc (`references-spec.md` §10, item 5).

## 8. The blind sample

**Purpose:** to calibrate the judgment parts, the category and the tie, against the author's independent reading.
Files: `blind-sample/`.

**Frame.** Every numeral the reader finds in the `f59430a` manuscript, outside the References section: 1,158 units
(`blind-sample/frame.csv`). The References section is left out by its place in the document, not by a judgment rule.

**Strata.** The v0 category on `f59430a`, used only to stratify; it never reaches the sheet. The allocation and the seed
(`20261104`) were fixed in `blind-sample/draw.py` before the draw.

| Stratum (v0) | Units in the frame | In the sample |
|---|---:|---:|
| `resultado` | 479 | 25 |
| `parametro` | 136 | 7 |
| `notacion` | 217 | 5 |
| `texto` | 185 | 4 |
| `derivacion` | 75 | 4 |
| `entorno` | 12 | 2 |
| `sin-clasificar` | 27 | 2 |
| `referencia` (in the text) | 27 | 1 |
| **Total** | **1,158** | **50** |

Half the sample goes to results, which is where H1 lives. The other half is spread so that a result the matrix excludes
can show up. The frame counts are in `frame.csv`. `draw.py` uses only the standard library and runs under Actuarii;
re-running it reproduces `sheet.csv` (`test_draw.py`).

**The sheet** (`blind-sample/sheet.csv`) shows, for each unit:

- its location: line, rank on the line, token, section, context, and table row and column;
- the line itself, with the figure marked ⟦like this⟧.

It shows no category, status, check or datum, and its units are shuffled.

**What the author fills in:**

- `category`, from the list of §4 without `unclassified`;
- `tied`, only for results: `yes`, `no` or `unsure`;
- `root`: where in code output the figure comes from, in free text;
- `note`.

**While filling it in,** the author reads code and artifacts only. The author does not open `matrix/matrix.csv`,
`matrix/summary.md`, `blind-sample/frame.csv`, the verifier's output, or `paper/claims.md`, which is a claim, not
evidence (`outline.md`, decision 10). Decision 12 is about what the author has already seen; this rule is about what the
author consults while filling in the sheet.

**Where and when.**

- The filled sheet goes to `method-paper/blind-sample/sheet.csv`. That is a governed path, so no write by the agent
  can change the author's labels without a receipt.
- The author commits it with `Human-Record: author`, before the definitive run.

**Joining.** Units are joined to the definitive matrix by line, rank and token, on the normalized line (`{,}` read as
`,`). A unit the definitive reader does not find is reported, not dropped.

**The analysis, fixed now.** A comparison producer runs it after the definitive run.

- Category agreement: per stratum, and overall weighted by the frame counts; with the confusion matrix.
- **False exclusions:** every unit the author calls a result and the matrix does not, listed one by one. Weighted by
  the frame, they give an estimate of how many results the matrix misses.
- Tie agreement, on the units both call results: a two-by-two table, with `unsure` apart.
- Agreement on the root, where both name one: reported, not scored.

There is no threshold, and no rule changes after the comparison. The paper reports the matrix's H1 count with this
calibration next to it.

## 9. Governed paths this adds

- `method-paper/producers/matrix.py` and `method-paper/producers/matrix_declarations.toml`, under `producers/`, already
  governed.
- `method-paper/case-history/f59430a/`, under `case-history/`, already governed.
- `method-paper/blind-sample/`, new.

## 10. Decisions for the author

1. **Which version to measure:** the release `f59430a` (recommended, §1) or `main`.
2. **The sample's allocation and seed** (§8). They are fixed in `draw.py`, and the sheet is already drawn.
3. **The closed list of interactions** (§5).
4. **The unclassified occurrences, about 80** (§4). *Recommendation:* the author decides them, rather than adding a
   rule for them before the run. A rule written after v0 was seen is the riskier path.
