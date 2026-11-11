# Keeping every number tied to evidence: a claims registry and a verifier in CI

## Abstract

Any text that cites figures from code, data or experiments can drift from its source, whether it is written by a person or an AI. This report describes a method for keeping every figure tied to its source: a registry with one row per figure, and a verifier in CI that checks that every figure registered as checked matches its artifact. The case is my Polar Projector paper: the verifier checks the registered figures, but not whether the code does what the text describes, as happened with figures that passed it and were later retracted. As a pilot, the report was written with Actuarii, my governance kit for coding agents, and it counts which writes went through its channel. The method gives traceability, not reproducibility.

## 1 Introduction

Any text that cites figures from outside itself, from code, data or experiments, can differ from its source, whether it is written by a person or by an AI. Working with LLMs makes writing faster, but it also produces more text than there is time to check. The mechanical part of this check, making sure that each figure matches its source, can be done by code. This way, people can devote their attention to what code does not judge: whether the reasoning holds up.

This report presents a method for keeping every figure in a text tied to its source: a registry with one row per figure, and a verifier that runs in continuous integration (CI) and checks that every figure registered as checked matches its source. Figures in the text that are not in the registry are not checked. The case is my Polar Projector paper, as it was published. The report was written in one week with Actuarii, my governance kit for coding agents. With it, the agent can write to governed paths only with a receipt issued by a validator outside the model, and each commit that changes a governed path records which writes went through that channel and which did not. The report counts what was recorded.

## 1.1 The case as it was

The Polar Projector is an operator that places a note's embedding without reading the corpus, so its cost per vector does not depend on the size of the corpus. It returns a projection coefficient and an orthogonal residual. The paper mainly measures that cost and the recall of each query's nearest neighbours.

The registry, `paper/claims.md`, holds one row per claim, with an identifier and a status, and its rule is that nothing enters the text without a row. It has 42 rows: 31 `checked`, whose figures the verifier checks; 4 `construction`, facts read from the code, which name their source instead of a check; and 7 `remove`, which must not appear in the paper.

Not every experiment in the paper was pre-registered, so each row carries a label: `yes (commit)`, if the protocol was committed before its results; `no`, if the script and the results entered in the same commit; and `post hoc`, if it was specified after seeing the result. What backs each label is the order of the commits.

## 2.1 What the verifier checked

Table 1 lists, for each direction between the registry, the code and the text, whether a check in the case started
from one and looked in the other.

Three checks ran. From the registry to the code, every checked row must name a check the verifier runs, or `pytest`,
which it accepts by name without tying the row to any test. From the code to the text, each check stores a figure as the
manuscript prints it and compares it, at the printed precision, with the committed artifact: 281 figures pass. Each must
then appear in the manuscript. The verifier finds 261 of them; the other 20 are single characters, which it counts but
does not look for. From the text to the code, and only for the tables of Appendices B and C, it compares each printed
cell with a value stored in the verifier and recomputes those values from the operator on every run.

The presence check has a known limit: it confirms that a string is printed somewhere, not that it is printed where the
claim is made. No check starts from the text, or from the code, to find the row a figure belongs to. The verifier also
checks a figure's value, not how it was obtained: no check compares a row's pre-registration label with the commit
order.

**Table 1.** For each direction, whether the case had a check that starts from the first and finds each item in the
second.

| Direction | What a check would confirm | In the case | Where |
|---|---|---|---|
| Registry → code | Each checked row names a check that runs | Yes, except rows that name `pytest` | `_verify_registry` |
| Code → text | Each figure agrees with its artifact and is printed | Yes, by presence, not location | `_verify_artifacts`, `_verify_presence` |
| Text → code | Each printed figure has a checked source | Only the tables of Appendices B and C | `_verify_manuscript_tables` |
| Code → registry | Each check has a row, and the labels follow the commit order | No: no code writes the registry, a check can lose its row and CI stays green, and the labels are not compared with the commit order | — |
| Text → registry | Each printed figure has a row | No | — |
| Registry → text | Each row's claim is printed, and no `remove` row is | Only through code, for checked rows | — |
| None | What a sentence says about a figure | Not checked | — |

