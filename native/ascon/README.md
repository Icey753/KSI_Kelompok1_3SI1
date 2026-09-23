# Native Ascon Backend

Backend Ascon C dipanggil lewat `ctypes` (`src/cipher_ascon.py`).

## Pakai (tanpa compiler)

`bin/libcrypto_aead_asconaead128_ref.dll` sudah di-commit, siap pakai di **Windows x64**
(cuma butuh `KERNEL32.dll` + Universal CRT bawaan Windows 10/11, cek pakai `objdump -p`).

**Riwayat bug:** build sebelumnya dicompile dengan `-march=native -mtune=native` (default
`ascon-c` punya `CMakeLists.txt`), yang hard-code instruksi CPU spesifik ke mesin yang build
DLL-nya. Di CPU lain yang gak support instruksi itu, load DLL sukses tapi crash pas dipanggil
(`OSError: [WinError -1073741795] STATUS_ILLEGAL_INSTRUCTION`). DLL yang di-commit sekarang
di-build tanpa `-march=native` (lihat command di bawah), jadi portable ke semua CPU x86-64.

Kalau load tetap gagal total (bukan crash, tapi `_ASCON_C` jadi `None`), kode otomatis fallback
ke package Python `ascon` (lihat `_load_c_backend()` di `src/cipher_ascon.py`) — lebih lambat
tapi tetap benar. Linux/macOS belum ada binary, build sendiri di bawah.

## Build ulang

Butuh `git`, `cmake`, dan compiler C (MinGW/gcc/clang).

```bash
cd native/ascon
git clone https://github.com/ascon/ascon-c.git
cd ascon-c
git checkout 446347f21b209f3921c65ece70027c366cbe1693   # versi yang dipakai
cmake -S . -B build -G "MinGW Makefiles" \
  -DBUILD_SHARED_LIBS=ON \
  -DREL_FLAGS="-std=c99;-O2;-fomit-frame-pointer"        # Linux/macOS: tanpa -G
cmake --build build --target crypto_aead_asconaead128_ref
```

`-DBUILD_SHARED_LIBS=ON` wajib biar hasilnya `.dll`/`.so` (default-nya static `.a`).
`REL_FLAGS` di-override tanpa `-march=native -mtune=native` (default upstream) biar DLL-nya
portable ke CPU manapun, bukan cuma CPU yang build.

Salin hasil build (`libcrypto_aead_asconaead128_ref.dll` / `.so` / `.dylib`) ke `native/ascon/bin/`.
Untuk `.so`/`.dylib`, tambahkan nama file itu ke daftar kandidat di `src/cipher_ascon.py`.

Folder `ascon-c/` di-ignore git (clone upstream, punya `.git` sendiri).
