# Penjelasan Dashboard AES-GCM vs Ascon-128

## 1. Pembuka

Dashboard ini bandingin dua algoritma enkripsi terautentikasi (AEAD): AES-GCM, standar industri yang dipercepat hardware AES-NI, dan Ascon-128, pemenang kompetisi NIST Lightweight Cryptography 2023 buat perangkat terbatas seperti IoT. Semua yang saya tunjukkan ini jalan langsung, saya upload file, dashboard yang eksekusi benchmark-nya.

## 2. Bagian "Benchmark File"

Ini bagian utama, alurnya tiga langkah.

Pertama, upload file: drag-drop JSON atau gambar (PNG, JPG, WEBP, GIF, BMP), maksimal beberapa MB. File langsung diklasifikasi ukurannya, kecil, sedang, atau besar. Kategori ini nentuin berapa iterasi benchmark yang jalan: file kecil diulang 10 kali biar hasilnya stabil, file besar cukup 1 kali karena udah berat.

Kedua, tekan Jalankan Benchmark. Dashboard enkripsi dan dekripsi file yang sama pakai kedua algoritma, catat waktunya.

Hasilnya muncul di empat kartu metrik: rata-rata waktu enkripsi, rata-rata dekripsi, overhead ukuran ciphertext, dan persentase uji tamper yang lolos, artinya berapa kali percobaan mengubah data terdeteksi dan ditolak sistem.

Di bawahnya tiga grafik batang. Ada juga tabel detail per baris hasil, bisa difilter dan diurutkan.

### Latensi enkripsi

Angka waktu murni proses mengubah plaintext jadi ciphertext, diukur dari saat fungsi enkripsi mulai jalan sampai selesai, dirata-rata dari beberapa iterasi biar gak kena noise satu kali eksekusi yang kebetulan lambat. Garis error di grafiknya itu simpangan baku antar iterasi, kalau garisnya panjang berarti waktunya gak stabil, run-to-run bisa beda jauh.

### Latensi dekripsi

Mirip enkripsi, tapi ada tambahan kerja yang gak ada di enkripsi: verifikasi tag autentikasi. Sebelum plaintext dikembalikan, algoritma harus hitung ulang tag dari ciphertext yang diterima terus dibandingkan sama tag asli. Kalau gak cocok, dekripsi ditolak, plaintext gak pernah dikembalikan. Karena ada langkah verifikasi ini, latensi dekripsi biasanya sedikit lebih tinggi dari enkripsi meskipun beban komputasi intinya mirip.

### Overhead ciphertext

Selisih ukuran antara ciphertext dan plaintext aslinya, dalam persen. Selisih ini bukan karena datanya "digembungkan", tapi karena ciphertext harus bawa tag autentikasi menempel di belakangnya, 16 byte buat AES-GCM dan Ascon-128 sama-sama 16 byte. Jadi buat file kecil, overheadnya kelihatan besar secara persentase karena 16 byte itu porsinya signifikan dibanding ukuran filenya. Buat file besar, 16 byte itu hampir gak kerasa, overhead persennya turun mendekati nol. Itu kenapa grafiknya dipecah per kategori ukuran, biar polanya kelihatan.

### Manfaat unduh ciphertext Base64 dan metadata

Bukan cuma buat arsip. Ciphertext-nya disimpan dalam bentuk teks Base64 supaya bisa dipindahkan lewat medium yang cuma terima teks, dikirim lewat email, ditempel di JSON, disimpan di database text field, tanpa risiko byte rusak kayak kalau dikirim mentah sebagai binary. Metadata-nya isinya nonce, tag, dan algoritma yang dipakai, dalam format JSON. Ini yang bikin ciphertext itu bisa didekripsi ulang di luar dashboard, karena AES-GCM dan Ascon-128 butuh nonce yang sama persis buat proses dekripsi, jadi kalau nonce-nya gak disimpan bareng ciphertext-nya, data itu gak akan pernah bisa dibuka lagi. Jadi dua file ini sengaja dipisah biar bisa didemoin: ambil ciphertext base64-nya, ambil metadatanya, terus buktiin bisa didekripsi manual pakai script lain.

## 3. Bagian "Demo Interaktif"

Bagian ini nunjukin buktinya, bukan cuma angka. Key dan nonce selalu diacak ulang tiap klik. Ada lima demo.

