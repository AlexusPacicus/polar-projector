# Outline: a five-page paper on how the Polar Projector paper kept its numbers tied to evidence

Phase 0 preparation (`method-paper/BRIEF.md:50`). Built with the author in the session of 2026-11-03, section by
section, and revised the same day for the triangle (decisions 9 and 10). It replaces the version of 2026-11-02, which
the agent wrote alone and which carried decisions the author had not taken. Revised on 2026-11-04 for the author's
decisions 11 to 14: references are adopted, Table 1 becomes the before/after, and the measurement is split into
authoring and mechanical writes. Written by an AI agent (Claude) in a cloud session, outside the governed channel by
design (`method-paper/BRIEF.md:30-32`).

The data comes from `case-data.md` and from `matrix/`, which is exploratory (see decision 3); the bibliography
candidates are in `related-work.md`; how references work is in `references-spec.md`.

## Constraints taken from the brief

- **Length:** at most five pages, about 2,500 words, one or two tables (`method-paper/BRIEF.md:9`).
- **Subject:** the claims registry, the pre-registration labels, the refutation criteria and the verifier that runs
  in CI, with the Polar Projector paper as the case. The case is not modified (`method-paper/BRIEF.md:9-11`, `:93`).
- **Who writes what:**
  - The agent drafts the tables and the description of the method (`method-paper/BRIEF.md:56-58`).
  - The author writes the introduction, the contribution, the limits and the conclusion, reviews the agent's drafts
    and approves every number (`method-paper/BRIEF.md:60-61`).
  - The paper states who did what (`method-paper/BRIEF.md:64`).
- **This paper's registry:** the agent keeps `method-paper/claims.md`, one row per number in the paper
  (`method-paper/BRIEF.md:25`, `:56`). The verifier changes only as far as needed to check this paper against it
  (`method-paper/BRIEF.md:94-95`).
- **Secondary goal:** report what Actuarii recorded while this paper was written, as an observation and not a test
  (`method-paper/BRIEF.md:13-14`, `:73-87`).
- **Honesty:** Actuarii did not govern the original paper (`method-paper/BRIEF.md:96`), and Phase 0 is declared as
  agent work outside the governed channel (`method-paper/BRIEF.md:32`).

## Decisions taken on 2026-11-03

1. **Scope: the brief plus the matrix.** H1 is the core. H2 is developed only if there is time; that is decided on
   day 3, and if it does not make it, it goes to Limits.
2. **Out of scope:**
   - *Reproducing the laboratory,* that is, regenerating the figures on another machine. It is a different
     objective; reformulating to it mid-course is what the author's method rules out (`docs/METHODOLOGY.md:24-27`).
     It goes to future work.
   - *Porting the method to other projects.* That is modularisation and does not belong to this objective.
3. **The matrix of 2026-11-02 is exploration only.** It stays in the repository, marked as exploratory, and the paper
   declares that it was run. In Phase 1 it is rebuilt from a specification:
   - the specification comes first and the author approves it; the code is then adapted to it, never the other way
     round;
   - the mechanical parts are kept after review and tests: reading the numbers, taking the checks from the verifier,
     finding each check's artifact by perturbation;
   - the judgment parts are decided again in the specification;
   - before seeing the matrix's output, the author classifies a blind sample of about 50 figures, and the two are
     compared;
   - there is one test per rule, and a declared list of derivations;
   - the code is frozen when the protocol is registered. Only the definitive run feeds the paper.
4. **The case is the thread.** The method is shown as it appears in the case, not set out in the abstract first.
5. **The case facts are a separate subsection.** The agent drafts the facts and the author reviews them.
6. **Authorship lives in the record, not in labels in the prose:**
   - the agent writes through the governed channel and leaves a receipt;
   - the author edits in separate commits carrying `Human-Record: author` (`method-paper/BRIEF.md:61-62`), never
     mixed with agent writes;
   - "Who did what" is computed from the history of `method-paper/paper.md`, section by section;
   - two limits are stated: a trailer is a declaration (`method-paper/BRIEF.md:87`), and "outside the channel" does
     not mean "written by the author" (`method-paper/BRIEF.md:86`);
   - optionally, a review marker in the source, removed before publication, as a working aid only.
