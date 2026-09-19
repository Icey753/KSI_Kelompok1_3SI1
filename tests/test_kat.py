from pathlib import Path

import pytest

from src.cipher_aes import aes_gcm_decrypt, aes_gcm_encrypt
from src.cipher_ascon import BACKEND, ascon_128_decrypt, ascon_128_encrypt

KAT_PATH = (
    Path(__file__).resolve().parent.parent
    / "native/ascon/ascon-c/crypto_aead/asconaead128/LWC_AEAD_KAT_128_128.txt"
)

needs_c_backend = pytest.mark.skipif(
    not BACKEND.startswith("C"), reason="KAT Ascon-AEAD128 hanya berlaku untuk backend C"
)
needs_kat_file = pytest.mark.skipif(not KAT_PATH.exists(), reason="file KAT ascon-c tidak ada")

# (key, nonce, ad, plaintext, ciphertext, tag) - NIST/McGrew-Viega GCM Test Case 1, 2, 4
AES_GCM_VECTORS = [
    ("00" * 16, "00" * 12, "", "", "", "58e2fccefa7e3061367f1d57a4e7455a"),
    ("00" * 16, "00" * 12, "", "00" * 16, "0388dace60b6a392f328c2b971b2fe78",
     "ab6e47d42cec13bdf53a67b21257bddf"),
    (
        "feffe9928665731c6d6a8f9467308308",
        "cafebabefacedbaddecaf888",
        "feedfacedeadbeeffeedfacedeadbeefabaddad2",
        "d9313225f88406e5a55909c5aff5269a86a7a9531534f7da2e4c303d8a318a72"
        "1c3c0c95956809532fcf0e2449a6b525b16aedf5aa0de657ba637b39",
        "42831ec2217774244b7221b784d0d49ce3aa212f2c02a4e035c17e2329aca12e"
        "21d514b25466931c7d8f6a5aac84aa051ba30b396a0aac973d58e091",
        "5bc94fbc3221a5db94fae95ae7121a47",
    ),
]


def _parse_kat(path: Path) -> list[dict]:
    vectors, current = [], {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            if current:
                vectors.append(current)
                current = {}
            continue
        name, _, value = line.partition("=")
        current[name.strip()] = value.strip()
    if current:
        vectors.append(current)
    return vectors


@pytest.mark.parametrize("key,nonce,ad,pt,ct,tag", AES_GCM_VECTORS)
def test_aes_gcm_nist_vectors(key, nonce, ad, pt, ct, tag):
    k, n, a, p = (bytes.fromhex(x) for x in (key, nonce, ad, pt))
    out_ct, out_tag = aes_gcm_encrypt(k, n, a, p)
    assert out_ct.hex() == ct
    assert out_tag.hex() == tag
    assert aes_gcm_decrypt(k, n, a, out_ct, out_tag) == p


def test_aes_gcm_rejects_flipped_tag():
    k, n = bytes(16), bytes(12)
    ct, tag = aes_gcm_encrypt(k, n, b"", b"hello")
    bad_tag = bytes([tag[0] ^ 1]) + tag[1:]
    assert aes_gcm_decrypt(k, n, b"", ct, bad_tag) is None


@needs_c_backend
@needs_kat_file
def test_ascon_aead128_matches_all_official_kat_vectors():
    vectors = _parse_kat(KAT_PATH)
    assert len(vectors) == 1089
    mismatches = []
    for v in vectors:
        key, nonce, ad, pt = (bytes.fromhex(v[f]) for f in ("Key", "Nonce", "AD", "PT"))
        out = ascon_128_encrypt(key, nonce, ad, pt)
        if out.hex().upper() != v["CT"].upper() or ascon_128_decrypt(key, nonce, ad, out) != pt:
            mismatches.append(v["Count"])
    assert not mismatches, f"KAT mismatch pada Count: {mismatches[:10]}"


@needs_c_backend
def test_ascon_rejects_flipped_tag():
    k, n = bytes(16), bytes(16)
    ct = ascon_128_encrypt(k, n, b"", b"hello")
    bad = ct[:-1] + bytes([ct[-1] ^ 1])
    assert ascon_128_decrypt(k, n, b"", bad) is None
