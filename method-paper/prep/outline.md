# Outline: a five-page paper on how the Polar Projector paper kept its numbers tied to evidence

Phase 0 preparation (`method-paper/BRIEF.md:50`). Built with the author in the session of 2026-11-03, section by
section. It replaces the version of 2026-11-02, which the agent wrote alone and which carried decisions the author
had not taken. Written by an AI agent (Claude) in a cloud session, outside the governed channel by design
(`method-paper/BRIEF.md:30-32`).

The data comes from `case-data.md` and from `matrix/`, which is exploratory (see decision 3); the references are in
`related-work.md`.

## Constraints taken from the brief

- **Length:** at most five pages, about 2,500 words, one or two tables (`method-paper/BRIEF.md:9`).
- **Subject:** the claims registry, the pre-registration labels, the refutation criteria and the verifier that runs
  in CI, with the Polar Projector paper as the case. The case is not modified (`method-paper/BRIEF.md:9-11`, `:93`).
- **Who writes what:**
  - The agent drafts the tables and the description of the method (`method-paper/BRIEF.md:56-58`).
  - The author writes the introduction, the contribution, the limits and the conclusion, reviews the agent's drafts
    and approves every number (`method-paper/BRIEF.md:60-61`).
  - The paper states who did what (`method-paper/BRIEF.md:64`).
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

## The central sentence

The author's words, a working draft:

> La gobernanza de un resultado no está en el texto sino en el código. El texto es una representación del hallazgo y
> se puede maquillar, lo escriba una persona o una IA. Lo que mantiene a cada cifra fiel a su hallazgo es un chequeo
> ejecutable, y tiene que funcionar en las dos direcciones: del registro al texto y del texto al código.

A working translation by the agent; the author rewrites it:

> A result is governed by code, not by text. The text represents the finding and can be dressed up, whether a person
> or an AI writes it. What keeps each figure faithful to its finding is an executable check, and it has to run in both
> directions: from the registry to the text, and from the text to the code.

Two qualifications the paper has to carry:

1. **In the case, part of the governance was text.** The registry is a Markdown document the code reads only in part:
   - nothing checks the `remove` rows (`tools/verify_paper_tables.py:656-657`);
   - the pre-registration labels, the reasons for corrections and the manuscript's sentence on pre-registration are
     prose.

   Where governance was text, nothing stopped the drift (§1.1).
2. **Code governs the representation, not the truth of the code.** A check keeps the text in line with the code's
   output, but cannot tell whether the code measures what it claims to. That is H2.

## Hypotheses

**H1 (core).** Every result figure printed in the manuscript has a root in code output, reached through a declared
interaction and confirmed by recomputation at the printed precision.

- *Refuter:* a result figure without a checked root.
- *Instrument:* the matrix, rebuilt from the specification in Phase 1.
- *Why it is open:* the verifier checks one direction only, from registry to text
  (`tools/verify_paper_tables.py:599-627`). It reads the text back only for the Appendix B and C tables
  (`tools/verify_paper_tables.py:165-201`).
- *Status:* the exploratory run of 2026-11-02 has already been seen (`matrix/summary.md`). With the instrument
  frozen, H1 is a confirmation and not a blind prediction, and the paper says so.

**H2 (conditional on day 3).** Consistency checks do not see instrument errors; tests written from the claim, in both
directions, see some of them.

- *Refuter:* an instrument error that a consistency check catches on the state before the fix.
- *Reported:* which of the historical instrument errors the claim-derived tests catch, and which they do not.

## Word budget

The budgets are planning targets, not repository facts. The full column sums to 2,500, the brief's target
(`method-paper/BRIEF.md:9`); the cut column sums to 1,500, the brief's fallback (`method-paper/BRIEF.md:91-92`).
Budgets count prose; tables and references fall outside them.

| § | Section | Writer | Words | Cut | Table |
|---|---|---|---:|---:|---|
| — | Abstract | Author | 150 | 100 | |
| 1 | Introduction | Author | 250 | 100 | |
| 1.1 | The case as it was | Agent drafts, author reviews | 300 | 200 | 1 |
| 2.1 | From registry to text: the verifier | Agent drafts, author reviews | 300 | 200 | |
| 2.2 | From text to code: the matrix (H1) | Agent drafts, author approves every number | 550 | 450 | 2 |
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

The problem, the thesis, the case, the two directions, the H1 result and the limit.

### 1. Introduction (250; cut 100). Author.

- Text can be dressed up, by a person or by an AI; governance lives in code.
- The contribution, on a real case:
  - separate what code governed from what text governed;
  - add the direction that was missing;
  - mark what code does not govern.
- What this is not: a tool, or an evaluation across papers.

### 1.1 The case as it was (300; cut 200). Agent drafts, author reviews. Table 1.

- **The paper as released:** `v1.0-paper` at `f59430a` (`case-data.md` §4).
- **Its four components:**
  - the registry, with 42 rows: 31 checked, 4 construction, 7 remove (`paper/claims.md:68-124`;
    `tools/verify_paper_tables.py:670`);
  - the pre-registration labels (`paper/claims.md:52-56`);
  - the refutation criteria, F1, F2 and the Bound (`paper/claims.md:14-21`);
  - the verifier in CI (`.github/workflows/ci.yml:50-51`).
- **Table 1** says which components code enforced and which were text only.
- **Where text governed, it drifted:**
  - the manuscript's sentence on pre-registration appears to disagree with the registry
    (`paper/polar-projector-paper.md:902-908`; `case-data.md` §9, item 1; to be confirmed by the author);
  - the sources of R1 and R2 are stale (`paper/claims.md:121-122`);
  - the labels `n/a` and `—` are used but undefined (`paper/claims.md:52-56`);
  - a registered protocol changed its aggregation after its first run, and the labels do not record it (`1e9d217`;
    `case-data.md` §8).

