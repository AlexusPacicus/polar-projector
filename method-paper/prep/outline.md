# Outline: a five-page paper on how the Polar Projector paper kept its numbers tied to evidence

Phase 0 preparation (`method-paper/BRIEF.md:50`). A proposal for the author to cut, reorder or reject: the author
decides what goes in (`method-paper/BRIEF.md:60`). Written on 2026-11-02 by an AI agent (Claude) in a cloud session,
outside the governed channel (`method-paper/BRIEF.md:30-32`), and revised the same day to record the framing agreed
with the author. The data it draws on is in `case-data.md` and `matrix/`; the references are in `related-work.md`.

## Constraints taken from the brief

- **Length:** at most five pages, about 2,500 words, one or two tables (`method-paper/BRIEF.md:9`).
- **Subject:** the claims registry, the pre-registration labels, the refutation criteria and the verifier that runs
  in CI, with the Polar Projector paper as the case. The case is not modified (`method-paper/BRIEF.md:9-11`, `:93`).
- **Who writes what:**
  - The agent drafts the tables and the description of the method (`method-paper/BRIEF.md:56-58`).
  - The author writes the introduction, the contribution, the limits and the conclusion, reviews or rewrites the
    agent's drafts, and approves every number (`method-paper/BRIEF.md:60-61`).
  - The paper states who did what (`method-paper/BRIEF.md:64`).
- **Secondary goal:** report what Actuarii recorded while this paper was written, as a pilot observation, not a
  test (`method-paper/BRIEF.md:13-14`), using the measurement fixed in advance (`method-paper/BRIEF.md:73-87`).
- **Honesty:** Actuarii did not govern the original paper, and the paper must not say it did
  (`method-paper/BRIEF.md:96`). Phase 0, this outline included, is declared as agent work outside the governed
  channel (`method-paper/BRIEF.md:32`).
- **Numbers:** every number in the paper gets a row in `method-paper/claims.md` and passes the verifier
  (`method-paper/BRIEF.md:25`, `:100-101`).

## Framing agreed on 2026-11-02

Agreed with the author in the Phase 0 session and recorded here so that a protocol can be committed on day 1. The
wording of the problem and of the contribution stays the author's (`method-paper/BRIEF.md:60`).

**The problem, in one sentence.** The author chooses one of these or writes another:

- *A, general:* a revised paper's numbers drift away from the evidence that produced them. What mechanism, small
  enough to live in the paper's own repository, keeps the link, and what escapes it?
- *B, case report:* describe one concrete mechanism and document, on one case, which errors it caught and which it
  did not.
- *Out of scope:* whether the Polar Projector results are right; generalising beyond one case; changing the case
  paper or its registry; whether Actuarii's receipts are faithful (`method-paper/BRIEF.md:93-95`).

**Principles.**

1. **Where a number comes from is untouchable.** The only evidence is code output: the artifacts in `bench/results/`
   written by committed scripts, and the values the verifier recomputes.
2. **Anything an LLM wrote is a claim to verify, not evidence.** That covers the manuscript, the registry, the commit
   messages, and the agent's own notes and scripts.
3. **Each number is judged by its logical category,** together with its structure: where it is printed and what it
   depends on. Each category requires its own kind of evidence (`matrix/README.md`).

**H1, coverage.** Every result figure printed in the manuscript is tied to code output, in one of two ways:

