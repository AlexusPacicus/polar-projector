# References: specification, for the author's approval

Phase 0 (`method-paper/BRIEF.md:30-32`). Drafted on 2026-11-04 by an AI agent (Claude) in a cloud session, outside the
governed channel. It records decision 11 of `outline.md` and specifies how it is carried out. Nothing here is
implemented. The rule of decision 3 applies: the author approves this specification first, and the code is then written
to it, never the other way round.

## 1. The decision

The author's words, 2026-11-04:

> adopta las referencias, da igual que yo las haya visto para el punto 2. adoptamos las referencias para una tabla con
> el antes/después

A working translation by the agent: "adopt the references; for point 2 it does not matter that I have seen them. We
adopt the references for a table with the before and after."

**The agent's reading. The author has to confirm it.**

- **(a) Scope.** Every figure printed in `method-paper/paper.md` is written as a reference that code resolves. This
  settles the open question in `outline.md` ("decided on day 1").
- **(b) The table.** The paper carries a before/after table. *Before* is the case: bare figures checked by the verifier.
  *After* is this paper: figures written as references. Section 7 gives its layout.
- **If the author meant references only for that table,** the scope in (a) shrinks to that table's cells. Every other
  section still holds.

"Point 2" is the blind sample. It does not exclude the figures the author already saw in `matrix/summary.md`. The paper
already declares that the exploratory run was seen (`outline.md`, H1, *Status*).

## 2. Requirements

What the references have to achieve. Each one rules out an alternative, named in section 3.

- **R1. Located.** For every figure, the check knows which characters in `paper.md` are the figure and which key they
  claim to be. This is the opposite of the case's presence check (`tools/verify_paper_tables.py:599-627`), which finds a
  string anywhere.
- **R2. Exact.** The printed string equals the formatted code output, character for character, unit included.
- **R3. Visible.** A changed figure is a write to `paper.md`. It goes through the governed channel and leaves a
  receipt, and the author sees the new number in the diff. A figure must never change in the PDF without a change to
  `paper.md`.
- **R4. Readable.** `paper.md` reads correctly as it is, on GitHub and in a diff, with no build step.
- **R5. Tools read, print and fail. They never write a governed path.** Every write to `paper.md` and
  `method-paper/claims.md` stays a write by the agent or the author, so Actuarii's counts
  (`method-paper/BRIEF.md:73-87`) keep meaning what the brief says.
- **R6. Built by the existing toolchain.** The syntax goes through pandoc to LaTeX unchanged, as `tools/build_arxiv.py`
  does for the case.

## 3. Syntax

```
<!--ref:KEY-->STRING<!--/ref-->
```

- **KEY** is a dotted name: `[a-z][a-z0-9_]*(\.[a-z0-9_]+)+`, for example `case.registry.rows_checked`. Names describe
  what the figure is, so a reader of the source can see when a sentence quotes the wrong key (section 8, question 3).
- **STRING** is the figure exactly as printed, unit included: `29×`, `281`, `49–384 s`.
- **A span does not nest and does not cross a line break.** It cannot sit inside math, a code span, a heading or link
  text.
- **One span per figure.** A range is a single figure when its key's value is a list and its format has two fields
  (`{0}–{1} s`).
- **The escape** is `<!--noref:REASON-->STRING<!--/noref-->`. It is for a numeral that is not a figure and that no
  exclusion in section 6 covers. Every escape is counted and listed with its reason (section 7).

**Checked in this session.**

- pandoc 3.1.3 drops both comments when writing LaTeX. This holds in prose and in pipe-table cells, and the value stays
  in place.
- When writing GitHub Markdown, pandoc keeps the comments. GitHub does not display HTML comments.
- The case manuscript contains neither `<!--` nor `{{`, so the syntax collides with nothing the build already handles.

**Alternatives ruled out.**

- **`{{KEY}}` resolved at build time** (the form `outline.md` proposed). It fails R3 and R4. A figure would change
  without any write to `paper.md`, which puts it outside Actuarii's governance of that path and outside the author's
  review of the diff. The source would also show keys where numbers should be.
- **A pandoc span, `[29×]{ref=KEY}`.** It fails R4, because GitHub prints the braces.
- **A key after a bare value, `29×<!--KEY-->`.** The check would have to guess where the value starts, which fails R1 for
  ranges and arrows.

## 4. Where values come from

Code output is the root (`outline.md`, decision 10). There are three layers:

1. **Producers,** under `method-paper/producers/`. These are versioned scripts. Each one writes one JSON artifact to
   `method-paper/results/`, using the envelope the case already uses (`README.md`: `{experiment, config, host,
   thread_env, results}`). Two fields are added: the commit the producer ran from, and the commit it measured.
