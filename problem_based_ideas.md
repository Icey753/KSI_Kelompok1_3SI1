# Ide Pengembangan Berbasis Masalah (Problem-Based)

Dokumen ini merangkum empat arah pengembangan konsep proyek yang dibingkai dari masalah nyata, bukan sekadar fitur tambahan. Tiap ide mencakup: problem, penjelasan, referensi paper/artikel, perkiraan perubahan di repo/dashboard, kelebihan, dan kekurangan penerapannya.

Konteks saat ini: aplikasi cuma alur satu arah (upload file -> enkripsi AES-GCM/Ascon -> output ciphertext), dashboard cuma visualisasi proses dan angka benchmark.

---

## 1. IoT / Perangkat Baterai Kecil — Payload Kecil Berulang

**Problem**
Mana yang lebih hemat waktu/energi buat kirim data sensor kecil terus-terusan: AES-GCM (butuh AES-NI) atau Ascon (didesain buat ini)?

**Penjelasan**
AES-GCM cepat kalau ada AES-NI (instruksi hardware khusus di CPU modern), tapi mikrokontroler kecil (sensor IoT) biasanya gak punya AES-NI, jadi AES jatuh ke software murni yang lambat. Ascon didesain dari awal buat jalan efisien tanpa hardware khusus — makanya NIST pilih dia buat standar lightweight (SP 800-232, 2023/2025). Problem ini nunjuk kenapa "satu algoritma cepat di PC" belum tentu cepat di semua device.

