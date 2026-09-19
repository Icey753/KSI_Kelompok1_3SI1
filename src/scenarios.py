import math
import os
import time

import numpy as np
import pandas as pd

from src import report
from src.aead import ALL_VARIANTS, NONCE_LEN, TAG_LEN, open_sealed, seal

AD = b"scenario"
SMALL_MESSAGE_SIZES = (64, 256, 1024, 4096)
ACCEL_SIZES = (1024, 65536, 1048576, 10485760)


def run_small_message_scenario(
    message_sizes=SMALL_MESSAGE_SIZES, n_messages: int = 2000, warm_ups: int = 200
) -> list[dict]:
    rows: list[dict] = []
    for algorithm in ALL_VARIANTS:
        for size in message_sizes:
            key = os.urandom(16)
            warm_messages = [os.urandom(size) for _ in range(warm_ups)]
            warm_nonces = [os.urandom(NONCE_LEN[algorithm]) for _ in range(warm_ups)]
            for warm_message, warm_nonce in zip(warm_messages, warm_nonces):
                seal(algorithm, key, warm_nonce, AD, warm_message)

            messages = [os.urandom(size) for _ in range(n_messages)]
            nonces = [os.urandom(NONCE_LEN[algorithm]) for _ in range(n_messages)]
            per_message_ns = []
            for message, nonce in zip(messages, nonces):
                start = time.perf_counter_ns()
                seal(algorithm, key, nonce, AD, message)
                per_message_ns.append(time.perf_counter_ns() - start)

            # MessagesPerSec and ThroughputMBps are seal-only rates (sum of per-call seal times; loop overhead excluded)
            total_seconds = sum(per_message_ns) / 1e9
            per_message_us = np.array(per_message_ns) / 1000.0
            rows.append(
                {
                    "Algorithm": algorithm,
                    "MessageSizeBytes": size,
                    "Messages": n_messages,
                    "MessagesPerSec": n_messages / total_seconds,
                    "LatencyMedianUs": float(np.median(per_message_us)),
                    "LatencyP95Us": float(np.percentile(per_message_us, 95)),
                    "ThroughputMBps": (n_messages * size / 1e6) / total_seconds,
                }
            )
    return rows


def run_acceleration_scenario(sizes=ACCEL_SIZES, iterations: int = 20, warm_ups: int = 3) -> list[dict]:
    rows: list[dict] = []
    for algorithm in ALL_VARIANTS:
        for size in sizes:
            # Key+nonce reuse is for timing only; ciphertext is discarded (never persisted)
            key, nonce, data = os.urandom(16), os.urandom(NONCE_LEN[algorithm]), os.urandom(size)
            for _ in range(warm_ups):
                seal(algorithm, key, nonce, AD, data)
            times_ms = []
            for _ in range(iterations):
                start = time.perf_counter()
                seal(algorithm, key, nonce, AD, data)
                times_ms.append((time.perf_counter() - start) * 1000)
            rows.append({"Algorithm": algorithm, "SizeBytes": size, "EncMedianMs": float(np.median(times_ms))})
    return rows


def _chunk_nonce(base_nonce: bytes, index: int) -> bytes:
    return base_nonce[:-8] + index.to_bytes(8, "big")


def _chunk_ad(index: int, is_last: bool) -> bytes:
    return AD + index.to_bytes(8, "big") + (b"\x01" if is_last else b"\x00")


def encrypt_chunked(algorithm: str, key: bytes, base_nonce: bytes, data: bytes, chunk_size: int) -> list[tuple[bytes, bytes]]:
    if chunk_size <= 0:
        raise ValueError("chunk_size harus positif")
    count = max(1, math.ceil(len(data) / chunk_size))
    return [
        seal(
            algorithm,
            key,
            _chunk_nonce(base_nonce, i),
            _chunk_ad(i, i == count - 1),
            data[i * chunk_size : (i + 1) * chunk_size],
        )
        for i in range(count)
    ]


