"""
NeuroState-R dimensionality and trajectory analysis.

Inputs:  traces_all.csv (or per-scenario CSVs) from neurostate-r-traces repo
Outputs: printed markdown report + figures saved to neurostate_r_analysis/

Usage:
    python experiments/analyze_neurostate_r.py
    python experiments/analyze_neurostate_r.py --data path/to/traces_all.csv
"""

import argparse
import os
import sys
import textwrap

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

DIMS = ["G", "C", "D", "S", "O", "E"]
OUT_DIR = os.path.join(os.path.dirname(__file__), "neurostate_r_analysis")


# ── data loading ─────────────────────────────────────────────────────────────

def load_traces(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df = df.sort_values(["scenario", "model", "trial", "turn"]).reset_index(drop=True)
    return df


def compute_deltas(df: pd.DataFrame) -> pd.DataFrame:
    """Return a DataFrame of per-turn delta vectors (one row per turn > 0)."""
    rows = []
    for (scen, model, trial), g in df.groupby(["scenario", "model", "trial"], sort=False):
        g = g.sort_values("turn")
        vals = g[DIMS].values
        success = g["success"].iloc[0]
        for i in range(1, len(vals)):
            delta = vals[i] - vals[i - 1]
            rows.append(dict(
                scenario=scen, model=model, trial=trial,
                turn=g["turn"].iloc[i], success=success,
                **{f"d{d}": delta[j] for j, d in enumerate(DIMS)},
            ))
    return pd.DataFrame(rows)


# ── PCA ──────────────────────────────────────────────────────────────────────

def run_pca(deltas: pd.DataFrame, label: str = "all") -> dict:
    X = deltas[[f"d{d}" for d in DIMS]].dropna().values
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    pca = PCA(n_components=len(DIMS))
    pca.fit(X_scaled)
    evr = pca.explained_variance_ratio_
    loadings = pd.DataFrame(
        pca.components_.T,
        index=DIMS,
        columns=[f"PC{i+1}" for i in range(len(DIMS))],
    )
    return {"label": label, "evr": evr, "loadings": loadings, "n": len(X)}


def fmt_pca_report(r: dict) -> str:
    evr = r["evr"]
    cumulative = np.cumsum(evr)
    lines = [
        f"\n### PCA — {r['label']} (n={r['n']} delta vectors)",
        "",
        "| PC | Explained var | Cumulative |",
        "|----|--------------|------------|",
    ]
    for i, (e, c) in enumerate(zip(evr, cumulative)):
        lines.append(f"| PC{i+1} | {e:.3f} | {c:.3f} |")
    lines += [
        "",
        "**Loadings (top 3 PCs):**",
        "",
        r["loadings"].iloc[:, :3].round(3).to_markdown(),
        "",
    ]
    if evr[0] > 0.80:
        lines.append("**Result: PC1 > 80% variance → 6D direction is essentially 1D.**")
    elif evr[0] > 0.60:
        lines.append("**Result: PC1 > 60% but < 80% → dominant 1D structure, secondary components non-trivial.**")
    else:
        lines.append("**Result: PC1 < 60% → genuine multi-dimensional structure.**")
    return "\n".join(lines)


# ── correlation matrix ────────────────────────────────────────────────────────

def run_corr(deltas: pd.DataFrame, label: str = "all") -> pd.DataFrame:
    return deltas[[f"d{d}" for d in DIMS]].rename(columns=lambda c: c[1:]).corr()


def fmt_corr_report(corr: pd.DataFrame, label: str) -> str:
    collapsed = [
        f"{a}/{b}" for i, a in enumerate(corr.columns)
        for j, b in enumerate(corr.columns)
        if j > i and abs(corr.iloc[i, j]) > 0.9
    ]
    lines = [
        f"\n### Correlation — {label}",
        "",
        corr.round(3).to_markdown(),
        "",
    ]
    if collapsed:
        lines.append(f"**Collapsed pairs (|r|>0.9):** {', '.join(collapsed)}")
    else:
        lines.append("**No collapsed pairs (|r|>0.9)**")
    return "\n".join(lines)


# ── trajectory split ──────────────────────────────────────────────────────────

def trajectory_split(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Mean trajectory per (scenario, success) group."""
    result = {}
    for scen in sorted(df.scenario.unique()):
        sub = df[df.scenario == scen]
        for suc, grp in sub.groupby("success"):
            key = f"{scen}_{'success' if suc else 'failed'}"
            result[key] = grp.groupby("turn")[DIMS].mean()
    return result


def fmt_trajectory_report(trajectories: dict) -> str:
    lines = ["\n### Trajectory split (failed vs successful, mean values + net displacement)"]
    scenarios = sorted({k.rsplit("_", 1)[0] for k in trajectories})
    for scen in scenarios:
        s_key = f"{scen}_success"
        f_key = f"{scen}_failed"
        lines.append(f"\n**{scen}**")
        for key, label in [(s_key, "success"), (f_key, "failed ")]:
            if key not in trajectories:
                continue
            traj = trajectories[key]
            first = traj.iloc[0]
            last = traj.iloc[-1]
            net = last - first
            dirs = " ".join(
                f"{'↑' if net[d] > 0 else '↓'}{d}({net[d]:+.1f})"
                for d in DIMS
            )
            lines.append(f"- {label}: {dirs}")
        # compare magnitudes between success vs failed
        if s_key in trajectories and f_key in trajectories:
            s_net = trajectories[s_key].iloc[-1] - trajectories[s_key].iloc[0]
            f_net = trajectories[f_key].iloc[-1] - trajectories[f_key].iloc[0]
            bigger = {d: abs(s_net[d]) > abs(f_net[d]) for d in DIMS}
            lines.append(
                f"  → successful trials drift further on: "
                f"{', '.join(d for d in DIMS if bigger[d]) or 'none'}"
            )
    return "\n".join(lines)


# ── figures ───────────────────────────────────────────────────────────────────

def save_pca_variance_plot(results: list[dict], out_dir: str) -> str:
    fig, ax = plt.subplots(figsize=(7, 4))
    x = [f"PC{i+1}" for i in range(len(DIMS))]
    for r in results:
        ax.plot(x, np.cumsum(r["evr"]), marker="o", label=r["label"])
    ax.axhline(0.8, color="gray", linestyle="--", linewidth=0.8)
    ax.set_ylabel("Cumulative explained variance")
    ax.set_title("PCA — cumulative explained variance")
    ax.legend()
    path = os.path.join(out_dir, "pca_variance.png")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


def save_corr_heatmap(corr: pd.DataFrame, label: str, out_dir: str) -> str:
    fig, ax = plt.subplots(figsize=(5, 4))
    im = ax.imshow(corr.values, vmin=-1, vmax=1, cmap="RdBu_r")
    ax.set_xticks(range(len(DIMS)))
    ax.set_yticks(range(len(DIMS)))
    ax.set_xticklabels(DIMS)
    ax.set_yticklabels(DIMS)
    for i in range(len(DIMS)):
        for j in range(len(DIMS)):
            ax.text(j, i, f"{corr.iloc[i, j]:.2f}", ha="center", va="center",
                    fontsize=8, color="white" if abs(corr.iloc[i, j]) > 0.6 else "black")
    plt.colorbar(im, ax=ax)
    ax.set_title(f"Δ-correlation — {label}")
    slug = label.lower().replace(" ", "_")
    path = os.path.join(out_dir, f"corr_{slug}.png")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


def save_trajectory_plots(df: pd.DataFrame, out_dir: str) -> list[str]:
    paths = []
    for scen in sorted(df.scenario.unique()):
        sub = df[df.scenario == scen]
        fig, axes = plt.subplots(2, 3, figsize=(12, 7))
        axes = axes.flatten()
        for idx, dim in enumerate(DIMS):
            ax = axes[idx]
            for suc, grp in sub.groupby("success"):
                mean_traj = grp.groupby("turn")[dim].mean()
                std_traj = grp.groupby("turn")[dim].std().fillna(0)
                label = f"{'success' if suc else 'failed'} (n={grp.trial.nunique()})"
                color = "#d62728" if suc else "#1f77b4"
                ax.plot(mean_traj.index, mean_traj.values, marker="o", label=label, color=color)
                ax.fill_between(
                    mean_traj.index,
                    mean_traj.values - std_traj.values,
                    mean_traj.values + std_traj.values,
                    alpha=0.15, color=color,
                )
            ax.set_title(dim)
            ax.set_xlabel("turn")
            ax.legend(fontsize=7)
        fig.suptitle(f"NeuroState-R trajectories — {scen}", fontweight="bold")
        fig.tight_layout()
        path = os.path.join(out_dir, f"trajectory_{scen}.png")
        fig.savefig(path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        paths.append(path)
    return paths


# ── normalization check ───────────────────────────────────────────────────────

def normalization_check(deltas: pd.DataFrame) -> str:
    """
    Heuristic: if all dimensions are derived from a single scalar (shared denominator),
    then the sum-of-absolute-deltas per row should be nearly proportional across dims.
    More concretely: if rank(delta_matrix) ≈ 1, it's 1D.
    """
    X = deltas[[f"d{d}" for d in DIMS]].dropna().values
    # singular values of the centered delta matrix
    X_c = X - X.mean(axis=0)
    _, s, _ = np.linalg.svd(X_c, full_matrices=False)
    total = np.sum(s ** 2)
    sv_ratio = (s ** 2) / total
    lines = [
        "\n### Normalization / rank check",
        "",
        "Singular value spectrum of Δ matrix (centered):",
        "",
        "| SV | Energy fraction | Cumulative |",
        "|----|-----------------|------------|",
    ]
    cumulative = 0.0
    for i, r in enumerate(sv_ratio):
        cumulative += r
        lines.append(f"| {i+1} | {r:.4f} | {cumulative:.4f} |")
    lines.append("")
    if sv_ratio[0] > 0.90:
        lines.append(
            "**SV1 > 90% energy → matrix is effectively rank-1. "
            "All 6 dimensions share a single underlying scalar (shared denominator likely).**"
        )
    elif sv_ratio[0] > 0.70:
        lines.append("**SV1 70–90%: strong 1D bias, secondary structure present.**")
    else:
        lines.append("**SV1 < 70%: dimensions carry genuinely independent information.**")
    return "\n".join(lines)


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--data",
        default=os.path.join(os.path.dirname(__file__),
                             "neurostate_r_traces", "traces_all.csv"),
    )
    args = parser.parse_args()

    if not os.path.exists(args.data):
        sys.exit(f"Data file not found: {args.data}")

    os.makedirs(OUT_DIR, exist_ok=True)

    print(f"Loading {args.data} ...")
    df = load_traces(args.data)
    print(f"  {len(df)} rows | scenarios: {sorted(df.scenario.unique())} | "
          f"models: {sorted(df.model.unique())}")

    deltas = compute_deltas(df)
    print(f"  {len(deltas)} delta vectors computed\n")

    # ── PCA ────────────────────────────────────────────────────────────────
    pca_results = []
    pca_results.append(run_pca(deltas, label="all scenarios"))
    for scen in sorted(df.scenario.unique()):
        sub = deltas[deltas.scenario == scen]
        pca_results.append(run_pca(sub, label=scen))

    print("## NeuroState-R Analysis Report\n")
    print("### Dataset overview")
    overview = df.groupby(["scenario", "success"])["trial"].nunique().unstack(fill_value=0)
    overview.columns = ["failed", "success"]
    print(overview.to_markdown())

    for r in pca_results:
        print(fmt_pca_report(r))

    # ── correlation ─────────────────────────────────────────────────────────
    corr_all = run_corr(deltas, "all")
    print(fmt_corr_report(corr_all, "all scenarios"))

    for suc_val, label in [(1, "success=1"), (0, "success=0")]:
        sub = deltas[deltas.success == suc_val]
        if len(sub) > 10:
            corr_sub = run_corr(sub, label)
            print(fmt_corr_report(corr_sub, label))

    # ── normalization check ─────────────────────────────────────────────────
    print(normalization_check(deltas))

    # ── trajectory split ────────────────────────────────────────────────────
    trajectories = trajectory_split(df)
    print(fmt_trajectory_report(trajectories))

    # ── figures ─────────────────────────────────────────────────────────────
    save_pca_variance_plot(pca_results, OUT_DIR)
    save_corr_heatmap(corr_all, "all", OUT_DIR)
    traj_paths = save_trajectory_plots(df, OUT_DIR)

    print(f"\nFigures saved to {OUT_DIR}/")
    for p in [os.path.join(OUT_DIR, "pca_variance.png"),
               os.path.join(OUT_DIR, "corr_all.png")] + traj_paths:
        print(f"  {p}")


if __name__ == "__main__":
    main()
