# Method paper: brief and pre-registration

Committed by the author on 2026-11-02, before any work on the method paper starts. Drafted with Claude (claude.ai);
reviewed, edited and committed by the author. Agents working in this repository read this file before doing anything
for the method paper, and do not modify it.

## Goal

**Primary.** A new paper of at most five pages (about 2,500 words, one or two tables) on how the Polar Projector paper
kept every number tied to evidence: the claims registry, the pre-registration labels, the refutation criteria and the
verifier that runs in CI. The Polar Projector paper is the case. It is not modified.

**Secondary.** Write the new paper with Actuarii governing the writes, and report what it recorded. This is a pilot
observation, not a test of anything.

**Deliverable.** The paper in this repository, with a Zenodo DOI. A forum post follows the week after.

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
requires does not run in cloud sessions. Read-only on every existing file. Output goes only to `method-paper/prep/`, on
the branch `prep/method-paper`. The paper declares this phase as agent work outside the governed channel.

**Phase 1: writing.** Local and governed, five working days from 2026-11-05.

- Day 1: install Actuarii, govern the paths listed below, confirm the measurement section of this file.
- Days 2 to 4: writing.
- Day 5: verify and publish as it stands.

## Phase 0 tasks

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

## Measurement (pre-registered)

Counted over Phase 1 only:

1. governed writes made by the agent with a receipt;
2. commits that carry a `Human-Record` trailer;
3. changes to governed paths that carry neither;
4. denied writes;
5. governed files that commit trailers mark as changed outside the channel, with what escaped and why, when known.

Reported as an observation of one author over one week. No hypothesis is tested.

Known limits of the measurement: the rationale in each receipt is written by the model and is not the reason for the
change; "changed outside the channel" does not mean "written by the human"; a `Human-Record` trailer is a declaration
by the author, not a proof.

## Limits

- **Length:** at most five pages. Cut rule on day 4: if the paper is not converging, cut it to the method, the case
  and the limits, about 1,500 words.
- **Out of scope:** changes to the Polar Projector paper and to `paper/claims.md`; new Actuarii features; the
  question of whether a receipt's rationale is faithful; Actuarii v0.2. In the verifier, only the minimal change needed
  to also check `method-paper/paper.md` against `method-paper/claims.md`.
- **Honesty:** Actuarii did not govern the original paper, and the new paper does not say it did.

## Done

Published in this repository with a Zenodo DOI; every number in the paper has a row in `method-paper/claims.md` and
passes the verifier; the limits are explicit; the measurement is reported as fixed in this file. "Almost done" is not
done.
