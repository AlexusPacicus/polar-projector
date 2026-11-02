#!/usr/bin/env python3
"""Traceability matrix for H1 of the method paper (draft v0).

One row per occurrence of a number in the manuscript. Each row gets a logical category,
the kind of number it is, and, as evidence, only what code produces:

  datos       the committed artifact value it matches (bench/results/*.json), or the value
              the verifier recomputes (Appendices B and C)
  pruebas     the verifier checks that compare it, and whether a check locates this
              occurrence or only finds the same string somewhere in the text
  codigo      the script that writes that artifact
  depende_de  the in-repository code and data that script depends on
  registro    the paper/claims.md rows that name those checks: cross-checked, not trusted

Everything an LLM wrote (manuscript, registry, commit messages, this script) is a claim to
verify; only code output counts as evidence. Read-only: it reads the repository at --root
and writes only to --out.

    python method-paper/prep/matrix/build_matrix.py [--root DIR] [--out DIR]
"""
from __future__ import annotations

import argparse
import ast
import csv
import importlib.util
import json
import math
import random
import re
import subprocess
import sys
import types
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

sys.dont_write_bytecode = True

HERE = Path(__file__).resolve().parent
DEFAULT_ROOT = HERE.parents[2]
MANUSCRIPT = Path("paper/polar-projector-paper.md")
REGISTRY = Path("paper/claims.md")
SPECIAL_CHECKS = {"pytest", "recompute:§B", "recompute:§C"}

CATEGORIES = ("resultado", "parametro", "derivacion", "entorno", "referencia", "texto", "notacion",
              "sin-clasificar")
EXCLUDED = {"referencia", "texto", "notacion"}


# --------------------------------------------------------------------------- verifier

