import json
import math

import pandas as pd
import pytest

from src import report
from src.sweep import find_crossover, make_payload, run_and_save_sweep, summarize_sweep


def test_make_payload_json_is_valid_and_close_to_size():
    payload = make_payload("json", 5000)
    assert 5000 <= len(payload) < 5000 + 300
    assert isinstance(json.loads(payload), list)


def test_make_payload_binary_exact_and_deterministic():
    assert len(make_payload("binary", 4096)) == 4096
    assert make_payload("binary", 4096) == make_payload("binary", 4096)


def test_make_payload_unknown_kind():
    with pytest.raises(ValueError):
        make_payload("video", 100)


def _summary(ratios, sizes=(1024, 4096, 16384, 65536)):
    return pd.DataFrame(
        {"Kind": "json", "SizeBytes": list(sizes), "RatioAsconOverAes": ratios}
    )


def test_find_crossover_interpolates_between_sizes():
    x = find_crossover(_summary([0.5, 0.8, 1.2, 2.0]), "json")
    assert 4096 < x < 16384


def test_find_crossover_none_when_no_sign_change():
    assert find_crossover(_summary([0.5, 0.6, 0.7, 0.8]), "json") is None
    assert find_crossover(_summary([2.0, 2.5, 3.0, 4.0]), "json") is None


def test_find_crossover_exact_formula():
    x = find_crossover(_summary([0.5, 0.8, 1.25, 2.0]), "json")
    # log-log simetris di sekitar 1.0: tepat di tengah geometris 4096 dan 16384
    assert x == pytest.approx(math.sqrt(4096 * 16384), rel=1e-6)


def test_summarize_sweep_builds_ratio_and_pvalue():
    def row(alg, size, median, samples):
        return {
            "Algorithm": alg,
            "FileType": "json",
            "PlaintextSizeBytes": size,
            "EncLatencyMedianMs": median,
            "_EncSamplesMs": samples,
        }

    rows = [
        row("AES-GCM", 1000, 0.10, [0.10] * 20),
        row("Ascon-128", 1000, 0.05, [0.05] * 20),
    ]
    df = summarize_sweep(rows)
    assert len(df) == 1
    assert df.loc[0, "RatioAsconOverAes"] == pytest.approx(0.5)
    assert df.loc[0, "EncPValue"] < 0.05


def test_run_and_save_sweep_writes_three_csvs(tmp_path, monkeypatch):
    monkeypatch.setattr(report, "RESULTS_DIR", str(tmp_path))
    summary = run_and_save_sweep(sizes=[1024, 2048], kinds=("json",), warm_ups=1, iterations=5)
    assert len(summary) == 2
    for name in ("size_sweep.csv", "size_sweep_raw.csv", "size_sweep_summary.csv"):
        assert (tmp_path / name).exists()