- *Directly:* a check compares it with an artifact value or a recomputation.
- *By derivation:* a declared formula over code output, recomputed from the artifacts, gives it at the printed
  precision. A derivable figure counts as tied only once that recomputation runs (the author's rule, 2026-11-02).

The rest of H1's specification:

- *Refuter:* a result figure tied in neither way.
- *Instrument:* the traceability matrix and its self-tests (`matrix/README.md`).
- *Why it is an open question:* the verifier checks one direction only, from registry to text
  (`tools/verify_paper_tables.py:599-627`). It reads the text the other way only for the Appendix B and C tables
  (`tools/verify_paper_tables.py:165-201`).

**H2, what consistency cannot see.** Consistency checks catch figures that are unbacked or mistranscribed. They do not
catch instrument errors, where the code output itself is wrong.

H1 is what makes H2 decidable. With each figure linked to its data, its code and its checks, every historical
correction can be classified from code output alone:

- *transcription:* the printed figure changed and its artifact did not;
- *instrument:* the artifact changed because the script that writes it changed;
- *object:* the operator, `polar_projector/`, changed.

The rest of H2's specification:

- *Refuter:* an instrument change where the verifier, run on the state before the fix, fails because of that figure.
- *A nuance the paper must state:* in `34b44b3`, exporting a missing artifact so that a figure could be checked
  exposed a protocol error. The check did not see it; preparing the figure for the check did (`case-data.md` §5.1,
  item 5).

**Status of today's results.** The matrix rules were tuned while looking at their output on the real manuscript. So
every H1 number from 2026-11-02 (`matrix/summary.md`) is exploratory: post hoc, in the registry's own vocabulary
(`paper/claims.md:56`). None of it tests H1.

**Protocol to commit on day 1, before the definitive run.** A proposal for the author:

1. *Definitions:* result figure (the categories of `matrix/README.md`); tied (directly, or by a recomputed
   derivation); the refuters of H1 and H2 given above.
2. *Rule fixes found on 2026-11-02, applied before the run:*
   - mathematics written in prose ("rising to 1", "toward 0", "toward 1") goes to derivation;
   - a new "external assumption" category takes figures no code produces ("60 Hz");
   - definitions printed with a × sign ("1×", the reference row's "1.00×") leave the result category.
3. *Derivation checks:* for each derivable figure, a declared formula over artifact values, recomputed and compared
   at the printed precision. The formula is an LLM claim; the recomputation is the evidence.
4. *Frozen code:* the matrix code is frozen in the commit that registers the protocol. Any later change is recorded
   as post hoc.

**What only the author can change.** Agents do not modify the brief (`method-paper/BRIEF.md:4-5`). On day 1
(`method-paper/BRIEF.md:36`) the author would:

- add H1 and H2 to the goal, if they stay (`method-paper/BRIEF.md:9-11`);
- add the matrix to the governed paths, as agreed (`method-paper/BRIEF.md:66-71`);
- confirm the measurement section in that light.

The paper declares that the framing, the matrix and today's exploratory numbers came from Phase 0, outside the
governed channel (`method-paper/BRIEF.md:32`).

## About the numbers in this file

- **Word budgets are planning targets set here,** not repository facts. The full budget sums to 2,500, the brief's
  target (`method-paper/BRIEF.md:9`). The cut-rule budget sums to 1,500, the brief's fallback
  (`method-paper/BRIEF.md:91-92`).
- **Budgets count prose,** abstract included. Tables, captions and references fall outside them. If the template
  counts those against five pages, trim §4's prose first.
- **Case numbers cite their source** where they appear, and are collected under "Numbers the paper would print",
  each a candidate row for `method-paper/claims.md`. Numbers from `matrix/summary.md` are exploratory until the
  day-1 run.

## Working title (options)

1. *Tied to code output: what a claims registry and a CI verifier caught in one paper, and what they could not*
2. *Every number has a row? Checking one paper's figures against the code that produced them*
3. *What a claims registry caught, and what it could not: one paper's record*

## Word budget

| § | Section | Writer, per the brief | Words | Cut rule | Tables |
|---|---|---|---:|---:|---|
| — | Abstract | Not assigned by the brief; suggested: author | 150 | 100 | |
| 1 | Introduction and contribution | Author (`method-paper/BRIEF.md:60`) | 300 | 0 | |
| 2 | The case | Agent drafts, author reviews | 150 | 100 | |
| 3 | The method | Agent drafts (`method-paper/BRIEF.md:56-58`), author reviews | 550 | 400 | |
| 4 | H1 and H2: what the record shows | Agent drafts, author approves every number (`method-paper/BRIEF.md:61`) | 650 | 450 | 1 and 2 |
| 5 | Pilot: this paper written under Actuarii | Agent counts, author interprets | 200 | 100 | |
| 6 | Limits | Author (`method-paper/BRIEF.md:60`) | 300 | 300 | |
| 7 | Who did what | Author | 100 | 50 | |
| 8 | Conclusion | Author (`method-paper/BRIEF.md:61`) | 100 | 0 | |
| | **Total** | | **2,500** | **1,500** | |

**The cut rule and the "done" criteria pull in different directions.** The rule keeps "the method, the case and the
limits" (`method-paper/BRIEF.md:91-92`). "Done" still requires the measurement to be reported
(`method-paper/BRIEF.md:101-102`), and the paper must state who did what (`method-paper/BRIEF.md:64`). The cut column
therefore keeps §5 and §7 at minimum length, counts the H1 and H2 results as part of "the case", and drops §1 and §8,
leaving the abstract to frame the paper. The author should confirm that reading.

## Section by section

### Abstract (150 words; cut: 100)

One sentence each:

- The problem: a revised paper's printed numbers drift away from their evidence.
- The case and its scale: 42 registry rows (`paper/claims.md:68-124`), 281 figures checked against committed
  artifacts (verifier at `501c67f`, `case-data.md` §7).
- The four components, and the instrument added to test how far they reach.
- The H1 and H2 results, from the day-1 run.
- The main limit: consistency is not validity (`README.md:124-125`).

### 1. Introduction and contribution (300 words; cut: 0). Author.

- **The problem, in the case's own examples.** Refit costs that "no committed drift.json contains" (`2f8e532`),
  and clamp figures that "were in no artifact" (`b505d76`).
- **What exists** (`related-work.md`):
  - reproducible-research practice (Buckheit & Donoho 1995; Peng 2011; Sandve et al. 2013, Rule 9);
  - preregistration (Nosek et al. 2018);
  - experiments re-run in CI (Jimenez et al. 2017);
  - after-the-fact consistency checks (Nuijten et al. 2016);
  - artifact badges (ACM 2020);
  - executable papers (Nowakowski et al. 2011).
- **The gap:** a per-claim record that links each printed number in an ordinary static manuscript to a script, an
  artifact, a pre-registration label and a check that CI runs. And a test of whether every printed figure, not just
  every registered one, is tied to code output.
- **Contribution (author's words):** the four components, a full account of one case, and a test of how far they
  reach (H1) and of what they cannot see (H2). Say what this is not: not a tool, not an evaluation across papers.

### 2. The case (150 words; cut: 100). Agent drafts.

- **What it is:** the paper's title (`CITATION.cff:20`), the release `v1.0-paper` at `f59430a` (`git show-ref
  --tags`), and its measured-report stance: "a baseline simple enough to write in a few lines matches or beats the
  operator, and the paper says so" (`README.md:19-20`).
- **Timeline:** first manuscript commit on 2026-09-11 (`e5d134d`), release tag on 2026-09-16 (`f59430a`), 78
  commits in between inclusive, 54 of them touching the manuscript (`case-data.md` §7). The registry appeared
  part-way, on 2026-09-13 (`2f8e532`).
- **Scale:** 42 registry rows; 281 figures checked against 11 of the 12 committed artifacts, all but
  `batched.json`, whose claims were removed (`tools/verify_paper_tables.py:257-535`; `case-data.md` §7); 800 tests;
  a 735-line verifier against a 432-line operator (`wc -l` at `501c67f`; `docs/ARCHITECTURE.md:35`).
- **Suggestion:** no pipeline figure. The brief allows tables only (`method-paper/BRIEF.md:9`), and the five stages
  fit in one sentence (`docs/ARCHITECTURE.md:9-17`).

### 3. The method (550 words; cut: 400). Agent drafts, author reviews.

**3.1 Claims registry (150; cut 100).**

- One row per claim, with an ID, the claim, a status, a pre-registration label, a source and the CI checks
  (`paper/claims.md:66`).
- The rule: "Nothing enters the manuscript without a row here" (`paper/claims.md:3`).
- Seven statuses (`paper/claims.md:40-50`). One of them, `construction`, was added for facts read from code rather
  than measured (`8359755`). An open claim was closed by reading a library's source instead of measuring (R5 became
  C21, `57c5200`).
- At release: 31 checked, 4 construction, 7 remove (`tools/verify_paper_tables.py:670`; `case-data.md` §1). By
  pre-registration label: 13 yes, 7 no, 4 post hoc, 6 mixed, 8 n/a, 4 with no label (`case-data.md` §2).
- A "must not appear" table (`paper/claims.md:117-124`), and an exploration notebook of figures with no script,
  none of them admissible (`paper/claims.md:126-135`).
- Cite Sandve et al. (2013), Rule 9.

**3.2 Pre-registration labels (125; cut 100).**

- Three labels (`paper/claims.md:52-56`). "Registered" means the protocol commit precedes the results commit; one
  worked example is E8 (`498d0ab` → `dd9e5b5`).
- `no` is "not wrong, but it may not be described as pre-registered" (`paper/claims.md:54-55`); `post hoc` must be
  labelled exploratory in the text (`paper/claims.md:56`).
- Cite Nosek et al. (2018).

**3.3 Registered question and refutation criteria (75; cut 50).**

- F1, F2 and the Bound, each with its measured outcome (`paper/claims.md:14-21`).
- The revision is kept beside the superseded question (`paper/claims.md:30-36`), and it added no experiment
  (`paper/claims.md:27-28`).

**3.4 The verifier in CI (200; cut 150).**

- What it does:
  - recomputes Appendices B and C from the operator;
  - compares each published figure with its committed artifact at the printed precision (`34b44b3` message);
  - checks that each checked figure is printed in the manuscript (`tools/verify_paper_tables.py:599-627`);
  - checks that each `checked` row names a real check (`tools/verify_paper_tables.py:640-672`).
- When it runs: on pushes to `main` and on pull requests (`.github/workflows/ci.yml:3-6`, `:50-51`).
- How the checked surface grew: 112 figures (`34b44b3`) to 281 (`65c3ebf`), re-run at each step (`case-data.md`
  §7).
- What it does not do, which motivates H1: it never reads a printed number back to the registry, except in the
  Appendix B and C tables (`tools/verify_paper_tables.py:165-201`).
- Cite Jimenez et al. (2017) and Nuijten et al. (2016).

### 4. H1 and H2: what the record shows (650 words; cut: 450). Agent drafts, author approves every number.

**4.1 The instrument (150; cut 100).**

- The matrix: one row per printed number, with its logical category and the evidence that category requires
  (`matrix/README.md`).
- Evidence comes only from code output. The checks come from running the verifier, and the artifact behind each
  check is found by perturbing one artifact at a time.
- Self-tests: errors planted in copies of the repository, three of which the verifier lets through
  (`matrix/test_matrix.py`; `matrix/README.md`).

**4.2 H1 (250; cut 175). Table 1.**

- The result comes from the day-1 run.
- Exploratory figures from 2026-11-02, for orientation only: 478 result figures. Of these, 454 are tied directly (420
  by presence, 26 located, 8 single-character), 10 are matched only by short strings from another section, and 14
  are untied (`matrix/summary.md:17`).
- The clearest case is Appendix A's "vs. d = 16" column (`paper/polar-projector-paper.md:1095-1103`). Of its seven
  figures one has a check, and three others pass only because their string matches a different figure
  (`matrix/summary.md:41-46`).
- Derivable figures become tied once their recomputation runs (protocol, item 3). Whatever is still untied after
  that refutes H1.
- How blind presence is: 31 check strings are shared by several checks, and 86 checked strings are printed in more
  than one place (`matrix/summary.md:9-10`).

**4.3 H2 (250; cut 175). Table 2.**

- The result is the code-only classification of historical changes, computed on day 1 or later.
- Data already in hand:
  - the code review changed the figures of 9 rows that were `checked`, while the verifier passed (`97e9306` →
    `65c3ebf`; 277/277 at `97e9306`; `case-data.md` §5.1, §7);
  - C16 is the clearest instrument case (`paper/claims.md:103`);
  - the method notes single out two failures, a cost column that mixed operations and a label used both as input
    and as reference (`docs/METHODOLOGY.md:39-43`; `97e9306`).
- The `34b44b3` nuance (see the framing above).

### 5. Pilot: this paper written under Actuarii (200 words; cut: 100)

- **Report the five counts the brief fixes** (`method-paper/BRIEF.md:77-81`), over Phase 1 only
  (`method-paper/BRIEF.md:75`), as an observation of one author over one week (`method-paper/BRIEF.md:83`).
- **State the brief's own limits on those counts** (`method-paper/BRIEF.md:85-87`).
- **Say that Phase 0 ran outside the channel** (`method-paper/BRIEF.md:30-32`), and that it included the framing
  and the first version of the matrix. **Say that Actuarii did not govern the Polar Projector paper**
  (`method-paper/BRIEF.md:96`).
- No hypothesis and no interpretation beyond what escaped and why, when known (`method-paper/BRIEF.md:81`). The
  counts do not exist yet; this section is a placeholder until day 5 (`method-paper/BRIEF.md:38`).

### 6. Limits (300 words; cut: 300). Author.

Candidate points, each with its evidence; the author chooses and words them.

1. **Consistency, not validity.** The verifier "cannot catch a benchmark that measures something other than what the
   paper says it measures" (`README.md:124-125`). C16's figures passed until a code review found the arm wrong
   (`65c3ebf`). H2 measures how far this goes.
2. **Presence, not location** (`paper/claims.md:61-62`). Single-character figures are counted, not located: 20 at
   `501c67f` (`case-data.md` §7). The matrix does not fully solve this either: a string matching a string is not
   the same figure, so it flags these cases and leaves them for reading (`matrix/README.md`).
3. **Prose about provenance is unchecked.** The manuscript's pre-registration sentence appears to disagree with the
   registry (`paper/polar-projector-paper.md:902-908`; `case-data.md` §9, item 1). Use it only once the author has
   confirmed it.
4. **`remove` and `construction` rows are not checked by CI** (`tools/verify_paper_tables.py:656-657`), and two
   `remove` rows carry stale source text (`paper/claims.md:121-122`).
5. **Commit-order registration is self-registration.** The protocol-to-results gaps run from 49 to 384 seconds, with
   no outside timestamp (`case-data.md` §8). One registered protocol changed its aggregation after the first run
   (`1e9d217`).
6. **The label vocabulary is incomplete:** `n/a` and `—` are used but undefined (`paper/claims.md:52-56`).
7. **One case, one author, and an instrument an LLM wrote.** The matrix's categories are rules written by the
   agent. Its self-tests show what it detects, not that its categories are right, and the 2026-11-02 numbers are
   exploratory.
8. **AI involvement is recorded by declaration.** 64 of 89 commits carry a co-author trailer
   (`git log --grep='^Co-Authored-By:'`), and the manuscript states what assistants did
   (`paper/polar-projector-paper.md:1003-1011`). Neither says who wrote which line.

### 7. Who did what (100 words; cut: 50)

- **The original paper:** its AI statement (`paper/polar-projector-paper.md:1003-1011`) and the trailer count
  (`case-data.md` §7).
- **This paper:** the roles in `method-paper/BRIEF.md:54-64`. Phase 0 was done by the agent outside the governed
  channel (`method-paper/BRIEF.md:30-32`): this preparation, the first matrix, and the framing, agreed with the
  author in conversation. Phase 1 runs under Actuarii (`method-paper/BRIEF.md:34-38`), with `Human-Record`
  trailers on the author's commits (`method-paper/BRIEF.md:61-62`).

### 8. Conclusion (100 words; cut: 0). Author.

- What a reader can reuse as is: the status vocabulary, the label split, and the verifier's pattern of recomputing,
  comparing cell by cell and requiring presence (`docs/ARCHITECTURE.md:55-63`).
- What H1 and H2 add: the direction the verifier does not check, and the class of error no consistency check sees.

## Proposed tables

**Table 1. H1: result figures by status.** Source: the matrix at the day-1 run, regenerated into
`matrix/summary.md`. The exploratory column comes from 2026-11-02 (`matrix/summary.md:17`); the other categories
(parameter, derivation, environment, excluded, unclassified) are in `matrix/summary.md:17-25`.

| Status | Exploratory, 2026-11-02 | Day-1 run |
|---|---:|---:|
| Tied, located (Appendices B and C) | 26 | |
| Tied by presence | 420 | |
| Tied by value, single character | 8 | |
| Presence matched only by a short string of another section | 10 | |
| Tied by derivation, recomputed | — | |
| Untied | 14 | |
| **Result figures** | **478** | |

**Table 2. H2: corrections by what changed, and whether the verifier caught them.** Layout only. What changed is read
from code output, not commit messages: whether the commit changed the text, the artifact, the script or the
operator. Whether the verifier caught it comes from running it on the state before the fix. Values come from the
day-1 run or later; the examples are candidates to classify.

| What changed | Verifier passed before the fix | Verifier failed before the fix | Candidate example |
|---|---:|---:|---|
| Transcription: text changed, artifact did not | | | `0b90772`, A5's 1.3% → 1.4% |
| Instrument: artifact changed with its script | | | `65c3ebf`, C16 |
| Object: the operator changed | | | `c3dfb0b`, the clamp |
| **Total** | | | |

The earlier Table 1, the registry by status and pre-registration label, now fits in a sentence in §3.1; the counts
are in `case-data.md` §1–2. The earlier Table 2, corrections by route, rested on commit messages and is not evidence
(`case-data.md` §5.3).

## Numbers the paper would print

Candidate rows for `method-paper/claims.md`. Each needs the author's approval (`method-paper/BRIEF.md:61`). Those
marked *exploratory* come from the matrix and are replaced by the day-1 run.

| Number | What it is | Source |
|---|---|---|
| 42 | Registry rows | `paper/claims.md:68-124`; `case-data.md` §1 |
| 31 / 4 / 7 | checked / construction / remove | `tools/verify_paper_tables.py:670` at `501c67f`; `case-data.md` §1 |
| 7 statuses, 4 unused | Status vocabulary | `paper/claims.md:40-50`; `case-data.md` §1 |
| 13 / 7 / 4 / 6 / 8 / 4 | Label classes | `paper/claims.md:68-124`; rule in `case-data.md` §2 |
| 33 → 42 | Registry rows at creation and now | `2f8e532`, `65c3ebf`; `case-data.md` §4 |
| 281 | Figures checked against artifacts | Verifier at `f59430a` and `501c67f`; `case-data.md` §7 |
| 261 / 20 | Located / single-character figures | Same runs; `case-data.md` §7 |
| 112 → 281 | Growth of checked figures | Verifier at `34b44b3` and `65c3ebf`; `case-data.md` §7 |
| 12; 6; 14 | Artifacts; commits that rewrote them; file rewrites | `git log --name-status -- bench/results/`; `case-data.md` §5.2 |
| 6 | Protocol commits labelled `yes` | `case-data.md` §8 |
| 49–384 s | Protocol-to-results gaps | `21e8e45`→`c265abb`, `1c363bb`→`1e9d217`; `case-data.md` §8 |
| 9 | Checked rows whose figures the code review changed | `97e9306` → `65c3ebf`, `paper/claims.md`; `case-data.md` §5.1 |
| 78; 54 | Commits from manuscript to release; those touching it | `git rev-list --count e5d134d^..f59430a`; `case-data.md` §7 |
| 5 days | Manuscript to release, 2026-09-11 to 2026-09-16 | `e5d134d`, `f59430a` |
| 800 | Tests collected | `pytest --collect-only` at `501c67f`; `README.md:127` |
| 735 / 432 | Verifier / operator lines | `wc -l` at `501c67f`; `docs/ARCHITECTURE.md:35` |
| 64 of 89 | Commits with a co-author trailer | `git log --grep='^Co-Authored-By:'`; `case-data.md` §7 |
| 1,344 / 478 | Printed numbers / result figures (*exploratory*) | `matrix/summary.md:5`, `:17` |
| 454 / 10 / 14 | Result figures tied directly / matched only across sections / untied (*exploratory*) | `matrix/summary.md:17` |
| 7, 1 | Figures in Appendix A's "vs. d = 16" column, and those with a check (*exploratory*) | `paper/polar-projector-paper.md:1095-1103`; `matrix/summary.md:41-46` |
| 31; 86 | Check strings shared by several checks; checked strings printed in several places | `matrix/summary.md:9-10` |
| 0; 0 | Checks matching no printed number; checks with no artifact found | `matrix/summary.md:7-8` |

## Decisions for the author

1. **The problem statement:** A, B, or the author's own (framing above).
2. **The brief on day 1:** the goal (H1 and H2), the governed paths (the matrix) and the measurement section.
3. **The H1 and H2 protocol** proposed above: confirm or change it before it is committed.
4. **Whether to use `case-data.md` §9, item 1** (the manuscript's pre-registration sentence) as the example of
   what the verifier cannot see. Confirm it first; the case paper itself stays unmodified
   (`method-paper/BRIEF.md:93`).
5. **The cut column above,** which reads the cut rule together with the "done" criteria.
6. **Which run to cite "at release":** the verifier gives identical counts at `f59430a` and `501c67f`
   (`case-data.md` §7).
7. **References:** finish the link check in `related-work.md` before citing anything. It needs `doi.org`,
   `api.crossref.org` and `www.acm.org` allowed in the environment, or a manual check.
