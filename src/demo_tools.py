import hashlib
import io
import os

from PIL import Image

from src.aead import NONCE_LEN, open_sealed, seal

DEFAULT_AD = b"cipher-demo"
TAMPER_TARGETS = ("ciphertext", "tag", "nonce", "ad")
THUMB_MAX = 384


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def flip_bit(data: bytes, byte_index: int) -> bytes:
    mutable = bytearray(data)
    mutable[byte_index % len(data)] ^= 0x01
    return bytes(mutable)


def _xor(a: bytes, b: bytes) -> bytes:
    return bytes(x ^ y for x, y in zip(a, b))


def _new_key_nonce(algorithm: str) -> tuple[bytes, bytes]:
    return os.urandom(16), os.urandom(NONCE_LEN[algorithm])


def tamper_demo(algorithm, plaintext, target, byte_index=0, ad=DEFAULT_AD) -> dict:
    if target not in TAMPER_TARGETS:
        raise ValueError(f"Target tidak dikenal: {target}")
    key, nonce = _new_key_nonce(algorithm)
    ciphertext, tag = seal(algorithm, key, nonce, ad, plaintext)
    parts = {"ciphertext": ciphertext, "tag": tag, "nonce": nonce, "ad": ad}
    if not parts[target]:
        raise ValueError(f"Bagian '{target}' kosong, tidak bisa diubah")

    control = open_sealed(algorithm, key, nonce, ad, ciphertext, tag)
    flipped_index = byte_index % len(parts[target])
    parts[target] = flip_bit(parts[target], byte_index)
    result = open_sealed(
        algorithm, key, parts["nonce"], parts["ad"], parts["ciphertext"], parts["tag"]
    )
    return {
        "algorithm": algorithm,
        "target": target,
        "byte_index": flipped_index,
        "control_ok": control == plaintext,
        "rejected": result is None,
        "plaintext_returned": result is not None,
        "ciphertext_preview_hex": ciphertext[:16].hex(),
        "tag_hex": tag.hex(),
    }


def roundtrip_demo(algorithm, plaintext, ad=DEFAULT_AD) -> dict:
    key, nonce = _new_key_nonce(algorithm)
    ciphertext, tag = seal(algorithm, key, nonce, ad, plaintext)
    decrypted = open_sealed(algorithm, key, nonce, ad, ciphertext, tag)
    return {
        "algorithm": algorithm,
        "key_hex": key.hex(),
        "nonce_hex": nonce.hex(),
        "tag_hex": tag.hex(),
        "plaintext_bytes": len(plaintext),
        "ciphertext_bytes": len(ciphertext) + len(tag),
        "ciphertext_preview_hex": ciphertext[:32].hex(),
        "sha256_before": sha256_hex(plaintext),
        "sha256_after": sha256_hex(decrypted) if decrypted is not None else None,
        "match": decrypted == plaintext,
    }


def nonce_reuse_demo(algorithm, plaintext_a, plaintext_b, ad=DEFAULT_AD) -> dict:
    key, nonce = _new_key_nonce(algorithm)
    ct_a, _ = seal(algorithm, key, nonce, ad, plaintext_a)
    ct_b, _ = seal(algorithm, key, nonce, ad, plaintext_b)
    compared = min(len(ct_a), len(ct_b))
    ct_xor = _xor(ct_a[:compared], ct_b[:compared])
    pt_xor = _xor(plaintext_a[:compared], plaintext_b[:compared])
    leaked = 0
    while leaked < compared and ct_xor[leaked] == pt_xor[leaked]:
        leaked += 1
    recovered = _xor(ct_xor[:leaked], plaintext_a[:leaked])
    return {
        "algorithm": algorithm,
        "compared_bytes": compared,
        "leaked_bytes": leaked,
        "leak_fraction": leaked / compared if compared else 0.0,
        "ciphertext_xor_hex": ct_xor[:32].hex(),
        "recovered_matches_b": recovered == plaintext_b[:leaked],
        "recovered_preview": recovered.decode("utf-8", errors="replace")[:80],
    }


def _png_bytes(image: Image.Image) -> bytes:
    buffer = io.BytesIO()
    image.save(buffer, "PNG")
    return buffer.getvalue()


def image_encryption_demo(algorithm, image_path, ad=DEFAULT_AD) -> dict:
    with Image.open(image_path) as source:
        image = source.convert("RGB")
    image.thumbnail((THUMB_MAX, THUMB_MAX))
    width, height = image.size
    key, nonce = _new_key_nonce(algorithm)
    ciphertext, _ = seal(algorithm, key, nonce, ad, image.tobytes())
    noise = Image.frombytes("RGB", (width, height), ciphertext[: width * height * 3])
    return {
        "width": width,
        "height": height,
        "original_png": _png_bytes(image),
        "cipher_png": _png_bytes(noise),
        "ciphertext_sha256": sha256_hex(ciphertext),
    }
