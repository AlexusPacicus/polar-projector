#!/usr/bin/env python3
"""Negative tests for build_matrix.py.

The matrix is LLM-written code, so it has to show that it detects what it claims to detect.
Each test plants one error in a temporary copy of the repository and requires a specific
reaction from the matrix and, where it matters, from the verifier. The repository itself is
never touched.

    python method-paper/prep/matrix/test_matrix.py
"""
from __future__ import annotations

import csv
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
BUILD = HERE / "build_matrix.py"
PAPER = Path("paper/polar-projector-paper.md")
CLAIMS = Path("paper/claims.md")
TIED = {"atada-ubicada", "atada-presencia", "atada-un-caracter"}
ENV = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}


def snapshot(dst: Path) -> None:
    """Copy what the matrix and the verifier read; corpus embeddings and figures are not needed."""
    for d in ("paper", "bench", "tools", "polar_projector"):
        shutil.copytree(REPO / d, dst / d,
                        ignore=shutil.ignore_patterns("__pycache__", "build", "figures", "data"))


def edit_line(root: Path, rel: Path, needle: str, old: str, new: str) -> int:
    """Replace OLD with NEW on the single line containing NEEDLE; return its line number."""
    path = root / rel
    lines = path.read_text(encoding="utf-8").split("\n")
    hits = [i for i, ln in enumerate(lines) if needle in ln]
    assert len(hits) == 1, f"needle {needle!r} found on {len(hits)} lines"
    assert old in lines[hits[0]], f"{old!r} not on the line of {needle!r}"
    lines[hits[0]] = lines[hits[0]].replace(old, new, 1)
    path.write_text("\n".join(lines), encoding="utf-8")
    return hits[0] + 1


def build(root: Path) -> list[dict]:
    out = root / "_matrix"
    subprocess.run([sys.executable, str(BUILD), "--root", str(root), "--out", str(out)],
                   check=True, capture_output=True, text=True, env=ENV)
    with (out / "matrix.csv").open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def verifier_passes(root: Path) -> bool:
    run = subprocess.run([sys.executable, str(root / "tools" / "verify_paper_tables.py")], cwd=root,
                         capture_output=True, text=True, env={**ENV, "PYTHONPATH": str(root)})
    return run.returncode == 0


def rows_at(rows: list[dict], line: int, text: str) -> list[dict]:
    return [r for r in rows if int(r["linea"]) == line and r["cifra"] == text]


# --------------------------------------------------------------------------- tests

def test_baseline(root: Path) -> str:
    rows = build(root)
    assert verifier_passes(root), "verifier fails on an unmodified copy"
    summary = (root / "_matrix" / "summary.md").read_text(encoding="utf-8")
    assert "no casan con ninguna fila: 0" in summary, "some check matches no row on an unmodified copy"
    assert "sin artefacto detectado al perturbar: 0" in summary
    return f"{len(rows)} filas; verificador en verde; todos los chequeos casan con alguna fila"


def test_planted_figure(root: Path) -> str:
    """A new result in the prose of §3.5: the verifier never reads it, the matrix must."""
    line = edit_line(root, PAPER, "linear map competes on equal terms", "equal terms",
                     "equal terms (the operator is also 3.7× faster there)")
    rows = rows_at(build(root), line, "3.7×")
    assert rows and rows[0]["categoria"] == "resultado" and rows[0]["estado"] == "sin-respaldo", rows
    assert verifier_passes(root), "the verifier was expected to pass: it checks registry -> text only"
    return "3.7× plantada: la matriz la marca sin-respaldo; el verificador sigue en verde"


def test_altered_occurrence(root: Path) -> str:
    """One of the ten printed 0.981 changed: the presence check is still satisfied by the other nine."""
    line = edit_line(root, PAPER, "the radial coordinate bounds the operator — 0.981", "0.981", "0.987")
    rows = rows_at(build(root), line, "0.987")
    assert rows and rows[0]["categoria"] == "resultado" and rows[0]["estado"] not in TIED, rows
    assert verifier_passes(root), "the verifier was expected to pass: 0.981 is still printed elsewhere"
    return f"0.981 → 0.987 en L{line}: la matriz la marca {rows[0]['estado']}; el verificador sigue en verde"


def test_appendix_c_cell(root: Path) -> str:
    """A located table: the verifier fails, and the matrix marks the cell."""
    line = edit_line(root, PAPER, "| 0.500 | 2.638e-3 | 6.954e-6 | 379.31 |", "379.31", "379.32")
    rows = rows_at(build(root), line, "379.32")
    assert rows and rows[0]["estado"] == "prueba-falla", rows
    assert not verifier_passes(root), "the verifier was expected to fail on a changed Appendix C cell"
    return "celda 379.31 → 379.32 del Apéndice C: prueba-falla en la matriz; el verificador falla"


def test_registry_row_removed(root: Path) -> str:
    """Delete C13: its checks still run, CI stays green, and the matrix shows figures with no row."""
    path = root / CLAIMS
    lines = [ln for ln in path.read_text(encoding="utf-8").split("\n") if not ln.startswith("| C13 ")]
    path.write_text("\n".join(lines), encoding="utf-8")
    rows = build(root)
    orphans = [r for r in rows if "chequeo sin fila en el registro" in r["nota"]]
    assert any("radial_plain" in r["pruebas"] for r in orphans), "no figure lost its registry row"
    assert verifier_passes(root), "the verifier was expected to pass: no row requires every check"
    return f"fila C13 borrada: {len(orphans)} cifras quedan con chequeo y sin fila; el verificador sigue en verde"


def test_artifact_changed(root: Path) -> str:
    """The artifact behind 0.981 changed: the verifier fails, and every 0.981 is marked."""
    path = root / "bench/results/reanchor.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["results"]["radial_plain"]["mean_recall"] = 0.9
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    rows = [r for r in build(root) if r["cifra"] == "0.981"]
    failing = [r for r in rows if r["estado"] == "prueba-falla"]
    assert rows and len(failing) == len(rows), [(r["linea"], r["estado"]) for r in rows]
    assert not verifier_passes(root), "the verifier was expected to fail on a changed artifact"
    return f"artefacto alterado: las {len(rows)} apariciones de 0.981 quedan en prueba-falla; el verificador falla"


def test_reference_number(root: Path) -> str:
    """A number inside the reference list is excluded by category, explicitly."""
    line = edit_line(root, PAPER, "4. Boechler, P. M. (2001)", "(2001)", "(2001, reprinted 2099)")
    rows = rows_at(build(root), line, "2099")
    assert rows and rows[0]["categoria"] == "referencia" and rows[0]["estado"] == "excluida", rows
    return "2099 en una referencia: categoría referencia, excluida y listada"


TESTS = [test_baseline, test_planted_figure, test_altered_occurrence, test_appendix_c_cell,
         test_registry_row_removed, test_artifact_changed, test_reference_number]


def main() -> int:
    failures = 0
    for test in TESTS:
        with tempfile.TemporaryDirectory(prefix="matrix-test-") as tmp:
            root = Path(tmp)
            snapshot(root)
            try:
                print(f"PASS  {test.__name__}: {test(root)}")
            except (AssertionError, subprocess.CalledProcessError) as exc:
                failures += 1
                detail = exc.stderr[-500:] if isinstance(exc, subprocess.CalledProcessError) else exc
                print(f"FAIL  {test.__name__}: {detail}")
    print(f"\n{len(TESTS) - failures}/{len(TESTS)} pruebas pasan")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
