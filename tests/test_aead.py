import os

import pytest

from src.aead import ALGORITHMS, NONCE_LEN, TAG_LEN, open_sealed, seal


@pytest.mark.parametrize("algorithm", ALGORITHMS)
def test_seal_open_roundtrip(algorithm):
    key, nonce, ad, pt = os.urandom(16), os.urandom(NONCE_LEN[algorithm]), b"ad", b"hello world" * 10
    ct, tag = seal(algorithm, key, nonce, ad, pt)
    assert len(ct) == len(pt)
    assert len(tag) == TAG_LEN
    assert open_sealed(algorithm, key, nonce, ad, ct, tag) == pt


@pytest.mark.parametrize("algorithm", ALGORITHMS)
def test_open_rejects_wrong_key(algorithm):
    key, nonce = os.urandom(16), os.urandom(NONCE_LEN[algorithm])
    ct, tag = seal(algorithm, key, nonce, b"", b"secret")
    assert open_sealed(algorithm, os.urandom(16), nonce, b"", ct, tag) is None


def test_unknown_algorithm_raises():
    with pytest.raises(ValueError):
        seal("ROT13", b"k" * 16, b"n" * 12, b"", b"x")
    with pytest.raises(ValueError):
        open_sealed("ROT13", b"k" * 16, b"n" * 12, b"", b"x", b"t" * 16)