def load_verifier(root: Path):
    """Import tools/verify_paper_tables.py from ROOT, with ROOT's operator first on the path."""
    for p in (root / "tools", root):
        if str(p) not in sys.path:
            sys.path.insert(0, str(p))
    spec = importlib.util.spec_from_file_location("verify_under_matrix", root / "tools" / "verify_paper_tables.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _round_number(x: float) -> bool:
    """Values with at most two significant digits (0.001, 0.5, 1e-11, 384.0) often serve as
    lookup keys in the checks; perturbing them breaks the lookup instead of moving a value."""
    if x == 0.0:
        return False
    digits = f"{abs(x):.14e}".split("e")[0].replace(".", "").rstrip("0")
    return len(digits) <= 2


def _perturb(obj, rng: random.Random, mode: str):
    if isinstance(obj, bool):
        return (not obj) if mode == "flip" else obj
    if isinstance(obj, int):
        return obj + rng.randint(1, 9) if mode == "shift" else obj
    if isinstance(obj, float):
        if not math.isfinite(obj):
            return obj
        if mode == "affine" and not _round_number(obj):
            return obj * (1.0 + 0.3 * rng.random()) + 0.01 * (0.5 + rng.random())
        if mode == "strong" and not _round_number(obj):
            return obj * (1.0 + 3.0 * rng.random()) + 0.05 * (0.5 + rng.random())
        if mode == "tiny" and not _round_number(obj):
            return obj * 1e-12
        if mode == "round" and _round_number(obj):
            return obj * (1.0 + 0.3 * rng.random()) + 0.01 * (0.5 + rng.random())
        return obj
    if isinstance(obj, list):
        return [_perturb(x, rng, mode) for x in obj]
    if isinstance(obj, dict):
        return {k: _perturb(x, rng, mode) for k, x in obj.items()}
    return obj


def _same(a, b) -> bool:
    try:
        fa, fb = float(a), float(b)
    except (TypeError, ValueError):
        return a == b
    return (math.isnan(fa) and math.isnan(fb)) or fa == fb


def trace_checks(v):
    """The verifier's checks, each with the artifacts it reads.

    Found by running the checks again with one artifact perturbed at a time (two random
    affine changes, floats scaled to near zero, integers shifted, booleans flipped; round
    numbers kept, since they act as lookup keys) and recording which measured values move.
    This is code output, not a reading of the verifier's source.
    """
    base = v._artifact_checks()
    real = json
    sources: dict[str, set[str]] = defaultdict(set)
    errors: dict[str, list[str]] = defaultdict(list)
    for path in sorted(v.RESULTS.glob("*.json")):
        for mode in ("affine", "strong", "tiny", "round", "shift", "flip"):
            def load(fh, *a, _name=path.name, _mode=mode, **kw):
                data = real.load(fh, *a, **kw)
                if Path(getattr(fh, "name", "")).name == _name:
                    data = _perturb(data, random.Random(f"{_name}/{_mode}"), _mode)
                return data

            v.json = types.SimpleNamespace(load=load, loads=real.loads, dump=real.dump, dumps=real.dumps)
            try:
                moved = v._artifact_checks()
            except Exception as exc:  # a perturbation that breaks the computation tells us nothing
                errors[path.name].append(f"{mode}: {type(exc).__name__}")
                continue
            finally:
                v.json = real
            for (label, _, m0), (label1, _, m1) in zip(base, moved, strict=True):
                if label != label1:
                    raise RuntimeError(f"check order changed when perturbing {path.name}")
                if not _same(m0, m1):
                    sources[label].add(path.name)
    return base, {k: sorted(s) for k, s in sources.items()}, dict(errors)


# --------------------------------------------------------------------------- code and data

OUT_DEFAULT = re.compile(
    r"""(?:default\s*=\s*|\bor\s+)(?:RESULTS_DIR\s*/\s*|Path\(\s*)["'](?:bench/results/)?(?P<name>[\w.-]+\.json)["']""")


def artifact_writers(root: Path) -> dict[str, list[str]]:
    """Artifact -> scripts whose output path defaults to it (their --out default)."""
    writers: dict[str, set[str]] = defaultdict(set)
    for script in sorted([*root.glob("bench/*.py"), *root.glob("tools/*.py")]):
        for m in OUT_DEFAULT.finditer(script.read_text(encoding="utf-8")):
            writers[m.group("name")].add(script.relative_to(root).as_posix())
    return {k: sorted(s) for k, s in writers.items()}


def script_deps(root: Path, rel: str, seen: set[str] | None = None) -> set[str]:
    """In-repository modules and data a script depends on, from its imports (transitively)."""
    seen = set() if seen is None else seen
    if rel in seen:
        return set()
    seen.add(rel)
    src = (root / rel).read_text(encoding="utf-8")
    deps: set[str] = set()
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.Import):
            mods = [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module:
            mods = [node.module]
        else:
            continue
        for mod in mods:
            top = mod.split(".")[0]
            if top == "polar_projector":
                deps.add("polar_projector/")
                continue
            for folder in ("bench", "tools"):
                cand = f"{folder}/{top}.py"
                if cand != rel and (root / cand).exists():
                    deps.add(cand)
                    deps |= script_deps(root, cand, seen)
    if re.search(r"\bload_corpus\b|\bDATA_DIR\b|bench/data", src):
        deps.add("bench/data/")
    return deps


def load_artifacts(root: Path) -> dict[str, dict]:
    return {p.name: json.loads(p.read_text(encoding="utf-8")) for p in sorted((root / "bench/results").glob("*.json"))}


def numeric_leaves(obj, path: str = ""):
    if isinstance(obj, bool):
        return
    if isinstance(obj, (int, float)):
        if math.isfinite(obj):
            yield path, float(obj)
    elif isinstance(obj, dict):
        for k, x in obj.items():
            yield from numeric_leaves(x, f"{path}.{k}" if path else str(k))
    elif isinstance(obj, list):
        for i, x in enumerate(obj):
            yield from numeric_leaves(x, f"{path}[{i}]")


class DataIndex:
    """Numeric leaves of every artifact's results, findable at a printed precision."""

    def __init__(self, artifacts: dict[str, dict]):
        self.by_dec: dict[tuple[int, float], list[str]] = defaultdict(list)
        self.by_sig: dict[str, list[str]] = defaultdict(list)
        for name, data in artifacts.items():
            for path, x in numeric_leaves(data.get("results", {})):
                ref = f"{name}:{path}"
                for d in range(7):
                    self.by_dec[(d, round(x, d))].append(ref)
                for s in range(1, 7):
                    self.by_sig[f"{x:.{s - 1}e}"].append(ref)

    def find(self, occ: Occ) -> list[str]:
        if occ.kind == "plain" and "e" not in occ.num.lower():
            return self.by_dec.get((occ.dec, round(occ.value, occ.dec)), [])
        return self.by_sig.get(f"{occ.value:.{max(occ.sig, 1) - 1}e}", [])


def config_index(artifacts: dict[str, dict]) -> tuple[dict[float, list[str]], dict[int, list[str]]]:
    """Settings each artifact records in its config: scalars and members of short lists; and,
    separately, integer members of any list (a sweep over 10^-k records k)."""
    out: dict[float, list[str]] = defaultdict(list)
    ints: dict[int, list[str]] = defaultdict(list)

    def walk(obj, path, name, in_list=False):
        if isinstance(obj, bool):
            return
        if isinstance(obj, (int, float)):
            if not in_list or in_list == "short":
                out[float(obj)].append(f"{name}:config.{path}")
            if isinstance(obj, int) and in_list:
                ints[obj].append(f"{name}:config.{path}")
        elif isinstance(obj, dict):
            for k, x in obj.items():
                walk(x, f"{path}.{k}" if path else k, name)
        elif isinstance(obj, list):
            for i, x in enumerate(obj):
                walk(x, f"{path}[{i}]", name, "short" if len(obj) <= 12 else "long")

    for name, data in artifacts.items():
        walk(data.get("config", {}), "", name)
    return out, ints


def environment_text(artifacts: dict[str, dict]) -> str:
    return " ".join(json.dumps({k: d.get(k) for k in ("host", "thread_env")}) for d in artifacts.values())


def code_literals(root: Path) -> dict[float, list[str]]:
    """Numeric literals in the code (weak evidence for a parameter: the code as written)."""
    out: dict[float, list[str]] = defaultdict(list)
    for f in sorted([*root.glob("bench/*.py"), *root.glob("tools/*.py"), *root.glob("polar_projector/*.py")]):
        for node in ast.walk(ast.parse(f.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) \
                    and not isinstance(node.value, bool):
                out[float(node.value)].append(f"{f.relative_to(root).as_posix()}:{node.lineno}")
    return out


# --------------------------------------------------------------------------- registry

def read_registry(root: Path) -> dict[str, tuple[str, list[str]]]:
    rows = {}
    for line in (root / REGISTRY).read_text(encoding="utf-8").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) == 6 and re.fullmatch(r"[ACPR]\d+", cells[0]):
            rows[cells[0]] = (cells[2], re.findall(r"`([^`]+)`", cells[5]))
    return rows


def _id_key(cid: str):
    return (cid[0], int(cid[1:]))


def registry_for(rows, label: str) -> list[str]:
    return sorted((cid for cid, (_, toks) in rows.items()
                   if any(t not in SPECIAL_CHECKS and label.startswith(t) for t in toks)), key=_id_key)


def registry_special(rows, token: str) -> list[str]:
    return sorted((cid for cid, (_, toks) in rows.items() if token in toks), key=_id_key)


# --------------------------------------------------------------------------- manuscript

TOKEN = re.compile(
    r"(?P<sci>(?P<m>\d+(?:\.\d+)?)\s*\\times\s*10\^(?:\{(?P<e>[-−]?\d+)\}|(?P<e1>\d)))"
    r"|(?P<pow>10\^(?:\{(?P<pe>[-−]?\d+)\}|(?P<pe1>\d)))"
    r"|(?P<ver>\d+\.\d+\.\d+(?:\.\d+)?)"
    r"|(?P<plain>\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?(?:[eE][-+−]?\d+)?)")
UNIT = re.compile(r"(?:\s?(?P<u>×|%|\\%|µs|ms|°)|(?P<circ>\^\\circ)|\s(?P<u2>s|GB)\b)")
SEPARATOR = re.compile(r"^\|[\s:|-]+\|\s*$")
PIPE = re.compile(r"(?<!\\)\|")


@dataclass
class Occ:
    line: int
    region: str
    section: str
    context: str
    text: str
    num: str
    mantissa: str
    value: float
    sig: int
    dec: int
    kind: str
    unit: str
    in_math: bool
    in_code: bool
    in_link: bool
    before: str
    after: str
    prefix: str = ""
    table_line: int = 0
    col: int = -1
    col_header: str = ""
    row_label: str = ""
    category: str = ""
    rule: str = ""
    status: str = ""
    tests: list[str] = field(default_factory=list)
    located: str = ""
    data: str = ""
    code: list[str] = field(default_factory=list)
    deps: list[str] = field(default_factory=list)
    registry: list[str] = field(default_factory=list)
    note: list[str] = field(default_factory=list)

    @property
    def table(self) -> str:
        if not self.table_line:
            return ""
        return f"tabla L{self.table_line} | fila '{self.row_label}' | columna '{self.col_header}'"


def _ranges(pattern: str, s: str) -> list[tuple[int, int]]:
    return [(m.start(), m.end()) for m in re.finditer(pattern, s)]


def _inside(pos: int, ranges) -> bool:
    return any(a <= pos < b for a, b in ranges)


def _sig_digits(mantissa: str) -> int:
    digits = re.sub(r"[^\d]", "", mantissa.split("e")[0].split("E")[0]).lstrip("0")
    return max(len(digits), 1)


def _region(h2: str) -> str:
    if h2 == "":
        return "portada"
    if h2.startswith("Abstract"):
        return "resumen"
    if h2.startswith("References"):
        return "referencias"
    if h2.startswith("Appendix"):
        return "apendice"
    if h2.startswith(("Code and Data Availability", "Use of Generative AI")):
        return "declaraciones"
    return "cuerpo"


def scan_manuscript(root: Path) -> list[Occ]:
    lines = [ln.replace("{,}", ",") for ln in (root / MANUSCRIPT).read_text(encoding="utf-8").split("\n")]
    occs: list[Occ] = []
    h2 = h3 = ""
    display = False
    math_open = False
    table_line = 0
    header: list[str] = []
    for i, line in enumerate(lines):
        no = i + 1
        if line.startswith("## "):
            h2, h3 = line[3:].strip(), ""
        elif line.startswith("### "):
            h3 = line[4:].strip()
        if line.strip() == "$$":
            display = not display
            continue
        # tables
        is_row = line.startswith("|")
        if is_row and not table_line and i + 1 < len(lines) and SEPARATOR.match(lines[i + 1]):
            table_line = no
            header = [c.strip() for c in PIPE.split(line.strip())[1:-1]]
        elif not is_row:
            table_line, header = 0, []
        if is_row and SEPARATOR.match(line):
            continue
        heading = line.startswith("#")
        context = ("encabezado" if heading else "formula" if display else "tabla" if is_row
                   else "leyenda" if line.startswith("![") else
                   "lista" if re.match(r"^\s*(?:[-*]|\d+\.)\s", line) else "prosa")
        # spans: inline math (may continue across lines), code, links
        math_ranges, start = [], (0 if math_open else None)
        for m in re.finditer(r"\\\(|\\\)|\\\[|\\\]", line):
            if m.group() in ("\\(", "\\[") and start is None:
                start = m.start()
            elif m.group() in ("\\)", "\\]") and start is not None:
                math_ranges.append((start, m.end()))
                start = None
        math_open = start is not None
        if math_open:
            math_ranges.append((start, len(line)))
        code_ranges = _ranges(r"`[^`]*`", line)
        link_ranges = _ranges(r"\]\([^)]*\)|<https?://[^>]*>|https?://\S+", line)
        pipes = [m.start() for m in PIPE.finditer(line)] if is_row else []
        prev_line = lines[i - 1] if i > 0 else ""
        next_line = lines[i + 1] if i + 1 < len(lines) else ""
        section = " > ".join(x for x in (h2, h3) if x)
        for m in TOKEN.finditer(line):
            s, e = m.start(), m.end()
            if m.group("sci"):
                kind, mant = "sci", m.group("m")
                exp = (m.group("e") or m.group("e1")).replace("−", "-")
                value = float(mant) * 10.0 ** int(exp)
                num, dec = f"{mant}e{exp}", 0
            elif m.group("pow"):
                kind, mant = "pow", "1"
                exp = (m.group("pe") or m.group("pe1")).replace("−", "-")
                value = 10.0 ** int(exp)
                num, dec = f"1e{exp}", 0
            elif m.group("ver"):
                kind = "version"
                num = mant = m.group("ver")
                value = float(".".join(num.split(".")[:2]))
                dec = 0
            else:
                kind = "plain"
                raw = m.group("plain")
                num = raw.replace(",", "")
                mant = num
                value = float(num.replace("−", "-"))
                dec = len(num.split(".")[1].split("e")[0].split("E")[0]) if "." in num else 0
            sign = ""
            if s > 0 and line[s - 1] in "+-−" and (s < 2 or not (line[s - 2].isalnum() or line[s - 2] in ")]}_")):
                sign = line[s - 1]
            elif line[:s].rstrip().endswith(("\\pm", "±")):
                sign = "±"
            if sign in "-−" and sign:
                value = -value
            um = UNIT.match(line, e)
            unit = ""
            if um:
                unit = "°" if um.group("circ") else (um.group("u") or um.group("u2") or "").replace("\\%", "%")
                e_text = um.end()
            else:
                e_text = e
                # the first end of a range inherits the unit printed after the second: '1.5–3.5%'
                rm = re.match(r"\s?[–-]\s?\d[\d.,]*\s?(×|%|µs|ms|s\b)", line[e:])
                if rm:
                    unit = rm.group(1)
            occ = Occ(
                line=no, region=_region(h2), section=section, context=context,
                text=f"{sign if sign not in ('±',) else ''}{line[s:e_text]}".strip(),
                num=num, mantissa=mant, value=value, sig=_sig_digits(mant), dec=dec, kind=kind, unit=unit,
                in_math=_inside(s, math_ranges) or display, in_code=_inside(s, code_ranges),
                in_link=_inside(s, link_ranges),
                before=(prev_line[-40:] + " " + line[:s - (1 if sign and sign != '±' else 0)])[-70:],
                after=(line[e_text:] + " " + next_line)[:50],
                prefix=line[:s - (1 if sign and sign != '±' else 0)],
            )
            if is_row and table_line and table_line != no:
                occ.table_line = table_line
                occ.col = max(sum(1 for p in pipes if p < s) - 1, 0)
                cells = [c.strip() for c in PIPE.split(line.strip())[1:-1]]
                occ.row_label = cells[0] if cells else ""
                occ.col_header = header[occ.col] if occ.col < len(header) else ""
            occs.append(occ)
    return occs


# --------------------------------------------------------------------------- categories

ENV_BEFORE = re.compile(r"(?:Apple\s+M|macOS\s+|[Nn]um[Pp]y\s+|Python\s+|umap-learn\s+|scikit-learn\s+|numba\s+)$")
ENV_AFTER = re.compile(r"^\s?(?:GB|GHz|cores?)\b")
LABEL_BEFORE = re.compile(
    r"(?:§\s?|\b(?:Sections?|Appendix|Appendices|Figures?|Fig\.|Tables?|Propositions?|Prop\.|Corollar(?:y|ies)|"
    r"Remarks?|Lemmas?|Algorithm|Eq\.|Equations?|Rules?|[Pp]hases?|Part|[Ii]tems?)\s+)"
    r"(?:§?[A-D]?\d+(?:\.\d+)*\s*(?:[–\-]|,|and|&|or)\s*)*§?$")
STEP_BEFORE = re.compile(r"\b[Ss]teps?\s+(?:\d+\s*[–\-]\s*)?$")
CITE_BEFORE = re.compile(r"(?:et al\.,?\s*|[A-Z][\w'À-ÿ-]+(?: et al\.)?,\s*|[A-Z][\w'À-ÿ-]+\s\(|;\s*)$")
PARAM_STRONG = re.compile(
    r"(?:@|(?<![\w\\])(?:d|N|K|k|B|n|W)\s*=\s*|\\delta\s*=\s*|δ\s*=\s*|\bseeds?\s+)(?:[\d.,]+\s*[–\-]\s*)?$")
PARAM_AFTER = re.compile(
    r"^(?:-|\s)(?:(?:growth|nearest|true|initial|first|last|full)\s+)?"
    r"(?:chunks?|quer(?:y|ies)|steps?|transitions?|stimul(?:i|us)|vectors?|centroids?|"
    r"parts?|repetitions?|reps|runs?|warm-?up|iterations?|samples?|dimensions?|dimensional|neighbou?rs?|"
    r"batch(?:es)?|points?|arms?|rules?|frames?|pairs?|axes|bins?|labels?|entries|times\b|"
    r"references|instruments?)\b")
AFTER_LETTER_OK = re.compile(r"^(?:D\b|st\b|nd\b|rd\b|th\b|x\b|×)")
PARAM_TABLE_HEADERS = ("Corpus size (N)", "\\( d \\)")


def categorize(o: Occ, check_hit: bool, check_hit_1c: bool, config_hit: bool, data_hits: int) -> tuple[str, str]:
    b, a = o.before, o.after
    if o.region == "referencias":
        return "referencia", "seccion-de-referencias"
    if o.region == "portada":
        return "texto", "portada"
    if o.context == "encabezado":
        return "texto", "encabezado"
    if o.in_code or o.in_link:
        return "notacion", "codigo-o-enlace"
    if o.region == "declaraciones":
        return "notacion", "declaraciones"
    if o.kind == "version" or o.unit == "GB" or ENV_BEFORE.search(b) or ENV_AFTER.match(a):
        return "entorno", "entorno"
    if o.context == "formula" and o.prefix.strip() == "" and a.startswith("\\quad"):
        return "texto", "paso-de-algoritmo"
    if o.kind == "plain" and re.search(r"[_^]\{?-?$", b):
        return "notacion", "subindice-o-exponente"
    if o.kind == "plain" and (re.search(r"[A-Za-z][A-Za-z\d]*-?$", b) and not re.search(r"\s$", b)):
        return "notacion", "identificador"
    if o.kind == "plain" and re.match(r"^[A-Za-z_]", a) and not AFTER_LETTER_OK.match(a) and not o.unit:
        return "notacion", "identificador"
    if LABEL_BEFORE.search(b) or (STEP_BEFORE.search(b) and o.dec == 0 and o.kind == "plain"):
        return "texto", "referencia-interna"
    if o.context == "lista" and o.prefix.strip() == "" and re.match(r"^\.\s", a):
        return "texto", "numeracion-de-lista"
    if o.kind == "plain" and o.dec == 0 and re.fullmatch(r"(19[5-9]\d|20[0-2]\d)", o.num) and CITE_BEFORE.search(b):
        return "referencia", "cita-en-el-texto"
    if PARAM_STRONG.search(b) or re.match(r"^D\b", a):
        return "parametro", "parametro-explicito"
    if o.table_line and o.section.startswith("Appendix > Appendix B") or \
            o.table_line and o.section.startswith("Appendix > Appendix C"):
        return ("parametro", "columna-de-parametros") if o.col == 0 else ("resultado", "celda-tabla-ubicada")
    if check_hit:
        return "resultado", "coincide-con-chequeo"
    if o.table_line and o.col == 0 and any(h in o.col_header for h in PARAM_TABLE_HEADERS):
        return "parametro", "columna-de-parametros"
    if PARAM_AFTER.match(a):
        return "parametro", "parametro-por-contexto"
    if o.kind == "plain" and re.search(r"\d/$", o.prefix):
        return "parametro", "denominador"
    if config_hit:
        return "parametro", "coincide-con-config"
    if check_hit_1c:
        return "resultado", "coincide-con-chequeo-un-caracter"
    if o.unit == "°":
        return "derivacion", "angulo"
    if o.kind == "pow" and o.value > 1 and not o.table_line:
        return "resultado", "orden-de-magnitud"
    if o.table_line and o.col >= 1 and not o.section.startswith("Notation"):
        return "resultado", "celda-de-tabla"
    if data_hits:
        return "resultado", "coincide-con-datos"
    if o.unit in ("×", "%", "µs", "ms", "s"):
        return "resultado", "unidad-de-resultado"
    if o.kind == "plain" and o.dec >= 1 and not o.in_math and o.context in ("prosa", "lista", "leyenda"):
        # A decimal in running text is a result unless an earlier rule says otherwise. This rule
        # does not look at the evidence: otherwise a wrong figure, which matches no check, would
        # fall out of the category and H1 would under-count it (found by test_altered_occurrence).
        return "resultado", "decimal-en-texto"
    if o.in_math or o.context == "formula":
        return "derivacion", "formula"
    return "sin-clasificar", "sin-regla"


# --------------------------------------------------------------------------- assembly

def _norm_pub(p: str) -> str:
    return p.lstrip("+-−").replace(",", "")


def _close_sig(a: float, b: float, sig: int) -> bool:
    s = max(sig, 1) - 1
    return f"{abs(a):.{s}e}" == f"{abs(b):.{s}e}"


def section_number(section: str) -> str:
    """'3. Numerical Behavior > 3.5 Re-anchoring…' -> '3.5'; 'Appendix > Appendix B — …' -> 'B'."""
    for part in reversed(section.split(" > ")):
        m = re.match(r"(?:Appendix\s+)?([A-D]|\d+(?:\.\d+)*)[.\s—-]", part + " ")
        if m:
            return m.group(1)
    return ""


def label_section(label: str) -> str:
    m = re.match(r"§\s?([A-D]|\d+(?:\.\d+)*)", label)
    return m.group(1) if m else ""


STOPWORDS = {"the", "and", "per", "with", "for", "from", "over", "against", "text", "times", "quad", "left", "right"}


def words(s: str) -> set[str]:
    """Lower-case words of three letters or more, and every number, for overlap tests."""
    out = set()
    for w in re.split(r"[^0-9a-z]+", s.lower().replace(",", "")):
        if w and (w.isdigit() or (len(w) >= 3 and w not in STOPWORDS)):
            out.add(w)
    return out


def label_words(label: str) -> set[str]:
    return words(re.sub(r"^§\s?(?:[A-D]|\d+(?:\.\d+)*)", "", label))


def _prefix_overlap(a: set[str], b: set[str]) -> bool:
    """'trust' names the column 'Trustworthiness': one word is a prefix of the other (4+ letters)."""
    return any((x == y) if (x.isdigit() or y.isdigit()) else
               (min(len(x), len(y)) >= 4 and (x.startswith(y) or y.startswith(x))) for x in a for y in b)


def check_hits(o: Occ, by_pub) -> tuple[list, list]:
    """Checks that cover this occurrence: (multi-character hits, single-character hits).

    Multi-character strings match anywhere, as the verifier's presence check does; each hit
    records whether the check belongs to the occurrence's own section. Single-character
    strings and bare mantissas ('4.3' of 4.3 x 10^-16) match only checks of the same section,
    since across sections they coincide by chance.
    """
    sec = section_number(o.section)
    multi, single = [], []
    if o.unit == "°":
        return multi, single  # no check measures an angle
    context = words(o.before[-60:] + " " + o.after[:40] + " " + o.row_label + " " + o.col_header)
    if o.kind == "plain":
        for label, pub, meas in by_pub.get(o.num, []):
            same = label_section(label) == sec
            if "%" in label and o.unit != "%" and "%" not in o.col_header:
                continue  # a percentage check does not cover a number printed without a percent sign
            if len(_norm_pub(pub)) <= 1:
                # single characters: same section, same signed value, and the check's words in the context
                if same and float(meas) == o.value and label_words(label) & context:
                    single.append((label, pub, meas, True))
            else:
                multi.append((label, pub, meas, same))
    elif o.kind in ("sci", "pow"):
        for label, pub, meas in by_pub.get(o.num, []):
            if _close_sig(meas, o.value, o.sig):
                multi.append((label, pub, meas, label_section(label) == sec))
        for label, pub, meas in by_pub.get(o.mantissa, []):
            if label_section(label) == sec and len(_norm_pub(pub)) > 1 and (
                    _close_sig(meas, o.value, o.sig) or _close_sig(meas, float(o.mantissa), o.sig)):
                multi.append((label, pub, meas, True))
    return multi, single


def appendix_tables(v, occs: list[Occ]) -> dict[tuple[str, int], tuple[float, float, str]]:
    """Per (appendix, table line, row key, column): printed vs guarded constant vs recomputed."""
    out = {}
    measured_b = {r: v._measure_conditioning(r) for r in v.PUBLISHED_CONDITIONING}
    measured_c = {dl: v._measure(dl) for dl in v.PUBLISHED}
    rows: dict[tuple[str, int], list[Occ]] = defaultdict(list)
    for o in occs:
        if o.table_line and o.section.startswith("Appendix > Appendix B"):
            rows[("B", o.line)].append(o)
        elif o.table_line and o.section.startswith("Appendix > Appendix C"):
            rows[("C", o.line)].append(o)
    for (app, line), row in rows.items():
        keyocc = next((o for o in row if o.col == 0), None)
        if keyocc is None:
            continue
        key = keyocc.value
        for o in row:
            if o.col == 0:
                guarded_keys = v.PUBLISHED_CONDITIONING if app == "B" else v.PUBLISHED
                ok = any(math.isclose(key, g, rel_tol=1e-12) for g in guarded_keys)
                out[(app, id(o))] = (key, key, "PASS" if ok else "MISMATCH")
                continue
            if app == "B":
                gk = next((g for g in v.PUBLISHED_CONDITIONING if math.isclose(g, key, rel_tol=1e-12)), None)
                if gk is None or o.col > 2:
                    out[(app, id(o))] = (o.value, float("nan"), "MISMATCH")
                    continue
                guarded = v.PUBLISHED_CONDITIONING[gk][o.col - 1]
                meas = measured_b[gk][o.col - 1]
                located = math.isclose(o.value, guarded, rel_tol=1e-12)
                status = v._log_status(meas, guarded)
            else:
                gk = next((g for g in v.PUBLISHED if math.isclose(g, key, rel_tol=1e-12)), None)
                if gk is None or o.col > 3:
                    out[(app, id(o))] = (o.value, float("nan"), "MISMATCH")
                    continue
                guarded = v.PUBLISHED[gk][o.col - 1]
                meas = measured_c[gk][o.col - 1]
                located = math.isclose(o.value, guarded, rel_tol=1e-12)
                status = v._status(meas, guarded)
            out[(app, id(o))] = (guarded, meas, "PASS" if located and status == "PASS" else "MISMATCH")
    return out


def build(root: Path):
    v = load_verifier(root)
    checks, sources, trace_errors = trace_checks(v)
    artifacts = load_artifacts(root)
    writers = artifact_writers(root)
    data_index = DataIndex(artifacts)
    configs, config_ints = config_index(artifacts)
    literals = code_literals(root)
    env_text = environment_text(artifacts)
    registry = read_registry(root)
    occs = scan_manuscript(root)
    tables = appendix_tables(v, occs)

    by_pub: dict[str, list[tuple[str, str, float]]] = defaultdict(list)
    for label, pub, meas in checks:
        by_pub[_norm_pub(pub)].append((label, pub, meas))
    deps_cache: dict[str, list[str]] = {}

    def deps_of(script: str) -> list[str]:
        if script not in deps_cache:
            deps_cache[script] = sorted(script_deps(root, script))
        return deps_cache[script]

    def code_for(arts: list[str]) -> tuple[list[str], list[str]]:
        code, deps = [], []
        for art in arts:
            for w in writers.get(art, []):
                code.append(w)
                deps.extend(f"{art} ← {w} ← {d}" for d in deps_of(w))
            if not writers.get(art):
                code.append(f"{art}: escritor no encontrado")
        return sorted(set(code)), sorted(set(deps))

    num_count = Counter(o.num for o in occs)
    for o in occs:
        hits, hits_1c = check_hits(o, by_pub)
        data_hits = data_index.find(o) if o.sig >= 3 else []
        if o.kind == "plain" and (abs(o.value) >= 10 or (o.dec >= 1 and not o.in_math)):
            config_hits = configs.get(o.value, [])
        elif o.kind == "pow" and o.value < 1:  # 10^-k in a sweep that records k
            k = round(-math.log10(o.value))
            config_hits = [f"{p} (10^-{k})" for p in config_ints.get(k, [])]
        else:
            config_hits = []
        o.category, o.rule = categorize(o, bool(hits), bool(hits_1c), bool(config_hits), len(data_hits))

        if o.category in EXCLUDED:
            o.status = "excluida"
            continue
        if o.category == "sin-clasificar":
            o.status = "por-decidir"
            continue
        if o.category == "entorno":
            printed = o.num if o.kind == "version" else o.text.split()[0]
            found = len(printed) >= 3 and re.search(rf"(?<![\d.]){re.escape(printed)}(?![\d])", env_text)
            o.status = "en-artefacto" if found else "declarada"
            if found:
                o.data = "host/thread_env de los artefactos"
            continue
        if o.category == "derivacion":
            o.status = "por-mapear"
            continue

        app = "B" if o.section.startswith("Appendix > Appendix B") else "C" if o.section.startswith(
            "Appendix > Appendix C") else ""
        if app and o.table_line and (app, id(o)) in tables:
            guarded, meas, verdict = tables[(app, id(o))]
            tol = "±2.0 décadas" if app == "B" else "rel 1e-3"
            if o.col == 0:
                o.status = "fijado-en-codigo" if verdict == "PASS" else "prueba-falla"
                o.data = f"constante del verificador (fila de la tabla §{app})"
                o.tests = [f"tabla §{app}: filas impresas = filas guardadas"]
            else:
                o.status = "atada-ubicada" if verdict == "PASS" else "prueba-falla"
                o.data = f"recálculo: {meas:.4g} (constante guardada {guarded:.4g})"
                o.tests = [f"tabla §{app}: celda = constante (rel 1e-12); constante ≈ recálculo ({tol})"]
            o.located = "sí"
            o.code = ["tools/verify_paper_tables.py (recalcula con el operador)"]
            o.deps = ["polar_projector/", "polar_projector/fixtures.py"]
            o.registry = registry_special(registry, f"recompute:§{app}")
            continue

        if o.category == "resultado":
            use = hits or hits_1c
            if o.table_line and hits:
                # In a table, a check counts for this cell only if it names the cell's row, or
                # belongs to the same section and names the cell's column (code and prose may call
                # the same row differently: 'pc1_extremes' is printed as 'First-PC deciles').
                row, col = words(o.row_label), words(o.col_header)
                same_row = [h for h in hits
                            if label_words(h[0]) & row or (h[3] and _prefix_overlap(label_words(h[0]), col))]
                if not same_row:
                    o.status = "coincide-otra-cifra"
                    o.tests = sorted({h[0] for h in hits})
                    o.located = "no"
                    o.note.append("la cadena coincide con chequeos que no nombran ni esta fila ni esta columna")
                    o.data = "; ".join(f"{h[0]} = {h[2]:.6g}" for h in hits[:3])
                    continue
                use = hits = same_row
            if use:
                labels = sorted({h[0] for h in use})
                agree = [v._agree(h[2], h[1]) for h in use]
                o.tests = labels
                o.located = "no (presencia)" if hits else "no (un carácter)"
                arts = sorted({a for lab in labels for a in sources.get(lab, [])})
                o.data = "; ".join(f"{h[0]} = {h[2]:.6g}" for h in use[:3]) + (" …" if len(use) > 3 else "")
                o.code, o.deps = code_for(arts)
                o.registry = sorted({r for lab in labels for r in registry_for(registry, lab)}, key=_id_key)
                if not any(agree):
                    o.status = "prueba-falla"
                elif not hits:
                    o.status = "atada-un-caracter"
                elif not any(h[3] for h in hits) and max(len(_norm_pub(h[1])) for h in hits) <= 3:
                    # a short string ('29', '24', '2.7') matched only by a check of another section:
                    # it may be the same figure repeated or a different figure that prints the same
                    o.status = "presencia-dudosa"
                    o.note.append("cadena corta casada solo con un chequeo de otra sección")
                else:
                    o.status = "atada-presencia"
                if hits and not any(h[3] for h in hits):
                    o.note.append("chequeo de otra sección: "
                                  + ", ".join(sorted({"§" + label_section(h[0]) for h in hits})))
                if len(labels) > 1:
                    o.note.append(f"cadena compartida por {len(labels)} chequeos")
                if num_count[o.num] > 1:
                    o.note.append(f"la cadena aparece {num_count[o.num]} veces en el manuscrito")
                if not arts:
                    o.note.append("chequeo sin artefacto detectado")
                if not o.registry:
                    o.note.append("chequeo sin fila en el registro")
            elif data_hits:
                arts = sorted({h.split(":")[0] for h in data_hits})
                o.data = "; ".join(data_hits[:3]) + (f" … ({len(data_hits)} coincidencias)" if len(data_hits) > 3 else "")
                o.code, o.deps = code_for(arts)
                o.status = "datos-sin-prueba"
                o.note.append("sin chequeo; algún artefacto contiene ese valor a la precisión impresa, "
                              "lo que puede ser casual")
            else:
                o.status = "sin-respaldo"
            continue

        if o.category == "parametro":
            if config_hits:
                arts = sorted({h.split(":")[0] for h in config_hits})
                o.data = "; ".join(config_hits[:3]) + (" …" if len(config_hits) > 3 else "")
                o.code, o.deps = code_for(arts)
                o.status = "fijado-en-config"
            elif literals.get(o.value):
                lits = literals[o.value]
                o.data = "literal: " + "; ".join(lits[:3]) + (f" … ({len(lits)})" if len(lits) > 3 else "")
                o.status = "literal-en-codigo"
            else:
                o.status = "sin-respaldo-en-codigo"
    return dict(v=v, checks=checks, sources=sources, trace_errors=trace_errors, occs=occs,
                writers=writers, registry=registry)


# --------------------------------------------------------------------------- output

COLUMNS = ["id", "linea", "region", "seccion", "contexto", "tabla", "cifra", "valor", "categoria", "regla",
           "estado", "pruebas", "ubicada", "datos", "codigo", "depende_de", "registro", "nota"]


def write_csv(occs: list[Occ], path: Path) -> None:
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(COLUMNS)
        for n, o in enumerate(occs, 1):
            w.writerow([n, o.line, o.region, o.section, o.context, o.table, o.text, f"{o.value:.6g}", o.category,
                        o.rule, o.status, "; ".join(o.tests), o.located, o.data, "; ".join(o.code),
                        "; ".join(o.deps), "; ".join(o.registry), "; ".join(o.note)])


def _git(root: Path, *args: str) -> str:
    try:
        return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True,
                              check=True).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "(sin git)"


