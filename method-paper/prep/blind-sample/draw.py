#!/usr/bin/env python3
"""Draw the blind sample from frame.csv (matrix-spec.md section 9).

Stratified by the v0 category, with the allocation and seed fixed below before the draw. The sheet
shows each unit's location and the line it sits on, with the figure marked, and nothing the matrix
decides: no stratum, category, status, check or datum. Its units are shuffled, so strata are not
contiguous.

Standard library only, with no process, network or loader primitive, so it runs unchanged under
Actuarii in Phase 1, where re-running it must give the same sheet.

    python draw.py --frame frame.csv --manuscript CASE_TREE/paper/polar-projector-paper.md [--out sheet.csv]
"""
from __future__ import annotations

import argparse
import csv
import random
import sys
from pathlib import Path

SEED = 20261104

# Units per stratum, 50 in all: half to results, where H1 lives, and the rest across the other
# categories so that a result the matrix excludes can show up (matrix-spec.md section 9).
ALLOCATION = {
    "resultado": 25,
    "parametro": 7,
    "notacion": 5,
    "texto": 4,
    "derivacion": 4,
    "entorno": 2,
    "sin-clasificar": 2,
    "referencia": 1,
}

SHEET = ["unit", "line", "k", "token", "section", "context", "table_row", "table_col", "excerpt",
         "category", "tied", "root", "note"]


def draw(frame: list[dict], seed: int = SEED, allocation: dict[str, int] = ALLOCATION) -> list[dict]:
    rng = random.Random(seed)
    sample = []
    for stratum, n in allocation.items():
        units = sorted((u for u in frame if u["stratum"] == stratum), key=lambda u: (int(u["line"]), int(u["k"])))
        if len(units) < n:
            raise SystemExit(f"stratum {stratum!r} has {len(units)} units, {n} requested")
        sample.extend(rng.sample(units, n))
    rng.shuffle(sample)
    return sample


def sheet(sample: list[dict], lines: list[str]) -> list[dict]:
    out = []
    for i, u in enumerate(sample, start=1):
        text = lines[int(u["line"]) - 1]
        s, e = int(u["start"]), int(u["end"])
        if text[s:e] != u["token"]:
            raise SystemExit(f"line {u['line']}: {text[s:e]!r} is not the frame's token {u['token']!r}")
        out.append({
            "unit": f"S{i:02d}", "line": u["line"], "k": u["k"], "token": u["token"],
            "section": u["section"], "context": u["context"],
            "table_row": u["table_row"], "table_col": u["table_col"],
            "excerpt": f"{text[:s]}⟦{text[s:e]}⟧{text[e:]}".strip(),
            "category": "", "tied": "", "root": "", "note": "",
        })
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--frame", type=Path, required=True)
    ap.add_argument("--manuscript", type=Path, required=True, help="the case manuscript the frame was built on")
    ap.add_argument("--out", type=Path, help="defaults to stdout")
    args = ap.parse_args(argv)
    with args.frame.open(encoding="utf-8") as fh:
        frame = list(csv.DictReader(fh))
    lines = [ln.replace("{,}", ",") for ln in args.manuscript.read_text(encoding="utf-8").split("\n")]
    rows = sheet(draw(frame), lines)
    fh = args.out.open("w", encoding="utf-8", newline="") if args.out else sys.stdout
    w = csv.DictWriter(fh, fieldnames=SHEET, lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
    if args.out:
        fh.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
