import json

import pytest

from src.dashboard_demo import (
    DEFAULT_SAMPLE,
    _run_image_demo,
    build_demo_section,
    load_plaintext,
    render_cbc_comparison,
    render_nonce_reuse,
    render_roundtrip,
    render_tamper,
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


def _ids(component) -> set:
    found = set()
    if getattr(component, "id", None):
        found.add(component.id)
    children = getattr(component, "children", None)
    if isinstance(children, (list, tuple)):
        for child in children:
            found |= _ids(child)
    elif children is not None and not isinstance(children, str):
        found |= _ids(children)
    return found


def test_default_sample_is_valid_json():
    assert json.loads(DEFAULT_SAMPLE)


def test_load_plaintext_falls_back_to_sample():
    data, label = load_plaintext(None)
    assert data == DEFAULT_SAMPLE
    assert "contoh" in label.lower()


def test_load_plaintext_reads_uploaded_file(tmp_path):
    path = tmp_path / "x.json"
    path.write_bytes(b"[1,2,3]")
    data, label = load_plaintext({"file_path": str(path), "input_file_name": "x.json"})
    assert data == b"[1,2,3]"
    assert "x.json" in label


def test_render_tamper_rejected_and_accepted_wording():
    base = {"algorithm": "AES-GCM", "target": "tag", "byte_index": 3, "control_ok": True,
            "plaintext_returned": False, "ciphertext_preview_hex": "00", "tag_hex": "11"}
    assert "DITOLAK" in _text(render_tamper({**base, "rejected": True}))
    assert "DITERIMA" in _text(render_tamper({**base, "rejected": False, "plaintext_returned": True}))


def test_render_roundtrip_shows_match():
    result = {"algorithm": "AES-GCM", "key_hex": "aa", "nonce_hex": "bb", "tag_hex": "cc",
              "plaintext_bytes": 10, "ciphertext_bytes": 26, "ciphertext_preview_hex": "dd",
              "sha256_before": "h1", "sha256_after": "h1", "match": True}
    text = _text(render_roundtrip(result))
    assert "SAMA" in text and "h1" in text


def test_render_nonce_reuse_lists_both_algorithms():
    results = [
        {"algorithm": "AES-GCM", "compared_bytes": 64, "leaked_bytes": 64, "leak_fraction": 1.0,
         "ciphertext_xor_hex": "00", "recovered_matches_b": True, "recovered_preview": "B" * 8},
        {"algorithm": "Ascon-128", "compared_bytes": 64, "leaked_bytes": 16, "leak_fraction": 0.25,
         "ciphertext_xor_hex": "00", "recovered_matches_b": True, "recovered_preview": "B" * 8},
    ]
    text = _text(render_nonce_reuse(results))
    assert "AES-GCM" in text and "Ascon-128" in text and "16" in text


def test_demo_section_has_all_component_ids():
    ids = _ids(build_demo_section())
    for required in ("demo-algorithm", "demo-tamper-target", "demo-tamper-byte", "demo-tamper-run",
                     "demo-tamper-result", "demo-roundtrip-run", "demo-roundtrip-result",
                     "demo-nonce-text-a", "demo-nonce-text-b", "demo-nonce-run", "demo-nonce-result",
                     "demo-image-run", "demo-image-result"):
        assert required in ids, required


@pytest.mark.filterwarnings("ignore:(?s).*dash_table.DataTable.*:DeprecationWarning")
def test_dashboard_builds_with_demo_section():
    from src.dashboard_app import build_dash_app

    app = build_dash_app(None)
    assert "demo-tamper-run" in _ids(app.layout)


def _has_img(node) -> bool:
    if type(node).__name__ == "Img":
        return True
    children = getattr(node, "children", None)
    if isinstance(children, (list, tuple)):
        return any(_has_img(child) for child in children)
    return children is not None and not isinstance(children, str) and _has_img(children)


@pytest.mark.parametrize("state", [None, {"file_type": "json", "file_path": "x.json"}])
def test_run_image_demo_warns_when_no_image_upload(state):
    assert "Unggah file gambar" in _text(_run_image_demo("AES-GCM", state))


def test_run_image_demo_warns_when_file_missing(tmp_path):
    state = {"file_type": "image", "file_path": str(tmp_path / "hilang.png")}
    assert "Gambar tidak bisa dibaca" in _text(_run_image_demo("AES-GCM", state))


def test_run_image_demo_warns_when_image_corrupt(tmp_path):
    bad = tmp_path / "x.png"
    bad.write_bytes(b"ini bukan gambar")
    state = {"file_type": "image", "file_path": str(bad)}
    assert "Gambar tidak bisa dibaca" in _text(_run_image_demo("AES-GCM", state))


def test_run_image_demo_renders_images_for_valid_image(tmp_path):
    from PIL import Image

    path = tmp_path / "ok.png"
    Image.new("RGB", (8, 8), (10, 20, 30)).save(path)
    state = {"file_type": "image", "file_path": str(path)}
    assert _has_img(_run_image_demo("AES-GCM", state))


def test_render_cbc_comparison_shows_silent_corruption_vs_rejection():
    aead_result = {"algorithm": "AES-GCM", "target": "ciphertext", "byte_index": 0,
                   "control_ok": True, "rejected": True, "plaintext_returned": False,
                   "ciphertext_preview_hex": "00", "tag_hex": "11"}
    cbc_result = {"byte_index": 0, "control_ok": True, "rejected": False,
                  "plaintext_returned": True, "plaintext_corrupted": True,
                  "tampered_preview": "garbled...rest ok", "ciphertext_preview_hex": "22"}
    text = _text(render_cbc_comparison(aead_result, cbc_result))
    assert "DITOLAK" in text
    assert "diam-diam" in text.lower()


def test_demo_section_has_cbc_ids():
    ids = _ids(build_demo_section())
    assert "demo-cbc-run" in ids
    assert "demo-cbc-result" in ids
