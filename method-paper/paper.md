# Keeping every number tied to evidence: a claims registry and a verifier in CI
## 1 Introduction

Any text that cites figures from outside itself, from code, data or experiments, can differ from its source, whether it is written by a person or by an AI. Working with LLMs makes writing faster, but it also produces more text than there is time to check. The mechanical part of this check, making sure that each figure matches its source, can be done by code. This way, people can devote their attention to what code does not judge: whether the reasoning holds up.

This report presents a method for keeping every figure in a text tied to its source: a registry with one row per figure, and a verifier that runs in continuous integration (CI) and checks that every registered figure matches its source. Figures in the text that are not in the registry are not checked. The case is my Polar Projector paper, as it was published. The report was written in one week with Actuarii, my governance kit for coding agents. With it, the agent can write to governed paths only with a receipt issued by a validator outside the model, and each commit that changes a governed path records which writes went through that channel and which did not. The report counts what was recorded.
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

