import os
import time

import numpy as np

from src.aead import ALL_VARIANTS, NONCE_LEN, seal

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
            messages = [os.urandom(size) for _ in range(n_messages)]
            nonces = [os.urandom(NONCE_LEN[algorithm]) for _ in range(n_messages)]
            for i in range(min(warm_ups, n_messages)):
                seal(algorithm, key, nonces[i], AD, messages[i])

            per_message_ns = []
            for message, nonce in zip(messages, nonces):
                start = time.perf_counter_ns()
                seal(algorithm, key, nonce, AD, message)
                per_message_ns.append(time.perf_counter_ns() - start)

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
