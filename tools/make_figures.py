"""Generate the manuscript's three figures from committed data, deterministically.

Every value plotted comes from a committed artifact in bench/results/ or from the
operator evaluated on the hash-committed corpus in bench/data/; nothing is
re-measured, and no figure carries a number the manuscript does not already quote
through a registered claim. Output goes to paper/figures/: a PDF for the LaTeX build
and a PNG for review and for the Markdown.

  fig1_screen_mapping   §2.1  the published frame's chunks at unit and isometric scale
  fig2_displacement     §3.2  aligned p95 displacement per growth step, by arm
  fig3_scale_ratio      §3.5  local recall against the screen ratio (exploratory ablation)

Palette: the first four categorical slots of the validated default palette, checked
with the dataviz validator (adjacent pairs for lines; all pairs for the two scatter
series). Slots below 3:1 contrast carry direct labels, and every value is also in a
manuscript table.

Usage:
    python tools/make_figures.py
"""

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "bench"))
sys.path.insert(0, str(ROOT))

from _harness import dipole_poles, load_corpus  # noqa: E402
from drift import N_INITIAL  # noqa: E402

from polar_projector import PolarProjector  # noqa: E402

OUT = ROOT / "paper" / "figures"
RESULTS = ROOT / "bench" / "results"

SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]  # categorical slots 1-4, light
SURFACE = "#ffffff"
INK = "#0b0b0b"
INK_SECONDARY = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.size": 8.5,
    "axes.edgecolor": AXIS,
    "axes.labelcolor": INK_SECONDARY,
    "axes.linewidth": 0.75,
    "axes.titlesize": 9,
    "axes.titlecolor": INK,
    "xtick.color": MUTED,
    "ytick.color": MUTED,
    "xtick.labelcolor": INK_SECONDARY,
    "ytick.labelcolor": INK_SECONDARY,
    "legend.frameon": False,
    "legend.labelcolor": INK_SECONDARY,
    "figure.facecolor": SURFACE,
    "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE,
    "pdf.fonttype": 42,
    "svg.hashsalt": "polar-projector",
})


def results(name: str) -> dict:
    return json.loads((RESULTS / name).read_text(encoding="utf-8"))["results"]


def recessive(ax: plt.Axes, grid_axis: str = "y") -> None:
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.grid(axis=grid_axis, color=GRID, linewidth=0.6, linestyle="-")
    ax.set_axisbelow(True)
    ax.tick_params(length=2.5, width=0.6)


def save(fig: plt.Figure, stem: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / f"{stem}.pdf", bbox_inches="tight", metadata={"CreationDate": None, "ModDate": None})
    fig.savefig(OUT / f"{stem}.png", bbox_inches="tight", dpi=220, metadata={"Software": None})
    plt.close(fig)


