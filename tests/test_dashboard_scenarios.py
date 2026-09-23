import pandas as pd

from src.dashboard_scenarios import (
    build_acceleration_figure,
    build_chunked_figure,
    build_scenarios_section,
    build_small_message_figure,
    load_scenario,
)

VARIANTS = ("AES-GCM", "AES-GCM-noNI", "Ascon-128")


def _ids(node) -> set:
    found = set()
    if getattr(node, "id", None):
        found.add(node.id)
    children = getattr(node, "children", None)
    if isinstance(children, (list, tuple)):
        for child in children:
            found |= _ids(child)
    elif children is not None and not isinstance(children, str):
        found |= _ids(children)
    return found


def _small():
    return pd.DataFrame(
        [{"Algorithm": a, "MessageSizeBytes": s, "MessagesPerSec": 1000.0 * (i + 1) / s, "Messages": 2000}
         for i, a in enumerate(VARIANTS) for s in (64, 1024)]
    )


def _chunked():
    return pd.DataFrame(
        [{"Algorithm": a, "TotalBytes": 1_000_000, "ChunkSizeBytes": c, "EncMedianMs": 1.0 + i,
          "OverheadPct": 16 * (1_000_000 // c) / 1_000_000 * 100}
         for i, a in enumerate(VARIANTS) for c in (4096, 65536, 1_000_000)]
    )


def _accel():
    return pd.DataFrame(
        [{"Algorithm": a, "SizeBytes": s, "EncMedianMs": 0.1 * (i + 1) * s / 1024}
         for i, a in enumerate(VARIANTS) for s in (1024, 65536)]
    )


def test_small_message_figure_one_trace_per_variant():
    assert len(build_small_message_figure(_small()).data) == 3


def test_chunked_figure_has_overhead_and_latency_traces():
    # 1 garis overhead + 3 garis latensi
    assert len(build_chunked_figure(_chunked()).data) == 4


def test_acceleration_figure_one_trace_per_variant():
    assert len(build_acceleration_figure(_accel()).data) == 3


def test_figures_have_placeholder_when_no_data():
    for builder in (build_small_message_figure, build_chunked_figure, build_acceleration_figure):
        fig = builder(None)
        assert len(fig.data) == 0
        assert "belum" in fig.layout.annotations[0].text.lower()


def test_load_scenario_missing_and_present(tmp_path):
    assert load_scenario("chunked", tmp_path) is None
    _small().to_csv(tmp_path / "small_messages.csv", index=False)
    assert len(load_scenario("small_messages", tmp_path)) == 6


def test_section_ids():
    found = _ids(build_scenarios_section())
    for required in ("scenarios-run", "scenarios-status", "scenarios-small-graph",
                     "scenarios-chunked-graph", "scenarios-accel-graph"):
        assert required in found, required


def test_cumulative_time_figure_one_trace_per_variant():
    from src.dashboard_scenarios import build_cumulative_time_figure

    assert len(build_cumulative_time_figure(_small()).data) == 3


def test_cumulative_time_figure_placeholder_when_no_data():
    from src.dashboard_scenarios import build_cumulative_time_figure

    fig = build_cumulative_time_figure(None)
    assert len(fig.data) == 0


def test_section_ids_include_cumulative_graph():
    found = _ids(build_scenarios_section())
    assert "scenarios-small-cumulative-graph" in found
