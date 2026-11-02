# Case data: the Polar Projector paper's claims, corrections and removals

Phase 0 preparation for the method paper described in `method-paper/BRIEF.md`. This is extraction only. The author
has not reviewed any of it yet, and every count below is a candidate for `method-paper/claims.md`, not an approved
number.

Contents: 0 About this file · 1 Claims by status · 2 Claims by pre-registration label · 3 Registered question and
refutation criteria · 4 Registry history · 5 Corrections and re-measurements · 6 Claims removed from the manuscript ·
7 The verifier and CI · 8 Pre-registration evidence · 9 Observations for the author · 10 Commit index

## 0. About this file

- **Who and when.** Written on 2026-11-02 by an AI agent (Claude) in a cloud session. That is Phase 0, which the
  brief places outside the governed channel and asks the paper to declare as such (`method-paper/BRIEF.md:30-32`).
  The agent read files and git history and ran the existing verifier on snapshots extracted outside the repository.
  It modified no existing file.
- **Where.** In `method-paper/prep/`, where the brief puts Phase 0 output (`method-paper/BRIEF.md:23`, `:31`,
  `:42`, `:52`). The files were first committed under `notes/method-paper-prep/`, as the session had asked, and
  moved here in the next commit on this branch (`git log --follow`).
- **Citations.** `path:line` is that line at commit `501c67f`, the head of `main` when the session started.
  `abc1234:path:line` is a line of the file as it stood at commit `abc1234`. A bare 7-character hash is a commit;
  §10 gives each one's full hash, date and subject. "Message" means the commit message.
- **Dates.** Author dates from `git log --date=short`. Author and committer dates are identical for every commit
  except `faf2f10` and `501c67f`, whose author time is 13:36:01 and committer time 13:40:01
  (`git log --format='%h %ad %cd' faf2f10 501c67f`).
- **Counts.** Registry counts come from parsing `paper/claims.md` with the rule in §1. They agree with the tally
  the verifier prints itself (§7).
- **Re-runs.** "Verifier at X" means `python tools/verify_paper_tables.py` run in this session on a snapshot of
  commit X (`git archive X`), with Python 3.13.18 and numpy 2.5.3 on Linux x86_64 (`python3 --version`;
  `numpy.__version__`). CI pins a different environment: numpy 2.4.1 (`pyproject.toml:31`) on Python 3.11
  (`.github/workflows/ci.yml:35`).

## 1. Claims by status

`paper/claims.md` holds 42 claim rows in four tables: operator rows A1–A15 (15 rows, `paper/claims.md:68-82`),
registered-question rows C1–C22 (22 rows, `:88-109`), one post hoc row P1 (`:115`) and must-not-appear rows R1–R4
(4 rows, `:121-124`).

Parse rule: a row is a table line whose first cell matches `[ACPR]\d+`, the rule the verifier itself uses
(`tools/verify_paper_tables.py:646`).

| Status | Defined at | Rows | IDs |
|---|---|---:|---|
| `checked` | `paper/claims.md:41` | 31 | A1–A9, A13–A15, C1–C18, P1 |
| `construction` | `paper/claims.md:47-49` | 4 | C19–C22 |
| `remove` | `paper/claims.md:50` | 7 | A10–A12, R1–R4 |
| `not-in-ci` | `paper/claims.md:42` | 0 | — |
| `mismatch` | `paper/claims.md:43-44` | 0 | — |
| `unbacked` | `paper/claims.md:45` | 0 | — |
| `pending` | `paper/claims.md:46` | 0 | — |
| **Total** | | **42** | |

- **Cross-check.** The verifier at `501c67f` prints "31 checked, 4 construction, 7 remove" (the line comes from
  `tools/verify_paper_tables.py:670`).
- **What `checked` rests on.** From the CI-checks column (`paper/claims.md:68-115`): 4 rows name `pytest` (A1, A8,
  A14, A15), 2 name a recomputation (A2 `recompute:§B`, A13 `recompute:§C`), and 25 name verifier-label prefixes,
  73 prefixes in all.
- **Unused statuses.** 4 of the 7 defined statuses have no rows. Across all 10 versions of the registry,
  `not-in-ci` was used once, for C15 at creation (`2f8e532:paper/claims.md:72`). `mismatch`, `unbacked` and
  `pending` were never used (§4).
- **Not checked by CI.** `construction` rows quote no figure and name a source in place of a check
  (`paper/claims.md:47-49`). `remove` rows name no check. The verifier skips every row whose status is not
  `checked` (`tools/verify_paper_tables.py:656-657`).

## 2. Claims by pre-registration label

The vocabulary defines three labels (`paper/claims.md:52-56`):

- `yes (commit)`: the protocol was committed before its results.
- `no`: script and results entered in the same commit.
- `post hoc`: specified after seeing the result it explains.

The column also holds two values the vocabulary does not define: `n/a`, bare or with a qualifier (proof,
recomputed, derivation), in 8 rows, and `—` in the 4 R rows (`paper/claims.md:68-124`; every label is listed
verbatim below).

Grouping rule: a cell is classed by which of the three vocabulary labels it contains. One label gives that
class, two give "mixed", and a cell with none that starts with `n/a` is "n/a". Qualifiers after a label, such as
"access order changed 2026-09-16", do not change the class.

| Label class | All rows | checked | construction | remove | IDs |
|---|---:|---:|---:|---:|---|
| yes | 13 | 10 | 0 | 3 | A2, A3, A5, A10, A11, A12, C3, C4, C5, C8, C9, C10, C16 |
| no | 7 | 7 | 0 | 0 | A8, A9, C2, C11, C12, C15, C17 |
| post hoc | 4 | 4 | 0 | 0 | A7, C14, C18, P1 |
| mixed yes + no | 5 | 5 | 0 | 0 | A4, A6, C1, C6, C7 |
| mixed no + post hoc | 1 | 1 | 0 | 0 | C13 |
| n/a | 8 | 4 | 4 | 0 | A1, A13, A14, A15, C19, C20, C21, C22 |
| — | 4 | 0 | 0 | 4 | R1, R2, R3, R4 |
| **Total** | **42** | **31** | **4** | **7** | |

- **Rows that may appear in the manuscript** (`checked` plus `construction`, 35): yes 10, no 7, post hoc 4,
  mixed 6, n/a 8. This and the next bullet are sums over the table above.
- **Counting label parts instead of classes:** 18 rows carry a "yes" part (13 plus the 5 mixed yes + no), 13 a
  "no" part (7 plus the 6 mixed), 5 a "post hoc" part (4 plus C13).
- **Labels that record a change after registration.** Four, all dated 2026-09-16 and made in `97e9306` or
  `65c3ebf` (§5.1): A5 "access order changed 2026-09-16" (`paper/claims.md:72`), A6 "protocol changed 2026-09-16"
  (`:73`), C15 "cost columns redefined 2026-09-16 after the audit, recalls unchanged bit for bit" (`:102`) and C16
  "arm corrected 2026-09-16 after the code review" (`:103`). C4 also notes "timings from the c560801 rerun"
  (`:91`).

Every label, verbatim (`paper/claims.md`, line numbers at `501c67f`):