7. **A derivation is a column, not a status.** Every figure has a *root* in code output, an *interaction* from the
   root to the printed figure (identity, ratio, order of magnitude, threshold), and a flag for whether recomputing
   from the root gives the printed figure. A figure tied directly has the identity interaction. A figure with no
   checked root is untied.
8. **If H2 is developed, it uses TDD in both directions,** on four or five instrument errors from the history:
   - *from claim to code:* a test written from what the claim says the instrument measures fails on the code before
     the fix and passes on the code after it;
   - *from code to claim:* mutants of the fixed code make the test fail.

   This catches properties someone stated, not errors in properties nobody stated (`docs/METHODOLOGY.md:43-44`).
9. **A triangle, not two directions.** Governance runs on the edges between three nodes: the registry, the text and
   code (see "The triangle"). This corrects the earlier drafts, which called the verifier's direction "registry →
   text". It is code → text: the presence check starts from the verifier's own checks, not from the registry's rows
   (`tools/verify_paper_tables.py:599-627`), and the registry check starts from the rows and looks for checks
   (`tools/verify_paper_tables.py:640-672`).
10. **Three levels.**
    - Code output is the root, and the only evidence.
    - This paper's registry is generated by code, never by hand. The case's registry is not modified
      (`method-paper/BRIEF.md:93`).
    - Text is governed only through deterministic syntax, or by reading it back with the matrix. This paper's figures
      are written as references that code resolves (decision 11).

## Decisions taken on 2026-11-04

11. **References are adopted, for a before/after table.** The author's words: "adopta las referencias […] adoptamos las
    referencias para una tabla con el antes/después".
    - *How:* `references-spec.md`. It is a specification for the author's approval, and nothing is implemented yet. In
      short, each figure is written in place with its key, `<!--ref:KEY-->29×<!--/ref-->`, and a check fails when the
      printed string differs from the code output. Values come from versioned producers through a manifest. No tool
      writes a governed path.
    - *The table:* Table 1 becomes the before/after. *Before* is the case, with bare figures checked by the verifier.
      *After* is this paper, with figures written as references. "Before" and "after" now mean only that, so Table 2's
      columns are renamed after the verifier and the matrix.
    - *Scope:* every figure in `paper.md`. Confirmed by the author: "todas" (`references-spec.md` §10, item 1).
12. **The blind sample does not exclude what the author has seen.** The author's words: "da igual que yo las haya
    visto". The figures listed in `matrix/summary.md` stay eligible for the sample of about 50. The paper already
    declares that the exploratory run was seen (H1, *Status*).
13. **The measurement is split into authoring and mechanical writes.** The author's words: "sí, separar". The five
    pre-registered counts stay as totals. The rule decides from the diff, never from a receipt's rationale, and is
    registered on day 1 (`references-spec.md` §10, item 3).
14. **Each cascade goes in two commits, authoring then mechanical.** The author's words: "sí, es en 2 commits".
    Actuarii stores per write only hashes, not content, so the rule is applied commit by commit
    (`references-spec.md` §10, item 3).
15. **Pre-registration labels come from the commits,** derived by code from each producer's history. The manifest may
    only weaken a label (`references-spec.md` §10, item 5). The author's idea.
16. **Old commits are recovered as snapshots** checked against `git show`. They cover the 9 rows and the growth from 112
    to 281 (`references-spec.md` §10, item 6). The author's idea.
17. **The cascade is not reported for now.** The author's call.
18. **The rationale is quarantined.** It is the author's working hypothesis that a receipt's rationale is a
    probabilistic answer with no established meaning. It is kept but read by nothing: no check, count, classification,
    label or figure, not even as a count of trailers. The paper states the quarantine as a hypothesis, not a result
    (`references-spec.md` §10, item 8).