2. **The manifest,** `method-paper/figures.toml` (read with `tomllib`). It has one entry per key:
   - `claim`: the wording. This is prose, which the author approves.
   - `artifact` and `field`: where the value is.
   - `format`: a Python format string, unit included. **One key has one printed string.** The same quantity at another
     precision is another key, so the author approves each printed string in exactly one place.
3. **The registry,** `method-paper/claims.md`. It is generated from the manifest, the artifacts and `paper.md`, never
   written by hand (decision 10). It has one row per key: the claim, the printed string, the artifact and field, the
   producer, and the sections where it is printed. It lists sections, not lines, so that editing prose does not change
   the registry.

**Producer families.** Each is specified on its own in Phase 1, not here.

| Family | Source | Feeds |
|---|---|---|
| Case registry | `paper/claims.md` at a named commit, parsed by the verifier's own rule (`tools/verify_paper_tables.py:640-672`) | Case facts (§1.1) |
| Case verifier | `tools/verify_paper_tables.py` run at a named commit in a temporary worktree. Its summary lines are parsed with anchored patterns that fail when they do not match | Before column |
| Git history | Commits, dates, intervals | Case facts |
| Matrix | The definitive H1 run (decision 3) | Before column, text → code; Table 2 |
| Self | The check's own report on `paper.md` (section 5) | After column |
| Actuarii | The five pre-registered counts (`method-paper/BRIEF.md:73-87`) | §3 of the paper |

**Two stances, as in the case:**

- **Resolving does not re-derive.** The check reads artifacts and never runs a producer, in the same way the case
  verifier "compares reported figures against the stored artifacts; does NOT re-derive them"
  (`tools/verify_paper_tables.py:677`).
- **Freshness is checked separately.** CI re-runs the deterministic producers and requires an identical `results`
  block. This closes a gap the case had: an artifact older than its script.

## 5. The check

`method-paper/tools/refs.py` has two subcommands. `check` runs in CI. `registry` prints the generated registry to
stdout, and the agent writes it to `claims.md` through the channel (R5).

**`check` fails on any of the following.** Each failure names the edge of the triangle it closes.

| # | Fails when | Edge |
|---|---|---|
| C1 | A span is malformed: unclosed, nested, across a line break, or inside math, code or a heading | (syntax) |
| C2 | A key in `paper.md` has no manifest entry | text → registry |
| C3 | A manifest entry's artifact or field does not exist | registry → code |
| C4 | A printed string differs from `format(value)` | code → text, located |
| C5 | A manifest key is printed nowhere in `paper.md` | registry → text |
| C6 | `claims.md` differs from the generated registry | code → registry |
| C7 | A digit appears outside every span and every exclusion of section 6 | text → code |

**`check` reports, without failing:**

- the counts for the after column;
- every `noref` escape, with its reason;
- the keys printed more than once.

**The verifier's minimal change** (`method-paper/BRIEF.md:94-95`): `main()` runs the method paper's check and adds its
failures to the total. That is a few lines in `tools/verify_paper_tables.py`. All the logic stays in `refs.py`, so CI
keeps one entry point and the verifier is not rewritten.

**Tests.** Before the code is frozen, there is one test per rule, C1 to C7. Each test plants an error on a copy of the
files and requires the check to fail for that rule's reason. This is the same discipline as `matrix/test_matrix.py`.

## 6. Numerals that are not figures

These exclusions are deterministic. Anything they do not cover needs a span or an escape.

- headings;
- code spans and fenced code: paths, `path:line`, commit hashes, keys;
- link targets;
- cross-references: `§2.1`, `Table 1`, `Figure 2`, `Appendix B`, `decision 3`;
- citation years: `(Author, 2018)` and `Author et al. (2018)`;
- the References section;
- markers of ordered lists.

**A known gap:** spelled-out numbers ("five pages", "seven statuses") are not seen. The style rule is to write every
figure in digits so that it is governed. The paper states this gap as a limit.

## 7. The before/after table

The paper's Table 1: the triangle's edges, as the case closed them and as this paper closes them. Every cell is a
reference, so the table governs itself in the same way it describes. This section gives only the layout and the
quantities. The values come from the producers, and none is printed here.

