# Blind sample

Phase 0. Drawn on 2026-11-04 by an AI agent (Claude) in a cloud session, for `../matrix-spec.md` §8. That section
fixes the frame, the strata, the allocation, the analysis and the rules for filling the sheet in.

**Deferred with the matrix v1** (`../outline.md`, decision 20). Filling in the sheet is not part of the five days. The
sheet is kept for when the v1 runs.

## Files

| File | What it is |
|---|---|
| `frame.csv` | Every numeral in the `f59430a` manuscript outside References, with its v0 category as the stratum. Do not open it while filling in the sheet |
| `sheet.csv` | The 50 units to classify, with nothing the matrix decides |
| `build_frame.py` | Builds `frame.csv` from the v0 reader. Phase 0 only: it depends on v0, which does not run under Actuarii |
| `draw.py` | Draws `sheet.csv` from `frame.csv`. Standard library only, so it runs under Actuarii |
| `test_draw.py` | The draw is reproducible, honours the allocation, and leaks nothing |

## For the author

1. Read the manuscript at the release, where the line numbers apply:

   ```bash
   git show f59430a:paper/polar-projector-paper.md
   ```

2. For each unit, fill in:
   - `category`: one of `result`, `parameter`, `math`, `environment`, `citation`, `structure`, `notation`;
   - `tied`, for results only: `yes`, `no` or `unsure`;
   - `root`: where in code output the figure comes from;
   - `note`.
3. Read code and artifacts only. Do not open `../matrix/matrix.csv`, `../matrix/summary.md`, `frame.csv`, the
   verifier's output or `paper/claims.md`.
4. In Phase 1, put the filled sheet at `method-paper/blind-sample/sheet.csv` and commit it with `Human-Record: author`,
   before the definitive matrix run.

## Regenerating

```bash
git archive f59430a | tar -x -C CASE
```

```bash
python method-paper/prep/matrix/build_matrix.py --root CASE --out V0
```

```bash
python method-paper/prep/blind-sample/build_frame.py --root CASE --matrix-csv V0/matrix.csv --out method-paper/prep/blind-sample/frame.csv
```

```bash
python method-paper/prep/blind-sample/draw.py --frame method-paper/prep/blind-sample/frame.csv --manuscript CASE/paper/polar-projector-paper.md --out method-paper/prep/blind-sample/sheet.csv
```

```bash
pytest method-paper/prep/blind-sample/test_draw.py
```