| Line | ID | Status | Pre-registered |
|---:|---|---|---|
| 68 | A1 | checked | n/a (proof) |
| 69 | A2 | checked | yes (06c0d5c) |
| 70 | A3 | checked | yes (06c0d5c) |
| 71 | A4 | checked | 1.47× yes (06c0d5c); side by side no (bench/clamp.py) |
| 72 | A5 | checked | yes (c21024c); access order changed 2026-09-16 |
| 73 | A6 | checked | yes for latency (c21024c), protocol changed 2026-09-16; no for decompose |
| 74 | A7 | checked | post hoc (protocol 21e8e45, specified after E2) |
| 75 | A8 | checked | no (c3dfb0b) |
| 76 | A9 | checked | no (re-measurement of figures c3dfb0b never exported) |
| 77 | A10 | remove | yes (4b159d0) |
| 78 | A11 | remove | yes (4b159d0) |
| 79 | A12 | remove | yes (4b159d0) |
| 80 | A13 | checked | n/a (recomputed) |
| 81 | A14 | checked | n/a (derivation) |
| 82 | A15 | checked | n/a (derivation) |
| 88 | C1 | checked | operator yes (1c363bb); linear arms no (c560801) |
| 89 | C2 | checked | no (c560801) |
| 90 | C3 | checked | yes (1c363bb) |
| 91 | C4 | checked | yes (1c363bb); timings from the c560801 rerun |
| 92 | C5 | checked | unit yes (1c363bb); isometric yes (498d0ab) |
| 93 | C6 | checked | unit: operator yes, PCA arm no, E5 no; isometric yes (498d0ab) |
| 94 | C7 | checked | unit no (87d72cc); isometric yes (498d0ab) |
| 95 | C8 | checked | yes (498d0ab) |
| 96 | C9 | checked | yes (498d0ab) |
| 97 | C10 | checked | yes (498d0ab, descriptive) |
| 98 | C11 | checked | no (d12e03f) |
| 99 | C12 | checked | no (d12e03f) |
| 100 | C13 | checked | unit no (d12e03f); isometric post hoc (07255f7) |
| 101 | C14 | checked | post hoc (07255f7) |
| 102 | C15 | checked | no (d12e03f); cost columns redefined 2026-09-16 after the audit, recalls unchanged bit for bit |
| 103 | C16 | checked | yes (1c363bb); arm corrected 2026-09-16 after the code review |
| 104 | C17 | checked | no (52ab929) |
| 105 | C18 | checked | post hoc (07255f7) |
| 106 | C19 | construction | n/a |
| 107 | C20 | construction | n/a |
| 108 | C21 | construction | n/a |
| 109 | C22 | construction | n/a |
| 115 | P1 | checked | post hoc (computed during review before bench/poles.py existed) |
| 121 | R1 | remove | — |
| 122 | R2 | remove | — |
| 123 | R3 | remove | — |
| 124 | R4 | remove | — |

## 3. Registered question and refutation criteria

- **The question.** "Phase 1, revised 2026-09-13" (`paper/claims.md:5-12`). The superseded version, "approved
  earlier on 2026-09-13", is kept "for traceability" (`:30-36`). The first version entered with the registry in
  `2f8e532` (2026-09-13 13:59); the revision is `0981c1b` (2026-09-13 23:29).
- **What would refute it** (`paper/claims.md:14-21`):
  - F1: a method that re-centres by querying the corpus matches the re-anchored operator on local recall.
    Measured, does not hold: 0.023 against 0.543 (`:16-17`; rows C11, C12).
  - F2: a fixed map without re-centring matches it. Measured, does not hold: 0.056 (`:18-19`; C12).
  - Bound: the radial coordinate beats the operator. Measured, holds: 0.981 against 0.543 at unit scale, and
    against 0.925 in the exploratory isometric view (`:20-21`; C13).
- **What the revision changed.** No experiment: "every figure it rests on is already registered below"
  (`paper/claims.md:27-28`). The message gives the reason: the author's original motivation "turned out to
  organize the existing results better than the previous question did" (`0981c1b` message).
- **F3** is a robustness check, "not a refutation criterion" (`498d0ab` message). Its result is C8
  (`paper/claims.md:95`).

## 4. Registry history

Ten commits changed `paper/claims.md` (`git log -- paper/claims.md`). Each row below parses that commit's version
with the rule in §1 (`git show <hash>:paper/claims.md`). Where the verifier existed in that form, its tally agrees
(§7).

| Commit | Date | Rows | checked | not-in-ci | construction | remove | What changed |
|---|---|---:|---:|---:|---:|---:|---|
| `2f8e532` | 2026-09-13 | 33 | 28 | 1 | 0 | 4 | Registry created: A1–A13, C1–C15, P1, R1–R4 |
| `0b90772` | 2026-09-13 | 35 | 31 | 0 | 0 | 4 | C15 `not-in-ci` → `checked`; C16, C17 added; C11 28× → 29× |
| `5df86fe` | 2026-09-13 | 37 | 33 | 0 | 0 | 4 | A14, C18 added |
| `0981c1b` | 2026-09-13 | 37 | 33 | 0 | 0 | 4 | Question revised; F1, F2 and Bound added; no row changed |
| `8359755` | 2026-09-13 | 40 | 33 | 0 | 2 | 5 | `construction` status defined; C19, C20, R5 added |
| `57c5200` | 2026-09-14 | 40 | 33 | 0 | 3 | 4 | R5 resolved into C21 |
| `334ed1f` | 2026-09-14 | 41 | 34 | 0 | 3 | 4 | A15 added |
| `78973a4` | 2026-09-16 | 41 | 31 | 0 | 3 | 7 | A10–A12 `checked` → `remove` |
| `97e9306` | 2026-09-16 | 41 | 31 | 0 | 3 | 7 | C7 and C15 rewritten |
| `65c3ebf` | 2026-09-16 | 42 | 31 | 0 | 4 | 7 | C22 added; A1, A4–A9, C3, C4, C15, C16 rewritten |

- 43 distinct IDs have existed: the 42 current rows plus R5, which lived from `8359755` to `57c5200`.
- The registry has not changed since `65c3ebf`. The release tag `v1.0-paper` points to `f59430a`, a later commit
  (`git show-ref --tags`), so the registry at the release is the registry at `501c67f`.

## 5. Corrections and re-measurements

Three views of the same history: what the registry records, row by row (§5.1); the commits that rewrote a
committed result artifact (§5.2); and every commit whose message says it corrected something, with how it was
found (§5.3).

### 5.1 Recorded in the registry

Each entry gives the row and its current line, then each commit that changed it: date, old value → new value, and
the reason in the registry's or the message's words.

1. **C4, refit cost** (`paper/claims.md:91`)
   - `2f8e532`, 2026-09-13: §1 quoted 16.2–25.6 s against 0.072 s (226–356×), figures "that no committed
     drift.json contains". Replaced by 15.7–25.0 s against 0.051 s, 307–488× (`2f8e532` message;
     `2f8e532:paper/claims.md:61`). The old figures entered the manuscript in `2738884`
     (`git log -S'226–356' -- paper/polar-projector-paper.md`). The message calls this "the gap through which the
     refit cost below passed CI", closed by the presence check added in the same commit
     (`tools/verify_paper_tables.py:579-582`).
   - `65c3ebf`, 2026-09-16: re-timed "when drift.py was rerun": 12.6–24.9 s against 0.053 s, 240–474×
     (`paper/claims.md:91`).
2. **A9, clamp substitution** (`paper/claims.md:76`)
   - `b505d76`, 2026-09-13: the manuscript's clamp figures from `c3dfb0b` "were in no artifact": np.clip
     1.74 µs against 0.19 µs, 29% of the call, evaluate() 6.23 → 4.56 µs at 1.37×, and a scalar-form margin of
     1.23×. Re-measured as 1.88 against 0.23 µs, 30%, 6.34 → 4.54 µs, 1.40× (`b505d76` message;
     `2f8e532:paper/claims.md:48`). The message adds: "The historical 1.23x was itself misquoted: its artifact said
     1.2173."
   - `65c3ebf`, 2026-09-16: "re-measured 2026-09-16 with the corrected scalar arm": 1.37× (6.38 → 4.66 µs),
     1.86 against 0.23 µs, 29% (`paper/claims.md:76`).
3. **A4, scalar-form speed** (`paper/claims.md:71`)
   - `65c3ebf`, 2026-09-16: 1.47× (3.10 against 4.56 µs), with side-by-side margins of 1.24× and 1.45×
     (`97e9306:paper/claims.md:71`), became 1.39× (3.34 against 4.64 µs) and 1.18× under the old clamp. Reason:
     "the scalar arm previously skipped evaluate()'s input conversion and shape check, overstating it"
     (`paper/claims.md:71`).
   - The figure's earlier lineage, in messages: 1.23× (`e5d134d`), reproduced as 1.22× (`004db09`), 1.47× after
     the clamp change (`c3dfb0b`).