### 2.1 From registry to text: the verifier (300; cut 200). Agent drafts, author reviews.

- **What it checks** (`README.md:114-122`):
  - it recomputes the Appendix B and C tables;
  - it compares each published figure with its artifact at the printed precision;
  - it checks that each checked figure is printed somewhere in the manuscript;
  - it checks that every `checked` row names a real check.
- **How its coverage grew:** from 112 to 281 figures, re-run at each step (`case-data.md` §7).
- **Its limit:** one direction only (`tools/verify_paper_tables.py:599-627`), and presence, not location
  (`paper/claims.md:61-62`).
- **The evidence:** only facts that come from code, namely the verifier's runs and the diffs. Commit messages do not
  count.

### 2.2 From text to code: the matrix, H1 (550; cut 450). Agent drafts, author approves every number. Table 2.

- **The specification:** logical categories, the evidence each requires, and the root, interaction and checked
  columns (decision 7).
- **How the instrument was verified:** one test per rule; planted-error tests, including errors the verifier lets
  through; and agreement with the author's blind sample.
- **The result,** in Table 2, before and after.
- **The example:** Appendix A's "vs. d = 16" column (`paper/polar-projector-paper.md:1095-1103`).
- **The declaration:** an exploratory run preceded the protocol (decision 3).

### 2.3 What code does not govern, H2 (300; cut 0). Conditional on day 3.

TDD in both directions on four or five historical instrument errors (decision 8): which ones the claim-derived tests
catch, and which they do not.

### 3. Pilot: this paper written under Actuarii (200; cut 100). Agent counts, author interprets.

- The five counts and their limits (`method-paper/BRIEF.md:75-87`).
- Phase 0 is described in prose and stays outside the counts: the preparation, the exploratory matrix, and this
  framing, agreed in conversation.
- Actuarii did not govern the original paper (`method-paper/BRIEF.md:96`).
- The thesis applies to the pilot itself: the rationale in each receipt is text written by the model, not the reason
  for the change (`method-paper/BRIEF.md:85-86`).

### 4. Limits (250; cut 300). Author.

Candidates for the author to choose from and word:

- one case;
- an instrument written by an LLM, checked by tests and by the blind sample;
- the exploratory run came first;
- a string matching a string is not the same figure;
- the trailers are declarations;
- H2, if it did not make it;
- tracing is not reproducing: reproducing the laboratory is future work.

### 5. Conclusion (100; cut 0). Author.

### Who did what (100; cut 50). Computed from the history (decision 6).

## Tables

**Table 1. The case's governance: what code enforced and what was text only.** This is a draft. Each row is checked
against the code before it goes into the paper.

| Component | Enforced by code? | Evidence |
|---|---|---|
| Each `checked` row names an existing check | Yes | `tools/verify_paper_tables.py:640-672` |
| Each checked figure agrees with its artifact | Yes | `tools/verify_paper_tables.py:255`, `:675-686` |
| Each checked figure is printed in the manuscript | Yes, by presence | `tools/verify_paper_tables.py:599-627` |
| The Appendix B and C tables | Yes, located | `tools/verify_paper_tables.py:165-201` |
| Each printed figure has a row | No | Not checked, except the Appendix B and C tables |
| `remove` and `construction` rows | No | `tools/verify_paper_tables.py:656-657` |
| Pre-registration labels | No: the commit order is in git, but nothing checks the label against it | `paper/claims.md:52-56` |
| Refutation criteria | Their figures yes, through rows C11 to C13; their wording no | `paper/claims.md:14-21`, `:98-100` |
| Reasons for corrections | No: commit messages | `case-data.md` §5 |
| Prose about provenance | No | `paper/polar-projector-paper.md:902-908` |

**Table 2. Result figures seen from each direction.** Only the layout; the values come from the definitive run.

| Result figures | Before: the verifier (registry → text) | After: the matrix (text → code) |
|---|---|---|
| Tied directly (identity interaction) | | |
| Tied by a checked derivation | Not seen | |
| Passing only because the string matches another figure | Pass | |
| Untied | Not seen | |
| **Total** | | |

## Numbers the paper would print

Candidates for `method-paper/claims.md`; each needs the author's approval (`method-paper/BRIEF.md:61`). The H1
figures do not appear here: they come from the definitive run.

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

- **2026-11-04, still Phase 0:** draft the matrix specification together; prepare the blind sample for the author.
- **Day 1, 2026-11-05:**
  - the author updates the brief: the goal (the brief plus the matrix; H1 the core, H2 conditional), the governed
    paths (the matrix folder) and the measurement (`method-paper/BRIEF.md:36`, `:66-71`);
  - register the protocol, adapt the code to it, and freeze it.
- **Days 2 and 3:** the definitive H1 run and writing; the H2 decision on day 3.
- **Day 4:** the cut rule if the paper is not converging (`method-paper/BRIEF.md:91-92`).
- **Day 5:** verify and publish (`method-paper/BRIEF.md:38`).

## Still open

1. The English wording of the central sentence (the author).
2. The matrix specification (2026-11-04).
3. Whether to use the manuscript's sentence on pre-registration as the example of drift (confirm it first).
4. Related work for the "dressing up" of findings, the reporting literature on spin. It is not yet searched, and
   nothing is cited without verification.
5. The link check in `related-work.md`, which needs network access or a manual check.
