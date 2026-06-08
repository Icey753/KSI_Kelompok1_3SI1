import os
import ctypes
from ctypes import byref, c_ulonglong, create_string_buffer
from pathlib import Path

import ascon

BASE_DIR = Path(__file__).resolve().parent.parent
NATIVE_DIR = BASE_DIR / "native" / "ascon"
NATIVE_BIN_DIR = NATIVE_DIR / "bin"


def _load_c_backend():
    candidates = [
        NATIVE_BIN_DIR / "libcrypto_aead_asconaead128_ref.dll",
        NATIVE_BIN_DIR / "crypto_aead_asconaead128_ref.dll",
        NATIVE_BIN_DIR / "ascon.dll",
        NATIVE_DIR / "build" / "ascon.dll",
        NATIVE_DIR / "build" / "libascon.so",
        NATIVE_DIR / "build" / "libascon.dylib",
        NATIVE_DIR / "ascon.dll",
        NATIVE_DIR / "libascon.so",
        NATIVE_DIR / "libascon.dylib",
    ]

    for candidate in candidates:
        if candidate.exists():
            library = ctypes.CDLL(str(candidate))
            library.crypto_aead_encrypt.argtypes = [
                ctypes.POINTER(ctypes.c_ubyte),
                ctypes.POINTER(c_ulonglong),
                ctypes.POINTER(ctypes.c_ubyte),
                c_ulonglong,
                ctypes.POINTER(ctypes.c_ubyte),
                c_ulonglong,
                ctypes.POINTER(ctypes.c_ubyte),
                ctypes.POINTER(ctypes.c_ubyte),
                ctypes.POINTER(ctypes.c_ubyte),
            ]
            library.crypto_aead_encrypt.restype = ctypes.c_int
            library.crypto_aead_decrypt.argtypes = [
                ctypes.POINTER(ctypes.c_ubyte),
                ctypes.POINTER(c_ulonglong),
                ctypes.POINTER(ctypes.c_ubyte),
                ctypes.POINTER(ctypes.c_ubyte),
                c_ulonglong,
                ctypes.POINTER(ctypes.c_ubyte),
                c_ulonglong,
                ctypes.POINTER(ctypes.c_ubyte),
                ctypes.POINTER(ctypes.c_ubyte),
            ]
            library.crypto_aead_decrypt.restype = ctypes.c_int
            return library
    return None


_ASCON_C = _load_c_backend()


def _to_ubyte_buffer(data: bytes):
    return (ctypes.c_ubyte * len(data)).from_buffer_copy(data)

def ascon_128_encrypt(key: bytes, nonce: bytes, ad: bytes, plaintext: bytes) -> bytes:
    """
    Encrypts plaintext using Ascon-128.
    
    Args:
        key (bytes): 16 bytes key
        nonce (bytes): 16 bytes nonce
        ad (bytes): Associated authenticated data
        plaintext (bytes): The data to encrypt
        
    Returns:
        bytes: Combined ciphertext and 16-byte authentication tag
    """
    if _ASCON_C is None:
        return ascon.encrypt(key, nonce, ad, plaintext, variant="Ascon-128")

    output = create_string_buffer(len(plaintext) + 16)
    output_length = c_ulonglong()
    result = _ASCON_C.crypto_aead_encrypt(
        ctypes.cast(output, ctypes.POINTER(ctypes.c_ubyte)),
        byref(output_length),
        _to_ubyte_buffer(plaintext),
        len(plaintext),
        _to_ubyte_buffer(ad) if ad else None,
        len(ad),
        None,
        _to_ubyte_buffer(nonce),
        _to_ubyte_buffer(key),
    )
    if result != 0:
        raise RuntimeError("Ascon C backend encryption failed")
    return output.raw[: output_length.value]

def ascon_128_decrypt(key: bytes, nonce: bytes, ad: bytes, ciphertext_with_tag: bytes) -> bytes | None:
    """
    Decrypts and verifies ciphertext using Ascon-128.
    
    Args:
        key (bytes): 16 bytes key
        nonce (bytes): 16 bytes nonce
        ad (bytes): Associated authenticated data
        ciphertext_with_tag (bytes): Combined ciphertext and 16-byte authentication tag
        
    Returns:
        bytes: Decrypted plaintext if verification succeeds, None otherwise.
    """
    if _ASCON_C is None:
        return ascon.decrypt(key, nonce, ad, ciphertext_with_tag, variant="Ascon-128")

    if len(ciphertext_with_tag) < 16:
        return None

    output = create_string_buffer(len(ciphertext_with_tag))
    output_length = c_ulonglong()
    result = _ASCON_C.crypto_aead_decrypt(
        ctypes.cast(output, ctypes.POINTER(ctypes.c_ubyte)),
        byref(output_length),
        None,
        _to_ubyte_buffer(ciphertext_with_tag),
        len(ciphertext_with_tag),
        _to_ubyte_buffer(ad) if ad else None,
        len(ad),
        _to_ubyte_buffer(nonce),
        _to_ubyte_buffer(key),
    )
    if result != 0:
        return None
    return output.raw[: output_length.value]

if __name__ == "__main__":
    # Simple self-test
    print("Testing Ascon-128 wrapper...")
    test_key = os.urandom(16)
    test_nonce = os.urandom(16)
    test_ad = b"associated data"
    test_pt = b"This is a secret message for Ascon-128."
    
    ct_with_tag = ascon_128_encrypt(test_key, test_nonce, test_ad, test_pt)
    print(f"Combined Ciphertext + Tag length: {len(ct_with_tag)} bytes")
    
    decrypted = ascon_128_decrypt(test_key, test_nonce, test_ad, ct_with_tag)
    assert decrypted == test_pt, "Decryption verification failed!"
    print("Decryption successful: ", decrypted.decode('utf-8'))
    
    # Tampering test
    print("Testing tampering detection...")
    tampered_ct = bytearray(ct_with_tag)
    tampered_ct[0] ^= 0x01  # flip a bit
    failed_dec = ascon_128_decrypt(test_key, test_nonce, test_ad, bytes(tampered_ct))
    assert failed_dec is None, "Tampering was not detected!"
    print("Tampering correctly detected!")
