# Cipher Benchmark

Pipeline benchmarking berbasis Python untuk membandingkan performa **AES-GCM** dan **Ascon-128** pada beberapa ukuran file JSON dan gambar PNG.

## Tujuan

- Mengukur latensi enkripsi dan dekripsi
- Mengukur overhead ukuran ciphertext
- Memverifikasi integritas ciphertext lewat tampering test
- Menyimpan hasil benchmark ke CSV
- Menampilkan grafik statis dan dashboard interaktif

## Teknologi

- Python 3.10+
- `pycryptodome`
- `ascon`
- `faker`
- `pillow`
- `numpy`
- `pandas`
- `matplotlib`
- `plotly`
- `dash`

## Struktur Proyek

```text
.
├── data/
│   ├── json/
│   └── images/
├── output/
│   ├── results/
│   └── charts/
├── src/
│   ├── data_prep.py
│   ├── cipher_aes.py
│   ├── cipher_ascon.py
│   ├── benchmark.py
│   ├── report.py
│   └── visualize.py
├── main.py
├── dashboard.py
├── requirements.txt
└── perencanaan_cipher_benchmark.md
```

## Arsitektur

Pipeline dibagi menjadi 5 fase:

1. **Data Preparation**
   - Membuat dataset JSON dan gambar PNG dengan ukuran kecil, sedang, dan besar.
2. **Input**
   - Membaca file plaintext dari folder `data/`.
3. **Cipher**
   - Menjalankan AES-GCM dan Ascon-128 pada file yang sama.
4. **Report**
   - Menghitung rata-rata latensi, deviasi standar, overhead ukuran, dan hasil tampering test.
5. **Visualizer**
   - Membuat grafik statis dan dashboard interaktif.

## Alur Proses

1. `main.py` mengecek apakah dataset sudah tersedia.
2. Jika dataset belum lengkap, `src/data_prep.py` akan membuat:
   - `data/json/small.json`
   - `data/json/medium.json`
   - `data/json/large.json`
   - `data/images/small.png`
   - `data/images/medium.png`
   - `data/images/large.png`
3. `src/benchmark.py` membaca setiap file dan menjalankan:
   - warm-up run
   - loop pengukuran
   - verifikasi hasil decrypt
   - tampering test
4. `src/report.py` menyimpan hasil ke `output/results/benchmark_results.csv`.
5. `src/visualize.py` membuat grafik latensi ke `output/charts/latency_comparison.png`.
6. `dashboard.py` menampilkan dashboard interaktif melalui Dash.
   - Jika CSV belum ada, dashboard tetap bisa dibuka untuk upload file langsung.

## Build

### 1. Buat virtual environment

```bash
python -m venv .venv
```

### 2. Aktifkan environment

PowerShell:

```bash
.venv\Scripts\Activate.ps1
```

### 3. Install dependency

```bash
pip install -r requirements.txt
```

### 4. Backend Ascon C

Project ini sudah membawa DLL Ascon di `native/ascon/bin/`, sehingga clone lalu run sudah cukup tanpa build manual.

Untuk melakukan rebuild dari source, kode Ascon C tersedia di `https://github.com/ascon/ascon-c` yang menggunakan bahasa C lalu build menggunakan ctypes dan cmake.

DLL akan terbaca otomatis oleh `src/cipher_ascon.py` dari urutan berikut:

1. `native/ascon/bin/`
2. `native/ascon/ascon-c/build/`
3. fallback ke backend Python `ascon`

## Menjalankan Pipeline

Jalankan pipeline utama:

```bash
python main.py
```

Pipeline ini akan:

- memastikan dataset tersedia
- menjalankan benchmark semua ukuran file
- menyimpan CSV hasil benchmark
- membuat grafik statis

## Menjalankan Dashboard

Setelah `main.py` selesai, jalankan:

```bash
python dashboard.py
```

Lalu buka:

```text
http://127.0.0.1:8050/
```

Dashboard ini mendukung:

- upload file JSON atau gambar langsung dari browser
- menjalankan benchmark AES-GCM dan Ascon-128 pada file upload
- melihat preview file, ringkasan hasil, dan grafik perbandingan
- mengunduh ciphertext Base64 dan metadata hasil enkripsi
- menyimpan hasil benchmark upload ke CSV baru di `output/results/`
- Demo Interaktif: uji tamper (balik 1 bit pada ciphertext/tag/nonce/AD), enkripsi lalu dekripsi balik dengan hash SHA-256, demo bahaya nonce dipakai ulang, dan gambar asli vs ciphertext
- Analisis Ukuran Data dan Lingkungan: grafik size sweep dengan titik potong latensi Ascon vs AES-GCM, panel info lingkungan, tombol jalankan sweep, dan unduh CSV

Grafik sweep dan panel lingkungan dimuat saat server dashboard dijalankan, jadi restart server dashboard untuk melihat file terbaru setelah menjalankan `python -m src.sweep`.

## Output

- `output/results/benchmark_results.csv`
- `output/charts/latency_comparison.png`
- CSV baru hasil upload dashboard di `output/results/`
- ciphertext Base64 dan metadata artefak upload di `output/uploads/`

## Format Hasil Benchmark

Setiap baris CSV berisi:

- `Algorithm`
- `InputFileName`
- `FileType`
- `SizeCategory`
- `PlaintextSizeBytes`
- `CiphertextSizeBytes`
- `EncLatencyMeanMs`
- `EncLatencyStdMs`
- `DecLatencyMeanMs`
- `DecLatencyStdMs`
- `OverheadBytes`
- `OverheadPct`
- `TamperingIntegrityPassed`

