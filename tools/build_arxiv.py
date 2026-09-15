"""Build the arXiv LaTeX source from the canonical Markdown manuscript.

paper/polar-projector-paper.md stays the only place the manuscript is edited: CI
verifies its figures there. This script generates paper/build/main.tex from it, one
way, and never the reverse -- a correction found in the LaTeX goes back into the
Markdown and the source is rebuilt.

What the build does, and why:

- Strips the editorial note, which is repository scaffolding, and moves the title,
  author, date and abstract into pandoc metadata so they typeset as a title block.
- Shifts headings up one level: the manuscript's "##" sections become \\section.
- Points figures at the vector PDFs from tools/make_figures.py and copies them in.
- Rewrites every "\\|" inside math as "\\Vert". In a Markdown pipe table pandoc reads
  "\\|" as an escaped cell separator and would print |r| for the norm ||r||.
- Declares every non-ASCII character that pdfLaTeX (arXiv's default engine) cannot
  typeset from UTF-8 on its own, via newunicodechar. The build fails if a character
  appears that is neither declared nor known to be supported, rather than letting it
  surface as a compile error on arXiv.

It checks what it can without a TeX engine -- math spans preserved, no stray pipes
in math, no editorial note left, no unhandled characters -- and warns about TODO
markers still in the text. It does not compile; that needs pdfLaTeX.

Usage:
    python tools/build_arxiv.py
    python tools/build_arxiv.py --out paper/build
"""

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANUSCRIPT = ROOT / "paper" / "polar-projector-paper.md"

# Characters pdfLaTeX handles from UTF-8 with the LaTeX kernel's own definitions
# (T1 / TS1 encodings, LaTeX 2018 or later).
KERNEL_SUPPORTED = set("\u2014\u2013×§µüã†²·ĉ")  # em dash, en dash, then the rest literally

# Characters that need an explicit declaration. Box-drawing rules become hyphens so
# Algorithm 1 keeps its monospaced alignment.
UNICODE_DECLARATIONS = {
    "≈": r"\ensuremath{\approx}",
    "∎": r"\ensuremath{\blacksquare}",
    "δ": r"\ensuremath{\delta}",
    "ε": r"\ensuremath{\varepsilon}",
    "λ": r"\ensuremath{\lambda}",
    "\u03c3": r"\ensuremath{\sigma}",  # greek small sigma
    "‖": r"\ensuremath{\Vert}",
    "₁": r"\ensuremath{_1}",
    "₂": r"\ensuremath{_2}",
    "ₙ": r"\ensuremath{_n}",
    "←": r"\ensuremath{\leftarrow}",
    "−": r"\ensuremath{-}",
    "√": r"\ensuremath{\surd}",
    "≥": r"\ensuremath{\geq}",
    "⊥": r"\ensuremath{\perp}",
    "─": "-",
    "▷": r"\ensuremath{\triangleright}",
    "⟨": r"\ensuremath{\langle}",
    "⟩": r"\ensuremath{\rangle}",
    "°": r"\ensuremath{^\circ}",
}

MATH_SPAN = re.compile(r"\\\((.+?)\\\)|\\\[(.+?)\\\]", flags=re.S)

# pandoc's longtable output splits width evenly across columns when it can't
# infer a ratio from the Markdown source, which is most of the time for this
# manuscript's result tables: a wide row-label column next to several narrow
# numeric ones ends up with every column the same size, so the label wraps
# 4-5 lines deep and a long header ("Trustworthiness (isometric)") collides
# with its neighbour. This rebalances each wrapped (p{}-column) longtable by
# the actual text it holds, in two passes: total content length (so a column
# mostly full of short numbers stays narrow) and longest unbreakable word
# (so a header or a `texttt` identifier that cannot wrap gets enough room for
# one line). Monospace text is weighted up because Latin Modern Mono renders
# wider per character than the body roman font at the same size.
_LONGTABLE = re.compile(
    r"\\begin\{longtable\}\[\]\{@\{\}\n(.*?)@\{\}\}\n(.*?)(?=\\end\{longtable\})",
    flags=re.S,
)
_TABLE_HEADER = re.compile(r"\\toprule\\noalign\{\}\n(.*?)\\\\\n\\midrule", flags=re.S)
_TABLE_BODY = re.compile(r"\\endlastfoot\n(.*)$", flags=re.S)
_MINIPAGE_CELL = re.compile(r"\\begin\{minipage\}\[b\]\{\\linewidth\}\\ragged(?:right|left)\n?")
_MINIPAGE_SPLIT = re.compile(r"\\end\{minipage\}\s*&\s*")
_TEXTT_CELL = re.compile(r"\\texttt\{([^}]*)\}")
TABLE_MIN_FRACTION = 0.08
TABLE_MONO_WEIGHT = 1.6


