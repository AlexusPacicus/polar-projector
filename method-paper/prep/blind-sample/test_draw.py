"""Tests for draw.py: the sheet is reproducible, honours the allocation and leaks nothing the matrix decides.

    pytest method-paper/prep/blind-sample/test_draw.py
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import draw  # noqa: E402


def _frame() -> list[dict]:
    with (HERE / "frame.csv").open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _key(u: dict) -> tuple[str, str, str]:
    return (u["line"], u["k"], u["token"])


def test_the_same_seed_draws_the_same_units_in_the_same_order():
    frame = _frame()
    assert [_key(u) for u in draw.draw(frame)] == [_key(u) for u in draw.draw(frame)]


def test_another_seed_draws_another_sample():
    frame = _frame()
    assert {_key(u) for u in draw.draw(frame)} != {_key(u) for u in draw.draw(frame, seed=draw.SEED + 1)}


def test_each_stratum_gets_exactly_its_allocation_and_no_unit_twice():
    sample = draw.draw(_frame())
    assert len(sample) == sum(draw.ALLOCATION.values()) == 50
    for stratum, n in draw.ALLOCATION.items():
        assert sum(1 for u in sample if u["stratum"] == stratum) == n
    assert len({_key(u) for u in sample}) == len(sample)


def test_the_committed_sheet_is_what_the_draw_produces():
    with (HERE / "sheet.csv").open(encoding="utf-8") as fh:
        committed = list(csv.DictReader(fh))
    assert [(r["line"], r["k"], r["token"]) for r in committed] == [_key(u) for u in draw.draw(_frame())]


def test_the_sheet_carries_nothing_the_matrix_decides():
    assert not {"stratum", "categoria", "estado", "pruebas", "datos", "regla"} & set(draw.SHEET)
    with (HERE / "sheet.csv").open(encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    assert all(r["category"] == r["tied"] == r["root"] == r["note"] == "" for r in rows)


def test_a_stratum_too_small_for_its_allocation_stops_the_draw():
    frame = [u for u in _frame() if u["stratum"] != "entorno"]
    try:
        draw.draw(frame)
    except SystemExit as exc:
        assert "entorno" in str(exc)
    else:
        raise AssertionError("the draw went on with an empty stratum")
