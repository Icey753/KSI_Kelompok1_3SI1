from src.cipher_aes import aes_gcm_decrypt, aes_gcm_encrypt
from src.cipher_ascon import ascon_128_decrypt, ascon_128_encrypt

TAG_LEN = 16
NONCE_LEN = {"AES-GCM": 12, "Ascon-128": 16, "AES-GCM-noNI": 12}
ALGORITHMS = ("AES-GCM", "Ascon-128")
ALL_VARIANTS = tuple(NONCE_LEN)


def seal(algorithm: str, key: bytes, nonce: bytes, ad: bytes, plaintext: bytes) -> tuple[bytes, bytes]:
    if algorithm == "AES-GCM":
        return aes_gcm_encrypt(key, nonce, ad, plaintext)
    if algorithm == "AES-GCM-noNI":
        return aes_gcm_encrypt(key, nonce, ad, plaintext, use_aesni=False)
    if algorithm == "Ascon-128":
        combined = ascon_128_encrypt(key, nonce, ad, plaintext)
        return combined[:-TAG_LEN], combined[-TAG_LEN:]
    raise ValueError(f"Unsupported algorithm: {algorithm}")


def open_sealed(
    algorithm: str, key: bytes, nonce: bytes, ad: bytes, ciphertext: bytes, tag: bytes
) -> bytes | None:
    if algorithm == "AES-GCM":
        return aes_gcm_decrypt(key, nonce, ad, ciphertext, tag)
    if algorithm == "AES-GCM-noNI":
        return aes_gcm_decrypt(key, nonce, ad, ciphertext, tag, use_aesni=False)
    if algorithm == "Ascon-128":
        return ascon_128_decrypt(key, nonce, ad, ciphertext + tag)
    raise ValueError(f"Unsupported algorithm: {algorithm}")