def fig1_screen_mapping() -> None:
    """The published frame's corpus on screen, unit scale beside isometric scale."""
    vectors, parts = load_corpus()
    window, window_parts = vectors[:N_INITIAL], parts[:N_INITIAL]
    c_1 = window.mean(axis=0)
    c_A, c_B = dipole_poles(window, window_parts)
    projector = PolarProjector()
    frame = projector.prepare(c_1, c_A, c_B)
    dipole_norm = float(np.sqrt(frame.v_dipole_norm_sq))

    coords = np.array([projector.evaluate(v, frame, i)[1:] for i, v in enumerate(vectors)])
    lam, d_esc = coords[:, 0], coords[:, 1]
    saturated = np.abs(lam) == 1.0
    poles = [(projector.evaluate(p, frame, 0)[1], name) for p, name in
             ((c_A, "pole A (P1_GOD)"), (c_B, "pole B (P2_MIND)"))]

    fig, axes = plt.subplots(1, 2, figsize=(6.5, 2.9), sharey=True, constrained_layout=True)
    panels = [
        (axes[0], 1.0, "Unit scale ($S_x = S_y$)", r"$\lambda$"),
        (axes[1], dipole_norm, r"Isometric scale ($S_x = \Vert v_{dipole}\Vert_2\, S_y$)",
         r"$\lambda \cdot \Vert v_{dipole}\Vert_2$"),
    ]
    y_top = float(d_esc.max()) * 1.05
    for ax, scale, title, xlabel in panels:
        recessive(ax, grid_axis="both")
        for bound in (-scale, scale):
            ax.axvline(bound, color=MUTED, linewidth=0.6, zorder=1)
        ax.scatter(lam[~saturated] * scale, d_esc[~saturated], s=6, color=SERIES[0], alpha=0.45,
                   linewidths=0, label="unsaturated", zorder=2, rasterized=True)
        ax.scatter(lam[saturated] * scale, d_esc[saturated], s=6, color=SERIES[1], alpha=0.6,
                   linewidths=0, label=r"saturated, $|\lambda| = 1$", zorder=3, rasterized=True)
        for pole_lambda, name in poles:
            ax.plot(pole_lambda * scale, 0.0, marker="D", markersize=6, color=INK,
                    markeredgecolor=SURFACE, markeredgewidth=1.2, linestyle="none", zorder=4, clip_on=False)
        ax.set_xlim(-1.12, 1.12)
        ax.set_ylim(0.0, y_top)
        ax.set_aspect("equal")
        ax.set_title(title, loc="left")
        ax.set_xlabel(xlabel)
    axes[0].set_ylabel(r"$d_{esc}$")

    for pole_lambda, name in poles:
        axes[0].annotate(f"{name}\n$\\lambda = {pole_lambda:+.3f}$", xy=(pole_lambda, 0.0),
                         xytext=(pole_lambda + 0.06, y_top * 0.22), ha="left", va="bottom",
                         fontsize=7.5, color=INK_SECONDARY,
                         arrowprops={"arrowstyle": "-", "color": MUTED, "linewidth": 0.6,
                                     "shrinkA": 1, "shrinkB": 4})
    axes[0].text(0.96, y_top * 0.53, "clamp\n" + r"$\lambda = \pm 1$", ha="right", va="center",
                 fontsize=7.5, color=MUTED)
    legend_handles = [
        plt.Line2D([], [], marker="o", markersize=5, color=SERIES[0], linestyle="none"),
        plt.Line2D([], [], marker="o", markersize=5, color=SERIES[1], linestyle="none"),
        plt.Line2D([], [], marker="D", markersize=5, color=INK, markeredgecolor=SURFACE,
                   markeredgewidth=1.0, linestyle="none"),
    ]
    fig.legend(legend_handles, ["unsaturated", r"saturated, $|\lambda| = 1$", "poles"],
               loc="outside lower center", ncol=3, handletextpad=0.4, columnspacing=1.6)
    save(fig, "fig1_screen_mapping")


def fig2_displacement() -> None:
    """Aligned p95 displacement at each growth step: refits, fit-once, moving anchor, fixed maps."""
    drift = results("drift.json")
    sizes = [step["size"] for step in drift["polar_fixed"]["steps"]]

    def p95(arm: str) -> list[float]:
        return [step["aligned_p95"] for step in drift[arm]["steps"]]

    fixed = np.max([p95(a) for a in ("random_fixed", "pca_fit_once", "polar_fixed")], axis=0)

    fig, ax = plt.subplots(figsize=(6.5, 3.2), constrained_layout=True)
    recessive(ax)
    ax.plot(sizes, fixed, color=MUTED, linewidth=1.5, solid_capstyle="round", zorder=2,
            label="fixed maps: random projection, PCA fit once, operator with fixed anchor")
    arms = [("tsne_refit", "t-SNE, refit per step"), ("umap_refit", "UMAP, refit per step"),
            ("umap_fit_once", "UMAP, fit once + transform()"), ("polar_moving", "operator, moving anchor")]
    for color, (arm, label) in zip(SERIES, arms):
        ax.plot(sizes, p95(arm), color=color, linewidth=1.5, marker="o", markersize=5.5,
                markeredgecolor=SURFACE, markeredgewidth=1.2, solid_joinstyle="round",
                solid_capstyle="round", label=label, zorder=3)

    fit_once = p95("umap_fit_once")
    for size, value in zip(sizes, fit_once):
        if value >= 1e-9:
            above = value < 1.0
            ax.annotate(f"{value:.2f}", xy=(size, value), xytext=(0, 7) if above else (9, -4),
                        textcoords="offset points", ha="center" if above else "left",
                        va="bottom" if above else "top", fontsize=7.5, color=INK_SECONDARY)

    ax.set_xticks(sizes)
    ax.set_xticklabels([f"{s:,}" for s in sizes])
    ax.set_xlabel("corpus size after the growth step (chunks)")
    ax.set_ylabel("aligned p95 displacement\n(× layout RMS radius)")
    ax.set_ylim(-0.03, 1.45)
    fig.legend(loc="outside lower center", ncol=2, fontsize=7.5, handlelength=1.8, columnspacing=1.4)
    save(fig, "fig2_displacement")