4. **A5, flatness in N** (`paper/claims.md:72`)
   - `0b90772`, 2026-09-13: 1.3% → 1.4% "(artifact 1.37%)", one of the misquotes the new verifier rows caught
     (`0b90772` message).
   - `65c3ebf`, 2026-09-16: 11.46–11.61 µs and 1.4% (`97e9306:paper/claims.md:72`) became 11.86–12.18 µs and
     2.7%, with stimuli in random order. "The earlier 11.46–11.61 µs and 1.4% came from a front-to-back scan that
     hides cache misses" (`paper/claims.md:72`).
   - Not a correction: `70940d1` (2026-09-14) explains why 1.4%, computed on unrounded values, differs from the
     1.3% a reader gets from the printed table.
5. **A6, prepare/evaluate split** (`paper/claims.md:73`)
   - `65c3ebf`, 2026-09-16: evaluate 4.57, project 11.75 and prepare 6.87 µs, 59.7%, 2.57×, 4.4× and 4.0×,
     64.0×, 0.4% (`97e9306:paper/claims.md:73`) became 4.66, 12.20 and 7.22 µs, 60.0%, 2.62×, 4.3× and 3.8×,
     63.5×, 0.9%. "Re-measured 2026-09-16 with random access order, a harness_null arm, and prepare() copying c_1
     and rejecting non-finite frames" (`paper/claims.md:73`).
   - Before the registry, `34b44b3` (2026-09-12) found that the decomposition script "timed a single pass while the
     paper claimed 'means over three runs, spread under 2%'". Four runs gave evaluate() at 4.61, 4.60, 4.66 and
     5.53 µs, a 20% spread. The commit "Fixed the measurement rather than the claim": three repetitions,
     median reported, spread held to 0.5% (`34b44b3` message).
6. **A7, dispatch share** (`paper/claims.md:74`)
   - `65c3ebf`, 2026-09-16: re-measured with dimensions rotated across repetitions. The ratio's rise at d = 8,192
     (2.46×, spread 16.4%) "is not explained by the sweep", and "the earlier 'memory effect' attribution (2.92×) is
     retracted" (`paper/claims.md:74`). The attribution dates from `c265abb` ("a 65 MB working set leaving
     cache"); 2.92× entered the manuscript in `c3dfb0b` (`git log -S'2.92×'`).
7. **C3, refit relocation** (`paper/claims.md:90`)
   - `65c3ebf`, 2026-09-16: t-SNE 1.03–1.24 and UMAP 0.31–1.25 became 1.03–1.55 and 0.31–1.52, "with Procrustes
     restricted to proper rotations ... reflections had been allowed" (`paper/claims.md:90`).
   - Earlier, `2738884` (2026-09-12) corrected "roughly the full width of the layout at every step": true of t-SNE
     but false of UMAP refit, "which has steps at 0.31, 0.64 and 0.67" (`2738884` message).
8. **C11, re-anchoring factor** (`paper/claims.md:98`)
   - `0b90772`, 2026-09-13: 28× (`2f8e532:paper/claims.md:68`) became 29×, the "ratio of unrounded means 29.07",
     also in the abstract, §1 and §5 (`0b90772` message).
9. **C15, costs of §3.5** (`paper/claims.md:102`)
   - `0b90772`, 2026-09-13: status `not-in-ci` → `checked` (`2f8e532:paper/claims.md:72`). "Three orders of
     magnitude cheaper than either PCA fit" became 121× and 1,618×, and a table cell 10,691 became 10,690 µs
     (artifact 10690.49997) (`0b90772` message).
   - `97e9306`, 2026-09-16: the frame_us column (42.8 / 5,156 / 69,178 µs, 121×, 1,618×) "mixed frame-only and
     frame-plus-view timings and left the neighbour scan out of the local PCA" (`paper/claims.md:102`), and
     "hard-coded 0 for radial" (`97e9306` message). Replaced by one operation per column: per query 16.3 against
     3,889 µs, 238×; a 581 ms codebook build, 9.1× the global PCA's 63.7 ms (`97e9306:paper/claims.md:102`).
     Recalls unchanged bit for bit (`paper/claims.md:102`).
   - `65c3ebf`, 2026-09-16: "Re-measured ... with each query frame timed 20 times per repetition": 16.4 against
     3,749 µs, 229×; 534 ms, 8.5× the global PCA's 63.2 ms (`paper/claims.md:102`).
   - The method notes name this cost column as one of two failures that passed several audits with CI green
     (`docs/METHODOLOGY.md:39-42`, in Spanish).
10. **C16, fit-once UMAP** (`paper/claims.md:103`)
    - `0b90772`, 2026-09-13: "fit-once UMAP relocates twice (0.39 and 1.07), not once", caught by the new verifier
      rows (`0b90772` message; `0b90772:paper/claims.md:73`). "Once" came from E1's results: still for 5 of 7
      steps, then a 1.07 relocation (`1e9d217` message).
    - `65c3ebf`, 2026-09-16: retracted. The arm "used to re-transform every earlier point with each batch, which
      produced the retracted 'intermittent relocation' (0.39 and 1.07)". It is now still at 7 of 7 steps, with
      trustworthiness 0.7730 and median lift 1.55× (`paper/claims.md:103`). Found by "the four-agent code review"
      (`65c3ebf` subject). C22 records the cause (`paper/claims.md:109`).
11. **C7, pole-selection rules** (`paper/claims.md:94`)
    - `97e9306`, 2026-09-16: "four leak-free rules" (`78973a4:paper/claims.md:94`) became "three label-free; the
      published rule reads the window's part labels, which lift also scores" (`paper/claims.md:94`), and "the
      1.17x is no longer a design rule" (`97e9306` message).
    - The method notes name this label leak as the second failure that passed audits with CI green
      (`docs/METHODOLOGY.md:42-43`).
12. **C18, re-anchored saturation** (`paper/claims.md:105`)
    - `5df86fe`, 2026-09-13: the author's draft of §2.1 said 0.70%; it was integrated as 0.68% and flagged
      exploratory (`5df86fe` message). No committed manuscript printed 0.70%
      (`git log -S'0.70%' -- paper/polar-projector-paper.md` returns nothing).
13. **C21, formerly R5** (`paper/claims.md:108`)
    - `8359755`, 2026-09-13: R5 registered as `remove`. Whether fit-once UMAP needs the stored corpus was "not
      established by any code or measurement here" (`8359755:paper/claims.md:122`).
    - `57c5200`, 2026-09-14: resolved by reading umap-learn 0.5.12's `UMAP.transform`. "The question was open only
      because nobody had read `transform()`" (`paper/claims.md:108`). The only prose edit was a §4.1 table cell,
      from "not established" to "yes, its own training set" (`57c5200` message).
14. **C22** (`paper/claims.md:109`): added in `65c3ebf` (2026-09-16). It records that `transform()` is not a pure
    function of each vector, the cause of the C16 retraction.
15. **A8** (`paper/claims.md:75`): `65c3ebf` added tests that call evaluate() itself; "the older expression test
    never called evaluate()".
16. **A1** (`paper/claims.md:68`): `65c3ebf` added the tests that reach Proposition 2's collinear fallback, "which
    the properties file never reaches".
17. **A10–A12** (`paper/claims.md:77-79`): `78973a4`, 2026-09-16, `checked` → `remove` (§6.1).

Checked rows changed while CI was green: the 9 rows whose figures `65c3ebf` changed (A4, A5, A6, A7, A9, C3, C4,
C15, C16) were all `checked` in the previous version (`97e9306:paper/claims.md:71-103`), and the verifier passed at
`97e9306` (277/277, §7).

### 5.2 Re-measurements

At `501c67f`, `bench/results/` holds 12 artifacts (`git ls-files bench/results`), each created once. Ten creations
were first measurements: `1e9d217`, `ef2977e`, `004db09`, `103dcb1`, `52ab929`, `87d72cc`, `d12e03f`, `07255f7`,
`dd9e5b5`, `49f33ff`. The table lists the rest: 2 creations that backed figures already published, and the 6
commits that rewrote existing artifacts, 14 file rewrites in all (`git log --name-status -- bench/results/`).

