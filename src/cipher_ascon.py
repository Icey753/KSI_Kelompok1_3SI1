import ascon
import os

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
    return ascon.encrypt(key, nonce, ad, plaintext, variant="Ascon-128")

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
    return ascon.decrypt(key, nonce, ad, ciphertext_with_tag, variant="Ascon-128")

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