Uji tamper: saya balik satu bit di ciphertext lalu coba dekripsi. AEAD yang benar menolaknya, bukan mengembalikan data rusak diam-diam.

Enkripsi lalu dekripsi balik: bukti data kembali utuh, dibandingkan hash SHA-256 sebelum dan sesudah.

Bahaya nonce dipakai ulang: dua pesan dienkripsi pakai key dan nonce yang sama, lalu hasil XOR-nya dibandingkan. Contoh nyatanya ada, bug di software backup Kopia tahun 2023 sempat bikin nonce reuse kejadian di produksi.

Gambar asli vs ciphertext: piksel file gambar yang diupload dienkripsi, lalu ciphertext-nya dirender ulang jadi gambar, biar keliatan bedanya data acak dengan data asli.

### AEAD vs CBC, kenapa hasilnya beda

Satu byte ciphertext diubah di dua metode. AES-CBC standar itu cuma enkripsi, gak ada mekanisme verifikasi integritas bawaan. Waktu didekripsi, CBC cuma ngecek satu hal, padding di blok terakhir valid apa gak (skema PKCS7). Kalau kebetulan padding-nya masih keliatan valid setelah byte diubah, CBC tetap ngeluarin plaintext, cuma isinya udah rusak dan sistem gak tahu itu udah dirusak. Baru kalau paddingnya kebetulan jadi gak valid, CBC nolak, tapi itu murni kebetulan, bukan karena CBC memang ngecek keutuhan data.

AES-GCM beda, dia itu AEAD, tiap kali enkripsi ngehasilin tag autentikasi yang dihitung dari seluruh ciphertext. Waktu dekripsi, tag itu dihitung ulang dan dibandingkan sebelum plaintext dikasih ke pemanggil, jadi ubah satu byte di mana pun bakal bikin tag gak cocok, dan GCM nolak seratus persen dari waktu, gak kayak CBC yang nolaknya untung-untungan.

Itu sebabnya demo ini nunjukin AES-GCM selalu bilang "ditolak" sementara CBC hasilnya bisa "diterima, data rusak diam-diam" atau "ditolak, kebetulan padding jadi gak valid", tergantung byte mana yang diubah.

## 4. Bagian "Analisis Ukuran Data dan Lingkungan"

Bagian ini jawab pertanyaan: algoritma mana yang lebih cepat, tergantung ukuran datanya. Saya jalankan sweep dari 1 KB sampai 10 MB, JSON dan biner. Grafiknya dua panel: median latensi enkripsi, dan rasio kecepatan Ascon dibanding AES. Kalau rasionya di bawah 1, Ascon lebih cepat di titik itu. Ada titik potong yang ditandai, tempat kedua algoritma impas.

Di sebelahnya, panel info lingkungan pengujian: spesifikasi mesin yang menjalankan benchmark ini, termasuk apakah AES-NI aktif. Ini penting karena AES-GCM bisa berkali-kali lipat lebih cepat kalau prosesornya punya AES-NI. Tanpa itu, hasilnya bisa beda jauh dari yang sering dikutip literatur.

## 5. Bagian "Skenario Realistis"

Empat skenario yang meniru kondisi dunia nyata, bukan cuma benchmark satu file.

Ribuan pesan JSON kecil, gaya panggilan API: nonce baru tiap pesan, biar keliatan biaya inisialisasi per panggilan yang dominan waktu pesannya kecil.

Dengan dan tanpa AES-NI: saya matikan akselerasi hardware buat mensimulasikan perangkat IoT murah tanpa AES-NI, biar keliatan kenapa hasilnya beda dari literatur biasa.

Total waktu kirim semua pesan: datanya sama dengan skenario pertama, dibalik jadi total waktu buat kirim satu batch, biar lebih kebayang dampaknya di skala besar.

File besar dienkripsi per chunk: tiap potongan bawa tag otentikasi sendiri, jadi kalau chunk-nya kecil, overhead persentasenya makin besar. Indeks urutan chunk juga ikut diautentikasi, jadi penukaran urutan atau pemotongan ketahuan.

## 6. Penutup

Dashboard ini nampilin angka benchmark sekaligus perilaku keamanan AEAD-nya langsung di depan mata: gimana data yang diubah ditolak, gimana nonce reuse bocor, dan gimana CBC polos gagal deteksi kerusakan yang AES-GCM tangkap.
