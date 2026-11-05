# Method paper: brief and pre-registration

Committed by the author on 2026-11-02, before any work on the method paper starts. Drafted with Claude (claude.ai);
reviewed, edited and committed by the author. Updated by the author on 2026-11-05, day 1, before Phase 1 counting
starts, from a draft by Claude (`prep/brief-update-draft.md`). Agents working in this repository read this file before
doing anything for the method paper, and do not modify it.

## Goal

**Primary.** A new paper of about 1,500 words, with one table, on how the Polar Projector paper kept every number tied
to evidence: the claims registry, the pre-registration labels, the refutation criteria and the verifier that runs in
CI. It covers the method, the case and the limits. The Polar Projector paper is the case. It is not modified.

**Secondary.** Write the new paper with Actuarii governing the writes, and report what it recorded. This is a pilot
observation, not a test of anything.

**Deliverable.** The paper in this repository, with a Zenodo DOI. A forum post goes out with the DOI; without a DOI
there is no post.

## Layout

```
method-paper/
  BRIEF.md      this file
  prep/         Phase 0 output
  paper.md      the new paper
  claims.md     its claims registry: one row per number in paper.md
```

## Phases

**Phase 0: preparation.** Cloud session, until 2026-11-04. Not governed by Actuarii: the Bash sandbox that Actuarii
requires does not run in cloud sessions.

- It was read-only on every existing file, and its output went only to `method-paper/prep/`.
- That output reached `main` by fast-forward on 2026-11-04, with the author's approval. The branch
  `prep/method-paper` was then deleted, and the history keeps its commits.
- Beyond its three tasks, it produced specifications for references and for a traceability matrix, a blind sample,
  and a run of the exploratory matrix on the release. All of these are deferred (`prep/outline.md`, decisions 20
  and 21).
- The paper declares this phase as agent work outside the governed channel, including what it produced beyond its
  tasks.

**Phase 1: writing.** Local and governed, from 2026-11-05. The target for publication is 2026-11-06. The limit is
2026-11-11, the fifth working day.

- **Day 1:**
  - install Actuarii and govern the paths listed below;
  - confirm the measurement section of this file;
  - start `claims.md` and make the verifier's minimal change;
  - writing.
- **Day 2:** writing, then verify, and publish as it stands if it is ready.
- **Up to day 5:** the same, and publish as it stands by then.
- During Phase 1 there are no merges, only fast-forward.

## Phase 0 tasks

Done on 2026-11-04. The links in `related-work.md` were confirmed by the author on 2026-11-05. All open except two
secondary copies, in references 2 and 3, whose DOIs open.

Produce three files in `method-paper/prep/`. Every number in them cites the file and line, or the commit, it comes
from.

1. `case-data.md`: the claims in `paper/claims.md` counted by status and by pre-registration label; every correction
   or re-measurement, with its date, commit hash and reason, taken from the registry and the git history; and the
   claims removed from the manuscript, with the reason given.
2. `related-work.md`: 5 to 8 candidate references on reproducible research, verifiable artifacts and executable
   papers, each with a working link and one line on how it relates. Mark any reference you could not verify.
3. `outline.md`: an outline for five pages, about 2,500 words, with a word budget per section.

Do not modify any existing file. Do not write outside `method-paper/prep/`.

## Roles in Phase 1

**The agent** keeps `method-paper/claims.md` (one row per number in the paper), runs the verifier, extracts and
recomputes numbers, proposes cuts and structure, and drafts the technical parts: tables and the description of the
method. Every write goes through the governed channel.

**The author** decides what goes in; writes in his own words the introduction, the contribution, the limits and the
conclusion; reviews or rewrites the agent's drafts; approves every number; and marks his own commits with the trailer
`Human-Record: author`.

The paper states who did what.

## Governed paths in Phase 1

- `method-paper/BRIEF.md`
- `method-paper/paper.md`
- `method-paper/claims.md`
- `tools/verify_paper_tables.py`

Actuarii's installer also always governs `.actuarii.json`, `AGENTS.md`, `CLAUDE.md`, `.claude/**`, `.mcp.json` and
`tools/**`. `tools/**` covers the verifier, because the installer copies the kit into `tools/`.

Outside these paths, Phase 1 changes `pyproject.toml` once: it excludes the kit from ruff, which CI runs over
`tools/`. That change comes before the first push.

## Measurement (pre-registered)

Counted over Phase 1 only:

1. governed writes made by the agent with a receipt;
2. commits that carry a `Human-Record` trailer;
3. changes to governed paths that carry neither;
4. denied writes;
5. governed files that commit trailers mark as changed outside the channel, with what escaped and why, when known.

Reported as an observation of one author over one week. No hypothesis is tested.

**Where each count is read from:**

- count 1 from Actuarii's local audit database, one row per write;
- counts 2, 3 and 5 from the commit trailers;
- count 4 from the Claude Code session transcripts. Actuarii's write gate records nothing for a write it denies
  (Actuarii at `73eaf2b`, `tools/hooks/require_boundary_validation.py:48`). Proposals that the validator refuses are
  recorded in the audit database; they are not denied writes, and they are reported apart.

No count reads a receipt's rationale, not even the number of rationale trailers.

Known limits of the measurement: the rationale in each receipt is written by the model and is not the reason for the
change; "changed outside the channel" does not mean "written by the human"; a `Human-Record` trailer is a declaration
by the author, not a proof.

## Limits

- **Length:** about 1,500 words, one table.
- **Out of scope:**
  - changes to the Polar Projector paper and to `paper/claims.md`;
  - new Actuarii features;
  - the question of whether a receipt's rationale is faithful;
  - Actuarii v0.2;
  - what Phase 0 specified and deferred: figures written as references, the traceability matrix v1 with its blind
    sample, and H2.
- **The verifier:** only the minimal change needed to also check `method-paper/paper.md` against
  `method-paper/claims.md`.
- **Honesty:** Actuarii did not govern the original paper, and the new paper does not say it did.

## Done

Published in this repository with a Zenodo DOI; every number in the paper has a row in `method-paper/claims.md` and
passes the verifier; the limits are explicit; the measurement is reported as fixed in this file. "Almost done" is not
done.
