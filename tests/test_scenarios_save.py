from src import report
from src.scenarios import run_and_save_scenarios


def test_run_and_save_writes_three_csvs(tmp_path, monkeypatch):
    monkeypatch.setattr(report, "RESULTS_DIR", str(tmp_path))
    result = run_and_save_scenarios(n_messages=30, total_bytes=50_000, iterations=1, acceleration_sizes=(1024,))
    assert set(result) == {"small_messages", "chunked", "acceleration"}
    for name in ("small_messages.csv", "chunked.csv", "acceleration.csv"):
        assert (tmp_path / name).exists()
    assert len(result["acceleration"]) == 3
