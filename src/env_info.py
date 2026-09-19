import json
import os
import platform
import statistics
import time

import Crypto
from Crypto.Cipher import AES

from src.cipher_ascon import BACKEND, VARIANT

DEFAULT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output", "results", "environment.json"
)


def measure_aesni_speedup(size: int = 1 << 20, repeats: int = 5) -> float:
    data, key, nonce = os.urandom(size), os.urandom(16), os.urandom(12)

    def median_seconds(use_aesni: bool) -> float:
        times = []
        for _ in range(repeats):
            start = time.perf_counter()
            AES.new(key, AES.MODE_GCM, nonce=nonce, use_aesni=use_aesni).encrypt_and_digest(data)
            times.append(time.perf_counter() - start)
        return statistics.median(times)

    return median_seconds(False) / median_seconds(True)


def collect_env_info(aesni_repeats: int = 5) -> dict:
    return {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "processor": platform.processor(),
        "cpu_count": os.cpu_count(),
        "pycryptodome": Crypto.__version__,
        "ascon_backend": BACKEND,
        "ascon_variant": VARIANT,
        "aesni_speedup": round(measure_aesni_speedup(repeats=aesni_repeats), 2),
    }


def save_env_info(path: str | None = None) -> str:
    path = path or DEFAULT_PATH
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(collect_env_info(), handle, indent=2, ensure_ascii=False)
    return path
