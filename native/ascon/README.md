# Native Ascon Backend

Backend Ascon C dipanggil lewat `ctypes` (`src/cipher_ascon.py`).

## Pakai (tanpa compiler)

`bin/libcrypto_aead_asconaead128_ref.dll` sudah di-commit, siap pakai di **Windows x64**.
Linux/macOS belum ada binary, build sendiri (lihat di bawah).

## Build ulang

Butuh `git`, `cmake`, dan compiler C (MinGW/gcc/clang).

```bash
cd native/ascon
git clone https://github.com/ascon/ascon-c.git
cd ascon-c
git checkout 446347f21b209f3921c65ece70027c366cbe1693   # versi yang dipakai
cmake -S . -B build -G "MinGW Makefiles"                # Linux/macOS: tanpa -G
cmake --build build
```

Salin hasil build (`libcrypto_aead_asconaead128_ref.dll` / `.so` / `.dylib`) ke `native/ascon/bin/`.
Untuk `.so`/`.dylib`, tambahkan nama file itu ke daftar kandidat di `src/cipher_ascon.py`.

Folder `ascon-c/` di-ignore git (clone upstream, punya `.git` sendiri).
