from src.dashboard_safety import UPLOADS_DIR, is_within_uploads, trusted_upload


def test_path_inside_uploads_is_trusted():
    assert is_within_uploads(UPLOADS_DIR / "abc123" / "data.json")


def test_forged_paths_are_rejected(tmp_path):
    assert not is_within_uploads(tmp_path / "x.json")
    assert not is_within_uploads(UPLOADS_DIR / ".." / ".." / "requirements.txt")
    assert not is_within_uploads(None)


def test_trusted_upload_drops_forged_state(tmp_path):
    assert trusted_upload({"file_path": str(tmp_path / "x.json")}) is None
    assert trusted_upload(None) is None
    ok = {"file_path": str(UPLOADS_DIR / "abc" / "a.json")}
    assert trusted_upload(ok) is ok
