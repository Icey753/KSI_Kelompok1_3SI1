import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from src.cipher_aes import aes_gcm_decrypt, aes_gcm_encrypt
from src.cipher_ascon import ascon_128_decrypt, ascon_128_encrypt

AD = b"cipher-benchmark-metadata"


def _safe_stem(file_name: str) -> str:
    stem = Path(file_name).stem or "upload"
    safe_chars = []
    for character in stem:
        if character.isalnum() or character in {"-", "_"}:
            safe_chars.append(character)
        else:
            safe_chars.append("_")
    safe_stem = "".join(safe_chars).strip("._")
    return safe_stem or "upload"


def _build_result_row(
    algorithm: str,
    file_type: str,
    size_category: str,
    input_file_name: str,
    plaintext_size: int,
    ciphertext_size: int,
    enc_times: list[float],
    dec_times: list[float],
    overhead_bytes: int,
    overhead_pct: float,
    tampering_passed: bool,
) -> dict:
    return {
        "Algorithm": algorithm,
        "InputFileName": input_file_name,
        "FileType": file_type,
        "SizeCategory": size_category,
        "PlaintextSizeBytes": plaintext_size,
        "CiphertextSizeBytes": ciphertext_size,
        "EncLatencyMeanMs": float(np.mean(enc_times)),
        "EncLatencyStdMs": float(np.std(enc_times)),
        "DecLatencyMeanMs": float(np.mean(dec_times)),
        "DecLatencyStdMs": float(np.std(dec_times)),
        "OverheadBytes": overhead_bytes,
        "OverheadPct": overhead_pct,
        "TamperingIntegrityPassed": tampering_passed,
    }


