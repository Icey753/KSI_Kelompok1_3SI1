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

Project ini sudah membawa DLL Ascon di `native/ascon/bin/`, sehingga anggota tim cukup clone lalu run tanpa build manual.

Untuk melakukan rebuild dari source, kode Ascon C tersedia di `native/ascon/ascon-c/`.

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
- mengunduh ciphertext dan metadata hasil enkripsi
- menyimpan hasil benchmark upload ke CSV baru di `output/results/`

## Output

- `output/results/benchmark_results.csv`
- `output/charts/latency_comparison.png`
- CSV baru hasil upload dashboard di `output/results/`
- ciphertext dan metadata artefak upload di `output/uploads/`

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