def _cell_text(cell: str) -> str:
    """Strip LaTeX markup down to roughly what will be visible, for sizing only."""

    def _widen_mono(m: re.Match[str]) -> str:
        inner = m.group(1)
        return inner + "#" * round(len(inner) * (TABLE_MONO_WEIGHT - 1))

    cell = _TEXTT_CELL.sub(_widen_mono, cell)
    cell = _MINIPAGE_CELL.sub("", cell).replace("\\end{minipage}", "")
    cell = re.sub(r"\\[a-zA-Z]+\{", "", cell)  # \emph{ \textbf{ ... -> drop the opener
    cell = cell.replace("}", "")
    cell = re.sub(r"\\\(|\\\)", "", cell)
    cell = cell.replace("\\_", "_")
    cell = re.sub(r"\\[a-zA-Z]+", "", cell)  # remaining bare commands, e.g. \times
    cell = re.sub(r"\[[a-z]\]", "", cell)
    return cell


def _cell_lengths(cell: str) -> tuple[int, int]:
    """(visible character count, longest single unbreakable word) for one cell."""
    text = _cell_text(cell)
    words = re.split(r"[\s\-]+", text.strip())
    longest_word = max((len(w) for w in words if w), default=0) + 2  # rounding margin
    visible = len(re.sub(r"\s+", " ", text.replace("~", " ")).strip())
    return visible, longest_word


def _column_fractions(n_cols: int, header: str, body: str) -> list[float]:
    content_w = [1] * n_cols
    word_w = [1] * n_cols
    header_cells = _MINIPAGE_SPLIT.split(header)[:n_cols] if header else []
    for i, cell in enumerate(header_cells):
        visible, word = _cell_lengths(cell)
        content_w[i], word_w[i] = max(content_w[i], visible), max(word_w[i], word)
    for row in body.split("\\\\"):
        if not row.strip():
            continue
        cells = " ".join(row.split("\n")).split("&")[:n_cols]
        for i, cell in enumerate(cells):
            visible, word = _cell_lengths(cell.strip())
            content_w[i], word_w[i] = max(content_w[i], visible), max(word_w[i], word)

    def normalize(weights: list[float]) -> list[float]:
        total = sum(weights) or 1.0
        return [w / total for w in weights]

    fractions = [max(a, b) for a, b in zip(normalize(content_w), normalize(word_w))]
    fractions = normalize(fractions)
    deficits = [max(0.0, TABLE_MIN_FRACTION - f) for f in fractions]
    if any(deficits):
        excess = sum(deficits)
        above = [max(0.0, f - TABLE_MIN_FRACTION) for f in fractions]
        above_total = sum(above) or 1.0
        fractions = [f + d - excess * (a / above_total) for f, d, a in zip(fractions, deficits, above)]
    return normalize(fractions)


def rebalance_table_columns(tex: str) -> tuple[str, int]:
    """Recompute every wrapped longtable's column widths from its own text."""
    n_rebalanced = 0

    def fix_one(m: re.Match[str]) -> str:
        nonlocal n_rebalanced
        colspec, rest = m.group(1), m.group(2)
        n_cols = colspec.count("\\real{")
        if n_cols < 2:
            return m.group(0)
        header_m, body_m = _TABLE_HEADER.search(rest), _TABLE_BODY.search(rest)
        fractions = _column_fractions(
            n_cols, header_m.group(1) if header_m else "", body_m.group(1) if body_m else ""
        )
        n_rebalanced += 1
        tabcolsep_n = 2 * (n_cols - 1)
        lines = "\n".join(
            f"  >{{\\raggedright\\arraybackslash}}p{{(\\linewidth - {tabcolsep_n}\\tabcolsep) * \\real{{{f:.4f}}}}}"
            for f in fractions
        )
        return f"\\begin{{longtable}}[]{{@{{}}\n{lines}@{{}}}}\n{rest}"

    return _LONGTABLE.sub(fix_one, tex), n_rebalanced


def split_manuscript(text: str) -> tuple[str, dict[str, str], str, str]:
    """Title, front-matter fields, abstract and body of the manuscript."""
    lines = text.splitlines()
    if not lines[0].startswith("# "):
        raise SystemExit("ERR: the manuscript must open with a '# ' title line")
    title = lines[0][2:].strip()

    front = {}
    for key in ("Author", "Affiliation", "Date"):
        match = re.search(rf"^\*\*{key}:\*\*\s*(.+)$", text, flags=re.M)
        if match is None:
            raise SystemExit(f"ERR: front matter has no **{key}:** line")
        front[key.lower()] = match.group(1).strip()

    abstract_start = text.index("## Abstract\n")
    body_start = text.index("## 1. Introduction\n")
    abstract = text[abstract_start + len("## Abstract\n"):body_start].strip()
    body = text[body_start:]
    return title, front, abstract, body


