import os

import pytest

from src.aead import ALL_VARIANTS, NONCE_LEN
from src.scenarios import decrypt_chunked, encrypt_chunked, run_chunked_scenario


def _setup(algorithm):
    return os.urandom(16), os.urandom(NONCE_LEN[algorithm])


@pytest.mark.parametrize("algorithm", ALL_VARIANTS)
def test_chunked_roundtrip(algorithm):
    key, base = _setup(algorithm)
    data = os.urandom(10_000)
    chunks = encrypt_chunked(algorithm, key, base, data, 4096)
    assert len(chunks) == 3
    assert decrypt_chunked(algorithm, key, base, chunks) == data


def test_chunked_empty_data_roundtrip():
    key, base = _setup("AES-GCM")
    chunks = encrypt_chunked("AES-GCM", key, base, b"", 4096)
    assert len(chunks) == 1
    assert decrypt_chunked("AES-GCM", key, base, chunks) == b""


def test_chunk_size_must_be_positive():
    key, base = _setup("AES-GCM")
    with pytest.raises(ValueError):
        encrypt_chunked("AES-GCM", key, base, b"x", 0)


@pytest.mark.parametrize("algorithm", ("AES-GCM", "Ascon-128"))
def test_tampered_chunk_rejected(algorithm):
    key, base = _setup(algorithm)
    chunks = encrypt_chunked(algorithm, key, base, os.urandom(10_000), 4096)
    ct, tag = chunks[1]
    chunks[1] = (bytes([ct[0] ^ 1]) + ct[1:], tag)
    assert decrypt_chunked(algorithm, key, base, chunks) is None


@pytest.mark.parametrize("algorithm", ("AES-GCM", "Ascon-128"))
def test_reordered_chunks_rejected(algorithm):
    key, base = _setup(algorithm)
    chunks = encrypt_chunked(algorithm, key, base, os.urandom(10_000), 4096)
    chunks[0], chunks[1] = chunks[1], chunks[0]
    assert decrypt_chunked(algorithm, key, base, chunks) is None


@pytest.mark.parametrize("algorithm", ("AES-GCM", "Ascon-128"))
def test_truncated_stream_rejected(algorithm):
    key, base = _setup(algorithm)
    chunks = encrypt_chunked(algorithm, key, base, os.urandom(10_000), 4096)
    assert decrypt_chunked(algorithm, key, base, chunks[:-1]) is None


def test_chunked_scenario_overhead_and_shape():
    rows = run_chunked_scenario(total_bytes=100_000, chunk_sizes=(4096, None), iterations=1, warm_ups=0)
    assert len(rows) == len(ALL_VARIANTS) * 2
    aes_small = next(r for r in rows if r["Algorithm"] == "AES-GCM" and r["ChunkSizeBytes"] == 4096)
    aes_whole = next(r for r in rows if r["Algorithm"] == "AES-GCM" and r["ChunkSizeBytes"] == 100_000)
    ascon_small = next(r for r in rows if r["Algorithm"] == "Ascon-128" and r["ChunkSizeBytes"] == 4096)
    assert aes_small["Chunks"] == 25
    assert aes_small["OverheadBytes"] == 16 * 25 + 12
    assert ascon_small["OverheadBytes"] == 16 * 25 + 16
    assert aes_whole["Chunks"] == 1
    assert aes_whole["OverheadBytes"] == 16 + 12
    assert aes_small["OverheadPct"] > aes_whole["OverheadPct"]


@pytest.mark.parametrize("algorithm", ("AES-GCM", "Ascon-128"))
def test_empty_chunk_list_rejected(algorithm):
    key, base = _setup(algorithm)
    assert decrypt_chunked(algorithm, key, base, []) is None


@pytest.mark.parametrize("algorithm", ("AES-GCM", "Ascon-128"))
def test_appended_extra_chunk_rejected(algorithm):
    key, base = _setup(algorithm)
    chunks = encrypt_chunked(algorithm, key, base, os.urandom(10_000), 4096)
    chunks.append(chunks[-1])
    assert decrypt_chunked(algorithm, key, base, chunks) is None


@pytest.mark.parametrize("algorithm", ("AES-GCM", "Ascon-128"))
def test_duplicated_middle_chunk_rejected(algorithm):
    key, base = _setup(algorithm)
    chunks = encrypt_chunked(algorithm, key, base, os.urandom(10_000), 4096)
    chunks.insert(2, chunks[1])
    assert decrypt_chunked(algorithm, key, base, chunks) is None
