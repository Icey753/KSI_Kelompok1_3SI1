# Rencana PPT untuk Canva: Analisis Komparatif AES-GCM vs Ascon

Presentasi 20 menit: 1 slide judul (0:15) dan 19 slide isi (19:45). Dokumen ini hanya berisi isi dan layout, disusun agar bisa dibuat langsung di Canva. Angka diambil dari `output/results/*.csv`.

## Pengaturan Canva

- **Ukuran halaman:** Presentation 16:9, 1920 × 1080 px.
- **Brand Kit** (buat sekali, pakai di semua halaman):
  - Font: Inter (tersedia di Canva). Judul 56 px tebal, subjudul 40 px, isi 32 px (minimal 28 px), angka besar 120–160 px, keterangan 24 px, footer 20 px.
  - Warna:

    | Peran | Hex | Sumber |
    |---|---|---|
    | Latar | `#ffffff` | |
    | Teks utama | `#0f172a` | `bg` dashboard |
    | Teks lembut | `#475569` | |
    | Garis dan kartu | `#e2e8f0` | |
    | AES-GCM | `#3b82f6` | `aes_strong` |
    | Ascon | `#db2777` | `ascon_strong` |
    | AES-GCM tanpa AES-NI | `#fbbf24` | `warn` (hanya untuk isian batang, bukan teks) |

  - Latar terang dipilih karena grafik hasil benchmark berlatar abu terang dan berwarna biru (AES) dan merah muda (Ascon). Screenshot dashboard yang gelap dibingkai kartu di slide 16.
- **Margin:** 96 px di semua sisi (Rulers & guides). Judul di atas kiri, area isi dari y = 260 sampai 984, footer di y = 1030 berisi nomor slide dan nama bagian.
- **Catatan pembicara:** isi kolom Notes tiap slide dengan durasi dan poin yang dilisankan. Slide hanya memuat inti.
- **Transisi:** satu jenis sederhana (Dissolve) atau tanpa transisi. Tanpa animasi elemen.

## Lima Layout Dasar

Buat kelima layout ini di halaman kosong, lalu duplikat sesuai tabel pemetaan di bawah.

| Kode | Nama | Susunan (px, kanvas 1920 × 1080) |
|---|---|---|
| A | Dua kolom | Kolom kiri x 96–900, kolom kanan x 1020–1824. Isi teks di kiri, visual di kanan, atau dua teks sejajar. |
| B | Tiga kartu | Tiga kartu lebar 544 px, jarak 48 px (x = 96, 688, 1280), tinggi 724 px (y 260–984). Ikon atau angka di atas, teks di bawah. |
| C | Visual besar dan panel | Visual x 96–1200, panel samping x 1248–1824. Panel berisi angka sorotan atau tabel ringkas. |
| D | Tabel dan catatan | Tabel selebar penuh (x 96–1824, y 260–800), kotak catatan di bawah (y 840–984). |
| E | Kartu 2×2 | Empat kartu 840 × 338 px, jarak 48 px. Ikon kiri atas, judul kartu, satu kalimat. |

Kartu memakai isian `#f1f5f9` dengan sudut membulat dan garis `#e2e8f0`, tanpa bayangan.

## Pemetaan Slide ke Layout

| Slide | Layout | Slide | Layout |
|---|---|---|---|
| Judul | Khusus | 11 | E |
| 1 | A | 12 | B |
| 2 | B | 13 | C |
| 3 | A | 14 | C |
| 4 | A | 15 | B (empat kartu) |
| 5 | D | 16 | C |
| 6 | C | 17 | C (visual penuh) |
| 7 | A | 18 | A |
| 8 | C | 19 | B |
| 9 | D | | |
| 10 | A | | |

Semua grafik angka (slide 13, 14, 16) dibuat sebagai chart bawaan Canva, bukan gambar, supaya anggota lain bisa mengedit datanya dan warnanya mengikuti Brand Kit.

---

## Slide Judul (0:15)

- **Layout:** khusus. Teks rata kiri di x 96–1200, sisi kanan berisi satu bentuk dekoratif atau ikon gembok.
- **Isi:**
  - Judul (56 px tebal): Analisis Komparatif Performa AES-GCM dan Ascon-128 terhadap Overhead Ukuran File dan Latensi Eksekusi pada JSON dan Gambar
  - Mata kuliah Keamanan Sistem Informasi
  - Nama enam anggota (dua kolom, 28 px), dosen pengampu Farid Ridho, S.S.T., M.T.
  - Politeknik Statistika STIS, 2025/2026

