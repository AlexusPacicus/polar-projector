# References: specification, for the author's approval

Phase 0 (`method-paper/BRIEF.md:30-32`). Drafted on 2026-11-04 by an AI agent (Claude) in a cloud session, outside the
governed channel. It records decision 11 of `outline.md` and specifies how it is carried out. Nothing here is
implemented. The rule of decision 3 applies: the author approves this specification first, and the code is then written
to it, never the other way round.

Revised twice the same day:

- after the author's review, artifacts are governed (R7; section 10, item 2), and section 10, item 3 specifies how the
  measurement handles mechanical writes;
- after the author's answers on the open points and a reading of Actuarii at `73eaf2b`, the decisions are recorded in
  section 10. Section 4 adds what Actuarii imposes on producers.

## 1. The decision

The author's words, 2026-11-04:

> adopta las referencias, da igual que yo las haya visto para el punto 2. adoptamos las referencias para una tabla con
> el antes/después

A working translation by the agent: "adopt the references; for point 2 it does not matter that I have seen them. We
adopt the references for a table with the before and after."

**The agent's reading, confirmed by the author on 2026-11-04 ("todas"):**

- **(a) Scope.** Every figure printed in `method-paper/paper.md` is written as a reference that code resolves. This
  settles the open question in `outline.md` ("decided on day 1").
- **(b) The table.** The paper carries a before/after table. *Before* is the case: bare figures checked by the verifier.
  *After* is this paper: figures written as references. Section 7 gives its layout.

"Point 2" is the blind sample. It does not exclude the figures the author already saw in `matrix/summary.md`. The paper
already declares that the exploratory run was seen (`outline.md`, H1, *Status*).

## 2. Requirements

What the references have to achieve. R1 to R6 each rule out an alternative named in section 3; R7 rules out the first
draft's ungoverned artifacts (section 10, item 2).

- **R1. Located.** For every figure, the check knows which characters in `paper.md` are the figure and which key they
  claim to be. This is the opposite of the case's presence check (`tools/verify_paper_tables.py:599-627`), which finds a
  string anywhere.
- **R2. Exact.** The printed string equals the formatted code output, character for character, unit included.
- **R3. Visible.** A changed figure is a write to `paper.md`. It goes through the governed channel and leaves a
  receipt, and the author sees the new number in the diff. A figure must never change in the PDF without a change to
  `paper.md`.
- **R4. Readable.** `paper.md` reads correctly as it is, on GitHub and in a diff, with no build step.
- **R5. Tools read, print and fail. They never write a governed path.**
  - Every write to `paper.md`, `method-paper/claims.md` and the artifacts in `method-paper/results/` stays a write by
    the agent or the author. Actuarii's counts (`method-paper/BRIEF.md:73-87`) therefore keep meaning what the brief
    says.
  - Producers and `refs.py registry` print to stdout, and the agent writes the file through the channel.
  - Actuarii enforces this for `Bash`: the operating system's sandbox denies it any write to a governed path
    (Actuarii at `73eaf2b`, `README.md:82`).
- **R6. Built by the existing toolchain.** The syntax goes through pandoc to LaTeX unchanged, as `tools/build_arxiv.py`
  does for the case.
- **R7. Traced at the root.** A change to an artifact is a governed write with a receipt, like a change to the text.
  - The artifact is the root and the only evidence (decision 10), so its changes need the same trail as the text's.
  - Otherwise the receipt lands on the consequence and not the cause. The artifact changes without a receipt, C4
    fails, and the only receipt is the agent's later write to `paper.md`, which records that a figure followed an
    artifact. Why the artifact changed stays outside the channel.

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
- **A key after a bare value, `29×<!--KEY-->`.** The check would have to guess where the value starts, which fails R1
  for ranges and arrows.

## 4. Where values come from

Code output is the root (`outline.md`, decision 10). There are three layers:

1. **Producers,** under `method-paper/producers/`. These are versioned scripts.
   - Each one prints one JSON artifact to stdout, and the agent writes it to `method-paper/results/` through the
     channel (R5, R7).
   - The artifact uses the envelope the case already uses (`README.md`: `{experiment, config, host, thread_env,
     results}`), with two added fields: the commit the producer ran from, and the commit it measured.
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
| Case registry | `paper/claims.md` in the working tree, parsed by the verifier's own rule (`tools/verify_paper_tables.py:640-672`) | Case facts (§1.1) |
| Case verifier | `tools/verify_paper_tables.py`, imported and called on the working tree. The brief keeps the case unmodified (`method-paper/BRIEF.md:93`), so the working tree is the case; the artifact records the commit. `case-data.md` §7 found the same counts at `f59430a` and `501c67f` | Before column |
| Git history | Commits, dates, intervals, read from `git log` on stdin | Case facts |
| Matrix | The definitive H1 run (decision 3) | Before column, text → code; Table 2 |
| Self | The check's own report on `paper.md` (section 5) | After column |
| Actuarii | The five pre-registered counts (`method-paper/BRIEF.md:73-87`), split as section 10, item 3 decides | §3 of the paper |

