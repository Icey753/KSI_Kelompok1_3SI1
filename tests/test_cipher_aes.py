import os

from src.cipher_aes import CBC_IV_LEN, aes_cbc_decrypt, aes_cbc_encrypt


def test_cbc_roundtrip():
    key, iv = os.urandom(16), os.urandom(CBC_IV_LEN)
    plaintext = b"pesan rahasia lewat AES-CBC" * 3
    ciphertext = aes_cbc_encrypt(key, iv, plaintext)
    assert aes_cbc_decrypt(key, iv, ciphertext) == plaintext


def test_cbc_ciphertext_is_block_aligned():
    key, iv = os.urandom(16), os.urandom(CBC_IV_LEN)
    ciphertext = aes_cbc_encrypt(key, iv, b"12345")
    assert len(ciphertext) % 16 == 0


def test_cbc_decrypt_rejects_invalid_padding():
    key, iv = os.urandom(16), os.urandom(CBC_IV_LEN)
    ciphertext = aes_cbc_encrypt(key, iv, b"data" * 8)
    corrupted = bytearray(ciphertext)
    corrupted[-1] ^= 0xFF  # forces the last padding byte to be invalid
    assert aes_cbc_decrypt(key, iv, bytes(corrupted)) is None