---

## Bagian 1: Pendahuluan (2:30)

### 1. Latar belakang (1:00) · Layout A

- **Judul:** Data terus bertukar, dan Ascon adalah kandidat pengganti AES-GCM
- **Kiri:** tiga poin.
  - JSON (API) dan gambar butuh enkripsi terautentikasi (AEAD)
  - AES-GCM: standar server dan TLS. Ascon: keluarga ringan untuk IoT, standar NIST 2025
  - Kami menguji AES-128-GCM vs Ascon-AEAD128 (sama-sama kunci 128-bit, tag 16 B) di PC dengan AES-NI
- **Kanan:** garis waktu vertikal dari garis dan enam lingkaran (jarak sekitar 110 px, teks 24 px).
  - 2001: AES (FIPS 197)
  - 2007: mode GCM (SP 800-38D)
  - 2018: TLS 1.3 memakai AES-GCM (RFC 8446)
  - 2019: Ascon menang CAESAR kategori ringan
  - 2023: NIST memilih Ascon sebagai standar lightweight
  - 2025: SP 800-232 (Ascon-AEAD128)
- **Catatan:** tanggal ditulis dari ingatan, cek ke dokumen NIST sebelum slide difinalkan. Di catatan pembicara, sebut bahwa AES di IoT umumnya lewat mode CCM (BLE, Zigbee), dan ChaCha20-Poly1305 adalah alternatif untuk perangkat tanpa AES-NI (tidak diuji).

### 2. Rumusan masalah dan tujuan (1:00) · Layout B

- **Judul:** Tiga pertanyaan yang ingin dijawab
- **Kartu 1, Latensi:** ikon jam. Bagaimana perbandingan waktu enkripsi dan dekripsi?
- **Kartu 2, Overhead:** ikon ukuran file. Bagaimana pengaruh authentication tag terhadap pembengkakan ukuran?
- **Kartu 3, Rekomendasi:** ikon centang. Pada tipe data dan ukuran apa tiap algoritma lebih baik?

### 3. Ruang lingkup dan batasan (0:30) · Layout A

- **Judul:** Cakupan sengaja dibatasi
- **Kiri, "Diuji":** JSON dan PNG, tiga ukuran tiap tipe, latensi dan overhead, satu mesin, Python.
- **Kanan, "Tidak diuji":** side-channel, brute-force, kriptanalisis, lintas platform.
- Kedua kolom berjudul kecil berwarna: hijau untuk "Diuji", abu untuk "Tidak diuji".

---

## Bagian 2: Landasan (4:00)

### 4. CIA Triad dan AEAD (1:00) · Layout A

- **Judul:** AEAD menjaga kerahasiaan dan integritas sekaligus
- **Kiri:** tiga poin.
  - Confidentiality: plaintext menjadi ciphertext
  - Integrity: authentication tag mendeteksi perubahan
  - Availability: efisiensi komputasi
- **Kanan:** diagram dari bentuk dan panah Canva. Empat kotak masukan (key, nonce, associated data, plaintext) menuju satu kotak "AEAD", lalu dua kotak keluaran (ciphertext, tag).

### 5. AES-GCM vs Ascon-AEAD128 (1:15) · Layout D

- **Judul:** Dua desain berbeda dengan ukuran parameter serupa
- **Tabel (elemen Table Canva, tiga kolom).** Header kolom AES-GCM berisian `#3b82f6`, kolom Ascon berisian `#db2777`, teks putih.

  | | AES-GCM | Ascon-AEAD128 |
  |---|---|---|
  | Keluarga | AES-128/192/256, mode GCM dan CCM | Ascon-AEAD128, Ascon-Hash256, Ascon-XOF128 |
  | Desain | Block cipher, CTR + GHASH | Sponge, state 320-bit |
  | Kunci | 16 B | 16 B |
  | Nonce | 12 B | 16 B |
  | Tag | 16 B | 16 B |
  | Akselerasi hardware | AES-NI, CLMUL | Tidak ada |

- **Catatan (kotak di bawah tabel):** yang diuji hanya AES-128-GCM dan Ascon-AEAD128 (SP 800-232). Ascon-128 dan Ascon-128a v1.2 adalah versi lama dan tidak kompatibel. Fungsi hash dan XOF Ascon tidak diuji.

