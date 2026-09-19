import os

import matplotlib.pyplot as plt
import pandas as pd

from src.sweep import find_crossover

AES_COLOR = "#2563eb"
ASCON_COLOR = "#db2777"


def _prepare(out_path: str) -> None:
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)


def generate_sweep_chart(summary_csv: str, out_path: str) -> str:
    _prepare(out_path)
    df = pd.read_csv(summary_csv)
    fig, (ax_lat, ax_ratio) = plt.subplots(2, 1, figsize=(9, 9), sharex=True)

    for kind, style in zip(sorted(df["Kind"].unique()), ("-", "--")):
        sub = df[df["Kind"] == kind].sort_values("SizeBytes")
        ax_lat.plot(sub["SizeBytes"], sub["AesEncMedianMs"], style, marker="o", color=AES_COLOR, label=f"AES-GCM ({kind})")
        ax_lat.plot(sub["SizeBytes"], sub["AsconEncMedianMs"], style, marker="s", color=ASCON_COLOR, label=f"Ascon-128 ({kind})")
        ax_ratio.plot(sub["SizeBytes"], sub["RatioAsconOverAes"], style, marker="o", color="#7c3aed", label=kind)
        crossover = find_crossover(df, kind)
        if crossover is not None:
            ax_ratio.axvline(crossover, color="#7c3aed", linestyle=":", alpha=0.6)
            ax_ratio.annotate(f"titik potong ~{crossover / 1024:.0f} KB", (crossover, 1.0), textcoords="offset points", xytext=(6, 8))

    ax_lat.set_xscale("log")
    ax_lat.set_yscale("log")
    ax_lat.set_ylabel("Median latensi enkripsi (ms)")
    ax_lat.set_title("Latensi enkripsi vs ukuran data")
    ax_lat.legend()
    ax_ratio.axhline(1.0, color="gray", linewidth=1)
    ax_ratio.set_yscale("log")
    ax_ratio.set_xlabel("Ukuran data (byte, skala log)")
    ax_ratio.set_ylabel("Rasio Ascon / AES (<1 = Ascon lebih cepat)")
    ax_ratio.legend()
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return out_path


def generate_boxplot(raw_csv: str, out_path: str) -> str:
    _prepare(out_path)
    df = pd.read_csv(raw_csv)
    df = df[df["Op"] == "enc"]
    labels, data = [], []
    for (name, algorithm), group in df.groupby(["InputFileName", "Algorithm"], sort=False):
        labels.append(f"{name}\n{algorithm}")
        data.append(group["LatencyMs"].values)
    fig, ax = plt.subplots(figsize=(max(8, len(labels) * 1.3), 6))
    ax.boxplot(data)
    ax.set_xticklabels(labels, fontsize=8)
    ax.set_yscale("log")
    ax.set_ylabel("Latensi enkripsi (ms, skala log)")
    ax.set_title("Sebaran latensi enkripsi per file dan algoritma")
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return out_path