def fig3_scale_ratio() -> None:
    """Local recall of the re-anchored operator as the screen ratio varies."""
    ablation = results("reanchor_ablation.json")
    reanchor = results("reanchor.json")
    scales = [0.1, 0.25, 0.5, 1.0, 2.0]
    recall = [ablation[f"x_scale_{s}"]["mean_recall"] for s in scales]
    iso_x = ablation["frame"]["dipole_norm_median"]
    iso_y = ablation["isometric"]["mean_recall"]
    radial = reanchor["radial_plain"]["mean_recall"]
    residual_only = ablation["residual_norm_only"]["mean_recall"]

    fig, ax = plt.subplots(figsize=(5.2, 2.9), constrained_layout=True)
    recessive(ax)
    ax.set_xscale("log")
    for value, text, va, dy in ((residual_only, r"$\Vert r\Vert_2$ alone", "bottom", 0.012),
                                (radial, "radial coordinate", "top", -0.012)):
        ax.axhline(value, color=MUTED, linewidth=0.7, zorder=1)
        ax.text(0.085, value + dy, f"{text}: {value:.3f}", ha="left", va=va, fontsize=7.5, color=INK_SECONDARY)

    ax.plot(scales, recall, color=SERIES[0], linewidth=1.5, marker="o", markersize=5.5,
            markeredgecolor=SURFACE, markeredgewidth=1.2, solid_joinstyle="round", zorder=3,
            label=r"fixed ratio $s$: view $(s\lambda,\ d_{esc})$")
    ax.plot([iso_x], [iso_y], color=SERIES[1], marker="D", markersize=6.5, markeredgecolor=SURFACE,
            markeredgewidth=1.2, linestyle="none", zorder=4,
            label=r"per-frame $s = \Vert v_{dipole}\Vert_2$ (isometric)")

    unit_index = scales.index(1.0)
    ax.annotate(f"unit scale: {recall[unit_index]:.3f}", xy=(1.0, recall[unit_index]), xytext=(-8, -10),
                textcoords="offset points", ha="right", va="top", fontsize=7.5, color=INK_SECONDARY)
    ax.annotate(f"isometric: {iso_y:.3f}\n(median $s$ = {iso_x:.3f})", xy=(iso_x, iso_y), xytext=(-10, -6),
                textcoords="offset points", ha="right", va="top", fontsize=7.5, color=INK_SECONDARY)

    ax.set_xticks(scales)
    ax.set_xticklabels([f"{s:g}" for s in scales])
    ax.minorticks_off()
    ax.set_xlim(0.08, 2.3)
    ax.set_ylim(0.0, 1.1)
    ax.set_xlabel(r"screen ratio $s = S_x / S_y$ (log scale)")
    ax.set_ylabel("local recall@15 (mean of 50 queries)")
    ax.legend(loc="lower left", fontsize=7.5, handlelength=1.8)
    save(fig, "fig3_scale_ratio")


def main() -> int:
    fig1_screen_mapping()
    fig2_displacement()
    fig3_scale_ratio()
    for path in sorted(OUT.glob("*")):
        print(f"wrote {path.relative_to(ROOT)}  ({path.stat().st_size / 1024:.0f} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
