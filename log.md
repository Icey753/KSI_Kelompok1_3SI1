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

=======================================================
     Mulai Pipeline Cipher Benchmark AES-GCM vs Ascon  
=======================================================
Dataset terdeteksi lengkap. Melanjutkan ke benchmark...

Menjalankan benchmark dengan 50 iterasi dan 5 warm-up runs...

Benchmarking JSON (small): small.json
  AES-GCM    - Enc: 0.134 ms, Dec: 0.152 ms, Tamper Test: PASSED
Traceback (most recent call last):
  File "C:\Semester 6\KSI\Pertemuan 14\KSI_Kelompok1_3SI1\main.py", line 122, in <module>
    main()
    ~~~~^^
  File "C:\Semester 6\KSI\Pertemuan 14\KSI_Kelompok1_3SI1\main.py", line 85, in main
    file_results = run_single_file_benchmark(file_path, file_type, size_cat, warm_ups=warm, iterations=iters)
  File "C:\Semester 6\KSI\Pertemuan 14\KSI_Kelompok1_3SI1\src\benchmark.py", line 320, in run_single_file_benchmark
    benchmark_rows, _ = _run_plaintext_benchmark(
                        ~~~~~~~~~~~~~~~~~~~~~~~~^
        plaintext=plaintext,
        ^^^^^^^^^^^^^^^^^^^^
    ...<4 lines>...
        iterations=iterations,
        ^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "C:\Semester 6\KSI\Pertemuan 14\KSI_Kelompok1_3SI1\src\benchmark.py", line 278, in _run_plaintext_benchmark
    ascon_row, ascon_artifact = _run_algorithm_benchmark(
                                ~~~~~~~~~~~~~~~~~~~~~~~~^
        algorithm="Ascon-128",
        ^^^^^^^^^^^^^^^^^^^^^^
    ...<7 lines>...
        artifact_dir=artifact_path,
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "C:\Semester 6\KSI\Pertemuan 14\KSI_Kelompok1_3SI1\src\benchmark.py", line 157, in _run_algorithm_benchmark
    _ = ascon_128_decrypt(key, nonce, AD, ciphertext_with_tag)
  File "C:\Semester 6\KSI\Pertemuan 14\KSI_Kelompok1_3SI1\src\cipher_ascon.py", line 138, in ascon_128_decrypt
    result = _ASCON_C.crypto_aead_decrypt(
        ctypes.cast(output, ctypes.POINTER(ctypes.c_ubyte)),
    ...<7 lines>...
        _as_ubyte_ptr(key),
    )
OSError: [WinError -1073741795] Windows Error 0xc000001d