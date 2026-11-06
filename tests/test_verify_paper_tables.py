"""The case figures that method-paper/paper.md prints, as tools/verify_paper_tables.py checks them.

The method paper describes the Polar Projector paper as its case and prints counts about it:
rows of paper/claims.md by status, figures checked against artifacts, and how many of those the
presence check finds. A row of method-paper/claims.md can only be `checked` if it names a check
the verifier runs, so these counts need checks of their own, counted from the case's files.
"""

from tools import verify_paper_tables as vpt

HEADER = (
    "| ID | Claim | Status | Pre-registered | Source | CI checks |\n"
    "|----|-------|--------|----------------|--------|-----------|\n"
)


def test_case_figures_are_counted_from_the_case_files(tmp_path):
    claims = tmp_path / "claims.md"
    claims.write_text(
        HEADER
        + "| A1 | a | checked | no | x | `x one` |\n"
        + "| A2 | b | checked | no | x | `x two` |\n"
        + "| R1 | c | remove | no | x | |\n",
        encoding="utf-8",
    )
    paper = tmp_path / "paper.md"
    paper.write_text("It prints 11.86 and 7.\n", encoding="utf-8")
    checks = [("x one", "11.86", 11.86), ("x two", "12.50", 12.5), ("x three", "7", 7.0)]

    counted = {label: value for label, _, value in vpt._case_checks(checks, claims, paper)}

    assert counted == {
        "case registry rows": 3,
        "case registry checked": 2,
        "case registry construction": 0,
        "case registry remove": 1,
        "case artifact figures": 3,
        "case presence found": 1,  # 11.86; 12.50 is absent and 7 is a single character
        "case presence single-character": 1,
    }


def test_case_figures_agree_with_the_case_as_it_stands():
    case = vpt._case_checks(vpt._artifact_checks())

    assert [(label, printed) for label, printed, _ in case] == [
        ("case registry rows", "42"),
        ("case registry checked", "31"),
        ("case registry construction", "4"),
        ("case registry remove", "7"),
        ("case artifact figures", "281"),
        ("case presence found", "261"),
        ("case presence single-character", "20"),
    ]
    assert [label for label, printed, counted in case if not vpt._agree(counted, printed)] == []


def test_a_checked_row_naming_a_case_figure_requires_it_in_the_method_paper(tmp_path):
    claims = tmp_path / "claims.md"
    claims.write_text(HEADER + "| M1 | rows | checked | no | x | `case registry rows` |\n", encoding="utf-8")
    paper = tmp_path / "paper.md"
    checks = vpt._artifact_checks()

    paper.write_text("The registry has 41 rows.\n", encoding="utf-8")
    assert vpt._verify_method_paper(checks, claims, paper) == 1

    paper.write_text("The registry has 42 rows.\n", encoding="utf-8")
    assert vpt._verify_method_paper(checks, claims, paper) == 0
