[Running] python -u "c:\Semester 6\KSI\Pertemuan 14\KSI_Kelompok1_3SI1\diagnose_ascon.py"
python: C:\Users\Galang\AppData\Local\Python\pythoncore-3.14-64\python.exe
python version: 3.14.3 (tags/v3.14.3:323c59a, Feb  3 2026, 16:04:56) [MSC v.1944 64 bit (AMD64)]
dll path: C:\Semester 6\KSI\Pertemuan 14\KSI_Kelompok1_3SI1\native\ascon\bin\libcrypto_aead_asconaead128_ref.dll
dll exists: True
CDLL: ok
argtypes: ok

--- now importing via src.cipher_ascon (same path the app uses) ---
module NATIVE_BIN_DIR: C:\Semester 6\KSI\Pertemuan 14\KSI_Kelompok1_3SI1\native\ascon\bin
module _ASCON_C: None
module BACKEND: Python (ascon lib)

[Done] exited with code=0 in 0.483 seconds

---

Fix: set ASCON_BACKEND=c sebelum run biar backend C dipake (default-nya "python").

CMD (Command Prompt):
set ASCON_BACKEND=c
python diagnose_ascon.py

PowerShell:
$env:ASCON_BACKEND="c"
python diagnose_ascon.py
