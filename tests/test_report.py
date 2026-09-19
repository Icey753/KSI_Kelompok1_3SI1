import pandas as pd

from src import report


def _rows():
    return [
        {
            "Algorithm": "AES-GCM",
            "InputFileName": "a.json",
            "EncLatencyMeanMs": 1.0,
            "_EncSamplesMs": [1.0, 1.2],
            "_DecSamplesMs": [0.9, 1.1],
        }
    ]


def test_main_csv_drops_private_columns(tmp_path, monkeypatch):
    monkeypatch.setattr(report, "RESULTS_DIR", str(tmp_path))
    path = report.save_benchmark_results(_rows(), "main.csv")
    df = pd.read_csv(path)
    assert "EncLatencyMeanMs" in df.columns
    assert not any(c.startswith("_") for c in df.columns)


def test_raw_samples_are_exploded(tmp_path, monkeypatch):
    monkeypatch.setattr(report, "RESULTS_DIR", str(tmp_path))
    path = report.save_raw_samples(_rows(), "raw.csv")
    df = pd.read_csv(path)
    assert list(df.columns) == ["Algorithm", "InputFileName", "Op", "Iteration", "LatencyMs"]
    assert len(df) == 4
    assert set(df["Op"]) == {"enc", "dec"}
