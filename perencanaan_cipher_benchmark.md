# Perencanaan Pembangunan Aplikasi Cipher Benchmark
### AES-GCM vs Ascon-128 — Kelompok 1, 3SI1 | Keamanan Sistem Informasi

---

## 1. Gambaran Umum

Aplikasi ini merupakan pipeline benchmarking berbasis Python untuk membandingkan performa enkripsi/dekripsi dua algoritma AEAD:
- **AES-GCM** — standar industri berbasis block cipher (pycryptodome)
- **Ascon-128** — standar lightweight cryptography NIST SP 800-232 (library ascon)

**Metrik yang diukur:**
- Latensi eksekusi enkripsi & dekripsi (ms)
- Overhead ukuran file ciphertext vs plaintext (bytes & %)

**Tipe data yang diuji:**
- File **JSON** (data transaksi sintetis, skala mikro)
- File **gambar PNG/JPG** (data multimedia, skala makro)

---

## 2. Arsitektur Pipeline (5 Fase)

```
[Data Preparation] → [Input] → [Cipher] → [Report] → [Visualizer]
   Faker/Pillow       os/Path   AES-GCM    time +      matplotlib
                                Ascon-128   numpy       + Plotly Dash
```

### Fase 1 — Data Preparation *(opsional)*
- JSON dummy: library `Faker` → data transaksi (nama, ID, nominal)
- Gambar: library `Pillow` → PNG/JPG programatik ukuran 1–10 MB
- Jika dataset nyata tersedia, fase ini dilewati

### Fase 2 — Input
- Baca file JSON: `open()` + `json.load()`
- Baca file gambar: binary mode `rb`
- Tool: `os`, `pathlib`

### Fase 3 — Cipher *(inti)*

| | AES-GCM | Ascon-128 |
|---|---|---|
| Library | `pycryptodome` | `ascon` |
| Enkripsi | `AES.new(key, MODE_GCM, nonce).encrypt_and_digest()` | `ascon.encrypt(key, nonce, ad, plaintext)` |
| Dekripsi | `decrypt_and_verify()` | `ascon.decrypt()` |
| Auth Tag | 16 bytes (konstan) | 16 bytes (konstan) |
| Padding | Diperlukan (block cipher) | Tidak diperlukan (stream/sponge) |

Setiap variasi ukuran file diulang **50 kali** + **5 warm-up run** sebelum pencatatan.

### Fase 4 — Report
- Latensi: `time.perf_counter()` sebelum & sesudah cipher
- Size overhead: `os.path.getsize(ciphertext) - os.path.getsize(plaintext)`
- Agregasi 50 replikasi → `numpy.mean()`
- Output: CSV/Excel via `pandas`

### Fase 5 — Visualizer
- Grafik statis: `matplotlib` → PNG untuk laporan
- Dashboard interaktif: `Plotly Dash` → eksplorasi & presentasi

---

## 3. Struktur Direktori Proyek

```
cipher_benchmark/
├── data/
│   ├── json/              # Dataset JSON (small/medium/large)
│   └── images/            # Dataset gambar (PNG/JPG)
├── output/
│   ├── results/           # CSV hasil benchmarking
│   └── charts/            # PNG grafik matplotlib
├── src/
│   ├── data_prep.py       # Faker + Pillow → generate dataset
│   ├── cipher_aes.py      # Implementasi AES-GCM
│   ├── cipher_ascon.py    # Implementasi Ascon-128
│   ├── benchmark.py       # Runner utama (loop 50x, warm-up, timing)
│   ├── report.py          # Kalkulasi overhead, agregasi numpy
│   └── visualize.py       # Matplotlib + Plotly Dash
├── dashboard.py           # Entry point Dash app
├── main.py                # Entry point pipeline utama
└── requirements.txt
```

---

## 4. Skenario Pengujian

### Variasi Ukuran File