### 6. Bagaimana kedua algoritma bekerja secara internal (1:00) · Layout C

- **Judul:** Dua arsitektur berbeda: block cipher CTR+GHASH vs sponge/duplex
- **Visual:** ekspor PNG dari `assets/diagrams/aes-gcm-internals.html` dan `assets/diagrams/ascon128-internals.html` (tombol Export → Share Card di viewer archify), tempel berdampingan atau bertumpuk di area visual.
- **Panel:** dua blok poin.
  - AES-GCM: counter block dienkripsi AES jadi keystream, di-XOR ke plaintext jadi ciphertext. GHASH menggabungkan AD, ciphertext, dan length block lewat perkalian Galois untuk menghasilkan tag.
  - Ascon-128: satu state 320-bit dipermutasi terus menerus (sponge/duplex). Plaintext langsung di-XOR ke bagian rate menjadi ciphertext (tanpa keystream terpisah). Tag diambil dari state akhir setelah key di-XOR ulang dan permutasi terakhir.
- **Catatan:** diagram ini detail teknis tambahan di luar yang tertulis di proposal (proposal hanya sebut satu baris per algoritma di tabel slide 5); dibuat memakai skill Archify untuk memvisualisasikan mekanisme CTR+GHASH dan sponge construction secara eksplorasi.

### 7. Penelitian terkait dan posisi kita (0:45) · Layout A

- **Judul:** Literatur menguji perangkat IoT, kita menguji PC dengan AES-NI
- **Kiri:** empat baris ringkas (peneliti, tahun, temuan).
  - NIST IR 8454 (2023): Ascon dipilih sebagai standar
  - FELICS-AEAD (2019): Ascon kompetitif di perangkat terbatas
  - Mohajerani (2023): throughput dan efisiensi tinggi
  - Harvey (2025): Ascon sekitar 4–6× lebih cepat di Arduino
- **Kanan:** satu kartu sorotan berisian `#f1f5f9`, judul "Posisi penelitian kami": PC desktop dengan AES-NI, file JSON dan gambar.

---

## Bagian 3: Metodologi dan Sistem (5:00)

### 8. Arsitektur pipeline (1:15) · Layout C

- **Judul:** Satu perintah menjalankan seluruh pipeline
- **Visual:** unggah `assets/codeflow.png`, letakkan di area visual. Bila terlalu kecil, pangkas bagian yang penting. Alternatif: `output/aead-benchmark-flow.png`, diagram sequence baru (Dashboard → Benchmark Runner → AEAD Wrapper → cipher → tag verify) yang lebih rinci soal alur pemanggilan.
- **Panel:** tiga label lapisan bertumpuk.
  - Cipher: `aead.py`
  - Pengukuran: `benchmark`, `sweep`, `scenarios`
  - Penyajian: CSV, grafik, dashboard

### 9. Dataset dan prosedur uji (1:00) · Layout D

- **Judul:** Enam file, 5 warm-up, 50 iterasi
- **Tabel:** enam baris dataset.

  | Tipe | Ukuran |
  |---|---|
  | JSON | 100 KB, 1 MB, 3 MB |
  | PNG | 500 KB, 3 MB, 8 MB |

- **Catatan di bawah:** seed 42, PNG noise tanpa kompresi. 5 warm-up, 50 iterasi terukur dengan `time.perf_counter()`. Statistik: mean, median, std, CI 95%.

### 10. Implementasi cipher (1:15) · Layout A

- **Judul:** Satu antarmuka untuk dua algoritma
- **Kiri:** blok kode dari `src/aead.py` (10–12 baris, potongan `seal`). Pakai kotak teks berfont monospace di atas kartu gelap, atau tempel sebagai screenshot.
- **Kanan:** tiga poin.
  - AES-GCM: pycryptodome (AES-NI bila tersedia)
  - Ascon: backend C referensi (`ascon-c`) lewat `ctypes`, karena library Python `ascon` jauh lebih lambat
  - Verifikasi gagal mengembalikan `None`, tidak melempar exception

### 11. Skenario tambahan (1:00) · Layout E

- **Judul:** Selain enam file, kami menguji tiga skenario lain
- **Kartu 1, Size sweep:** 1 KB sampai 10 MB, JSON dan biner.
- **Kartu 2, Pesan kecil:** 64 B sampai 4 KB, 2000 pesan tiap ukuran.
- **Kartu 3, Chunked:** 8 MB dipecah 4 KB, 64 KB, 1 MB.
- **Kartu 4, Akselerasi:** AES-GCM dengan dan tanpa AES-NI.

