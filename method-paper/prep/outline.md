# Outline: a five-page paper on how the Polar Projector paper kept its numbers tied to evidence

Phase 0 preparation (`method-paper/BRIEF.md:50`). A proposal for the author to cut, reorder or reject: the author
decides what goes in (`method-paper/BRIEF.md:60`). Written on 2026-11-02 by an AI agent (Claude) in a cloud session,
outside the governed channel (`method-paper/BRIEF.md:30-32`). The data it draws on is in `case-data.md`; the
references are in `related-work.md`.

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

## About the numbers in this file

- **Word budgets are planning targets set here,** not repository facts. The full budget sums to 2,500, the brief's
  target (`method-paper/BRIEF.md:9`). The cut-rule budget sums to 1,500, the brief's fallback
  (`method-paper/BRIEF.md:91-92`).
- **Budgets count prose,** abstract included. Tables, captions and references fall outside them. If the template
  counts those against five pages, trim §4's prose first.
- **Case numbers cite their source** where they appear, and are collected under "Numbers the paper would print",
  each a candidate row for `method-paper/claims.md`.

## Working title (options)

1. *Every number has a row: tying a paper's figures to their evidence with a claims registry and a CI verifier*
2. *What a claims registry caught, and what it could not: one paper's record*

## Word budget

| § | Section | Writer, per the brief | Words | Cut rule | Tables |
|---|---|---|---:|---:|---|
| — | Abstract | Not assigned by the brief; suggested: author | 150 | 100 | |
| 1 | Introduction and contribution | Author (`method-paper/BRIEF.md:60`) | 300 | 0 | |
| 2 | The case | Agent drafts, author reviews | 200 | 150 | |
| 3 | The method | Agent drafts (`method-paper/BRIEF.md:56-58`), author reviews | 650 | 500 | |
| 4 | What the record shows | Agent drafts, author approves every number (`method-paper/BRIEF.md:61`) | 550 | 350 | 1 and 2 |
| 5 | Pilot: this paper written under Actuarii | Agent counts, author interprets | 200 | 100 | |
| 6 | Limits | Author (`method-paper/BRIEF.md:60`) | 300 | 250 | |
| 7 | Who did what | Author | 100 | 50 | |
| 8 | Conclusion | Author (`method-paper/BRIEF.md:61`) | 50 | 0 | |
| | **Total** | | **2,500** | **1,500** | |

**The cut rule and the "done" criteria pull in different directions.** The rule keeps "the method, the case and the
limits" (`method-paper/BRIEF.md:91-92`). "Done" still requires the measurement to be reported
(`method-paper/BRIEF.md:101-102`), and the paper must state who did what (`method-paper/BRIEF.md:64`). The cut
column therefore keeps §5 and §7 at minimum length and drops §1 and §8, leaving the abstract to frame the paper. The
author should confirm that reading.

## Section by section

### Abstract (150 words; cut: 100)

One sentence each:

- The problem: a revised paper's printed numbers drift away from their evidence.
- The case and its scale: 42 registry rows (`paper/claims.md:68-124`), 281 figures checked against committed
  artifacts (verifier at `501c67f`, `case-data.md` §7).
- The four components.
- What the record shows: the CI-side checks caught some errors; experiments, review and outside sources caught more,
  including figures that had passed CI (`case-data.md` §5.3).
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
  artifact, a pre-registration label and a check that CI runs.
