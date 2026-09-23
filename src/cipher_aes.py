from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import os

def aes_gcm_encrypt(key: bytes, nonce: bytes, ad: bytes, plaintext: bytes, use_aesni: bool = True) -> tuple[bytes, bytes]:
    """
    Encrypts plaintext using AES-GCM.
    
    Args:
        key (bytes): 16 bytes key (AES-128)
        nonce (bytes): 12 bytes nonce (standard NIST GCM)
        ad (bytes): Associated authenticated data
        plaintext (bytes): The data to encrypt
        
    Returns:
        tuple[bytes, bytes]: (ciphertext, auth_tag)
    """
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce, use_aesni=use_aesni)
    if ad:
        cipher.update(ad)
    ciphertext, tag = cipher.encrypt_and_digest(plaintext)
    return ciphertext, tag

def aes_gcm_decrypt(key: bytes, nonce: bytes, ad: bytes, ciphertext: bytes, tag: bytes, use_aesni: bool = True) -> bytes | None:
    """
    Decrypts and verifies ciphertext using AES-GCM.
    
    Args:
        key (bytes): 16 bytes key
        nonce (bytes): 12 bytes nonce
        ad (bytes): Associated authenticated data
        ciphertext (bytes): The ciphertext to decrypt
        tag (bytes): 16 bytes authentication tag
        
    Returns:
        bytes: Decrypted plaintext if verification succeeds, None otherwise.
    """
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce, use_aesni=use_aesni)
    if ad:
        cipher.update(ad)
    try:
        plaintext = cipher.decrypt_and_verify(ciphertext, tag)
        return plaintext
    except (ValueError, KeyError):
        return None

CBC_IV_LEN = 16


def aes_cbc_encrypt(key: bytes, iv: bytes, plaintext: bytes) -> bytes:
    """
    Encrypts plaintext using AES-CBC. No authentication tag: a tampered
    ciphertext is not detected unless it breaks PKCS7 padding.

    Args:
        key (bytes): 16 bytes key (AES-128)
        iv (bytes): 16 bytes initialization vector
        plaintext (bytes): The data to encrypt

    Returns:
        bytes: block-aligned ciphertext (PKCS7-padded)
    """
    cipher = AES.new(key, AES.MODE_CBC, iv=iv)
    return cipher.encrypt(pad(plaintext, AES.block_size))


def aes_cbc_decrypt(key: bytes, iv: bytes, ciphertext: bytes) -> bytes | None:
    """
    Decrypts AES-CBC ciphertext and removes PKCS7 padding.

    Returns:
        bytes: Decrypted plaintext if padding is valid, None otherwise.
        A valid-padding result does NOT mean the plaintext is unmodified —
        CBC has no authentication tag.
    """
    cipher = AES.new(key, AES.MODE_CBC, iv=iv)
    try:
        return unpad(cipher.decrypt(ciphertext), AES.block_size)
    except ValueError:
        return None

if __name__ == "__main__":
    # Simple self-test
    print("Testing AES-GCM wrapper...")
    test_key = os.urandom(16)
    test_nonce = os.urandom(12)
    test_ad = b"associated data"
    test_pt = b"This is a secret message for AES-GCM."
    
    ct, tag = aes_gcm_encrypt(test_key, test_nonce, test_ad, test_pt)
    print(f"Ciphertext length: {len(ct)} bytes")
    print(f"Tag length: {len(tag)} bytes")
    
    decrypted = aes_gcm_decrypt(test_key, test_nonce, test_ad, ct, tag)
    assert decrypted == test_pt, "Decryption verification failed!"
    print("Decryption successful: ", decrypted.decode('utf-8'))
    
    # Tampering test
    print("Testing tampering detection...")
    tampered_ct = bytearray(ct)
    tampered_ct[0] ^= 0x01  # flip a bit
    failed_dec = aes_gcm_decrypt(test_key, test_nonce, test_ad, bytes(tampered_ct), tag)
    assert failed_dec is None, "Tampering was not detected!"
    print("Tampering correctly detected!")