19. **The matrix specification's decisions** (`matrix-spec.md` §10):
    - the release `f59430a` is measured;
    - the sample's allocation and seed, and the closed list of interactions, are approved;
    - the unclassified occurrences are not classified by hand: H1 is evaluated with and without them;
    - the author does not remember having read the v0 output in full, and the paper treats it as seen.

## The central sentence

The author's words, a working draft, revised with the author on 2026-11-03 (decision 9). The earlier ending, "en las
dos direcciones: del registro al texto y del texto al código", became "cerrar el triángulo entre registro, texto y
código":

> La gobernanza de un resultado no está en el texto sino en el código. El texto es una representación del hallazgo y
> se puede maquillar, lo escriba una persona o una IA. Lo que mantiene a cada cifra fiel a su hallazgo es un chequeo
> ejecutable, y tiene que cerrar el triángulo entre registro, texto y código.

A working translation by the agent; the author rewrites it:

> A result is governed by code, not by text. The text represents the finding and can be dressed up, whether a person
> or an AI writes it. What keeps each figure faithful to its finding is an executable check, and it has to close the
> triangle between registry, text and code.

Three qualifications the paper has to carry:

1. **In the case, part of the governance was text.** The registry is a Markdown file that no code writes (only the
   verifier reads it) and that code reads only in part:
   - nothing checks the `remove` rows (`tools/verify_paper_tables.py:656-657`);
   - the pre-registration labels, the reasons for corrections and the manuscript's sentence on pre-registration are
     prose.

   Where governance was text, nothing stopped the drift (§1.1).
2. **Code governs text only where the text has deterministic syntax.** A figure can be resolved from the registry or
   read back against code; what the sentence around it says cannot. That is the residue (see "The triangle").
3. **Code governs the representation, not the truth of the code.** A check keeps the text in line with the code's
   output, but cannot tell whether the code measures what it claims to. That is H2.

## The triangle

**Three nodes:**

- *Code:* the artifacts in `bench/results/`, written by versioned scripts, and the checks that read them. Its output
  is the root.
- *The registry:* one row per claim; `paper/claims.md` in the case, `method-paper/claims.md` in this paper.
- *The text:* the manuscript.

**Six directed edges.** "A → B" means that, starting from each item of A, a check finds it, correctly, in B. Table 1
says which ones the case closed:

- *closed:* registry → code, and code → text by presence, not location;
- *partly closed:* text → code, for the Appendix B and C tables only; registry → text, only through code and only
  for `checked` rows;
- *open:* code → registry, text → registry, and text → code for every other figure.

**How this paper closes them, by level (decision 10):**

1. **Code output is the root.** Nothing else counts as evidence: not the manuscript, not the registry, not commit
   messages, not the rationale of a receipt (decision 18).
2. **The registry comes from code.** A generator writes `method-paper/claims.md` from the checks, which closes code →
   registry by construction.
   - Code can fill a row's figure, its artifact and its check, and perhaps its pre-registration label, from the
     commit order.
   - The claim's wording is prose, so it falls under level 3.
   - Which columns code fills is set in the specification.
3. **Text is governed only through deterministic syntax.** There are two routes:
   - *References,* adopted (decision 11): each figure is written in place with its key,
     `<!--ref:KEY-->29×<!--/ref-->`, and a check compares the printed string with the code output. That makes code →
     text located, not just present, and makes text → registry and registry → text checkable. The form `{{KEY}}`,
     resolved at build time, was dropped: a figure would change without any write to `paper.md`
     (`references-spec.md` §3).
   - *Reading back:* the matrix finds every figure printed as a bare number and looks for its root (H1).

**The residue.** What a sentence says about a figure has no deterministic syntax, so no edge checks it. This covers
the wording of a refutation criterion, the reason for a correction and a sentence about provenance. It is the limit
of the thesis, and a candidate for the conclusion.