- **Contribution (author's words):** a description of the four components and a full account of one case,
  including what they missed. Say what this is not: not a tool, not an evaluation across papers (one case).

### 2. The case (200 words; cut: 150). Agent drafts.

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

### 3. The method (650 words; cut: 500). Agent drafts, author reviews.

**3.1 Claims registry (200; cut 150).**

- One row per claim, with an ID, the claim, a status, a pre-registration label, a source and the CI checks
  (`paper/claims.md:66`).
- The rule: "Nothing enters the manuscript without a row here" (`paper/claims.md:3`).
- Seven statuses (`paper/claims.md:40-50`). One of them, `construction`, was added for facts read from code rather
  than measured (`8359755`).
- A "must not appear" table (`paper/claims.md:117-124`), and an exploration notebook of figures with no script,
  none of them admissible (`paper/claims.md:126-135`).
- Cite Sandve et al. (2013), Rule 9.

**3.2 Pre-registration labels (150; cut 125).**

- Three labels (`paper/claims.md:52-56`). "Registered" means the protocol commit precedes the results commit; one
  worked example is E8 (`498d0ab` → `dd9e5b5`).
- `no` is "not wrong, but it may not be described as pre-registered" (`paper/claims.md:54-55`); `post hoc` must be
  labelled exploratory in the text (`paper/claims.md:56`).
- Cite Nosek et al. (2018).

**3.3 Registered question and refutation criteria (100; cut 75).**

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
- Cite Jimenez et al. (2017) and Nuijten et al. (2016).

### 4. What the record shows (550 words; cut: 350). Agent drafts, author approves every number.

**4.1 The registry at release (Table 1; prose 100, cut 75).**

- 31 checked, 4 construction, 7 remove (`paper/claims.md:68-124`; the verifier's tally at
  `tools/verify_paper_tables.py:670`).
- By label: 13 yes, 7 no, 4 post hoc, 6 mixed, 8 n/a, 4 with no label (`case-data.md` §2).
- One sentence on the two labels the vocabulary does not define (`paper/claims.md:52-56`).

**4.2 Corrections and how they were found (Table 2; prose 350, cut 225).**

- 37 commits corrected something already committed (`case-data.md` §5.3).
- The strongest single datum: the code review changed the figures of 9 rows that were `checked` and passing CI
  (`97e9306` → `65c3ebf`; verifier 277/277 at `97e9306`).
- The clearest case is C16, a CI-green figure that was wrong because the arm was wrong (`paper/claims.md:103`).
- The two failures the method notes single out, a cost column that mixed operations and a label used both as input
  and as reference, were found by an audit, not by CI (`docs/METHODOLOGY.md:39-43`; `97e9306`).

**4.3 Claims removed (100; cut 50).**

- Seven `remove` rows and their reasons (`paper/claims.md:77-79`, `:121-124`).
- One open claim closed by reading a library's source instead of measuring (R5 to C21, `57c5200`).
- Removals that never got a row (`case-data.md` §6.2).

### 5. Pilot: this paper written under Actuarii (200 words; cut: 100)

- **Report the five counts the brief fixes** (`method-paper/BRIEF.md:77-81`), over Phase 1 only
  (`method-paper/BRIEF.md:75`), as an observation of one author over one week (`method-paper/BRIEF.md:83`).
- **State the brief's own limits on those counts** (`method-paper/BRIEF.md:85-87`).
- **Say that Phase 0 ran outside the channel** (`method-paper/BRIEF.md:30-32`), **and that Actuarii did not govern
  the Polar Projector paper** (`method-paper/BRIEF.md:96`).
- No hypothesis and no interpretation beyond what escaped and why, when known (`method-paper/BRIEF.md:81`). The
  counts do not exist yet; this section is a placeholder until day 5 (`method-paper/BRIEF.md:38`).

### 6. Limits (300 words; cut: 250). Author.

Candidate points, each with its evidence; the author chooses and words them.

1. **Consistency, not validity.** The verifier "cannot catch a benchmark that measures something other than what the
   paper says it measures" (`README.md:124-125`). C16's figures passed until a code review found the arm wrong
   (`65c3ebf`).
2. **Presence, not location** (`paper/claims.md:61-62`). Single-character figures are counted, not located: 20 at
   `501c67f` (`case-data.md` §7).
3. **Prose about provenance is unchecked.** The manuscript's pre-registration sentence appears to disagree with the
   registry (`paper/polar-projector-paper.md:902-908`; `case-data.md` §9, item 1). Use it only once the author has
   confirmed it.
4. **`remove` and `construction` rows are not checked by CI** (`tools/verify_paper_tables.py:656-657`), and two
   `remove` rows carry stale source text (`paper/claims.md:121-122`).
5. **Commit-order registration is self-registration.** The protocol-to-results gaps run from 49 to 384 seconds, with
   no outside timestamp (`case-data.md` §8). One registered protocol changed its aggregation after the first run
   (`1e9d217`).
6. **The label vocabulary is incomplete:** `n/a` and `—` are used but undefined (`paper/claims.md:52-56`).
7. **One case and one author.** The correction routes in Table 2 were coded by the agent from commit messages, and 9
   of the 37 commits name no route (`case-data.md` §5.3).
8. **AI involvement is recorded by declaration.** 64 of 89 commits carry a co-author trailer
   (`git log --grep='^Co-Authored-By:'`), and the manuscript states what assistants did
   (`paper/polar-projector-paper.md:1003-1011`). Neither says who wrote which line.

### 7. Who did what (100 words; cut: 50)

- **The original paper:** its AI statement (`paper/polar-projector-paper.md:1003-1011`) and the trailer count
  (`case-data.md` §7).
- **This paper:** the roles in `method-paper/BRIEF.md:54-64`. Phase 0, this preparation, was done by the agent
  outside the governed channel (`method-paper/BRIEF.md:30-32`); Phase 1 runs under Actuarii
  (`method-paper/BRIEF.md:34-38`), with `Human-Record` trailers on the author's commits
  (`method-paper/BRIEF.md:61-62`).

### 8. Conclusion (50 words; cut: 0). Author.

- What a reader can reuse as is: the status vocabulary, the label split, and the verifier's pattern of recomputing,
  comparing cell by cell and requiring presence (`docs/ARCHITECTURE.md:55-63`).

## Proposed tables

**Table 1. The registry at release: rows by status and pre-registration label.** Source: `paper/claims.md:68-124`,
grouped by the rule in `case-data.md` §2. The registry at `v1.0-paper` is the registry at `501c67f`
(`case-data.md` §4).

| Status | yes | no | post hoc | mixed | n/a | — | Total |
|---|---:|---:|---:|---:|---:|---:|---:|
| checked | 10 | 7 | 4 | 6 | 4 | 0 | 31 |
| construction | 0 | 0 | 0 | 0 | 4 | 0 | 4 |
| remove | 3 | 0 | 0 | 0 | 0 | 4 | 7 |
| **Total** | **13** | **7** | **4** | **6** | **8** | **4** | **42** |

**Table 2. Correction commits by how they were found.** Source: `case-data.md` §5.3: 37 commits, coded by the agent
from their messages, for the author to confirm. Shown at a coarser grain than `case-data.md`: "CI-side work" groups
registry or verifier (5), artifact export (1) and cross-host CI (1); "Review" groups manual review (10) and code
review (1). **Not evidence as it stands:** commit messages are largely LLM output (`case-data.md` §5.3), so this
table needs replacing by the code-only classification planned in `matrix/README.md`.

| How it was found | Commits | Example |
|---|---:|---|
| Review (full read, audit, integration of author drafts, code review) | 11 | `65c3ebf`: 9 checked rows' figures changed |
| CI-side work (presence check, verifier rows, artifact export, second host) | 7 | `2f8e532`: refit costs no artifact contained |
| Experiment (new or pre-registered measurement) | 7 | `c560801`: any fixed linear map is exactly stable |
| Outside source (library code, another repository, reference databases) | 3 | `57c5200`: R5 closed by reading `transform()` |
| Not stated in the message | 9 | `a773513`: two errors in Proposition 1 |
| **Total** | **37** | |

Alternative Table 2, if the author prefers growth to routes: the number of figures under check at each commit, 112
to 281 (`case-data.md` §7).

## Numbers the paper would print

Candidate rows for `method-paper/claims.md`. Each needs the author's approval (`method-paper/BRIEF.md:61`).

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
| 37 | Correction commits | `case-data.md` §5.3 (agent coding) |
| 11 / 7 / 7 / 3 / 9 | Routes, coarse (Table 2) | `case-data.md` §5.3 |
| 9 | Checked rows whose figures the code review changed | `97e9306` → `65c3ebf`, `paper/claims.md`; `case-data.md` §5.1 |
| 78; 54 | Commits from manuscript to release; those touching it | `git rev-list --count e5d134d^..f59430a`; `case-data.md` §7 |
| 5 days | Manuscript to release, 2026-09-11 to 2026-09-16 | `e5d134d`, `f59430a` |
| 800 | Tests collected | `pytest --collect-only` at `501c67f`; `README.md:127` |
| 735 / 432 | Verifier / operator lines | `wc -l` at `501c67f`; `docs/ARCHITECTURE.md:35` |
| 64 of 89 | Commits with a co-author trailer | `git log --grep='^Co-Authored-By:'`; `case-data.md` §7 |

## Decisions for the author

1. **Whether to use `case-data.md` §9, item 1** (the manuscript's pre-registration sentence) as the example of
   what the verifier cannot see. Confirm it first; the case paper itself stays unmodified
   (`method-paper/BRIEF.md:93`).
2. **The cut column above,** which reads the cut rule together with the "done" criteria.
3. **Table 2's coding:** confirm or recode the 37 commits, and choose the coarse or fine grouping.
4. **Which run to cite "at release":** the verifier gives identical counts at `f59430a` and `501c67f`
   (`case-data.md` §7).
5. **References:** finish the link check in `related-work.md` before citing anything.