**Referensi**
- [NIST Ascon Status Update (finalist doc)](https://csrc.nist.gov/csrc/media/Projects/lightweight-cryptography/documents/finalist-round/status-updates/ascon-update.pdf)
- [Adaptive Lightweight Security for Performance Efficiency in Critical Healthcare Monitoring (arXiv 2406.03786)](https://arxiv.org/pdf/2406.03786)

**Perkiraan Perubahan Repo/Dashboard**
- `src/scenarios.py`: tambah skenario "IoT burst" — kirim N pesan kecil berturut-turut, key/nonce baru tiap pesan (bukan reuse ala benchmark timing biasa).
- `src/dashboard_scenarios.py`: tambah kartu/grafik total waktu kumulatif untuk skenario ini, bukan cuma rata-rata per pesan.
- Opsional: `src/env_info.py` diperluas buat estimasi energi kasar (proxy dari CPU time, bukan pengukuran daya asli — riset energi sungguhan butuh hardware meter).

**Kelebihan**
- Reuse langsung `sweep.py`/skenario pesan kecil yang sudah ada, effort implementasi kecil.
- Narasi kuat: nyambung ke alasan NIST bikin standar lightweight, bukan cuma angka lab.

**Kekurangan**
- Tanpa hardware IoT beneran (Raspberry Pi/mikrokontroler), klaim "hemat energi" cuma estimasi dari CPU time di PC — kurang valid secara ilmiah.
- Simulasi "1000x kirim pesan kecil" di PC ber-AES-NI tetap bias ke AES-GCM, gak representasi device tanpa AES-NI kecuali eksplisit pakai mode `AES-GCM-noNI` yang sudah ada.

---

## 2. Transfer File Besar — Bandwidth Terbatas

**Problem**
Overhead ciphertext (tag + nonce) nambah ukuran berapa persen, worth it gak buat koneksi lambat?

**Penjelasan**
Tiap pesan terenkripsi AEAD nambah tag 16 byte plus nonce (12 byte AES-GCM, 16 byte Ascon) di luar data asli. Buat file besar, overhead ini gak kerasa (persentase kecil). Tapi buat pesan kecil berulang (API call, sensor), overhead itu bisa jadi porsi besar dari total data terkirim — makin sering kirim, makin kerasa. Studi ini nunjuk titik potong: di ukuran berapa overhead mulai gak signifikan.

**Referensi**
- [Light-weight Encryption and Hashing Performance Tests](https://asecuritysite.com/ascon/light) — data konkret Ascon ~8-11x lebih efisien di pesan kecil (8 byte), tapi beda makin kecil di pesan besar (1 KB, Ascon cuma ~2x lebih baik).

**Perkiraan Perubahan Repo/Dashboard**
- `src/visualize.py`/`src/sweep_charts.py`: tambah chart baru "overhead persen vs ukuran file" dengan garis threshold/cutoff yang ditandai eksplisit.
- `src/dashboard_analysis.py`: tambah panel rekomendasi otomatis (teks dinamis) — "di bawah X KB pakai Ascon, di atas pakai AES-GCM" — dihitung dari data CSV, bukan hardcode.
- Tidak perlu cipher baru, cuma olah ulang data `output/results/*.csv` yang sudah ada.

**Kelebihan**
- Data sudah ada (`output/results/benchmark_results.csv`), ini murni analisis + visualisasi baru, hampir tanpa risiko bug baru di layer enkripsi.
- Hasil rekomendasi konkret dan actionable, enak buat kesimpulan tugas.

**Kekurangan**
- Titik potong hasil cuma valid untuk kombinasi hardware+dataset yang diuji (PC dengan AES-NI) — gak otomatis general ke device lain.
- Kalau overhead persen dihitung naif (tag+nonce dibagi ukuran plaintext), bisa menyesatkan untuk file yang sangat kecil (dominasi overhead) vs sangat besar (overhead nyaris nol) — perlu skala grafik (log) biar gak salah baca.

---

## 3. Integritas Data — MITM / Tamper di Transit

**Problem**
Gimana AEAD nolak data yang diubah walau 1 bit, dibanding enkripsi non-autentikasi (AES-CBC polos)?

**Penjelasan**
Enkripsi biasa (CBC) cuma bikin data gak kebaca, tapi gak ngecek apakah data itu diubah orang di tengah jalan — attacker bisa modifikasi ciphertext dan sistem tetap "berhasil" decrypt (walau hasilnya jadi sampah atau bahkan berbahaya kalau formatnya predictable, contoh: padding oracle). AEAD (GCM, Ascon) nambah authentication tag: kalau satu bit aja diubah, verifikasi gagal total, decrypt ditolak. Ini problem yang paling gampang dipahami orang awam kenapa AEAD lebih baik dari enkripsi polos.

**Referensi**
- [Cryptographic Implementation Vulnerabilities: AES-GCM Nonce Reuse, Timing Attacks, Padding Oracles — AquilaX](https://aquilax.ai/blog/cryptographic-implementation-vulnerabilities)

**Perkiraan Perubahan Repo/Dashboard**
- `src/cipher_aes.py`: tambah implementasi AES-CBC (mode pembanding, bukan pengganti) — pakai `pycryptodome` yang sudah jadi dependency.
- `src/demo_tools.py`: tambah `cbc_tamper_demo()` — enkripsi CBC, tamper 1 byte, decrypt tetap "sukses" tapi hasil rusak (dibanding `tamper_demo()` existing yang return `None`).
- `src/dashboard_demo.py`: tambah kartu perbandingan side-by-side "CBC: decrypt sukses tapi data rusak diam-diam" vs "AEAD: decrypt ditolak tegas".

**Kelebihan**
- Kontras visual sangat jelas (rusak diam-diam vs ditolak tegas) — paling mudah dijelaskan ke audiens non-teknis/dosen penguji.
- Modul demo (`demo_tools.py`) sudah punya pola serupa (`tamper_demo`), tinggal extend, bukan bikin arsitektur baru.

**Kekurangan**
- Menambah algoritma pembanding ketiga (CBC) sedikit melebarkan scope "AES-GCM vs Ascon" jadi tiga arah — perlu dipastikan gak bikin bingung fokus tugas.
- AES-CBC butuh padding (PKCS7) dan IV terpisah — implementasi minor tapi nambah permukaan bug/testing (perlu test tambahan di `tests/`).

---

## 4. Reuse Nonce — Kesalahan Developer Nyata

**Problem**
Developer sering salah reuse nonce/IV (angka yang harusnya sekali pakai). Apa akibatnya nyata di dua algoritma ini?

**Penjelasan**
AES-GCM dan Ascon sama-sama generate keystream dari kombinasi key+nonce. Kalau nonce yang sama dipakai buat dua pesan berbeda, keystream-nya identik. XOR dua ciphertext itu bakal ngasih XOR dari dua plaintext-nya — kalau satu plaintext ketauan (atau ditebak), plaintext lain langsung kebongkar tanpa perlu crack key sama sekali. Lebih parah lagi di GCM: reuse nonce juga bocorin authentication key (GHASH), jadi attacker bisa forge pesan baru yang keliatan valid. Ini bukan teori doang — kejadian ini beneran ditemuin di kode produksi.

**Referensi**
- [AES-GCM and breaking it on nonce reuse — matematika serangan step by step](https://frereit.de/aes_gcm/)
- [Random AES-GCM nonce reuse — kopia GitHub issue #5169 (bukti kasus nyata di kode production)](https://github.com/kopia/kopia/issues/5169)
- [Attacks on GCM with Repeated Nonces — elttam (analisis recover authentication key)](https://www.elttam.com/blog/key-recovery-attacks-on-gcm)
- [AES-GCM Nonce Reuse Writeup — Medium (walkthrough exploit gaya CTF)](https://medium.com/@malkhoori/aes-gcm-nonce-reuse-writeup-7d5a92b599cb)

**Perkiraan Perubahan Repo/Dashboard**
- `src/demo_tools.py`: `nonce_reuse_demo()` sudah ada — extend biar juga mengembalikan hasil XOR keystream (`c1 xor c2` vs `p1 xor p2`) buat pembuktian visual, bukan cuma status pass/fail.
- `src/dashboard_demo.py`: tambah panel "insiden nyata" — narasi teks referensi kasus (kopia, dll) berdampingan dengan hasil demo interaktif.
- Opsional lanjutan ke CTF-style (dibahas terpisah sebelumnya): user diberi dua ciphertext nonce-sama + satu plaintext diketahui, diminta cari plaintext kedua.

**Kelebihan**
- Paling kuat secara akademis — didukung banyak referensi dan kasus nyata terdokumentasi (bukan cuma potensi teoretis).
- Modul inti (`nonce_reuse_demo`) sudah ada, tinggal exposed lebih detail ke UI — risiko rendah.

**Kekurangan**
- Penjelasan matematis (XOR keystream, GHASH leak) butuh effort ekstra biar gak "terlalu teknis" buat audiens presentasi umum — perlu framing bertahap (poin 3 kalimat, sudah jadi kebiasaan proyek ini).
- Demo XOR keystream lebih meyakinkan kalau plaintext-nya mirip format (JSON dengan struktur dikenal) — kalau datanya random, bocoran gak sejelas itu, perlu pilih dataset demo yang representatif.

---

## Ringkasan Prioritas

| # | Ide | Effort | Risiko Scope Creep | Kekuatan Naratif |
|---|---|---|---|---|
| 1 | IoT payload kecil | Sedang | Rendah | Sedang (butuh hardware asli buat kuat) |
| 2 | Overhead vs bandwidth | Rendah | Rendah | Sedang |
| 3 | Integritas (AEAD vs CBC) | Sedang | Sedang (tambah algoritma) | Tinggi |
| 4 | Nonce reuse | Rendah–Sedang | Rendah | Tinggi (paling banyak referensi nyata) |

Ide 4 dan 3 paling kena kalau tujuan tugas menonjolkan pentingnya AEAD (bukan cuma race kecepatan). Ide 2 paling murah untuk diimplementasikan karena murni analisis data yang sudah ada.