## Hypotheses

**H1 (core).** Every result figure printed in the manuscript has a root in code output, reached through a declared
interaction and confirmed by recomputation at the printed precision.

- *Refuter:* a result figure without a checked root.
- *Instrument:* the matrix, rebuilt from the specification in Phase 1.
- *Why it is open:* the verifier checks from code to text. It takes each check's figure and looks for it in the
  manuscript (`tools/verify_paper_tables.py:599-627`). It reads the text back only for the Appendix B and C tables
  (`tools/verify_paper_tables.py:165-201`). No check starts from the other printed figures.
- *Status:* the exploratory run of 2026-11-02 has already been seen (`matrix/summary.md`). With the instrument
  frozen, H1 is a confirmation and not a blind prediction, and the paper says so.

**H2 (conditional on day 3).** Consistency checks do not see instrument errors; tests written from the claim, in both
directions, see some of them.

- *Refuter:* an instrument error that a consistency check catches on the state before the fix.
- *Reported:* which of the historical instrument errors the claim-derived tests catch, and which they do not.

## Word budget

The budgets are planning targets, not repository facts. The full column sums to 2,500, the brief's target
(`method-paper/BRIEF.md:9`); the cut column sums to 1,500, the brief's fallback (`method-paper/BRIEF.md:91-92`).
Budgets count prose; tables and references fall outside them. §2 has no text of its own: 2.1 opens it with the
triangle and Table 1.

| § | Section | Writer | Words | Cut | Table |
|---|---|---|---:|---:|---|
| — | Abstract | Author | 150 | 100 | |
| 1 | Introduction | Author | 250 | 100 | |
| 1.1 | The case as it was | Agent drafts, author reviews | 300 | 200 | |
| 2.1 | The edges the case had: the verifier | Agent drafts, author reviews | 300 | 200 | 1 |
| 2.2 | The edges it lacked: the matrix (H1), the generated registry and references | Agent drafts, author approves every number | 550 | 450 | 2 |
| 2.3 | What code does not govern (H2) | Agent drafts, author reviews | 300 | 0 | |
| 3 | Pilot: this paper written under Actuarii | Agent counts, author interprets | 200 | 100 | |
| 4 | Limits | Author | 250 | 300 | |
| 5 | Conclusion | Author | 100 | 0 | |
| — | Who did what | Computed from the history | 100 | 50 | |
| | **Total** | | **2,500** | **1,500** | |

- **If H2 does not make it by day 3,** its 300 words go 100 to Limits, for the H2 paragraph, and 200 to §2.2.
- **The cut keeps the method, the case and the limits** (`method-paper/BRIEF.md:91-92`). Here that means §1.1, §2.1,
  §2.2 and §4. It also keeps the measurement and the authorship statement, because "done" requires them
  (`method-paper/BRIEF.md:64`, `:101-102`).

## Section by section

### Abstract (150; cut 100). Author.

The problem, the thesis, the case, the triangle and the edges the case lacked, the H1 result, and what code does not
govern.

### 1. Introduction (250; cut 100). Author.

- Text can be dressed up, by a person or by an AI; governance lives in code.
- The contribution, on a real case:
  - separate what code governed from what text governed;
  - close the edges of the triangle that the case left open;
  - mark what code does not govern: what the prose says (the residue), and whether the code measures what it claims
    (H2).
- What this is not: a tool, or an evaluation across papers.

### 1.1 The case as it was (300; cut 200). Agent drafts, author reviews.

- **The paper as released:** `v1.0-paper` at `f59430a` (`case-data.md` §4).
- **Its four components:**
  - the registry, with 42 rows: 31 checked, 4 construction, 7 remove (`paper/claims.md:68-124`;
    `tools/verify_paper_tables.py:670`);
  - the pre-registration labels (`paper/claims.md:52-56`);
  - the refutation criteria, F1, F2 and the Bound (`paper/claims.md:14-21`);
  - the verifier in CI (`.github/workflows/ci.yml:50-51`).