| Commit | Date | Files (A added, M modified) | Reason, from the message |
|---|---|---|---|
| `ad776cf` | 2026-09-11 | drift.json M | E1 re-run on the new shared harness; "every numeric result ... is bitwise identical"; only the envelope and wall-clock seconds changed |
| `c265abb` | 2026-09-11 | latency.json M | Adds the dimension sweep, specified after E2's results (`21e8e45`) |
| `c3dfb0b` | 2026-09-11 | conditioning.json M, latency.json M | Clamp substitution; latency figures "all re-measured rather than scaled"; every table of values unchanged |
| `34b44b3` | 2026-09-12 | decompose.json A | Exports "the one figure with no artifact"; doing so exposed the single-pass timing (§5.1, item 5) |
| `c560801` | 2026-09-12 | drift.json M, recall.json M | Two fixed linear arms added; "The five original arms reproduce bit-for-bit" |
| `b505d76` | 2026-09-13 | clamp.json A | Re-measures clamp figures "c3dfb0b never committed" (§5.1, item 2) |
| `97e9306` | 2026-09-16 | reanchor.json M | Cost columns redefined; "Recalls are bit-identical to the previous artifact" |
| `65c3ebf` | 2026-09-16 | clamp, conditioning, decompose, drift, latency, reanchor, recall: all M | Code-review fixes; "Timing artifacts were re-measured, so figures across §1, §3, §3.1, §3.5, §A and §B moved within noise" |

### 5.3 Every correction commit, and how it was found

**Inclusion rule.** A commit is listed when its message says that something already committed was wrong,
unbacked, misquoted, overstated or contradicted, and the commit changes it. "Something" means a figure, a claim,
a table cell, a check or a released file. Excluded: style, structure, length, build and licensing changes; new
results that do not say earlier text was wrong; clarifications such as `70940d1`. Borderline exclusions, which
the author may want to add back: `f59430a` (the abstract's opening reframed), `208104e` (code changed so that a
stated numpy-only property holds) and `c58004e` (author name in package metadata). Applied to all 89 commits, the
rule gives 37.

**Routes.** Each commit is coded from the words of its own message. The agent did the coding; the author should
confirm both the list and the routes before any of these counts is used.

**Not evidence (added after the framing discussion).** The agreed rule is that only code output is evidence and
anything an LLM wrote is a claim to verify. These routes rest on commit messages, and 64 of the 89 commits carry a
co-author trailer naming a Claude model (§7), so the route counts below are unverified claims. The replacement is a
code-only classification of each change (manuscript, artifact, script or operator), planned on top of the matrix in
`matrix/` (`matrix/README.md`).

- **Experiment:** a new or pre-registered measurement contradicted or narrowed the text.
- **Registry or verifier:** the presence check, new verifier rows, or a registry row (`remove` or "unregistered").
- **Manual review:** a full read, an audit, an editing pass, or review on integrating an author-written section.
- **Code review:** the four-agent code review.
- **Cross-host CI:** the first CI run on a second host.
- **External source:** reading a library's source, another repository, or bibliographic databases.
- **Artifact export:** writing a missing artifact exposed the problem. This happened while extending CI
  (`34b44b3` subject).
- **Not stated:** the message names no route.

| # | Commit | Date | What was corrected | The message's words on how | Route | Rows |
|---:|---|---|---|---|---|---|
| 1 | `4246c4f` | 2026-09-11 | §1's "no drift" narrowed to drift as a function of one caller-controlled variable | §3.4 "measures it" | Experiment | — |
| 2 | `afd62a5` | 2026-09-11 | Status block scoped to "Sections 4-7" in a document that ends at §6 | "terminology neutralization pass" | Manual review | — |
| 3 | `ef2977e` | 2026-09-11 | Latency table no longer left to imply a test of Proposition 1's O(d) claim | E2 results | Experiment | — |
| 4 | `c265abb` | 2026-09-11 | Microsecond figures: "Two consequences, both narrowing" | dimension sweep | Experiment | A7 |
| 5 | `103dcb1` | 2026-09-11 | Section 4.2's batching and energy-form assumptions: "two of which contradict what the section previously assumed" | E4 results | Experiment | A10–A12 |
| 6 | `e4049cd` | 2026-09-12 | Three unimplemented proposals, "a proposal wearing the clothes of a result" | "cut the manuscript" | Manual review | — |
| 7 | `2738884` | 2026-09-12 | "Roughly the full width ... at every step"; §3.2's zero stated at arithmetic resolution | — | Not stated | C3 |
| 8 | `34b44b3` | 2026-09-12 | Single-pass timing against a claimed mean of three runs | "Doing so exposed" | Artifact export | A6 |
| 9 | `087f245` | 2026-09-12 | "Thirteen corrections", three of them errors introduced by the preceding rewrites | "An audit of the whole manuscript" | Manual review | — |
| 10 | `c560801` | 2026-09-12 | Abstract and second contribution bullet "asserted an exclusivity this run disproves" | two fixed linear baselines | Experiment | C1, C2 |
| 11 | `6ec9528` | 2026-09-12 | The paper's central argument: "Three experiments say it cannot argue that" | E5–E7 | Experiment | — |
| 12 | `7c9e232` | 2026-09-13 | HCI premise restated as an inherited assumption, not a finding | — | Not stated | — |
| 13 | `bd4de9b` | 2026-09-13 | §3.5's mechanism ("The ablation refutes both") and §4's contradiction | E7 ablation, `07255f7` | Experiment | C13, C14, R4 |
| 14 | `6d62e35` | 2026-09-13 | Operator docstring claimed a bound "across every regime tested"; the benchmark measures up to 2.02 ε‖r‖ | — | Not stated | — |
| 15 | `b505d76` | 2026-09-13 | Clamp figures "in no artifact"; 1.23× misquoted | — (same timestamp as `2f8e532`) | Not stated | A9 |
| 16 | `2f8e532` | 2026-09-13 | Refit costs that no committed artifact contained | "the gap through which the refit cost ... passed CI" | Registry or verifier | C4 |
| 17 | `0b90772` | 2026-09-13 | Eight listed items, misquoted figures among them | "Those rows caught" | Registry or verifier | A5, C11, C15, C16, C17 |
| 18 | `5df86fe` | 2026-09-13 | Six corrections to the author's §2.1, 0.70% → 0.68% among them | "Corrections applied on integration" | Manual review | A14, C18 |
| 19 | `240f39d` | 2026-09-13 | Corrections to the author's §4.1 | "Corrections applied on integration" | Manual review | — |
| 20 | `77f1589` | 2026-09-13 | Corrections to the author's §4.2, two merged citations among them | "Corrections applied on integration" | Manual review | — |
| 21 | `b8ef523` | 2026-09-13 | Corrections to the author's §4.3, E8's pre-registration status among them | "Corrections applied on integration" | Manual review | — |
| 22 | `1eeab49` | 2026-09-14 | §3.5: what saturation accounts for | "the same misreading already fixed in §4.1" | Manual review | — |
| 23 | `d5d703a` | 2026-09-14 | R1 and two unregistered figures removed from §1 | "R1"; "the unregistered" | Registry or verifier | R1, R3 |
| 24 | `c697679` | 2026-09-14 | Corrections to the author's §5 | "Corrections applied on integration" | Manual review | — |
| 25 | `1e43c7f` | 2026-09-14 | "Relocates twice ... not once as the previous text said"; R1; a TODO citing an issue history that does not exist | "Removed: R1" | Registry or verifier | R1, C16 |
| 26 | `04cb4d2` | 2026-09-14 | "Errors the old abstract still carried after the body was corrected" | "Every figure is a registered string" | Registry or verifier | — |
| 27 | `cadcc3b` | 2026-09-14 | README §3.1 figures "brought in line with the manuscript" | — | Not stated | — |
| 28 | `53dae4d` | 2026-09-14 | §B cross-host tolerance widened from 0.5 to 2.0 decades | "First CI run on a real second host" | Cross-host CI | A2 |
| 29 | `dfeb42a` | 2026-09-14 | §1 implied that Traianus re-anchors on the query | "Checked against AlexusPacicus/Traianus" | External source | — |
| 30 | `a773513` | 2026-09-14 | "Two errors in Proposition 1's statement" | — | Not stated | A1 |
| 31 | `57c5200` | 2026-09-14 | §4.1 table cell "not established" → "yes, its own training set" | "Checked against installed umap-learn 0.5.12" | External source | C21 |
| 32 | `334ed1f` | 2026-09-14 | ‖r‖ presented as an unqualified stand-in for distance from the query | — | Not stated | A15 |
| 33 | `8f4b6ea` | 2026-09-15 | Author order of reference 9 | "Verifying all 21 references one by one against primary sources" | External source | — |
| 34 | `97e9306` | 2026-09-16 | §3.5 cost columns; label-leak caveat; sin θ fold and saturation explanations | "after the audit" (`paper/claims.md:102`) | Manual review | C7, C15 |
| 35 | `65c3ebf` | 2026-09-16 | Six findings "that changed published figures" | "the four-agent code review" | Code review | A1, A4–A9, C3, C4, C15, C16, C22 |
| 36 | `d7b354a` | 2026-09-16 | Upload zip "assembled by hand and had gone stale" | — | Not stated | — |
| 37 | `0b15002` | 2026-09-16 | Editorial scaffolding that "leaked into the v1.0-paper PDF" | — | Not stated | — |