def _persist_artifact_files(
    artifact_dir: Path,
    input_file_name: str,
    algorithm: str,
    ciphertext_bytes: bytes,
    metadata: dict,
) -> dict:
    artifact_dir.mkdir(parents=True, exist_ok=True)

    file_prefix = _safe_stem(input_file_name)
    algorithm_slug = algorithm.lower().replace("-", "_")
    ciphertext_path = artifact_dir / f"{file_prefix}_{algorithm_slug}_ciphertext.bin"
    metadata_path = artifact_dir / f"{file_prefix}_{algorithm_slug}_metadata.json"

    ciphertext_path.write_bytes(ciphertext_bytes)

    serializable_metadata = dict(metadata)
    serializable_metadata.update(
        {
            "ciphertext_filename": ciphertext_path.name,
            "ciphertext_path": str(ciphertext_path),
            "metadata_filename": metadata_path.name,
            "metadata_path": str(metadata_path),
        }
    )
    metadata_path.write_text(
        json.dumps(serializable_metadata, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    return {
        "ciphertext_path": str(ciphertext_path),
        "ciphertext_filename": ciphertext_path.name,
        "metadata_path": str(metadata_path),
        "metadata_filename": metadata_path.name,
    }


def _run_algorithm_benchmark(
    algorithm: str,
    plaintext: bytes,
    input_file_name: str,
    file_type: str,
    size_category: str,
    warm_ups: int,
    iterations: int,
    plaintext_size: int,
    artifact_dir: Path | None = None,
) -> tuple[dict, dict]:
    if algorithm == "AES-GCM":
        key = os.urandom(16)
        nonce = os.urandom(12)

        for _ in range(warm_ups):
            ciphertext, tag = aes_gcm_encrypt(key, nonce, AD, plaintext)
            _ = aes_gcm_decrypt(key, nonce, AD, ciphertext, tag)

        enc_times: list[float] = []
        dec_times: list[float] = []

        for _ in range(iterations):
            start = time.perf_counter()
            ciphertext, tag = aes_gcm_encrypt(key, nonce, AD, plaintext)
            end = time.perf_counter()
            enc_times.append((end - start) * 1000)

            start = time.perf_counter()
            decrypted = aes_gcm_decrypt(key, nonce, AD, ciphertext, tag)
            end = time.perf_counter()
            dec_times.append((end - start) * 1000)

            assert decrypted == plaintext, "AES-GCM decryption mismatch!"

        tampered_ciphertext = bytearray(ciphertext)
        tampered_ciphertext[0] ^= 0x01
        tampered_decrypted = aes_gcm_decrypt(key, nonce, AD, bytes(tampered_ciphertext), tag)
        tampering_passed = tampered_decrypted is None

        ciphertext_bytes = ciphertext + tag
        tag_bytes = tag
        nonce_bytes = nonce
    elif algorithm == "Ascon-128":
        key = os.urandom(16)
        nonce = os.urandom(16)

        for _ in range(warm_ups):
            ciphertext_with_tag = ascon_128_encrypt(key, nonce, AD, plaintext)
            _ = ascon_128_decrypt(key, nonce, AD, ciphertext_with_tag)

        enc_times = []
        dec_times = []

        for _ in range(iterations):
            start = time.perf_counter()
            ciphertext_with_tag = ascon_128_encrypt(key, nonce, AD, plaintext)
            end = time.perf_counter()
            enc_times.append((end - start) * 1000)

            start = time.perf_counter()
            decrypted = ascon_128_decrypt(key, nonce, AD, ciphertext_with_tag)
            end = time.perf_counter()
            dec_times.append((end - start) * 1000)

            assert decrypted == plaintext, "Ascon-128 decryption mismatch!"

        tampered_ciphertext = bytearray(ciphertext_with_tag)
        tampered_ciphertext[0] ^= 0x01
        tampered_decrypted = ascon_128_decrypt(key, nonce, AD, bytes(tampered_ciphertext))
        tampering_passed = tampered_decrypted is None

        ciphertext_bytes = ciphertext_with_tag
        tag_bytes = ciphertext_with_tag[-16:]
        nonce_bytes = nonce
    else:
        raise ValueError(f"Unsupported algorithm: {algorithm}")

    ciphertext_size = len(ciphertext_bytes)
    overhead_bytes = ciphertext_size - plaintext_size
    overhead_pct = (overhead_bytes / plaintext_size) * 100 if plaintext_size > 0 else 0.0

    row = _build_result_row(
        algorithm=algorithm,
        file_type=file_type,
        size_category=size_category,
        input_file_name=input_file_name,
        plaintext_size=plaintext_size,
        ciphertext_size=ciphertext_size,
        enc_times=enc_times,
        dec_times=dec_times,
        overhead_bytes=overhead_bytes,
        overhead_pct=overhead_pct,
        tampering_passed=tampering_passed,
    )

    metadata = {
        "algorithm": algorithm,
        "input_file_name": input_file_name,
        "file_type": file_type,
        "size_category": size_category,
        "plaintext_size_bytes": plaintext_size,
        "ciphertext_size_bytes": ciphertext_size,
        "nonce_hex": nonce_bytes.hex(),
        "tag_hex": tag_bytes.hex(),
        "associated_data_hex": AD.hex(),
        "enc_latency_mean_ms": float(np.mean(enc_times)),
        "enc_latency_std_ms": float(np.std(enc_times)),
        "dec_latency_mean_ms": float(np.mean(dec_times)),
        "dec_latency_std_ms": float(np.std(dec_times)),
        "overhead_bytes": overhead_bytes,
        "overhead_pct": overhead_pct,
        "tampering_integrity_passed": tampering_passed,
        "warm_ups": warm_ups,
        "iterations": iterations,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    artifact_info = {
        "algorithm": algorithm,
        "metadata": metadata,
    }

    if artifact_dir is not None:
        artifact_info.update(
            _persist_artifact_files(
                artifact_dir=artifact_dir,
                input_file_name=input_file_name,
                algorithm=algorithm,
                ciphertext_bytes=ciphertext_bytes,
                metadata=metadata,
            )
        )

    print(
        f"  {algorithm:<10} - Enc: {row['EncLatencyMeanMs']:.3f} ms, "
        f"Dec: {row['DecLatencyMeanMs']:.3f} ms, "
        f"Tamper Test: {'PASSED' if tampering_passed else 'FAILED'}"
    )

    return row, artifact_info


def _run_plaintext_benchmark(
    plaintext: bytes,
    input_file_name: str,
    file_type: str,
    size_category: str,
    warm_ups: int = 5,
    iterations: int = 50,
    artifact_dir: str | Path | None = None,
) -> tuple[list[dict], dict[str, dict]]:
    plaintext_size = len(plaintext)
    print(f"\nBenchmarking {file_type.upper()} ({size_category}): {input_file_name}")

    artifact_path = Path(artifact_dir) if artifact_dir is not None else None

    aes_row, aes_artifact = _run_algorithm_benchmark(
        algorithm="AES-GCM",
        plaintext=plaintext,
        input_file_name=input_file_name,
        file_type=file_type,
        size_category=size_category,
        warm_ups=warm_ups,
        iterations=iterations,
        plaintext_size=plaintext_size,
        artifact_dir=artifact_path,
    )

    ascon_row, ascon_artifact = _run_algorithm_benchmark(
        algorithm="Ascon-128",
        plaintext=plaintext,
        input_file_name=input_file_name,
        file_type=file_type,
        size_category=size_category,
        warm_ups=warm_ups,
        iterations=iterations,
        plaintext_size=plaintext_size,
        artifact_dir=artifact_path,
    )

    return [aes_row, ascon_row], {
        "AES-GCM": aes_artifact,
        "Ascon-128": ascon_artifact,
    }


def run_single_file_benchmark(
    file_path: str,
    file_type: str,
    size_category: str,
    warm_ups: int = 5,
    iterations: int = 50,
    input_file_name: str | None = None,
) -> list[dict]:
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
    with open(file_path, "rb") as file_handle:
        plaintext = file_handle.read()

    benchmark_rows, _ = _run_plaintext_benchmark(
        plaintext=plaintext,
        input_file_name=input_file_name or os.path.basename(file_path),
        file_type=file_type,
        size_category=size_category,
        warm_ups=warm_ups,
        iterations=iterations,
    )
    return benchmark_rows


def run_uploaded_file_benchmark(
    file_path: str,
    file_type: str,
    size_category: str,
    original_file_name: str | None = None,
    warm_ups: int = 5,
    iterations: int = 50,
    output_dir: str | None = None,
) -> tuple[list[dict], dict[str, dict]]:
    """
    Runs benchmark for a file uploaded from the dashboard and persists
    ciphertext plus metadata artifacts when an output directory is provided.
    """
    with open(file_path, "rb") as file_handle:
        plaintext = file_handle.read()

    return _run_plaintext_benchmark(
        plaintext=plaintext,
        input_file_name=original_file_name or os.path.basename(file_path),
        file_type=file_type,
        size_category=size_category,
        warm_ups=warm_ups,
        iterations=iterations,
        artifact_dir=output_dir,
    )

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
