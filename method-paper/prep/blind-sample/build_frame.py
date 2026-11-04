#!/usr/bin/env python3
"""Sampling frame for the blind sample (Phase 0 only).

One row per numeral the v0 reader finds in the case manuscript, outside the References section, with:

  key       line, the token's rank on its line (k), and the token as printed: the join key with the
            definitive matrix (matrix-spec.md section 9)
  location  start and end of the token on the normalized line ('{,}' read as ','), section, context,
            and for a table cell its row label and column header
  stratum   the v0 category, used only to stratify the draw; it never reaches the sheet

It reuses the v0 reader (../matrix/build_matrix.py: scan_manuscript, TOKEN) and the v0 categories from a
matrix.csv built on the same tree, and checks that the two agree row by row. v0 imports importlib and
subprocess, so this script does not run under Actuarii. It is Phase 0 tooling, and its output, frame.csv,
is committed. draw.py, which reads frame.csv, has no such dependency.

    python build_frame.py --root CASE_TREE --matrix-csv CASE_TREE_V0/matrix.csv --out frame.csv
"""
from __future__ import annotations

import argparse
import csv
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "matrix"))

from build_matrix import TOKEN, scan_manuscript  # noqa: E402  (v0 reader, Phase 0)

COLUMNS = ["line", "k", "token", "start", "end", "printed", "section", "context", "table_row", "table_col",
           "stratum"]


def build(root: Path, matrix_csv: Path) -> list[dict]:
    occs = scan_manuscript(root)
    with matrix_csv.open(encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    if len(rows) != len(occs):
        raise SystemExit(f"v0 matrix has {len(rows)} rows, the reader finds {len(occs)}: not the same tree")

    lines = [ln.replace("{,}", ",") for ln in (root / "paper" / "polar-projector-paper.md")
             .read_text(encoding="utf-8").split("\n")]
    tokens = {no: list(TOKEN.finditer(text)) for no, text in enumerate(lines, start=1)}
    rank: dict[int, int] = defaultdict(int)

    frame = []
    for occ, row in zip(occs, rows, strict=True):
        if int(row["linea"]) != occ.line or row["cifra"] != occ.text:
            raise SystemExit(f"row {row['id']}: v0 matrix and reader disagree ({row['cifra']!r} vs {occ.text!r})")
        k = rank[occ.line]
        rank[occ.line] += 1
        m = tokens[occ.line][k]
        if occ.region == "referencias":
            continue
        frame.append({
            "line": occ.line, "k": k, "token": m.group(), "start": m.start(), "end": m.end(),
            "printed": occ.text, "section": occ.section, "context": occ.context,
            "table_row": occ.row_label if occ.table_line else "",
            "table_col": occ.col_header if occ.table_line else "",
            "stratum": row["categoria"],
        })
    return frame


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--root", type=Path, required=True, help="tree of the case at the measured commit")
    ap.add_argument("--matrix-csv", type=Path, required=True, help="v0 matrix.csv built on that same tree")
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args(argv)
    frame = build(args.root, args.matrix_csv)
    with args.out.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUMNS, lineterminator="\n")
        w.writeheader()
        w.writerows(frame)
    print(f"{len(frame)} units -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
