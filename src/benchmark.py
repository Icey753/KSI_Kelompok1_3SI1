import os
import time
import numpy as np
from src.cipher_aes import aes_gcm_encrypt, aes_gcm_decrypt
from src.cipher_ascon import ascon_128_encrypt, ascon_128_decrypt

def run_single_file_benchmark(file_path: str, file_type: str, size_category: str, warm_ups: int = 5, iterations: int = 50) -> list[dict]:
    """
    Runs benchmark on a single file using AES-GCM and Ascon-128.
    
    Args:
        file_path (str): Path to the input file
        file_type (str): 'json' or 'image'
        size_category (str): 'small', 'medium', or 'large'
        warm_ups (int): Number of discarded warm-up runs
        iterations (int): Number of recorded iterations
        
    Returns:
        list[dict]: List containing result dictionaries for AES-GCM and Ascon-128
    """
    print(f"\nBenchmarking {file_type.upper()} ({size_category}): {os.path.basename(file_path)}")
    
    with open(file_path, "rb") as f:
        plaintext = f.read()
        
    plaintext_size = len(plaintext)
    ad = b"cipher-benchmark-metadata"
    
    results = []
    
    # ----------------------------------------------------
    # 1. AES-GCM Benchmark
    # ----------------------------------------------------
    aes_key = os.urandom(16)
    aes_nonce = os.urandom(12) # NIST standard for GCM is 12 bytes
    
    # Warm-up
    for _ in range(warm_ups):
        ct, tag = aes_gcm_encrypt(aes_key, aes_nonce, ad, plaintext)
        _ = aes_gcm_decrypt(aes_key, aes_nonce, ad, ct, tag)
        
    # Recorded run
    aes_enc_times = []
    aes_dec_times = []
    
    for _ in range(iterations):
        # Time encryption
        t0 = time.perf_counter()
        ct, tag = aes_gcm_encrypt(aes_key, aes_nonce, ad, plaintext)
        t1 = time.perf_counter()
        aes_enc_times.append((t1 - t0) * 1000) # Convert to ms
        
        # Time decryption
        t2 = time.perf_counter()
        pt_dec = aes_gcm_decrypt(aes_key, aes_nonce, ad, ct, tag)
        t3 = time.perf_counter()
        aes_dec_times.append((t3 - t2) * 1000) # Convert to ms
        
        # Verify correctness
        assert pt_dec == plaintext, "AES-GCM decryption mismatch!"
        
    # Tampering test
    tampered_ct = bytearray(ct)
    tampered_ct[0] ^= 0x01
    tampered_dec = aes_gcm_decrypt(aes_key, aes_nonce, ad, bytes(tampered_ct), tag)
    aes_tamper_ok = (tampered_dec is None)
    
    aes_encrypted_size = len(ct) + len(tag) # Combined size of ciphertext + tag
    aes_overhead_bytes = aes_encrypted_size - plaintext_size
    aes_overhead_pct = (aes_overhead_bytes / plaintext_size) * 100 if plaintext_size > 0 else 0
    
    results.append({
        "Algorithm": "AES-GCM",
        "FileType": file_type,
        "SizeCategory": size_category,
        "PlaintextSizeBytes": plaintext_size,
        "CiphertextSizeBytes": aes_encrypted_size,
        "EncLatencyMeanMs": np.mean(aes_enc_times),
        "EncLatencyStdMs": np.std(aes_enc_times),
        "DecLatencyMeanMs": np.mean(aes_dec_times),
        "DecLatencyStdMs": np.std(aes_dec_times),
        "OverheadBytes": aes_overhead_bytes,
        "OverheadPct": aes_overhead_pct,
        "TamperingIntegrityPassed": aes_tamper_ok
    })
    
    # ----------------------------------------------------
    # 2. Ascon-128 Benchmark
    # ----------------------------------------------------
    ascon_key = os.urandom(16)
    ascon_nonce = os.urandom(16) # Ascon nonce is 16 bytes
    
    # Warm-up
    for _ in range(warm_ups):
        ct_with_tag = ascon_128_encrypt(ascon_key, ascon_nonce, ad, plaintext)
        _ = ascon_128_decrypt(ascon_key, ascon_nonce, ad, ct_with_tag)
        
    # Recorded run
    ascon_enc_times = []
    ascon_dec_times = []
    
    for _ in range(iterations):
        # Time encryption
        t0 = time.perf_counter()
        ct_with_tag = ascon_128_encrypt(ascon_key, ascon_nonce, ad, plaintext)
        t1 = time.perf_counter()
        ascon_enc_times.append((t1 - t0) * 1000) # Convert to ms
        
        # Time decryption
        t2 = time.perf_counter()
        pt_dec = ascon_128_decrypt(ascon_key, ascon_nonce, ad, ct_with_tag)
        t3 = time.perf_counter()
        ascon_dec_times.append((t3 - t2) * 1000) # Convert to ms
        
        # Verify correctness
        assert pt_dec == plaintext, "Ascon-128 decryption mismatch!"
        
    # Tampering test
    tampered_ct_ascon = bytearray(ct_with_tag)
    tampered_ct_ascon[0] ^= 0x01
    tampered_dec_ascon = ascon_128_decrypt(ascon_key, ascon_nonce, ad, bytes(tampered_ct_ascon))
    ascon_tamper_ok = (tampered_dec_ascon is None)
    
    ascon_encrypted_size = len(ct_with_tag)
    ascon_overhead_bytes = ascon_encrypted_size - plaintext_size
    ascon_overhead_pct = (ascon_overhead_bytes / plaintext_size) * 100 if plaintext_size > 0 else 0
    
    results.append({
        "Algorithm": "Ascon-128",
        "FileType": file_type,
        "SizeCategory": size_category,
        "PlaintextSizeBytes": plaintext_size,
        "CiphertextSizeBytes": ascon_encrypted_size,
        "EncLatencyMeanMs": np.mean(ascon_enc_times),
        "EncLatencyStdMs": np.std(ascon_enc_times),
        "DecLatencyMeanMs": np.mean(ascon_dec_times),
        "DecLatencyStdMs": np.std(ascon_dec_times),
        "OverheadBytes": ascon_overhead_bytes,
        "OverheadPct": ascon_overhead_pct,
        "TamperingIntegrityPassed": ascon_tamper_ok
    })
    
    print(f"  AES-GCM   - Enc: {results[0]['EncLatencyMeanMs']:.3f} ms, Dec: {results[0]['DecLatencyMeanMs']:.3f} ms, Tamper Test: {'PASSED' if aes_tamper_ok else 'FAILED'}")
    print(f"  Ascon-128 - Enc: {results[1]['EncLatencyMeanMs']:.3f} ms, Dec: {results[1]['DecLatencyMeanMs']:.3f} ms, Tamper Test: {'PASSED' if ascon_tamper_ok else 'FAILED'}")
    
    return results

if __name__ == "__main__":
    # Create temp directory for testing
    import tempfile
    
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(b"Hello world benchmark test payload! " * 100)
        tmp_name = tmp.name
        
    try:
        res = run_single_file_benchmark(tmp_name, "json", "small", warm_ups=2, iterations=10)
        print("Self-test results:")
        for r in res:
            print(r)
    finally:
        os.unlink(tmp_name)