Totals by route, 37 commits: Manual review 10 (#2, 6, 9, 18, 19, 20, 21, 22, 24, 34); Experiment 7 (#1, 3, 4, 5,
10, 11, 13); Registry or verifier 5 (#16, 17, 23, 25, 26); External source 3 (#29, 31, 33); Code review 1 (#35);
Cross-host CI 1 (#28); Artifact export 1 (#8); Not stated 9 (#7, 12, 14, 15, 27, 30, 32, 36, 37).

By date: 2026-09-11 5, 2026-09-12 6, 2026-09-13 10, 2026-09-14 11, 2026-09-15 1, 2026-09-16 4. Fifteen came before
the registry's creation commit (#1–#15) and 22 from it onward (#16–#37). The two failures the method notes single
out (`docs/METHODOLOGY.md:39-43`) are both in #34. The retracted C16 figures, which had passed the verifier, are in
#35.

## 6. Claims removed from the manuscript

### 6.1 Registry rows with status `remove`

| Row | Claim (shortened) | Reason given | Removed in | Absent at `501c67f`? |
|---|---|---|---|---|
| A10 (`paper/claims.md:77`) | Batching peaks at 5.16× (B = 256), is 0.39× at B = 1, and is non-monotone | "out of scope for the registered question — `evaluate_batch()` is never used by any §3 result"; "removed from Appendix D, phase 5" | `78973a4` (2026-09-16) | Yes: the appendix headings are A, B and C only (`paper/polar-projector-paper.md:1087`, `:1141`, `:1194`) |
| A11 (`paper/claims.md:78`) | Batched agreement bounds (≤ 0.19 ε in λ, ≤ 2.02 ε‖r‖ in d_esc) | "same as A10" | `78973a4` | Yes |
| A12 (`paper/claims.md:79`) | The square root costs 1.0–1.6%, so the energy form is not worth shipping | "same as A10" | `78973a4` | Yes |
| R1 (`paper/claims.md:121`) | λ is a bounded coordinate between two named poles | "contradicted by P1", which puts the poles at +0.182 and −0.818 (`paper/claims.md:115`) | `d5d703a` (§1), `c697679` (§5), `1e43c7f` (§6), per their messages | Yes: no match for "named pole", "bounded coordinate" or "interpretable" |
| R2 (`paper/claims.md:122`) | (λ, d_esc) is consumed as a planar position by at least one system | "the system this operator came from renders (λ, ⟨v, ĉ₁⟩)" | `0b90772` (§3 prose), per its message | The claim is not found. Lines 298 and 516 of the manuscript describe the paper's own screen mapping, not a system using it; a judgment call |
| R3 (`paper/claims.md:123`) | The O(N²) force-simulation column and the SQLite deployment figures | "reproduced by no code in this repository" | `0b90772` (§3); the SQLite paragraph of §1 in `d5d703a` | Yes: no match for "SQLite", "force-sim" or "O(N²)" |
| R4 (`paper/claims.md:124`) | Determinism is the paper's contribution | "removed from §4 in bd4de9b" | `bd4de9b` (2026-09-13) | Yes: "determinis*" occurs on 11 lines, each describing a property (`grep -n -i determinis`) |

- Absence was checked in this session by text search only. The verifier does not check `remove` rows
  (`tools/verify_paper_tables.py:656-657`).
- The Source cells of R1 and R2 still say "currently in §1 ..., §5 and §4.3" and "currently in §2.1 and §3.2"
  (`paper/claims.md:121-122`), although the commits above removed those passages. See §9.
- R5 was removed from the registry, not from the manuscript: registered in `8359755`, resolved into C21 in
  `57c5200` (§5.1, item 13).

### 6.2 Removed according to the git history, with no registry row

| Commit | Date | What was removed | Reason given in the message |
|---|---|---|---|
| `103dcb1` | 2026-09-11 | The energy form E_esc, "withdrawn rather than shipped" | The square root's saving is "1.0-1.6% ... inside the run-to-run spread" |
| `e4049cd` | 2026-09-12 | Multi-axis tangent frame and tripolar model, adaptive delta calibration, active-codebook eviction | "None is implemented in projector.py and none supported a contribution the paper claims" |
| `087f245` | 2026-09-12 | That the baselines scale quadratically; that Proposition 2 covers an unrepresentative anchor | "Barnes-Hut t-SNE is O(N log N)"; "the fallback handles a collapsed contrast axis, not a badly placed origin" |
| `0b90772` | 2026-09-13 | "Statistically indistinguishable"; the 5.53 µs throttled pass; "three orders of magnitude cheaper" | "had no test behind it"; "in no artifact"; replaced by 121× and 1,618× |
| `d5d703a` | 2026-09-14 | "Every other stable arm falls to chance"; "a linear projection reorients but cannot recentre"; the unregistered "5.2 ms" and "69 ms" | "fit-once UMAP holds 1.12x"; the other two not stated beyond "unregistered" |
| `1e43c7f` | 2026-09-14 | "The least representative point of both"; a TODO note | The TODO cited "a repository issue history that does not exist" |
| `04cb4d2` | 2026-09-14 | Six errors the old abstract still carried | "after the body was corrected" |
| `dfeb42a` | 2026-09-14 | "It is the navigation primitive these requirements describe" | Traianus "picks the anchor and poles ... never from the consulted note" |
| `97e9306` | 2026-09-16 | The 1.17× as a design rule | "the published pole rule reads the part labels that lift scores" |
| `65c3ebf` | 2026-09-16 | §4.3's jumps-versus-drift question; the d = 8,192 "memory effect"; Appendix C's normal-theory sampling bound | The re-transform behind the jumps; the sweep does not explain the rise; no reason given for the bound |
| `78973a4` | 2026-09-16 | Appendix D and the Conclusion's batching bullet | `evaluate_batch()` "supports no result in §3 and no claim in the registered question" |
| `0b15002` | 2026-09-16 | Editorial scaffolding: mirror link, provenance, DRAFT status, CI description | It "leaked into the v1.0-paper PDF, whose build did not yet strip them" |

## 7. The verifier and CI

- **When it runs.** On pushes to `main` and on pull requests (`.github/workflows/ci.yml:3-6`), in the quality job
  (`:50-51`), on Python 3.11 (`:35`) with `.[test,repro]` (`:40`). That pins numpy 2.4.1 (`pyproject.toml:31`)
  and leaves out the `bench` extra (`pyproject.toml:35`). CI therefore compares the manuscript with committed
  artifacts and recomputes only Appendices B and C; it "does NOT re-derive" the rest
  (`tools/verify_paper_tables.py:676-677`). It reads 11 of the 12 artifacts in `bench/results/`; the exception is
  `batched.json`, whose rows A10–A12 were removed (`tools/verify_paper_tables.py:257-535`, every `_load` and
  `RESULTS /` call).
- **What it checks.** `README.md:114-122`. Its declared limit: "It cannot catch a benchmark that measures something
  other than what the paper says it measures" (`README.md:124-125`). The presence check is "a presence check, not a
  location check" (`tools/verify_paper_tables.py:584-586`; also `paper/claims.md:61-62`).
- **Sizes at `501c67f`** (`wc -l`): the verifier is 735 lines; the operator package 533 (`projector.py` 432);
  tests 1,389 lines, with 800 tests collected (`pytest --collect-only`); `bench/*.py` 3,135 lines; the manuscript
  1,218 lines; the registry 138. `docs/ARCHITECTURE.md:13-17` and `:35` quote the same figures except the
  manuscript's (§9).
- **Verifier at `501c67f`.** ALL PASS: 281/281 figures agree with their artifact; 261 present, 0 absent, 0 awaiting
  text and 20 single-character; registry 31 checked, 4 construction, 7 remove. The scalar-form error at
  d_esc/‖r‖ = 1e-7 came out at 1.180e-03 against the published 1.2e-03.
- **Figures under check over time.** Every row is the verifier at that commit, re-run in this session; every run
  printed "ALL PASS". The counts agree with those the messages state (`34b44b3` 112, `087f245` 113, `6ec9528` 165,
  `07255f7` 183, `2f8e532` 256, `0b90772` 302, `5df86fe` 303 with 280 locatable, `78973a4` 267).

| Commit | Date | Artifact figures | Present / awaiting / single-character | Registry tally |
|---|---|---:|---|---|
| `004db09` | 2026-09-11 | — (10 table rows recomputed: 4 conditioning, 6 δ-sweep) | — | — |
| `34b44b3` | 2026-09-12 | 112 | — | — |
| `087f245` | 2026-09-12 | 113 | — | — |
| `c560801` | 2026-09-12 | 113 | — | — |
| `6ec9528` | 2026-09-12 | 165 | — | — |
| `07255f7` | 2026-09-13 | 183 | — | — |
| `2f8e532` | 2026-09-13 | 256 | 218 / 17 / 21 | 28 checked, 1 not-in-ci, 4 remove |
| `0b90772` | 2026-09-13 | 302 | 272 / 7 / 23 | 31 checked, 4 remove |
| `5df86fe` | 2026-09-13 | 303 | 280 / 0 / 23 | 33 checked, 4 remove |
| `78973a4` | 2026-09-16 | 267 | 245 / 0 / 22 | 31 checked, 3 construction, 7 remove |
| `97e9306` | 2026-09-16 | 277 | 256 / 0 / 21 | 31 checked, 3 construction, 7 remove |
| `65c3ebf` | 2026-09-16 | 281 | 261 / 0 / 20 | 31 checked, 4 construction, 7 remove |
| `f59430a` (`v1.0-paper`) | 2026-09-16 | 281 | 261 / 0 / 20 | 31 checked, 4 construction, 7 remove |
| `501c67f` | 2026-11-02 | 281 | 261 / 0 / 20 | 31 checked, 4 construction, 7 remove |

- **The `AWAITING_TEXT` exception** has been empty since `5df86fe` (`tools/verify_paper_tables.py:593`; `5df86fe`
  message: "AWAITING_TEXT is now empty").
- **The verifier's own history.** 16 commits changed it under either of its two names: `e5d134d` and `ff1b39f` as
  `tools/verify_polar_delta_table.py`, renamed in `004db09`, then `c3dfb0b`, `e4049cd`, `34b44b3`, `087f245`,
  `6ec9528`, `07255f7`, `2f8e532`, `0b90772`, `5df86fe`, `53dae4d`, `78973a4`, `97e9306` and `65c3ebf`
  (`git log -- tools/verify_polar_delta_table.py`; `git log --follow -- tools/verify_paper_tables.py`).
- **Time span.** From the manuscript's first commit (`e5d134d`, 2026-09-11) to the release tag (`f59430a`,
  2026-09-16), 78 commits inclusive, 54 of which touch the manuscript (`git rev-list --count e5d134d^..f59430a`,
  with and without `-- paper/polar-projector-paper.md`). The repository has 89 commits in all.
- **Authorship record.** All 89 commits have the same author account (`git log --format=%an | sort | uniq -c`).
  64 carry a `Co-Authored-By:` trailer naming a Claude model and 25 carry none
  (`git log --grep='^Co-Authored-By:' --format=%h | wc -l`). No commit carries a `Human-Record` trailer, which the
  brief introduces for Phase 1 (`method-paper/BRIEF.md:61-62`). The trailers are declarations, as the brief says of
  its own `Human-Record` trailer (`method-paper/BRIEF.md:87`). The manuscript states what AI assistants were used
  for (`paper/polar-projector-paper.md:1003-1011`).

## 8. Pre-registration evidence

The registration mechanism is commit order on the public remote: "protocol committed before its results"
(`paper/claims.md:53`). Six protocol commits are cited as `yes`. In each pair the protocol commit is the direct
parent of the results commit (`git rev-list --count <protocol>..<results>` = 1). Gaps are author-time differences
(`git show -s --format=%at`).

| Experiment (where in the manuscript) | Protocol | Results | Gap | Rows citing the protocol |
|---|---|---|---:|---|
| E1 drift (§3.2) | `1c363bb` | `1e9d217` | 384 s | C1, C3, C4, C5, C16 (`paper/claims.md:88`, `:90-92`, `:103`) |
| E2 latency (§3.1) | `c21024c` | `ef2977e` | 160 s | A5, A6 (`:72-73`) |
| E2 dimension sweep (Appendix A) | `21e8e45` | `c265abb` | 49 s | A7, labelled post hoc (`:74`) |
| E3 conditioning (Appendix B) | `06c0d5c` | `004db09` | 125 s | A2, A3, A4 (`:69-71`) |
| E4 batched (former Appendix D) | `4b159d0` | `103dcb1` | 113 s | A10, A11, A12 (`:77-79`) |
| E8 declared scale (isometric columns of §3.2–§3.4) | `498d0ab` | `dd9e5b5` | 348 s | C5, C6, C7, C8, C9, C10 (`:92-97`) |

- **Where the experiments landed** comes from messages: `ef2977e` ("Adds section 3.1.1"); `e4049cd` (sweep to §A,
  conditioning to §B, δ-sweep to §C, batching to §D); `0b90772` (isometric columns).
- **Committed with their results** (`no`): the linear arms (`c560801`), E5 (`52ab929`), E6 (`87d72cc`), E7
  (`d12e03f`), the clamp change (`c3dfb0b`) and its re-measurement (`b505d76`). **Post hoc:** P1 (`49f33ff`) and the
  E7 ablation (`07255f7`).
- **Smoke runs before a protocol commit are disclosed:** `c21024c` ("It was used, and it writes no result file"),
  `4b159d0` ("A --smoke run ... verified execution and wrote nothing") and `498d0ab` ("it printed no metric and wrote
  nothing").
- **E1's aggregation changed after its first run.** Across-step means became median and worst step: "The
  aggregation was changed to median/worst after the first run showed this" (`1e9d217` message; compare
  `1c363bb:bench/drift.py` with `1e9d217:bench/drift.py`). The E1 rows' labels read "yes (1c363bb)" with no note of
  this (`paper/claims.md:88`, `:90-92`, `:103`).
- **Shared timestamps.** Three groups of commits share an author timestamp: `07255f7`, `bd4de9b` and `6d62e35`
  (2026-09-13 12:51:03); `b505d76` and `2f8e532` (13:59:23); `faf2f10` and `501c67f` (2026-11-02 13:36:01). None is a
  protocol/results pair. Git timestamps are set by the committer, so the evidence of order is the commit graph, not
  the clock.

## 9. Observations for the author

Found while extracting the data above and not acted on: the Polar Projector paper and its registry are out of
scope (`method-paper/BRIEF.md:93-94`). Each item is a candidate, with the evidence to check it.

1. **The manuscript's pre-registration sentence may disagree with the registry.**
   `paper/polar-projector-paper.md:902-908` says the protocols of "§3.2, Appendices A–C, and the isometric-scale
   rerun" were committed before their results.
   - Appendix C is the δ-sweep (`paper/polar-projector-paper.md:1194`), whose row is "n/a (recomputed)"
     (`paper/claims.md:80`). Its script entered with the manuscript in `e5d134d`, with no protocol commit.
   - §3.1, whose rows are "yes (c21024c)" (`paper/claims.md:72-73`), is not listed.
   - "Appendix A's dimension sweep was specified after its own results" differs from `21e8e45`, which was
     specified after E2's results and "Committed before running", and from `paper/claims.md:74`.
   - Origin: `5fe2a25` replaced "The protocols of E1–E4 and E8" with section references, using the mapping
     "E4=Appendix C" (`5fe2a25` message). At that commit Appendix C was the δ-sweep and Appendix D held the batched
     evaluation, which was E4 (`5fe2a25:paper/polar-projector-paper.md:1216`, `:1243`; `4b159d0` subject).
   - This sentence is prose about provenance, which the verifier does not check.
2. **Stale Source cells.** R1 and R2 say "currently in ..." (`paper/claims.md:121-122`), but those passages were
   removed (§6.1).
3. **Undefined labels.** `n/a` (8 rows) and `—` (4 rows) are used but not defined in `paper/claims.md:52-56`.
4. **A protocol change not shown in the labels.** E1's aggregation changed after its first run (§8).
5. **An unbacked number in the method notes.** `docs/ARCHITECTURE.md:15` gives the manuscript as 1,222 lines. At
   `501c67f` it has 1,218 (`wc -l`), and none of the 56 committed versions has 1,222
   (`git log -- paper/polar-projector-paper.md`, `wc -l` per version). The diagram's other four line counts, its
   test count and the verifier's 735 lines (`docs/ARCHITECTURE.md:35`) match (§7).
6. **Stale labels around the checks.** The CI step is named "Paper tables still reproduce (§3.2, §3.3)"
   (`.github/workflows/ci.yml:50`); those tables are now Appendices B and C (`tools/verify_paper_tables.py:5-7`).
   The module docstring still opens "Two tables are guarded" (`tools/verify_paper_tables.py:3`) and calls Appendix B
   "Section 3.2" (`:12`). The run prints "tolerance: 0% relative per cell" (`:694` formats `RTOL = 1e-3`, `:64`);
   the docstring says 0.1% (`:11-12`).
7. **Changes after the release tag.** `v1.0-paper` points to `f59430a`. `3ca439c` and `0b15002` changed the
   manuscript afterwards, and `0b15002` says the scaffolding "leaked into the v1.0-paper PDF". The verifier gives
   identical counts at `f59430a` and `501c67f` (§7).
8. **Inconsistent experiment labels.** `5fe2a25` notes that "bench/reanchor.py's own docstring and commit 87d72cc
   disagree on whether frame_sensitivity is E5 or E6".
9. **The question was revised after its results existed** (`0981c1b`, §3), for the stated reason that it
   organizes them better. The general method notes, written later (`501c67f`, 2026-11-02), allow reformulation only
   after a refuter held (`docs/METHODOLOGY.md:24-27`, in Spanish). The method paper may want to describe the
   revision as it happened.

## 10. Commit index

Every commit cited in this file: short hash, full hash, author date, subject (`git log`).

| Short | Full hash | Date | Subject |
|---|---|---|---|
| `e5d134d` | `e5d134d63c54a653dcf52bd1ba38bd0fa349c61e` | 2026-09-11 | docs(papers): add Polar Projector manuscript with committed reproducibility tooling |
| `ff1b39f` | `ff1b39f9483d924e97880b989c954379f962cf6a` | 2026-09-11 | build: make the extracted operator a standalone numpy-only package |
| `1c363bb` | `1c363bbf3c7fe421714c0e0e30d9e76c8547273a` | 2026-09-11 | bench: E1 drift study design and frozen corpus, before any results |
| `1e9d217` | `1e9d2178cb190d0e1a2ec307c0e1729ab5f8d036` | 2026-09-11 | bench: E1 drift results — stability is real, and it is paid for |
| `4246c4f` | `4246c4f3687df56210a1f4ab55c9e01cfb2da74c` | 2026-09-11 | docs(paper): fold the E1 drift study into the manuscript, including what it costs us |
| `afd62a5` | `afd62a5d36a7c573064c9d05d165e7d0dead71ee` | 2026-09-11 | docs: close the terminology neutralization pass across the repository |
| `ad776cf` | `ad776cfd8d0bb73267ffb43a434549fde710ae7e` | 2026-09-11 | bench: shared measurement harness for the E1-E4 suite |
| `c21024c` | `c21024c73d8149f7fc4c492fcf649120d540fcb0` | 2026-09-11 | bench: E2 latency protocol and arms, before any results |
| `ef2977e` | `ef2977e898c1d2589beb25a0765cc417ce519c22` | 2026-09-11 | bench: E2 latency results — the operator is 6x the floor, and the microseconds are not measuring what they appear to |
| `21e8e45` | `21e8e459940aac2f870796846d3169d49592453c` | 2026-09-11 | bench: dimension sweep for E2, before any results |
| `c265abb` | `c265abb67035daa96b2e7c89e598de6b1da51cd1` | 2026-09-11 | bench: dimension sweep results — 88% of the per-call cost at d=384 is not d |
| `06c0d5c` | `06c0d5c6570ddbf734b8da0fd4f791590fdbd986` | 2026-09-11 | bench: E3 conditioning protocol, before any results |
| `004db09` | `004db09fcb2f0ae663e48d5be629e73ea83ad202` | 2026-09-11 | bench: E3 results — the scalar form's failure is undetectable, not merely large |
| `c3dfb0b` | `c3dfb0b4580b7b6c31b62d9e4e92bf1a87622082` | 2026-09-11 | feat(geometry): clamp lambda with min/max — 1.37x faster, bit-for-bit identical |
| `4b159d0` | `4b159d0a47aea468b47754181c25641e63247b03` | 2026-09-11 | bench: E4 batched protocol, before any results |
| `103dcb1` | `103dcb1defab7af27d3379ae7733f87c6677623c` | 2026-09-11 | bench: E4 results — batching peaks at 5.2x and then gets worse, and the sqrt is free |
| `208104e` | `208104e43f5e0c2d2e836e72e4addf5249c508c0` | 2026-09-11 | fix(bench): polar arms of E1 no longer require scikit-learn |
| `52ab929` | `52ab9291ee653330552fc10bdbea5e0c60d02d3c` | 2026-09-12 | bench: E5 same-part retrieval — the fidelity gap survives a second instrument |
| `e4049cd` | `e4049cd97f3198e16fde8c69d4994f3ba813f555` | 2026-09-12 | docs(paper): cut the manuscript to the navigation core |
| `2738884` | `2738884575d41a023f907166ba98b3fcbcf96c33` | 2026-09-12 | docs(paper): reframe around the two constraints a spatial PKM actually imposes |
| `34b44b3` | `34b44b3fccc185fa3a0fcddf25337993e71de4e1` | 2026-09-12 | docs(paper): 20 verified references, and extend CI to 112 published figures |
| `087f245` | `087f245f05ef8c8e1e9dbecd8e42e219bdea877e` | 2026-09-12 | docs(paper): thirteen corrections from a full read of the manuscript |
| `c560801` | `c560801a22ca70b57bab5c3f940bc3615f0f2854` | 2026-09-12 | bench: two fixed linear baselines — exact stability turns out to be free |
| `87d72cc` | `87d72cc841f092b836929f80f5a6a3fb8d95b7aa` | 2026-09-12 | bench: E6 frame sensitivity — the pole-selection rule is a knob, not a detail |
| `d12e03f` | `d12e03fc3a83ba9e819ee360cfb3f18cced04cc6` | 2026-09-12 | bench: E7 re-anchoring — the movable origin is the value, and a radial baseline still wins |
| `6ec9528` | `6ec95283a0e402def7bb04a32402a0ef2ae5d7f0` | 2026-09-12 | docs(paper): rewrite as a measured account of a design space |
| `7c9e232` | `7c9e23264a929870942cbec0deb44a2e3941b339` | 2026-09-13 | docs(paper): state the HCI premise as an inherited assumption, not a finding |
| `07255f7` | `07255f7c053a39e6072872b6848ed367da1ea305` | 2026-09-13 | bench: E7 ablation — the re-anchored operator's recall gap is units, not information |
| `6d62e35` | `6d62e35a02e7870bb0dfabdc47ae3abfbf80d1ba` | 2026-09-13 | docs(geometry): stop presenting the batched agreement bound as proven |
| `bd4de9b` | `bd4de9ba99d63f2acfbc208d6444ca7654a7732e` | 2026-09-13 | docs(paper): correct §3.5's mechanism and §4's contradiction — frozen state, not final prose |
| `498d0ab` | `498d0ab695cfc26759f11e91876436f0234d311c` | 2026-09-13 | bench: E8 declared-scale protocol, before any results |
| `dd9e5b5` | `dd9e5b570892e7dab61c32a35e75b7361bc7a09c` | 2026-09-13 | bench: E8 results — the declared scale barely moves §3.2-§3.4, and no ordering changes |
| `49f33ff` | `49f33ff57b14017706541dab6aa2983b479ce2e3` | 2026-09-13 | bench: P1 — the named poles sit at +0.182 and -0.818, exactly as two parts predict |
| `2f8e532` | `2f8e532a42151a03f37ff7ab14d9a6e4d9724673` | 2026-09-13 | docs(paper): phase 2 — claims registry, manuscript-presence check, and C4 corrected |
| `b505d76` | `b505d76edc2f8e8a96e1f65be032ad5dc46026da` | 2026-09-13 | bench: A9 — re-measure the lambda clamp and export figures c3dfb0b never committed |
| `0b90772` | `0b9077263999bf1db6349c1fd1f056ea34515efc` | 2026-09-13 | docs(paper): phase 4 — §3 tables at both scales, §3 prose, and the figures its new rows caught |
| `5df86fe` | `5df86fe77701f6539d5f904a6d2ffbc5c9f1aa6e` | 2026-09-13 | docs(paper): §2.1 rewritten by the author, with its claims under test |
| `240f39d` | `240f39d092086112ef1610b28e937338c7d7fedc` | 2026-09-13 | docs(paper): §4.1 written by the author; §4 cut to its agreed shape |
| `77f1589` | `77f15895c2c8f7fe4397639918443842bf9d8e6d` | 2026-09-13 | docs(paper): §4.2 written by the author — prior work, with semantic axes added |
| `b8ef523` | `b8ef5236d2b7e03065dacb753cde5256d3b7b6f5` | 2026-09-13 | docs(paper): §4.3 written by the author — limitations, completing §4 |
| `0981c1b` | `0981c1b835ffe312666fbd6902872626df7e699e` | 2026-09-13 | docs(paper): phase 1 revised — the question is decoupling interaction from corpus state |
| `8359755` | `835975544562f8209f7336249a02fe12ed7d20e8` | 2026-09-13 | docs(paper): phase 2 for the revised question — construction facts get a status of their own |
| `1eeab49` | `1eeab49996baa91430dcd9fc3936e6b855443bd2` | 2026-09-14 | docs(paper): §3.5 and §4.1 read through the revised question — re-centring without re-coupling |
| `d5d703a` | `d5d703abb66c023e2fca5fa7290bacd58e8d796e` | 2026-09-14 | docs(paper): §1 rewritten around the revised question — decoupling, then re-centring |
| `c697679` | `c697679dbbd92767aa137b3209e92af079d360a6` | 2026-09-14 | docs(paper): §5 written by the author around the revised question |
| `1e43c7f` | `1e43c7f08b00f2e3b0c7206c826f3ead2a1653ef` | 2026-09-14 | docs(paper): §6 rewritten — open questions ordered from usefulness down |
| `04cb4d2` | `04cb4d289a7e4f4f70ebf07386247af073e29429` | 2026-09-14 | docs(paper): title and abstract for the revised question |
| `cadcc3b` | `cadcc3b335106f0635d5256059be76a7e06cb3dc` | 2026-09-14 | build: generate arXiv LaTeX from the Markdown manuscript, one way |
| `c58004e` | `c58004e33460881e1b4b018f8e17fb7e9dc52267` | 2026-09-14 | build: align author name with the manuscript byline, wire in Contact |
| `53dae4d` | `53dae4d4496a355088af5a6c7be9334291222e4f` | 2026-09-14 | fix(verify): widen §B's cross-host tolerance from 0.5 to 2.0 decades |
| `dfeb42a` | `dfeb42a0694e17fecbf050f6d3424b169f9aee4c` | 2026-09-14 | docs(paper): stop implying Traianus re-anchors on the query (§1) |
| `a773513` | `a773513c67b44f0fcb0fc53f805f0d08be016418` | 2026-09-14 | docs(paper): fix P_perp's codomain and stop overspecifying Prop 1's poles |
| `70940d1` | `70940d158baac486e9955b26ff9322b04c298c52` | 2026-09-14 | docs(paper): explain why 1.4% and the printed table give different spreads |
| `57c5200` | `57c520072609eafa5bd67e86a7b2d11b174bc544` | 2026-09-14 | docs(claims): establish that UMAP fit-once reads the corpus at transform() |
| `334ed1f` | `334ed1f90b5a06e1bb5ab4c772a2577dca550e57` | 2026-09-14 | docs+test(A15): the re-anchored \|\|r\|\| folds at 90 degrees, radial doesn't |
| `5fe2a25` | `5fe2a25a7e42c0be9f742da5f65d49821816f4d1` | 2026-09-14 | docs(paper): replace E1-E8 experiment labels with section references (§4.3) |
| `8f4b6ea` | `8f4b6ea62d0a99ff70714a3e22598b0f424609c9` | 2026-09-15 | docs(refs): fix author order on Espadoto et al. (2021) |
| `78973a4` | `78973a4c4a1984d9e40b1ff416bd1a75ced4de34` | 2026-09-16 | docs(paper): trim the manuscript for length before arXiv submission |
| `97e9306` | `97e9306bd6c51192608c634eacf5e0666f8077be` | 2026-09-16 | docs(paper): close v1 — corrected §3.5 costs, label-leak caveat, declarations |
| `65c3ebf` | `65c3ebf9531ad6166086119bfa7a304fa396e485` | 2026-09-16 | fix: resolve the four-agent code review across operator, benchmarks and verifier |
| `d7b354a` | `d7b354a7ad358d5362a847c13b92a225987d9847` | 2026-09-16 | build(paper): write the upload zip from every build |
| `f59430a` | `f59430a027355a514df846916ba0bef6d35af322` | 2026-09-16 | docs(paper): open the abstract with the two requirements, not a diagnosis |
| `3ca439c` | `3ca439caa22684b2122537878d9af66733afacc6` | 2026-09-16 | chore(release): relicense to Apache-2.0/CC BY 4.0, fix byline, add citation metadata |
| `0b15002` | `0b15002640f9e3024fa2d1de8a9cf4191346dab2` | 2026-09-16 | docs(paper): strip the editorial note and set Algorithm 1 in LaTeX math |
| `501c67f` | `501c67f425a262d27bc8dd3ec503aea118cfa9d0` | 2026-11-02 | docs: add notes on the working method and the evidence pipeline |
| `faf2f10` | `faf2f103f54b62ba0bb154702e53db4bb6b0d733` | 2026-11-02 | docs(method-paper): pre-register the brief for the method paper |