def write_summary(res: dict, root: Path, path: Path) -> None:
    occs: list[Occ] = res["occs"]
    checks = res["checks"]
    by_cat = Counter(o.category for o in occs)
    by_cat_status = Counter((o.category, o.status) for o in occs)
    statuses = sorted({o.status for o in occs})
    multi = [(lab, pub) for lab, pub, _ in checks if len(_norm_pub(pub)) > 1]
    matched = {t for o in occs for t in o.tests}
    unmatched = [(lab, pub) for lab, pub in multi if lab not in matched]
    no_source = [lab for lab, _, _ in checks if lab not in res["sources"]]
    shared = Counter(_norm_pub(p) for _, p, _ in checks if len(_norm_pub(p)) > 1)
    res_rows = [o for o in occs if o.category == "resultado"]
    L = []
    L.append("# Matriz de trazabilidad: resumen (generado)\n")
    inputs = _git(root, "log", "-1", "--format=%h", "--", "paper", "bench", "tools", "polar_projector")
    L.append(f"Generado por `method-paper/prep/matrix/build_matrix.py` en el commit "
             f"`{_git(root, 'rev-parse', '--short', 'HEAD')}`; el último commit que cambió sus entradas "
             f"(`paper/`, `bench/`, `tools/`, `polar_projector/`) es `{inputs}`. No editar a mano: se "
             f"regenera con `python method-paper/prep/matrix/build_matrix.py`.\n")
    L.append(f"- Filas (apariciones de cifras en el manuscrito): {len(occs)}")
    L.append(f"- Chequeos del verificador: {len(checks)}; con cadena de más de un carácter: {len(multi)}")
    L.append(f"- Chequeos de más de un carácter que no casan con ninguna fila: {len(unmatched)}")
    L.append(f"- Chequeos sin artefacto detectado al perturbar: {len(no_source)}")
    L.append(f"- Cadenas comprobadas que aparecen en más de un sitio del manuscrito: "
             f"{sum(1 for k in shared if Counter(o.num for o in occs)[k] > 1)}")
    L.append(f"- Cadenas compartidas por más de un chequeo: {sum(1 for k, n in shared.items() if n > 1)}")
    pres = [o for o in occs if o.status == "atada-presencia"]
    other = [o for o in pres if any(n.startswith("chequeo de otra sección") for n in o.note)]
    L.append(f"- Cifras atadas por presencia: {len(pres)}; con el chequeo en otra sección: {len(other)}\n")
    L.append("## Categoría lógica × estado\n")
    L.append("| Categoría | " + " | ".join(statuses) + " | Total |")
    L.append("|---|" + "---:|" * (len(statuses) + 1))
    for cat in CATEGORIES:
        if by_cat[cat]:
            L.append(f"| {cat} | " + " | ".join(str(by_cat_status[(cat, s)] or "") for s in statuses)
                     + f" | {by_cat[cat]} |")
    L.append(f"| **Total** | " + " | ".join(str(sum(by_cat_status[(c, s)] for c in CATEGORIES)) for s in statuses)
             + f" | **{len(occs)}** |\n")
    def row(o: Occ) -> str:
        ctx = (o.table or o.before[-45:]).replace("|", "/").replace("\n", " ")
        return (f"| {o.line} | {o.text.replace('|', '')} | {o.status} | {o.rule} | "
                f"{o.data[:60].replace('|', '/')} | {ctx[:90]} |")

    L.append("## H1: cifras de resultado que no están atadas\n")
    L.append("Candidatas a refutar H1. Cada una pide revisión humana: la categoría la asignó una regla.\n")
    L.append("| Línea | Cifra | Estado | Regla | Datos | Contexto |")
    L.append("|---:|---|---|---|---|---|")
    for o in res_rows:
        if o.status not in ("atada-ubicada", "atada-presencia", "atada-un-caracter", "presencia-dudosa"):
            L.append(row(o))
    L.append("\n## Presencia dudosa: cadenas cortas casadas con un chequeo de otra sección\n")
    L.append("Pueden ser la misma cifra repetida (el 29× del resumen es el del §3.5) o una cifra distinta "
             "que se imprime igual. Solo leyendo se distingue.\n")
    L.append("| Línea | Cifra | Estado | Regla | Datos | Contexto |")
    L.append("|---:|---|---|---|---|---|")
    for o in res_rows:
        if o.status == "presencia-dudosa":
            L.append(row(o))
    L.append("\n## Atadas solo por valor: cifras de un carácter\n")
    L.append("El verificador las cuenta pero no las ubica. Aquí se aceptan si un chequeo de la misma sección "
             "tiene el mismo valor y comparte palabras con el texto que las rodea.\n")
    L.append("| Línea | Cifra | Estado | Regla | Datos | Contexto |")
    L.append("|---:|---|---|---|---|---|")
    for o in res_rows:
        if o.status == "atada-un-caracter":
            L.append(row(o))
    L.append("\n## Chequeos que no casan con ninguna fila\n")
    L.append("Si no es cero, el lector de la matriz no reconoce una cifra que el verificador sí encuentra.\n")
    for lab, pub in unmatched:
        L.append(f"- `{lab}` = `{pub}`")
    if not unmatched:
        L.append("- Ninguno.")
    L.append("\n## Chequeos sin artefacto detectado al perturbar\n")
    for lab in no_source:
        L.append(f"- `{lab}`")
    if not no_source:
        L.append("- Ninguno.")
    if res["trace_errors"]:
        L.append("\nPerturbaciones que rompieron el cálculo (no aportan dependencia):\n")
        for art, errs in sorted(res["trace_errors"].items()):
            L.append(f"- `{art}`: {', '.join(errs)}")
    L.append("\n## Sin clasificar (por decidir)\n")
    for o in occs:
        if o.category == "sin-clasificar":
            L.append(f"- L{o.line} `{o.text}` … {o.before[-40:].strip()} ⟨{o.text}⟩ {o.after[:25].strip()}")
    L.append("\n## Reglas que asignaron cada categoría\n")
    L.append("| Categoría | Regla | Filas |")
    L.append("|---|---|---:|")
    for (cat, rule), n in sorted(Counter((o.category, o.rule) for o in occs).items()):
        L.append(f"| {cat} | {rule} | {n} |")
    path.write_text("\n".join(L) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    ap.add_argument("--out", type=Path, default=HERE)
    args = ap.parse_args(argv)
    root, out = args.root.resolve(), args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    res = build(root)
    write_csv(res["occs"], out / "matrix.csv")
    write_summary(res, root, out / "summary.md")
    print(f"{len(res['occs'])} filas -> {out / 'matrix.csv'}; resumen -> {out / 'summary.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
