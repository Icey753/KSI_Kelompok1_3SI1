import os

from src.aead import ALGORITHMS, ALL_VARIANTS, NONCE_LEN, open_sealed, seal


def test_algorithms_unchanged_and_variants_include_noni():
    assert ALGORITHMS == ("AES-GCM", "Ascon-128")
    assert ALL_VARIANTS == ("AES-GCM", "Ascon-128", "AES-GCM-noNI")


def test_noni_output_identical_to_aesni():
    key, nonce, ad, pt = os.urandom(16), os.urandom(12), b"ad", os.urandom(4096)
    assert seal("AES-GCM-noNI", key, nonce, ad, pt) == seal("AES-GCM", key, nonce, ad, pt)


def test_noni_roundtrip_and_cross_decrypt():
    key, nonce, ad, pt = os.urandom(16), os.urandom(NONCE_LEN["AES-GCM-noNI"]), b"", b"halo dunia" * 20
    ct, tag = seal("AES-GCM-noNI", key, nonce, ad, pt)
    assert open_sealed("AES-GCM-noNI", key, nonce, ad, ct, tag) == pt
    assert open_sealed("AES-GCM", key, nonce, ad, ct, tag) == pt


def test_noni_rejects_tampered_ciphertext():
    key, nonce = os.urandom(16), os.urandom(12)
    ct, tag = seal("AES-GCM-noNI", key, nonce, b"", b"secret data")
    bad = bytes([ct[0] ^ 1]) + ct[1:]
    assert open_sealed("AES-GCM-noNI", key, nonce, b"", bad, tag) is None
