import pytest
from PIL import Image

from src.aead import ALGORITHMS
from src.demo_tools import (
    TAMPER_TARGETS,
    flip_bit,
    image_encryption_demo,
    nonce_reuse_demo,
    roundtrip_demo,
    sha256_hex,
    tamper_demo,
)

PNG_MAGIC = b"\x89PNG"


def _make_png(path, size):
    pixels = bytes((i * 7) % 256 for i in range(size[0] * size[1] * 3))
    Image.frombytes("RGB", size, pixels).save(path)


def test_flip_bit_changes_exactly_one_bit_and_wraps_index():
    assert flip_bit(b"\x00\x00", 1) == b"\x00\x01"
    assert flip_bit(b"\x00\x00", 3) == b"\x00\x01"  # 3 % 2 == 1


@pytest.mark.parametrize("algorithm", ALGORITHMS)
@pytest.mark.parametrize("target", TAMPER_TARGETS)
def test_every_tamper_target_is_rejected(algorithm, target):
    result = tamper_demo(algorithm, b"data transaksi penting" * 4, target, byte_index=5)
    assert result["control_ok"] is True
    assert result["rejected"] is True
    assert result["plaintext_returned"] is False


def test_tamper_unknown_target_raises():
    with pytest.raises(ValueError):
        tamper_demo("AES-GCM", b"abc", "padding")


def test_tamper_empty_part_raises():
    with pytest.raises(ValueError):
        tamper_demo("AES-GCM", b"", "ciphertext")


@pytest.mark.parametrize("algorithm", ALGORITHMS)
def test_roundtrip_hashes_match(algorithm):
    data = b'{"amount": 100}' * 50
    result = roundtrip_demo(algorithm, data)
    assert result["match"] is True
    assert result["sha256_before"] == result["sha256_after"] == sha256_hex(data)
    assert result["ciphertext_bytes"] == len(data) + 16


def test_nonce_reuse_aes_leaks_everything():
    result = nonce_reuse_demo("AES-GCM", b"A" * 64, b"B" * 64)
    assert result["leaked_bytes"] == 64
    assert result["leak_fraction"] == 1.0
    assert result["recovered_matches_b"] is True


def test_nonce_reuse_ascon_leaks_first_block_but_not_everything():
    result = nonce_reuse_demo("Ascon-128", b"A" * 64, b"B" * 64)
    # first rate block (16 bytes) always leaks; bytes after it match only by chance (~1/256 each)
    assert 16 <= result["leaked_bytes"] < result["compared_bytes"]
    assert result["leak_fraction"] < 1.0
    assert result["recovered_matches_b"] is True




@pytest.mark.parametrize("algorithm", ALGORITHMS)
def test_image_demo_returns_two_pngs_of_same_size(algorithm, tmp_path):
    path = tmp_path / "img.png"
    _make_png(path, (100, 80))
    result = image_encryption_demo(algorithm, str(path))
    assert (result["width"], result["height"]) == (100, 80)
    assert result["original_png"].startswith(PNG_MAGIC)
    assert result["cipher_png"].startswith(PNG_MAGIC)
    assert result["cipher_png"] != result["original_png"]


def test_image_demo_downsizes_large_images(tmp_path):
    path = tmp_path / "big.png"
    Image.new("RGB", (1000, 500), (10, 20, 30)).save(path)
    result = image_encryption_demo("AES-GCM", str(path))
    assert max(result["width"], result["height"]) <= 384
