import json

import pandas as pd

from src.dashboard_analysis import (
    build_analysis_section,
    build_env_panel,
    build_sweep_figure,
    load_env_info,
    load_sweep_summary,
)


def _summary():
    return pd.DataFrame(
        {
            "Kind": ["json"] * 4,
            "SizeBytes": [1024, 4096, 16384, 65536],
            "AesEncMedianMs": [0.07, 0.08, 0.10, 0.30],
            "AsconEncMedianMs": [0.03, 0.06, 0.12, 0.60],
            "RatioAsconOverAes": [0.5, 0.8, 1.2, 2.0],
            "EncPValue": [0.001] * 4,
        }
    )


def _text(component) -> str:
    parts = []

    def walk(node):
        if isinstance(node, str):
            parts.append(node)
        children = getattr(node, "children", None)
        if isinstance(children, (list, tuple)):
            for child in children:
                walk(child)
        elif children is not None:
            walk(children)

    walk(component)
    return " ".join(parts)


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


def test_sweep_figure_has_lines_and_crossover_marker():
    fig = build_sweep_figure(_summary())
    # AES, Ascon, rasio, penanda titik potong
    assert len(fig.data) == 4


def test_sweep_figure_placeholder_when_no_data():
    fig = build_sweep_figure(None)
    assert len(fig.data) == 0
    assert "sweep" in fig.layout.annotations[0].text.lower()


def test_load_helpers_return_none_when_missing(tmp_path):
    assert load_sweep_summary(tmp_path / "nope.csv") is None
    assert load_env_info(tmp_path / "nope.json") is None


def test_load_helpers_read_files(tmp_path):
    _summary().to_csv(tmp_path / "s.csv", index=False)
    (tmp_path / "e.json").write_text(json.dumps({"ascon_variant": "Ascon-AEAD128"}), encoding="utf-8")
    assert len(load_sweep_summary(tmp_path / "s.csv")) == 4
    assert load_env_info(tmp_path / "e.json")["ascon_variant"] == "Ascon-AEAD128"


def test_env_panel_explains_aesni_effect():
    info = {"python": "3.14", "platform": "Windows", "processor": "x", "cpu_count": 8,
            "pycryptodome": "3.20", "ascon_backend": "C (ascon-c ref)",
            "ascon_variant": "Ascon-AEAD128 (NIST SP 800-232)", "aesni_speedup": 4.2}
    text = _text(build_env_panel(info))
    assert "Ascon-AEAD128" in text and "4.2" in text


def test_env_panel_handles_missing_info():
    assert "belum" in _text(build_env_panel(None)).lower()


def test_section_component_ids():
    found = _ids(build_analysis_section())
    for required in ("analysis-run-sweep", "analysis-sweep-graph", "analysis-sweep-status",
                     "analysis-download-csv", "analysis-download", "analysis-env-panel"):
        assert required in found, required
