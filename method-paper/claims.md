# Claims registry of the method paper

Nothing enters `method-paper/paper.md` without a row here, and a row whose status is `checked` must name at least one check that `tools/verify_paper_tables.py` actually runs. This registry keeps the rule of `paper/claims.md`; it has one row per number in the paper.

## Vocabulary

The statuses (`checked`, `not-in-ci`, `mismatch`, `unbacked`, `pending`, `construction`, `remove`), the pre-registration labels (`yes (commit)`, `no`, `post hoc`) and the form of the CI checks are those defined in the Vocabulary section of `paper/claims.md`. They are not copied here, so that the two registries cannot drift apart.

## Claims

| ID | Claim | Status | Pre-registered | Source | CI checks |
|----|-------|--------|----------------|--------|-----------|
| M1 | The Polar Projector paper's claims registry has 42 rows | pending | no | paper/claims.md, counted by tools/verify_paper_tables.py; prep/case-data.md §1 | `case registry rows` |
| M2 | Of those rows, 31 are checked, 4 construction and 7 remove | pending | no | paper/claims.md, counted by tools/verify_paper_tables.py; prep/case-data.md §1 | `case registry checked`; `case registry construction`; `case registry remove` |
| M3 | Its verifier checks 281 figures against committed artifacts | checked | no | tools/verify_paper_tables.py, its artifact checks; prep/case-data.md §7 | `case artifact figures` |
| M4 | Of those figures, the presence check finds 261 in the manuscript; 20 are single characters and are not located | checked | no | tools/verify_paper_tables.py, its presence check over paper/polar-projector-paper.md; prep/case-data.md §7 | `case presence found`; `case presence single-character` |