| Tipe | Ukuran Kecil | Ukuran Sedang | Ukuran Besar |
|---|---|---|---|
| JSON | ~1 KB | ~100 KB | ~1 MB |
| Gambar | ~100 KB | ~1 MB | ~10 MB |

### Prosedur per Skenario
1. **Warm-up**: 5 eksekusi awal (buang hasilnya)
2. **Loop**: 50 iterasi pencatatan latensi
3. **Agregasi**: hitung mean dari 50 iterasi
4. **Overhead**: hitung delta bytes & persentase

### Uji Integritas (Tampering Test)
- Modifikasi 1 byte pada ciphertext
- Verifikasi bahwa `decrypt_and_verify()` / `ascon.decrypt()` memicu exception
- Konfirmasi Authentication Tag bekerja benar

---

## 5. Dependencies

```txt
# requirements.txt
pycryptodome>=3.20.0
ascon>=1.0.0
faker>=24.0.0
pillow>=10.0.0
numpy>=1.26.0
pandas>=2.2.0
matplotlib>=3.8.0
plotly>=5.20.0
dash>=2.16.0
```

---

## 6. Alur Eksekusi `main.py`

```python
# Pseudocode alur utama
1. parse_args()                          # ukuran file, jumlah replikasi
2. prepare_dataset()                     # Fase 1 (jika belum ada)
3. for file_type in [JSON, IMAGE]:
     for size in SIZE_VARIANTS:
       warmup(cipher_func, n=5)
       results = []
       for i in range(50):
         t_start = time.perf_counter()
         ciphertext, tag = cipher_func(plaintext)
         t_end = time.perf_counter()
         results.append(t_end - t_start)
       log_result(mean(results), overhead(ciphertext, plaintext))
4. export_csv(results)                   # Fase 4
5. generate_charts()                     # Fase 5 static
6. launch_dashboard()                    # Fase 5 interactive
```

---

## 7. Output yang Dihasilkan

| Output | Format | Keterangan |
|---|---|---|
| Tabel hasil benchmarking | CSV / Excel | Mean latensi + overhead per variasi |
| Grafik bar latensi | PNG | Perbandingan ms AES-GCM vs Ascon-128 |
| Grafik line overhead ratio | PNG | % pembengkakan vs ukuran file |
| Dashboard interaktif | Plotly Dash (localhost) | Filter by tipe file, ukuran, algoritma |

---

## 8. Pembagian Implementasi Anggota

| Anggota | Peran | Modul |
|---|---|---|
| Galang | Project Manager | Koordinasi + dokumentasi BAB I |
| Ilham (gw) | Crypto Dev AES-GCM | `cipher_aes.py`, `benchmark.py` (Fase 1–2) |
| Irish | Crypto Dev Ascon-128 | `cipher_ascon.py`, skenario pengujian |
| Miftahul | Data & Tester | `data_prep.py`, uji integritas tampering |
| Sancha | Data Analyst | `report.py`, `visualize.py` (matplotlib) |
| Yulia | Tech Writer | Dokumentasi tools + penelitian terkait |

---

## 9. Catatan Teknis Penting

- **Benchmark single-machine** — tidak lintas platform, tidak distributed
- **AES-NI**: AES-GCM kemungkinan lebih cepat di desktop karena akselerasi hardware (instruksi AES-NI di x86)
- **Ascon overhead**: murni +16 bytes (Auth Tag), tanpa padding karena stream-based
- **AES overhead**: +16 bytes Auth Tag. Karena block cipher 128-bit, ada kemungkinan padding tergantung implementasi mode
- **Hipotesis awal**: Ascon lebih unggul di file kecil (JSON), AES-GCM lebih kompetitif di file besar berkat hardware acceleration
- Gunakan `time.perf_counter()`, **bukan** `time.time()` — resolusi lebih tinggi
- Seed acak untuk Faker/Pillow sebaiknya dikunci agar dataset reproducible