- **Which components code enforced** is Table 1, in §2.1.
- **Where text governed, it drifted:**
  - the manuscript's sentence on pre-registration appears to disagree with the registry
    (`paper/polar-projector-paper.md:902-908`; `case-data.md` §9, item 1; to be confirmed by the author);
  - the sources of R1 and R2 are stale (`paper/claims.md:121-122`);
  - the labels `n/a` and `—` are used but undefined (`paper/claims.md:52-56`);
  - a registered protocol changed its aggregation after its first run, and the labels do not record it (`1e9d217`;
    `case-data.md` §8).

### 2. Governance in code: the triangle

No text of its own; 2.1 opens it.

### 2.1 The edges the case had: the verifier (300; cut 200). Agent drafts, author reviews. Table 1.

- **The triangle:** three nodes, six edges, and Table 1, the before/after (decision 11). This section reads its
  *before* column; 2.2 reads the *after* column.
- **What the verifier checks** (`README.md:114-122`), edge by edge:
  - *registry → code:* every `checked` row names a check that exists (`tools/verify_paper_tables.py:640-672`);
  - *code → text:* each check's figure agrees with its artifact at the printed precision
    (`tools/verify_paper_tables.py:255`, `:675-686`) and is printed somewhere in the manuscript (`:599-627`);
  - *text → code, for two tables:* it recomputes the Appendix B and C tables and compares them cell by cell
    (`:165-201`).
- **How its coverage grew:** from 112 to 281 figures, re-run at each step (`case-data.md` §7).
- **Its limits:**
  - presence, not location (`paper/claims.md:61-62`);
  - no check starts from the text or from the code to look for a row (Table 1).
- **The evidence:** only facts that come from code, namely the verifier's runs and the diffs. Commit messages do not
  count.

### 2.2 The edges it lacked: the matrix, H1, the generated registry and references (550; cut 450). Agent drafts, author approves every number. Table 2.

- **Text → code: the matrix.**
  - *The specification:* logical categories, the evidence each requires, and the root, interaction and checked
    columns (decision 7).
  - *How the instrument was verified:* one test per rule; planted-error tests, including errors the verifier lets
    through; and agreement with the author's blind sample.
  - *The result,* in Table 2: the case's figures as the verifier sees them and as the matrix sees them.
  - *The example:* Appendix A's "vs. d = 16" column (`paper/polar-projector-paper.md:1095-1103`).
  - *The declaration:* an exploratory run preceded the protocol (decision 3).
- **Text → registry:** the matrix's registry column, which gives the rows that name each figure's checks.
- **Code → registry:** this paper's registry, generated by code. It is shown on this paper and not on the case,
  because the case's registry is not modified (`method-paper/BRIEF.md:93`).
- **Code → text, located, and text → registry: references** (decision 11; `references-spec.md`).
  - Table 1's *after* column comes from the check's own report on the final `paper.md`.
  - Most of its cells are enforced by the build rather than observed, and the table marks which. The observations are
    the escapes and the keys printed more than once (`references-spec.md` §8).

### 2.3 What code does not govern, H2 (300; cut 0). Conditional on day 3.

TDD in both directions on four or five historical instrument errors (decision 8): which ones the claim-derived tests
catch, and which they do not.

### 3. Pilot: this paper written under Actuarii (200; cut 100). Agent counts, author interprets.

- The five counts and their limits (`method-paper/BRIEF.md:75-87`).
- Phase 0 is described in prose and stays outside the counts: the preparation, the exploratory matrix, and this
  framing, agreed in conversation.
- Actuarii did not govern the original paper (`method-paper/BRIEF.md:96`).
- The thesis applies to the pilot itself: the rationale in each receipt is text written by the model, not the reason
  for the change (`method-paper/BRIEF.md:85-86`). It is quarantined (decision 18).

