# Native Ascon Backend

Backend Ascon C dipanggil lewat `ctypes` (`src/cipher_ascon.py`).

## Pakai (tanpa compiler)

`bin/libcrypto_aead_asconaead128_ref.dll` sudah di-commit, tapi dia dynamically linked ke
`libgcc_s_dw2-1.dll` (runtime MinGW 32-bit) yang **tidak** ikut di-commit. Kalau komputer kamu
gak punya MinGW yang persis sama di PATH, load DLL gagal dan kode otomatis fallback ke package
Python `ascon` (lihat `_load_c_backend()` di `src/cipher_ascon.py`) — ini penyebab paling umum
"ascon gak kebaca pas di-clone". Fallback ini aman (benchmark tetap jalan, cuma lebih lambat),
tapi kalau mau backend C beneran jalan, build ulang statis (lihat di bawah) biar gak butuh DLL
runtime tambahan. Linux/macOS belum ada binary, build sendiri juga.

## Build ulang

Butuh `git`, `cmake`, dan compiler C (MinGW/gcc/clang).

```bash
cd native/ascon
git clone https://github.com/ascon/ascon-c.git
cd ascon-c
git checkout 446347f21b209f3921c65ece70027c366cbe1693   # versi yang dipakai
cmake -S . -B build -G "MinGW Makefiles" -DCMAKE_C_FLAGS="-static-libgcc -static"  # Linux/macOS: tanpa -G
cmake --build build
```

`-static-libgcc -static` bikin DLL gak butuh `libgcc_s_*.dll`/`libwinpthread-1.dll` eksternal lagi,
jadi langsung jalan di komputer lain tanpa install MinGW.

Salin hasil build (`libcrypto_aead_asconaead128_ref.dll` / `.so` / `.dylib`) ke `native/ascon/bin/`.
Untuk `.so`/`.dylib`, tambahkan nama file itu ke daftar kandidat di `src/cipher_ascon.py`.

Folder `ascon-c/` di-ignore git (clone upstream, punya `.git` sendiri).