**What Actuarii imposes on producers** (Actuarii at `73eaf2b`):

- **Python runs only scripts committed in `HEAD`,** from the kit's directory and the `python_script_dirs` of
  `.actuarii.json` (`README.md:83`; `tools/hooks/deny_python_escapes.py:1-3`).
  - The configuration lists `method-paper/producers` and `method-paper/tools`.
  - A producer runs only once it is committed, so changing a producer and regenerating its artifact take two commits
    (section 10, item 3).
- **A governed Python file cannot introduce a process, network or loader primitive:** `subprocess`, `importlib` and
  `os.system`, among others (`tools/boundary_validator/primitives.py:22`). No producer runs git or any other process.
  - Git data reaches a producer on stdin, from a read-only command of the kit's list. `git log` and `git show` are
    in it (`.claude/settings.json:14-15`).
  - Each producer names its exact command in its docstring and rejects input without the expected header. CI writes
    the same command in the workflow.
- **No producer can run code from an older commit.** That needs a checkout and a process. Section 10, item 6 deals
  with the figures this affects.

**Two stances, as in the case:**

- **Resolving does not re-derive.** The check reads artifacts and never runs a producer, in the same way the case
  verifier "compares reported figures against the stored artifacts; does NOT re-derive them"
  (`tools/verify_paper_tables.py:677`).
- **Freshness is checked separately, and it covers the value only.** CI re-runs the deterministic producers and
  requires an identical `results` block. This closes a gap the case had: an artifact older than its script.
  - Freshness shows that an artifact equals what its producer produces now. It does not show who changed the artifact,
    when, or through which channel. Only governance records that (R7).
  - A producer that cannot run in CI has no freshness check, so governance is its only trail. The Actuarii counts are
    such a case if the receipts live only on the author's machine (section 10, item 4).

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
keeps one entry point and the verifier is not rewritten. The verifier imports `refs.py` after adding
`method-paper/tools` to `sys.path`. `importlib` is a primitive, so the gate would deny it in a governed file.

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

The brief currently governs four paths (`method-paper/BRIEF.md:66-71`). This specification proposes adding:

- `method-paper/figures.toml`. The manifest holds author-approved content: the wording and the printed formats.
- `method-paper/tools/`: `refs.py` and the classifier of section 10, item 3.
- `method-paper/producers/`.
- `method-paper/results/`. The artifacts are the root (R7). Counts 3 and 5 of the measurement only see changes to
  governed paths (`method-paper/BRIEF.md:79`, `:81`), so an ungoverned artifact would not even show up as an escape.

**In `.actuarii.json`.** The paths above go in `governed_paths`. `method-paper/producers` and `method-paper/tools` go in
`python_script_dirs`.

**What the installer brings with it** (Actuarii at `73eaf2b`, `INSTALL.md:3-5`, `:66-70`):

- It copies the kit into this repository's `tools/`, next to the verifier, and always governs `tools/**`. That already
  covers `tools/verify_paper_tables.py`. No file name collides; this was checked in this session.
- **The kit breaks CI as it stands.** CI runs `ruff check` over `tools/` (`.github/workflows/ci.yml`). With this
  repository's configuration and ruff 0.16.5, ruff finds 87 errors in the kit's code, checked in this session.
- *On day 1:* exclude the kit's directories from ruff in `pyproject.toml` before the first push.

## 10. Decisions

Recorded on 2026-11-04 from the author's answers, and checked against Actuarii at `73eaf2b`.

**Decided**

1. **Scope: every figure** (section 1). The author's answer: "todas".
2. **Producers and artifacts are both governed** (section 9).
   - *What the first draft said, and why it was dropped.* It recommended governing producers but not artifacts,
     relying on CI's freshness step. That traded change traceability for a cleaner count. Freshness covers the value
     only, and not for producers that cannot run in CI (R7, section 4).
   - *How a producer's output reaches `results/`:* the agent writes it with a file tool and a receipt. In Actuarii
     v0.1 this is the only way: `Bash` cannot write a governed path (R5).