def rewrite_math_norms(text: str) -> tuple[str, int]:
    """Replace \\| with \\Vert inside math spans; count what was rewritten."""
    count = 0

    def fix(match: re.Match[str]) -> str:
        nonlocal count
        span = match.group(0)
        count += span.count("\\|")
        return span.replace("\\|", "\\Vert ")

    rewritten = MATH_SPAN.sub(fix, text)
    outside = MATH_SPAN.sub("", rewritten)
    if "\\|" in outside:
        raise SystemExit("ERR: a '\\|' appears outside math; rewriting it would change prose")
    return rewritten, count


def shift_headings(text: str) -> str:
    return re.sub(r"^(#{2,6}) ", lambda m: "#" * (len(m.group(1)) - 1) + " ", text, flags=re.M)


def yaml_block(value: str) -> str:
    return "|\n" + "\n".join(f"  {line}" if line else "" for line in value.splitlines())


def header_tex() -> str:
    lines = [
        r"\usepackage{amsmath,amssymb}",
        r"\usepackage{newunicodechar}",
        r"\usepackage{microtype}",
    ]
    lines += [rf"\newunicodechar{{{ch}}}{{{tex}}}" for ch, tex in UNICODE_DECLARATIONS.items()]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT / "paper" / "build")
    args = parser.parse_args()
    out: Path = args.out
    out.mkdir(parents=True, exist_ok=True)

    source = MANUSCRIPT.read_text(encoding="utf-8")
    title, front, abstract, body = split_manuscript(source)

    unhandled = sorted({ch for ch in title + abstract + body if ord(ch) > 126}
                       - KERNEL_SUPPORTED - set(UNICODE_DECLARATIONS))
    if unhandled:
        raise SystemExit(f"ERR: characters with no pdfLaTeX handling: {unhandled}")

    abstract, abstract_norms = rewrite_math_norms(abstract)
    body, body_norms = rewrite_math_norms(body)
    body = shift_headings(body)
    # Figures: the Markdown shows PNGs; LaTeX includes the vector PDFs beside them.
    body, n_figures = re.subn(r"\]\(figures/([\w\-]+)\.png\)", r"](figures/\1.pdf)", body)
    figures_dir = MANUSCRIPT.parent / "figures"
    if n_figures:
        shutil.copytree(figures_dir, out / "figures", dirs_exist_ok=True)

    metadata = "\n".join([
        "---",
        f"title: {yaml_block(title)}",
        f"author: {yaml_block(front['author'] + ', ' + front['affiliation'])}",
        f"date: {yaml_block(front['date'])}",
        f"abstract: {yaml_block(abstract)}",
        "---",
        "",
    ])
    (out / "arxiv.md").write_text(metadata + body, encoding="utf-8")
    (out / "header.tex").write_text(header_tex(), encoding="utf-8")

    subprocess.run(
        [
            "pandoc", str(out / "arxiv.md"),
            "--from", "markdown+tex_math_single_backslash",
            "--resource-path", str(out),
            "--to", "latex", "--standalone",
            "--include-in-header", str(out / "header.tex"),
            "--columns", "100",
            "-V", "documentclass=article",
            "-V", "fontsize=10pt",
            "-V", "geometry:margin=1in",
            "-V", "colorlinks=true",
            "--output", str(out / "main.tex"),
        ],
        check=True,
    )

    tex, n_rebalanced = rebalance_table_columns((out / "main.tex").read_text(encoding="utf-8"))
    (out / "main.tex").write_text(tex, encoding="utf-8")

    source_math = len(MATH_SPAN.findall(source[source.index("## Abstract"):]))
    tex_math = tex.count("\\(") + tex.count("\\[")
    problems = []
    if "Editorial note" in tex:
        problems.append("the editorial note reached the LaTeX")
    if re.search(r"\\\((?:(?!\\\)).)*\\textbar(?:(?!\\\)).)*\\\)", tex, flags=re.S):
        problems.append("a \\textbar survived inside inline math")
    if tex.count("\\includegraphics") != n_figures:
        problems.append("a figure in the manuscript did not reach the LaTeX")
    if tex_math < source_math:
        problems.append(f"math spans dropped: {source_math} in the manuscript, {tex_math} in the LaTeX")

    print(f"wrote {out / 'main.tex'}")
    print(f"  sections {tex.count(chr(92) + 'section{')}, subsections {tex.count(chr(92) + 'subsection{')}, "
          f"tables {tex.count(chr(92) + 'begin{longtable}')}, math spans {tex_math} (manuscript {source_math})")
    print(f"  norms rewritten to \\Vert: {abstract_norms + body_norms}; "
          f"unicode characters declared: {len(UNICODE_DECLARATIONS)}; "
          f"figures {tex.count(chr(92) + 'includegraphics')} (manuscript {n_figures})")
    print(f"  table columns rebalanced by content: {n_rebalanced}")
    todos = [m.start() for m in re.finditer(r"TODO", tex)]
    if todos:
        print(f"  WARNING: {len(todos)} TODO marker(s) still in the text")
    for problem in problems:
        print(f"  ERROR: {problem}")
    print("  not compiled: this checks the conversion, not the typesetting (needs pdfLaTeX)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