## Catatan Performa

- AES-GCM biasanya jauh lebih cepat karena dukungan akselerasi hardware pada banyak CPU modern.
- Ascon-128 pada implementasi pure Python dapat sangat lambat untuk file besar.
- Untuk menguji satu skenario saja tanpa menjalankan pipeline penuh, gunakan modul `src/benchmark.py` secara langsung.

## Kolaborasi

Yang sebaiknya di-commit ke repo ini:

- kode Python di `src/`
- `main.py`, `dashboard.py`, `README.md`, dan `requirements.txt`
- dokumentasi dan konfigurasi build yang dipakai bersama

## Pengujian Manual

Untuk mencoba benchmark satu file secara langsung:

```bash
python -c "from src.benchmark import run_single_file_benchmark; print(run_single_file_benchmark('data/json/small.json', 'json', 'small', warm_ups=3, iterations=10))"
```

## Rencana Benchmark

Rencana pengujian mengikuti ukuran file berikut:

- JSON kecil, sedang, besar
- Gambar kecil, sedang, besar

Jumlah iterasi pada implementasi saat ini disesuaikan agar pipeline tetap realistis untuk dijalankan di satu mesin.

## Pengujian dan Validasi

```
python -m pytest -v
```

Tes mencakup test vector resmi AES-GCM (NIST) dan Ascon-AEAD128 (1089 vektor dari `native/ascon/ascon-c`).

**Catatan varian Ascon:** backend C yang dimuat (`libcrypto_aead_asconaead128_ref.dll`) mengimplementasikan Ascon-AEAD128 dari NIST SP 800-232. Library Python `ascon` dengan `variant="Ascon-128"` adalah Ascon-128 v1.2 (varian berbeda, tidak kompatibel). Kolom `Backend` di CSV dan `output/results/environment.json` mencatat backend yang dipakai.

## Size sweep

`python -m src.sweep` mengukur ukuran 1 KB sampai 10 MB (JSON dan biner) dan mencetak titik potong latensi Ascon vs AES-GCM. Hasil: `output/results/size_sweep*.csv` dan `output/charts/size_sweep.png`.

## Batasan Pengukuran

- **Salinan output pada pembungkus Ascon.** Pembungkus Ascon (ctypes) masih menyalin output (alokasi buffer + `output.raw`), sedangkan AES-GCM (pycryptodome) tidak. Perkiraan porsi overhead ini terhadap latensi enkripsi Ascon (median, 200 pengulangan): sekitar 2,5% pada 16 KB, 14,6% pada 1 MB, dan 12,9% pada 10 MB. Salinan input sudah dihilangkan (zero-copy); sebelumnya salinan itu menambah sekitar 2,6% (16 KB), 6,9% (1 MB), dan 5,6% (10 MB). Angka ini pengukuran satu mesin, bukan konstanta.
- **Urutan pengujian tetap.** Untuk setiap file, AES-GCM dijalankan sebelum Ascon (tanpa interleaving), sehingga drift frekuensi CPU bisa memengaruhi selisih kecil di sekitar titik potong.
- **`aesni_speedup`** hanya mengukur efek AES-NI pada block cipher (`use_aesni=False`). GHASH/CLMUL dipilih terpisah oleh pycryptodome, jadi angka ini meremehkan efek akselerasi hardware penuh.
- **`EncLatencyCI95Ms` / `DecLatencyCI95Ms`** adalah setengah-lebar CI 95% pendekatan normal untuk RATA-RATA (bukan median), dengan asumsi n >= 30.
- **Test vector Ascon (1089 vektor)** dibaca dari `native/ascon/ascon-c/crypto_aead/asconaead128/LWC_AEAD_KAT_128_128.txt`. Di git hanya DLL `native/ascon/bin/libcrypto_aead_asconaead128_ref.dll` (dan `native/ascon/README.md`) yang tercatat; folder sumber `native/ascon/ascon-c` (termasuk file KAT) belum ada di git. Jika file KAT tidak ada, dua tes KAT Ascon di-SKIP (bukan gagal). Untuk mengaktifkannya, letakkan sumber ascon-c di `native/ascon/ascon-c`.

## Skenario Realistis

`python -m src.scenarios` menjalankan tiga skenario dan menyimpan `output/results/small_messages.csv`, `chunked.csv`, dan `acceleration.csv`:

- **Pesan kecil (gaya API):** 64 B sampai 4 KB, nonce baru per pesan, dilaporkan sebagai pesan/detik dan latensi median/P95.
- **Chunked:** file 8 MB dienkripsi per chunk (4 KB, 64 KB, 1 MB, utuh). Tiap chunk membawa tag 16 byte dan AD berisi indeks chunk, sehingga penukaran urutan atau pemotongan aliran terdeteksi.
- **Akselerasi:** `AES-GCM` (dengan AES-NI), `AES-GCM-noNI` (opsi `use_aesni=False` pada pycryptodome), dan `Ascon-128`, untuk menjelaskan mengapa hasil di PC desktop berbeda dari literatur perangkat IoT.

Dashboard (`python dashboard.py`) menampilkan ketiganya di bagian "Skenario Realistis". Tombol "Jalankan skenario (cepat)" di dashboard menyimpan hasilnya ke `output/results/quick/` dan tidak menimpa hasil lengkap dari `python -m src.scenarios`.
