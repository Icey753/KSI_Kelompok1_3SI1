from src import report
from src.scenarios import run_and_save_scenarios


def test_run_and_save_writes_three_csvs(tmp_path, monkeypatch):
    monkeypatch.setattr(report, "RESULTS_DIR", str(tmp_path))
    result = run_and_save_scenarios(n_messages=30, total_bytes=50_000, iterations=1, acceleration_sizes=(1024,))
    assert set(result) == {"small_messages", "chunked", "acceleration"}
    for name in ("small_messages.csv", "chunked.csv", "acceleration.csv"):
        assert (tmp_path / name).exists()
    assert len(result["acceleration"]) == 3
    assert list(result["small_messages"].columns) == [
        "Algorithm", "MessageSizeBytes", "Messages", "MessagesPerSec", "LatencyMedianUs", "LatencyP95Us", "ThroughputMBps",
    ]
    assert list(result["chunked"].columns) == [
        "Algorithm", "TotalBytes", "ChunkSizeBytes", "Chunks", "EncMedianMs", "DecMedianMs",
        "OverheadBytes", "OverheadPct", "ThroughputMBps",
    ]
    assert list(result["acceleration"].columns) == ["Algorithm", "SizeBytes", "EncMedianMs"]


def test_run_and_save_respects_results_dir(tmp_path, monkeypatch):
    full = tmp_path / "full"
    full.mkdir()
    monkeypatch.setattr(report, "RESULTS_DIR", str(full))
    run_and_save_scenarios(
        n_messages=30, total_bytes=50_000, iterations=1, acceleration_sizes=(1024,), results_dir=str(tmp_path / "quick")
    )
    for name in ("small_messages.csv", "chunked.csv", "acceleration.csv"):
        assert (tmp_path / "quick" / name).exists()
    assert list(full.glob("*.csv")) == []
