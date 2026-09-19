import json
import math
import os
import random

import pandas as pd

from src import report
from src.benchmark import _run_plaintext_benchmark
from src.stats_utils import mann_whitney_p

SWEEP_SIZES = [1024, 4096, 16384, 65536, 262144, 1048576, 4194304, 10485760]
SWEEP_KINDS = ("json", "binary")
_CATEGORIES = ["Retail", "Grocery", "Electronics", "Utilities", "Entertainment"]
_STATUSES = ["Completed", "Pending", "Failed"]


def make_payload(kind: str, size: int, seed: int = 42) -> bytes:
    rng = random.Random(seed)
    if kind == "binary":
        return rng.randbytes(size)
    if kind != "json":
        raise ValueError(f"Unknown payload kind: {kind}")

    pieces: list[str] = []
    length = 2  # "[" dan "]"
    while length < size:
        piece = json.dumps(
            {
                "transaction_id": f"{rng.getrandbits(128):032x}",
                "amount": round(rng.uniform(10, 10000), 2),
                "category": rng.choice(_CATEGORIES),
                "status": rng.choice(_STATUSES),
            }
        )
        length += len(piece) + (1 if pieces else 0)
        pieces.append(piece)
    return ("[" + ",".join(pieces) + "]").encode()


def run_size_sweep(
    sizes=SWEEP_SIZES, kinds=SWEEP_KINDS, warm_ups: int = 5, iterations: int = 50
) -> list[dict]:
    rows: list[dict] = []
    for kind in kinds:
        for size in sizes:
            payload = make_payload(kind, size)
            kind_rows, _ = _run_plaintext_benchmark(
                plaintext=payload,
                input_file_name=f"{kind}_{size}",
                file_type=kind,
                size_category=str(size),
                warm_ups=warm_ups,
                iterations=iterations,
            )
            rows.extend(kind_rows)
    return rows


def summarize_sweep(rows: list[dict]) -> pd.DataFrame:
    def pick(kind, size, algorithm):
        return next(
            r
            for r in rows
            if r["FileType"] == kind
            and r["PlaintextSizeBytes"] == size
            and r["Algorithm"] == algorithm
        )

    keys = sorted({(r["FileType"], r["PlaintextSizeBytes"]) for r in rows})
    records = []
    for kind, size in keys:
        aes = pick(kind, size, "AES-GCM")
        ascon = pick(kind, size, "Ascon-128")
        records.append(
            {
                "Kind": kind,
                "SizeBytes": size,
                "AesEncMedianMs": aes["EncLatencyMedianMs"],
                "AsconEncMedianMs": ascon["EncLatencyMedianMs"],
                "RatioAsconOverAes": ascon["EncLatencyMedianMs"] / aes["EncLatencyMedianMs"],
                "EncPValue": mann_whitney_p(aes["_EncSamplesMs"], ascon["_EncSamplesMs"]),
            }
        )
    return pd.DataFrame(records)


def find_crossover(summary: pd.DataFrame, kind: str) -> float | None:
    sub = summary[summary["Kind"] == kind].sort_values("SizeBytes")
    sizes = sub["SizeBytes"].tolist()
    ratios = sub["RatioAsconOverAes"].tolist()
    for (s1, r1), (s2, r2) in zip(zip(sizes, ratios), zip(sizes[1:], ratios[1:])):
        if (r1 - 1.0) * (r2 - 1.0) < 0:
            t = (0.0 - math.log(r1)) / (math.log(r2) - math.log(r1))
            return math.exp(math.log(s1) + t * (math.log(s2) - math.log(s1)))
    return None


def run_and_save_sweep(
    sizes=SWEEP_SIZES, kinds=SWEEP_KINDS, warm_ups: int = 5, iterations: int = 50
) -> pd.DataFrame:
    rows = run_size_sweep(sizes, kinds, warm_ups, iterations)
    report.save_benchmark_results(rows, "size_sweep.csv")
    report.save_raw_samples(rows, "size_sweep_raw.csv")
    summary = summarize_sweep(rows)
    summary.to_csv(os.path.join(report.RESULTS_DIR, "size_sweep_summary.csv"), index=False)
    return summary


if __name__ == "__main__":
    result = run_and_save_sweep()
    print(result.to_string(index=False))
    for sweep_kind in SWEEP_KINDS:
        crossover = find_crossover(result, sweep_kind)
        label = f"{crossover / 1024:.1f} KB" if crossover else "tidak ada titik potong"
        print(f"Titik potong {sweep_kind}: {label}")