## 2.2 The same check on this note

This note has a registry of its own, `method-paper/claims.md`, with one row per figure; each row says where its figure
comes from.

The verifier changed as little as possible to cover the note. It now reads the note's registry and its text as well, and
it adds one check for each figure the note prints about the case. Each check stores the figure as it is printed and, on
every run, compares it with a count made on the case's files as they stand now (`_case_checks` in
`tools/verify_paper_tables.py`).

The note's registry goes through the same checks as the case's registry in §2.1. Every row marked `checked` must name a
check that exists, and every figure so checked must appear in the note.

The same limit holds. The verifier confirms that a figure is printed in the note, not where. The single-character
figures of §1.1 are compared with the case, but they are not searched for in the text.

## 3 This note written under Actuarii

The pilot has one author and one week, from installing Actuarii (2f7ce81, outside the range) to cutoff d41bd0b. Later
commits, this one and the abstract's among them, are not counted. An agent did the preparation outside the channel,
including what it produced beyond its tasks. Actuarii did not govern the case.

The agent made 42 governed writes with a receipt, leaving out an edit the author rejected. The range has 4 commits with
a Human-Record trailer and 0 changes to governed paths with neither receipt nor trailer. The gate denied 4 writes.
Separately, the validator rejected 1 proposal. One governed file, method-paper/paper.md, changed outside the channel,
in 4 commits: the author's sections, written by hand, as the author declares.

The model writes each receipt's rationale, which is not the reason for the change. No count reads it, by a written
rule, not by code. "Outside the channel" does not mean written by the human; the Human-Record trailer is a
declaration. The write and denial counts come from local records outside the repository; CI checks no count. No
hypothesis is tested.

## 4 Limits

The verifier works in any order: it compares the text with the artifacts whenever it runs. Pre-registration only needs the protocol to be committed before the results. Committing the claim and its row first adds one more guarantee: the claim cannot be chosen once the results are known. The case did not follow that full order: the registry was created when part of the manuscript already existed, and not every experiment was pre-registered.

The order of the commits backs the label yes (commit), but it does not show whether the protocol changed after a result was seen. This happened in E1, the paper’s drift experiment: after the first run, the way the results were aggregated changed, and the change went into the results commit (1e9d217), whose message explains it. Its rows are still labelled as pre-registered.

A figure in the text that matches its artifact does not prove that the code does what the text describes. The text, the code and the checks all come from the same author, so their agreement does not show that any of them is right. This happened with C16: its figures passed the verifier and were later retracted, because the code that produced them re-transformed every earlier point with each batch. The verifier did not catch it; a code review done with agents did. Tests written from the claim before the code, with checks in both directions between the registry, the text and the code, in the order set out in the first paragraph, would catch part of this; the rest needs judgment about what the code measures. Neither was tested here.

The method gives traceability, not reproducibility. Each registered figure is tied to the stored artifact that contains it, but not to the data, the environment or the procedure that produced it: the verifier compares with what was stored and does not recompute it, except in the tables in Appendices B and C. Achieving complete reproducibility, the entire laboratory, is left for future work.

The method has been applied to only one case, a paper by a single author. The pilot observes one week, the week in which this note was written, and the verifier itself was written by an LLM. It is an early observation, not an evaluation: it remains to be seen whether the method works for other texts, other authors or other verifiers.

## 5 Conclusion

The method checks on every push that every figure registered as checked still matches its artifact, without relying on manual review. What it does not judge is whether the code does what the text describes: that still needs review, as C16 showed. The next step is to tie the entire laboratory to the text, not just the figures, and to test the method on other texts.

## Who did what

The author wrote the introduction, the contribution, §1.1, the limits, the conclusion and the abstract, and approved every figure. The
agent drafted §2.1, Table 1, §2.2 and §3, kept the registry and changed the verifier through the governed channel. The
preparation work was done by an agent outside the channel, as §3 says.