| Edge | Before: the case (bare figures, verifier) | After: this paper (references) |
|---|---|---|
| Registry → code | Rows whose named checks exist, out of all rows; rows no check reads (`construction`, `remove`) | Manifest entries that resolve to an artifact field, out of all entries *(enforced, C3)* |
| Code → registry | Verifier checks that no row names; whether the registry is written by hand | Whether the registry equals the generated one *(enforced, C6)* |
| Code → text | Figures that agree with their artifact; of those, located only by presence, single-character, and printed in more than one place | Occurrences located by their key, out of all occurrences *(enforced, C4)* |
| Text → code | Printed result figures with a checked root (H1, definitive run), out of all; tables recomputed cell by cell | Numerals outside spans and exclusions *(enforced, C7)*; `noref` escapes, with reasons *(measured)* |
| Text → registry | Printed result figures whose check some row names (matrix, registry column) | Keys without a manifest entry *(enforced, C2)* |
| Registry → text | `remove` rows checked for absence | Manifest keys printed nowhere *(enforced, C5)* |
| The residue | What a sentence says about a figure: not checked | Not checked. In addition, a sentence that quotes the right number under the wrong key (section 8) |

**Producers.**

- The before column comes from the case-registry, case-verifier and matrix producers at the release commit
  (`f59430a`).
- The after column comes from the self producer, run on the final `paper.md`.
- The table's own cells are references, so the after column counts itself. This is a fixed point: a count of spans
  does not depend on the values printed in them. The paper says so.

**Relation to Table 2.** Table 2 stays as `outline.md` lays it out: H1 on the case, as the verifier saw it and as the
matrix sees it. Table 1 compares mechanisms; Table 2 gives the case's content. Two tables in total, the most the brief
allows (`method-paper/BRIEF.md:9`).

## 8. Instrument audit, before any value

These are the three fixed questions of step 2(a) of `docs/METHODOLOGY.md`, applied to the before/after table before it
is run.

1. **Do both columns measure the same thing, in the same units?**
   - *No.* They describe two documents of different sizes. One was written without the rule, the other under it. The
     case's figures are benchmark measurements; this paper's are counts over a repository.
   - *Consequence:* the table compares mechanisms edge by edge. Each column reports fractions of its own document, and
     no cell compares raw counts across columns.
2. **Is a truth used to judge also an input to what is judged?**
   - *Yes, in the after column.* The check that enforces each edge is also the one that reports it, so "none untied" is
     a guarantee of the build, not a finding.
   - *Consequence:* each after cell is marked *enforced* or *measured*. Only the measured cells are observations: the
     `noref` escapes and the keys printed more than once.
3. **Are baseline and treatment really comparable?**
   - *Partly.* References were adopted after the case's lessons, for a short paper whose figures are easy to tie to
     code. The after column does not show that references would scale to the case, whose numerals the exploratory
     matrix counted at 1,344 occurrences (`matrix/summary.md`).
   - *The residue moves rather than shrinks.* A reference proves that the string comes from its key. It does not prove
     that the sentence describes that key. Descriptive key names and the claim wording in the generated registry let
     the author catch this in review; no check catches it.

## 9. Governed paths to add when the brief is updated (day 1)

The brief currently governs four paths (`method-paper/BRIEF.md:66-71`). This specification adds:

- `method-paper/figures.toml`. The manifest holds author-approved content: the wording and the printed formats.
- `method-paper/tools/refs.py`.
- *For the author to decide:* `method-paper/producers/` and `method-paper/results/` (see section 10).

## 10. Open decisions for the author

1. **Scope** (section 1): every figure, the agent's reading, or only the before/after table.
2. **Are producers and artifacts governed paths?** *Recommendation:* govern the producers, not the artifacts. An
   artifact is the output of a governed script, and CI's freshness step catches one edited by hand.
3. **Mechanical writes in the measurement.** With references, every change of a figure and every regeneration of
   `claims.md` is a governed write. The brief has to say whether these are counted apart from writing. The
   measurement is pre-registered (`method-paper/BRIEF.md:73-87`), so only the author can decide this, on day 1.
4. **Actuarii counts in CI.** Whether the Actuarii producer can run in CI or only locally depends on where the receipts
   live.
5. **Pre-registration labels as a manifest field,** checked against the order of commits. This would mechanize what the
   case left as prose (`case-data.md` §9, item 1). *Recommendation:* leave it out of the five days and list it as
   future work.

## 11. What this does not do

- It does not touch the case: `paper/polar-projector-paper.md` and `paper/claims.md` stay as they are
  (`method-paper/BRIEF.md:93`).
- It does not govern what a sentence says (the residue), and it does not govern spelled-out numbers.
- It does not establish that a producer measures what its claim says. That is H2.

## 12. Order of work after approval (Phase 1)

1. The author approves this specification and decides the open points of section 10.
2. A manifest skeleton for the numbers listed in `outline.md` ("Numbers the paper would print").
3. The case-registry, case-verifier and git-history producers.
4. `refs.py check` and `refs.py registry`, with one test per rule.
5. The hook in the verifier. Freeze the code.
6. Writing. The self producer runs on the final `paper.md`.
