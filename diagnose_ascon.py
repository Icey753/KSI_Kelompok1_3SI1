"""Standalone diagnostic for the Ascon native-DLL load path.

Run: python diagnose_ascon.py
"""
import ctypes
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
NATIVE_BIN_DIR = BASE_DIR / "native" / "ascon" / "bin"
DLL_PATH = NATIVE_BIN_DIR / "libcrypto_aead_asconaead128_ref.dll"

print("python:", sys.executable)
print("python version:", sys.version)
print("dll path:", DLL_PATH)
print("dll exists:", DLL_PATH.exists())

try:
    lib = ctypes.CDLL(str(DLL_PATH))
    print("CDLL: ok")
    lib.crypto_aead_encrypt.argtypes = [ctypes.POINTER(ctypes.c_ubyte)] * 9
    lib.crypto_aead_decrypt.argtypes = [ctypes.POINTER(ctypes.c_ubyte)] * 8
    print("argtypes: ok")
except Exception as exc:
    print("FAILED:", type(exc).__name__, exc)
    sys.exit(1)

print()
print("--- now importing via src.cipher_ascon (same path the app uses) ---")
sys.path.insert(0, str(BASE_DIR))
from src.cipher_ascon import BACKEND, _ASCON_C, NATIVE_BIN_DIR as MODULE_NATIVE_BIN_DIR

print("module NATIVE_BIN_DIR:", MODULE_NATIVE_BIN_DIR)
print("module _ASCON_C:", _ASCON_C)
print("module BACKEND:", BACKEND)
