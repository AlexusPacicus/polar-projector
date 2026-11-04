# v0 on the release

The exploratory v0 matrix (`../build_matrix.py`) run on the case as released, `f59430a`, on 2026-11-04 in a Phase 0
cloud session, outside the governed channel. It is generated and is not edited by hand. Its header says `(sin git)`
because it ran on an exported tree, not on a clone.

This is the root of the exploratory text → code figures the note may print (`../../outline.md`, decision 20). The
sibling `../matrix.csv` and `../summary.md` are the same v0 run on `main`'s manuscript, made on 2026-11-02.

```bash
git archive f59430a | tar -x -C CASE
```

```bash
python method-paper/prep/matrix/build_matrix.py --root CASE --out method-paper/prep/matrix/release
```