### 4. Limits (250; cut 300). Author.

Candidates for the author to choose from and word:

- one case;
- an instrument written by an LLM, checked by tests and by the blind sample;
- the exploratory run came first;
- a string matching a string is not the same figure;
- the residue: what a sentence says about a figure is governed by no edge, references included;
- a reference proves that the string comes from its key, not that the sentence describes that key; spelled-out
  numbers are not governed (`references-spec.md` §6, §8);
- Table 1's two columns describe different documents, so it compares mechanisms, not counts
  (`references-spec.md` §8);
- the trailers are declarations;
- H2, if it did not make it;
- tracing is not reproducing: reproducing the laboratory is future work.

### 5. Conclusion (100; cut 0). Author.

A candidate, for the author to take or leave: the residue. Code can govern every figure in the text, through the
registry and deterministic syntax, but not what the sentence around it says.

### Who did what (100; cut 50). Computed from the history (decision 6).

## Tables

**Table 1. The triangle's edges, before and after (decision 11).** *Before:* the case, its figures bare and checked by
the verifier. *After:* this paper, its figures written as references. "A → B" means that, starting from each item of A,
a check finds it, correctly, in B. This is a draft. Each row is checked against the code before it goes into the
paper. In the paper, every cell is a reference to a producer's output; `references-spec.md` §7 gives the quantities.
In the *after* column, "enforced" means that the build fails otherwise (rules C2 to C7 of `references-spec.md` §5).

| Edge | What it checks | Before: the case | After: this paper | Evidence in the case |
|---|---|---|---|---|
| Registry → code | Each row resolves to code | Yes, for `checked` rows: each names a check that exists | Each manifest entry resolves to an artifact field (enforced, C3) | `tools/verify_paper_tables.py:640-672` |
| Code → text | Each figure agrees with code output and is found in the text | Yes, by presence, not location | Located: each occurrence carries its key and must equal the code output (enforced, C4) | `tools/verify_paper_tables.py:255`, `:599-627`, `:675-686`; `paper/claims.md:61-62` |
| Text → code | Each printed result figure has a checked root | Only the Appendix B and C tables, located; the matrix (H1) measures the rest | Every numeral is a reference, an exclusion or a counted escape (enforced, C7) | `tools/verify_paper_tables.py:165-201` |
| Code → registry | Each check has a row, and the rows come from code | No: no code writes the registry; a check can lose its row and CI stays green; the pre-registration labels are not checked against the commit order | The registry is generated and compared byte for byte (enforced, C6) | `matrix/test_matrix.py:107-116` (exploratory); `paper/claims.md:52-56` |
| Text → registry | Each printed figure has a row | No: the checks start from the code or from the rows, never from the text | Each key has a manifest entry (enforced, C2) | `tools/verify_paper_tables.py:599-627`, `:640-672` |
| Registry → text | Each row's claim is in the text, and no `remove` row is | Only through code, for `checked` rows; `remove` and `construction` rows unchecked | Each key is printed (enforced, C5); a row's wording stays prose | `tools/verify_paper_tables.py:656-657` |
| None: the residue | What a sentence says about a figure | Not checked: the wording of the refutation criteria (their figures are checked through rows C11 to C13), the reasons for corrections, prose about provenance | Not checked; also a right number quoted under the wrong key | `paper/claims.md:14-21`, `:98-100`; `case-data.md` §5; `paper/polar-projector-paper.md:902-908` |

**Table 2. Result figures seen from each direction.** Only the layout; the values come from the definitive run.

| Result figures | Seen by the verifier (code → text) | Seen by the matrix (text → code) |
|---|---|---|
| Tied directly (identity interaction) | | |
| Tied by a checked derivation | Not seen | |
| Passing only because the string matches another figure | Pass | |
| Untied | Not seen | |
| **Total** | | |

## Numbers the paper would print

