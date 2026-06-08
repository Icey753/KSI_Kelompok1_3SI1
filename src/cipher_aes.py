from Crypto.Cipher import AES
import os

def aes_gcm_encrypt(key: bytes, nonce: bytes, ad: bytes, plaintext: bytes) -> tuple[bytes, bytes]:
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
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    if ad:
        cipher.update(ad)
    ciphertext, tag = cipher.encrypt_and_digest(plaintext)
    return ciphertext, tag

def aes_gcm_decrypt(key: bytes, nonce: bytes, ad: bytes, ciphertext: bytes, tag: bytes) -> bytes | None:
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
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    if ad:
        cipher.update(ad)
    try:
        plaintext = cipher.decrypt_and_verify(ciphertext, tag)
        return plaintext
    except (ValueError, KeyError):
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