def decrypt_chunked(algorithm: str, key: bytes, base_nonce: bytes, chunks: list[tuple[bytes, bytes]]) -> bytes | None:
    if not chunks:
        return None
    parts = []
    for i, (ciphertext, tag) in enumerate(chunks):
        plaintext = open_sealed(
            algorithm, key, _chunk_nonce(base_nonce, i), _chunk_ad(i, i == len(chunks) - 1), ciphertext, tag
        )
        if plaintext is None:
            return None
        parts.append(plaintext)
    return b"".join(parts)


# For very small chunk sizes, Python call overhead dominates the measured latency
# (about total_bytes/chunk_size Python-level seal calls), so small-chunk numbers reflect
# this implementation overhead, not the algorithm alone.
def run_chunked_scenario(
    total_bytes: int = 8 * 1024 * 1024,
    chunk_sizes=(4096, 65536, 1048576, None),
    iterations: int = 10,
    warm_ups: int = 2,
) -> list[dict]:
    if iterations < 1:
        raise ValueError("iterations harus >= 1")
    data = os.urandom(total_bytes)
    rows: list[dict] = []
    for algorithm in ALL_VARIANTS:
        for requested in chunk_sizes:
            # Fresh key+nonce per (algorithm, chunk size); iterations within one configuration re-encrypt
            # identical data under identical nonces for timing only, and the ciphertext is discarded.
            key, base_nonce = os.urandom(16), os.urandom(NONCE_LEN[algorithm])
            chunk_size = total_bytes if requested is None else requested
            for _ in range(warm_ups):
                decrypt_chunked(algorithm, key, base_nonce, encrypt_chunked(algorithm, key, base_nonce, data, chunk_size))

            enc_ms, dec_ms = [], []
            chunks = []
            for _ in range(iterations):
                start = time.perf_counter()
                chunks = encrypt_chunked(algorithm, key, base_nonce, data, chunk_size)
                enc_ms.append((time.perf_counter() - start) * 1000)
                start = time.perf_counter()
                decrypted = decrypt_chunked(algorithm, key, base_nonce, chunks)
                dec_ms.append((time.perf_counter() - start) * 1000)
            if decrypted != data:
                raise ValueError("Dekripsi chunked tidak cocok dengan data asli")

            overhead = TAG_LEN * len(chunks) + len(base_nonce)
            enc_median = float(np.median(enc_ms))
            rows.append(
                {
                    "Algorithm": algorithm,
                    "TotalBytes": total_bytes,
                    "ChunkSizeBytes": chunk_size,
                    "Chunks": len(chunks),
                    "EncMedianMs": enc_median,
                    "DecMedianMs": float(np.median(dec_ms)),
                    "OverheadBytes": overhead,
                    "OverheadPct": overhead / total_bytes * 100,
                    "ThroughputMBps": (total_bytes / 1e6) / (enc_median / 1000),
                }
            )
    return rows


def run_and_save_scenarios(
    n_messages: int = 2000,
    total_bytes: int = 8 * 1024 * 1024,
    iterations: int = 10,
    acceleration_sizes=ACCEL_SIZES,
    results_dir=None,
) -> dict[str, pd.DataFrame]:
    outputs = {
        "small_messages": run_small_message_scenario(n_messages=n_messages, warm_ups=min(200, n_messages)),
        "chunked": run_chunked_scenario(total_bytes=total_bytes, iterations=iterations),
        "acceleration": run_acceleration_scenario(sizes=acceleration_sizes, iterations=iterations),
    }
    results_dir = report.RESULTS_DIR if results_dir is None else results_dir
    os.makedirs(results_dir, exist_ok=True)
    frames = {}
    for name, rows in outputs.items():
        frames[name] = pd.DataFrame(rows)
        frames[name].to_csv(os.path.join(results_dir, f"{name}.csv"), index=False)
    return frames


if __name__ == "__main__":
    for scenario_name, frame in run_and_save_scenarios().items():
        print(f"\n== {scenario_name} ==")
        print(frame.to_string(index=False))