Candidates for `method-paper/claims.md`, which code will generate (decision 10); each needs the author's approval
(`method-paper/BRIEF.md:61`). The H1 figures do not appear here: they come from the definitive run. Under decision
11 each becomes a key in `method-paper/figures.toml`, with a producer that computes it (`references-spec.md` §4).

| Number | What it is | Source |
|---|---|---|
| 42 | Registry rows | `paper/claims.md:68-124`; `case-data.md` §1 |
| 31 / 4 / 7 | checked / construction / remove | `tools/verify_paper_tables.py:670` at `501c67f`; `case-data.md` §1 |
| 13 / 7 / 4 / 6 / 8 / 4 | Pre-registration label classes | `paper/claims.md:68-124`; rule in `case-data.md` §2 |
| 281 | Figures checked against artifacts | Verifier at `f59430a` and `501c67f`; `case-data.md` §7 |
| 261 / 20 | Figures located by presence / single-character figures | Same runs; `case-data.md` §7 |
| 112 → 281 | Growth of checked figures | Verifier at `34b44b3` and `65c3ebf`; `case-data.md` §7 |
| 9 | Checked rows whose figures the code review changed while the verifier passed | `97e9306` → `65c3ebf`; `case-data.md` §5.1, §7 |
| 49–384 s | Protocol-to-results gaps of the registered experiments | `21e8e45`→`c265abb`, `1c363bb`→`1e9d217`; `case-data.md` §8 |

## Plan from here

- **2026-11-04, still Phase 0:**
  - the matrix specification is drafted (`matrix-spec.md`), for the author's approval;
  - the blind sample of 50 figures is drawn by code with a fixed seed (`blind-sample/`; `matrix-spec.md` §8). It does
    not exclude the figures the author has seen (decision 12);
  - references: the specification is drafted (`references-spec.md`), for the author's approval.
- **Day 1, 2026-11-05:**
  - approve `references-spec.md` and decide its points still open (§10 there);
  - install Actuarii, and exclude the kit's code from ruff before the first push: CI would fail on 87 errors
    (`references-spec.md` §9);
  - the author updates the brief:
    - the goal: the brief plus the matrix, with H1 the core and H2 conditional;
    - the governed paths: `method-paper/figures.toml`, `method-paper/tools/`, `method-paper/producers/`,
      `method-paper/results/`, `method-paper/case-history/` and `method-paper/blind-sample/` (`references-spec.md`
      §9, `matrix-spec.md` §9). The definitive matrix lives in `producers/`; the v0 folder stays as exploration;
    - the measurement, with the split into authoring and mechanical writes (`references-spec.md` §10, item 3)
      registered before counting starts (`method-paper/BRIEF.md:36`, `:66-87`);
  - register the protocol, adapt the code to it, and freeze it.
- **Days 2 and 3:**
  - the producers and `refs.py`, with one test per rule, before any writing (`references-spec.md` §12);
  - the definitive H1 run;
  - generate `method-paper/claims.md` by code, and make the minimal verifier change
    (`method-paper/BRIEF.md:94-95`);
  - writing;
  - the H2 decision on day 3.
- **Day 4:** the cut rule if the paper is not converging (`method-paper/BRIEF.md:91-92`).
- **Day 5:** verify and publish (`method-paper/BRIEF.md:38`).

## Still open

1. The English wording of the central sentence (the author).
2. The matrix specification: drafted, and its decisions taken (decision 19).
3. Which registry columns code fills, and how the author reviews the claim's wording, which code cannot write:
   drafted (`references-spec.md` §4).
4. **References are adopted (decisions 11 and 13 to 17).** Nothing in `references-spec.md` §10 is open. Its rules are
   approved with the specification on day 1.
5. Whether to use the manuscript's sentence on pre-registration as the example of drift (confirm it first).
6. Related work for the "dressing up" of findings, the reporting literature on spin. It is not yet searched, and
   nothing is cited without verification.
7. The link check in `related-work.md`, which needs network access or a manual check.
