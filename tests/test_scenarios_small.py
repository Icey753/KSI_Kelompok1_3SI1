from src.aead import ALL_VARIANTS
from src.scenarios import run_acceleration_scenario, run_small_message_scenario


def test_small_message_rows_structure():
    rows = run_small_message_scenario(message_sizes=(64, 256), n_messages=50, warm_ups=5)
    assert len(rows) == len(ALL_VARIANTS) * 2
    assert {r["Algorithm"] for r in rows} == set(ALL_VARIANTS)
    for r in rows:
        assert r["Messages"] == 50
        assert r["MessagesPerSec"] > 0
        assert r["ThroughputMBps"] > 0
        assert r["LatencyP95Us"] >= r["LatencyMedianUs"] > 0


def test_acceleration_rows_structure():
    rows = run_acceleration_scenario(sizes=(1024, 4096), iterations=3, warm_ups=1)
    assert len(rows) == len(ALL_VARIANTS) * 2
    assert all(r["EncMedianMs"] > 0 for r in rows)
    assert {r["SizeBytes"] for r in rows} == {1024, 4096}