### 12. Validasi kebenaran (0:30) · Layout B

- **Judul:** Hasil benchmark valid karena implementasinya terbukti benar
- **Kartu 1:** angka besar 116, keterangan "tes pytest lulus".
- **Kartu 2:** angka besar 1089, keterangan "vektor uji Ascon-AEAD128 (ditambah 3 vektor GCM NIST)".
- **Kartu 3:** ikon perisai, keterangan "Tampering test: satu bit dibalik, dekripsi ditolak".

---

## Bagian 4: Hasil (5:00)

### 13. Latensi per file (1:15) · Layout C

- **Judul:** AES-GCM 2,5–4,3× lebih cepat pada keenam file
- **Visual:** chart batang berkelompok (Canva: Elements > Charts > Bar chart). Enam kategori, dua seri (AES-GCM biru, Ascon merah muda). Data (median enkripsi, ms):

  | File | AES-GCM | Ascon | Rasio Ascon/AES |
  |---|---|---|---|
  | small.json | 0,143 | 0,408 | 2,8× |
  | medium.json | 1,810 | 4,625 | 2,6× |
  | large.json | 4,490 | 13,643 | 3,0× |
  | small.png | 0,414 | 1,772 | 4,3× |
  | medium.png | 5,001 | 12,388 | 2,5× |
  | large.png | 13,130 | 33,657 | 2,6× |

- **Panel:** satu angka besar "2,5–4,3×" dan satu keterangan "Ascon lebih lambat pada semua file. Dekripsi serupa: 2,6–5,4×".
- **Sumber:** `output/results/benchmark_results.csv`.

### 14. Size sweep dan titik potong (1:45) · Layout C

- **Judul:** Ascon menang di bawah sekitar 16 KB, AES-GCM menang di atasnya
- **Visual:** chart garis Canva (Elements > Charts > Line chart). Sumbu x berupa kategori ukuran (1 KB, 4 KB, 16 KB, 64 KB, 256 KB, 1 MB, 4 MB, 10 MB), dua seri JSON dan biner berisi rasio Ascon/AES. Tambahkan satu garis horizontal putus-putus di nilai 1 (Elements > Lines) berlabel "rasio 1 = setara". Data dari `output/results/size_sweep_summary.csv` (kolom `RatioAsconOverAes`).
- **Panel:** tabel rasio kecil.

  | Ukuran | JSON | Biner |
  |---|---|---|
  | 1 KB | 0,25 | 0,25 |
  | 4 KB | 0,42 | 0,44 |
  | 16 KB | 0,98 (tidak signifikan) | 1,01 (tidak signifikan) |
  | 64 KB | 2,56 | 2,35 |
  | 1 MB | 2,64 | 3,54 |
  | 10 MB | 3,30 | 3,31 |

- **Catatan:** `output/charts/size_sweep.png` tidak dipakai langsung karena berbentuk hampir persegi dan label titik potongnya saling tumpang tindih. Sumbu kategori di Canva tidak berskala log, tapi ukurannya memang berkelipatan rapi sehingga tetap terbaca. Titik potong 16 KB dibulatkan dari dua titik uji terdekat (4 KB dan 16 KB); tidak ada titik uji di antaranya, jadi angka pastinya bisa di mana saja pada rentang itu.
- Ini slide inti, tekankan titik potongnya.

### 15. Overhead ukuran (0:45) · Layout B (empat kartu)

- **Judul:** Overhead selalu 16 byte, hanya persentasenya yang berubah
- **Susunan:** empat kartu selebar 396 px berjajar (jarak 48 px), bukan tiga. Grafik batang tidak dipakai karena rentang 25% sampai 0,0002% terlalu lebar.
- **Isi kartu:** ukuran data sebagai judul kecil, persentase overhead sebagai angka besar.
  - 64 B: 25%
  - 1 KB: 1,6%
  - 100 KB: 0,014%
  - 8 MB: sekitar 0,0002%
- **Baris di bawah kartu:** "Kedua algoritma +16 B (tag). Nonce tidak dihitung: 12 B untuk AES, 16 B untuk Ascon."
- **Sumber:** kolom `OverheadBytes` dan `OverheadPct` di `benchmark_results.csv`.

### 16. Mengapa AES-GCM menang di data besar (1:15) · Layout C