3. **The measurement is split into authoring and mechanical writes.** The author's answer: "sí, separar".
   - *Why.* With references, one decision triggers a cascade of governed writes.
     - *A fix to the case-verifier producer that changes one figure printed in two places:* the producer changes
       (authoring); the artifact is regenerated, the two strings in `paper.md` follow because C4 requires them to,
       and `claims.md` is regenerated because C6 requires it (all mechanical).
     - *Adding a figure:* the manifest entry and the span are authoring. The regenerated registry, the self producer's
       artifact and the Table 1 cells that print it are mechanical.
     - Count 1, governed writes by the agent with a receipt (`method-paper/BRIEF.md:77`), was pre-registered before
       references existed. Without the split it would mix writing the paper with propagating figures.
   - *The rule.* It is registered on day 1, before Phase 1 counting starts. A split added after seeing the counts would
     be post hoc in the case's own vocabulary (`paper/claims.md:56`).
     - The five pre-registered counts stay unchanged, as totals.
     - A governed change is mechanical if and only if its result is exactly what code requires:
       - `claims.md` equal to the output of `refs.py registry`;
       - an artifact equal to its producer's output;
       - a diff to `paper.md` that only changes strings inside existing spans, each to the value C4 requires.

       Everything else is authoring. The rule is code, with one test per clause, frozen with the rest of the code.
     - Nothing is classified by a receipt's rationale. It is text written by the model (`method-paper/BRIEF.md:85-86`).
     - Mechanical writes are not excluded from the counts.
   - *Two commits per cascade.* The author's answer: "sí, es en 2 commits".
     - The authoring commit comes first, the mechanical commit after it.
     - Actuarii forces this for a changed producer anyway, because a producer runs only once committed (section 4).
   - *What Actuarii records, and why the commit is the unit.* Its `writes` table holds, for each write, the file, the
     tool, the SHA-256 before and after, and the receipts. The rationale is in `audit_log`. No content is stored
     (`tools/boundary_validator/hook_gate.py:57`, `tools/boundary_validator/validator.py:31`, `:90`).
     - Hashes are enough for the first two clauses: compare `after_sha256` with the hash of the generator's output.
     - The third clause needs content, which only commits keep.
     - So the rule is applied per commit, from git. A commit is mechanical if every governed change in it meets a
       clause, and a mixed commit counts as authoring. Each write in the database belongs to the commit that records
       it.
4. **The Actuarii counts run locally, not in CI.** The database sits under `.data/`, which git ignores (`README.md:69`).
   - The Actuarii producer therefore has no freshness check, and governance is its only trail (R7).
   - Counts 2, 3 and 5 can be recomputed from git by anyone, because they come from commit trailers. Counts 1 and 4
     come only from the local database.

**Still open**

5. **Pre-registration labels as a manifest field,** checked against the order of commits. This would mechanize what the
   case left as prose (`case-data.md` §9, item 1). *Recommendation:* leave it out of the five days and list it as
   future work.
6. **Figures that need an older commit.** Two of the candidates in `outline.md` need the verifier run at an older
   commit: the growth from 112 to 281 checked figures, and the 9 rows the code review changed while the verifier
   passed (`case-data.md` §5.1, §7). Under Actuarii v0.1 no governed producer can compute them (section 4).
   - *Option A:* a CI job checks out each named commit, runs the producer there, and checks the committed artifact on
     every push. The author writes the first artifact, with a `Human-Record` trailer.
   - *Option B:* leave them out.
   - *Recommendation:* A for the 9. It is direct evidence that a consistency check does not see instrument errors, which
     is H2's ground. B for the growth figure, which is case history.
7. **Report the cascade itself,** as mechanical writes per authoring write: an observation of what governance costs.
   It adds to a pre-registered measurement, so it is the author's call on day 1.

## 11. What this does not do

- It does not touch the case: `paper/polar-projector-paper.md` and `paper/claims.md` stay as they are
  (`method-paper/BRIEF.md:93`).
- It does not govern what a sentence says (the residue), and it does not govern spelled-out numbers.
- It does not establish that a producer measures what its claim says. That is H2.

## 12. Order of work after approval (Phase 1)

1. The author approves this specification and decides the points still open in section 10.
   - Install Actuarii.
   - Exclude the kit from ruff (section 9).
   - Set `governed_paths` and `python_script_dirs`.
2. A manifest skeleton for the numbers listed in `outline.md` ("Numbers the paper would print").
3. The case-registry, case-verifier and git-history producers. Each prints its artifact, and the agent writes it
   through the channel.
4. `refs.py check` and `refs.py registry`, with one test per rule.
5. The classifier of section 10, item 3, with one test per clause.
6. The hook in the verifier. Freeze the code.
7. Writing. The self producer runs on the final `paper.md`.
