# Native Ascon Backend

Folder ini disiapkan untuk integrasi backend Ascon C melalui `ctypes`.

## Struktur yang diharapkan

- `src/cipher_ascon.py` tetap menjadi adapter Python
- `native/ascon/` menyimpan source C atau hasil build backend
- `native/ascon/build/` menyimpan shared library hasil kompilasi

## Shared library yang diharapkan

- Windows: `ascon.dll`
- Linux: `libascon.so`
- macOS: `libascon.dylib`

## Catatan

Wrapper Python akan tetap fallback ke backend Python jika shared library belum tersedia.