- **Judul:** Tanpa AES-NI, Ascon justru lebih cepat
- **Visual:** chart batang Canva, tiga batang pada ukuran 10 MB (median enkripsi, ms). Warna: AES-GCM `#3b82f6`, AES-GCM tanpa AES-NI `#fbbf24`, Ascon `#db2777`.

  | Varian | Median (ms) |
  |---|---|
  | AES-GCM | 8,55 |
  | AES-GCM tanpa AES-NI | 32,12 |
  | Ascon | 24,41 |

- **Panel:** dua angka besar.
  - "3,75×": AES-GCM tanpa AES-NI lebih lambat dari dengan AES-NI
  - "3,2×": pesan 64 B, Ascon 123 ribu pesan/detik vs AES-GCM 38 ribu
- **Sumber:** `output/results/acceleration.csv`, `small_messages.csv`.

---

## Bagian 5: Dashboard dan Penutup (3:15)

### 17. Dashboard visualisasi (0:30) · Layout C (visual penuh)

- **Judul:** Hasil dapat dijelajahi secara interaktif
- **Visual:** unggah screenshot dashboard (`python dashboard.py`, `http://127.0.0.1:8050/`), bingkai dengan sudut membulat, lebar sekitar 1400 px, di tengah.
- **Panel:** tiga label anotasi bergaris penunjuk.
  - Grafik latensi dan overhead
  - Grafik size sweep dan titik potong
  - Unggah file sendiri untuk diuji
- Tidak perlu demo langsung.

### 18. Perubahan dari proposal dan batasan (1:15) · Layout A

- **Judul:** Yang berubah dari proposal dan batasannya
- **Kiri, "Berubah dari proposal":** varian Ascon-AEAD128, backend C lewat `ctypes`, tambahan median, CI95, uji Mann-Whitney, size sweep, tiga skenario.
- **Kanan, "Batasan pengukuran":** satu mesin, AES diuji sebelum Ascon tanpa interleaving, key dan nonce dipakai ulang antar iterasi, gambar berupa noise acak, wrapper `ctypes` menyalin output.

### 19. Kesimpulan dan rekomendasi (1:30) · Layout B

- **Judul:** Pilih algoritma sesuai platform dan ukuran data
- **Kartu 1, Ascon:** pesan kecil (di bawah sekitar 11–17 KB) atau perangkat tanpa AES-NI. Aksen `#db2777`.
- **Kartu 2, AES-GCM:** PC atau server dengan AES-NI, data besar. Aksen `#3b82f6`.
- **Kartu 3, Overhead:** bukan pembeda, keduanya +16 B.
- **Baris di bawah kartu:** saran lanjutan, uji di ARM atau Raspberry Pi.
- Slide "Terima kasih" untuk tanya jawab menyusul di luar 19 slide isi.

---

## Alur Kerja di Canva

1. Buat Brand Kit (warna dan Inter), lalu buat halaman kosong 1920 × 1080 dengan panduan margin 96 px.
2. Buat lima layout dasar (A–E), simpan sebagai lima halaman, dan duplikat sesuai tabel pemetaan.
3. Unggah aset gambar: `assets/codeflow.png` (slide 7) dan screenshot dashboard (slide 16).
4. Isi chart bawaan Canva (slide 12, 13, 15) dengan menempel data dari tabel di atas. Warna diatur per seri.
5. Isi teks dan catatan pembicara. Cek dengan Present mode dan stopwatch.
6. Bila dikerjakan lewat konektor Canva, kemampuan tool baru diketahui setelah login. Bagian yang tidak bisa diotomasi (chart, ikon, bingkai) diselesaikan manual di Canva.

## Daftar Aset

| Slide | Aset | Sumber |
|---|---|---|
| 6 | Diagram internal AES-GCM & Ascon-128 | `output/aes-gcm-internals.png`, `output/ascon128-internals.png` (versi interaktif: `assets/diagrams/*.html`) |
| 8 | Diagram alur | `assets/codeflow.png` |
| 10 | Potongan kode | `src/aead.py` |
| 13, 14, 16 | Data chart | tabel di slide masing-masing (dari CSV) |
| 17 | Screenshot dashboard | jalankan `python dashboard.py` |
| 2, 4, 12 | Ikon | pustaka ikon Canva |
| 8 (alternatif) | Diagram sequence pipeline benchmark | `output/aead-benchmark-flow.png` (versi interaktif: `assets/diagrams/aead-benchmark-flow.html`) |  