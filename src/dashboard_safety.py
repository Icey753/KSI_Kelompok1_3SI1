from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
UPLOADS_DIR = BASE_DIR / "output" / "uploads"
MAX_UPLOAD_BYTES = 50 * 1024 * 1024


def is_within_uploads(path) -> bool:
    """dcc.Store data comes from the browser and can be forged: only trust paths under UPLOADS_DIR."""
    try:
        return Path(path).resolve().is_relative_to(UPLOADS_DIR.resolve())
    except (TypeError, ValueError, OSError):
        return False


def trusted_upload(upload_state: dict | None) -> dict | None:
    if upload_state and is_within_uploads(upload_state.get("file_path")):
        return upload_state
    return None
