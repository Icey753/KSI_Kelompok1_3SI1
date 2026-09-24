# Skrip Presentasi — Kelompok 1
## Analisis Komparatif Performa Algoritma AES-GCM dan Ascon-128
### terhadap Overhead Ukuran File dan Latensi Eksekusi pada Berkas Teks (JSON) dan Multimedia (Gambar)

---

**Slide 1 — Judul**

Selamat pagi/siang, kami dari Kelompok 1. Hari ini kami akan mempresentasikan hasil penelitian kami mengenai Analisis Komparatif Performa Algoritma AES-GCM dan Ascon-128, terhadap overhead ukuran file dan latensi eksekusi, pada dua jenis berkas: teks JSON dan multimedia berupa gambar.

---

**Slide 2 — Anggota Kelompok**

Perkenalkan, kelompok kami beranggotakan enam orang: Galang Dwi Nugroho, Ilham Akbar Tauhid, Irish Shanty Kinsella Puteri, Miftahul Husna, Sancha Isabel Da Costa Xavier, dan Yulia Dwi Utari.

---

**Slide 3 — Latar Belakang**

Masuk ke latar belakang. Pertukaran data digital saat ini didominasi dua format dengan karakteristik yang sangat kontras: JSON untuk komunikasi API, dan gambar untuk data multimedia. Keamanan data sendiri bertumpu pada Triad CIA — Confidentiality, Integrity, Availability — dan salah satu skema yang menjamin ini adalah AEAD, Authenticated Encryption with Associated Data. Intinya, AEAD itu enkripsi yang sekaligus membuktikan data tidak diubah orang lain — caranya dengan menempelkan semacam "segel" kecil bernama authentication tag di ciphertext, yang akan kami jelaskan lebih detail nanti. Ada dua algoritma AEAD populer yang jadi fokus kami: AES-GCM, yang berbasis block cipher dengan struktur substitusi-permutasi, dan Ascon-128, yang memakai pendekatan sponge construction berbasis permutasi. Pertanyaannya: dari kedua algoritma ini, mana yang paling efisien?

---

**Slide 4 — Rumusan Masalah**

Dari situ kami rumuskan tiga masalah penelitian. Pertama, bagaimana perbandingan latensi enkripsi dan dekripsi antara AES-GCM dan Ascon-128 pada berkas JSON dan gambar dengan berbagai ukuran? Kedua, bagaimana perbedaan overhead ratio antar kedua algoritma — overhead ratio ini maksudnya seberapa besar file "membengkak" setelah dienkripsi dibanding ukuran aslinya, dan seberapa besar pembengkakan itu disebabkan oleh authentication tag yang ditempelkan? Ketiga, pada tipe data dan ukuran file seperti apa masing-masing algoritma menunjukkan performa terbaiknya?

---

**Slide 5 — Tujuan Proyek**

Tujuan proyek kami ada tiga. Pertama, mengukur dan membandingkan secara empiris latensi eksekusi enkripsi-dekripsi kedua algoritma pada JSON dan gambar dengan variasi ukuran. Kedua, menganalisis overhead rasio ukuran ciphertext — yaitu selisih ukuran file terenkripsi dibanding file asli — yang dihasilkan kedua algoritma, sekaligus mengevaluasi seberapa besar authentication tag itu sendiri menyumbang ke pembengkakan ukurannya. Ketiga, memberikan rekomendasi pemilihan algoritma berdasarkan karakteristik tipe data, dengan mempertimbangkan trade-off antara latensi dan efisiensi ukuran.

---

**Slide 6 — AES-GCM vs Ascon-128 (Tabel)**

Sebelum masuk ke hasil, kami bandingkan dulu karakteristik dasar kedua algoritma. AES-GCM berbasis block cipher, pakai kunci 128 atau 256 bit, nonce 12 byte, dan punya akselerasi hardware AES-NI di hampir semua CPU modern — jadi ideal untuk server dan aplikasi desktop. Ascon-128 berbasis permutasi sponge, kunci 128 bit, nonce 16 byte, belum punya akselerasi hardware yang umum tersedia — makanya secara desain lebih cocok untuk IoT dan perangkat embedded dengan sumber daya terbatas.

Perlu kami garis bawahi satu keterbatasan penting di sini: klaim "cocok untuk IoT" pada tabel ini murni berdasarkan karakteristik desain algoritma, bukan hasil pengujian kami secara langsung di perangkat IoT. Seluruh benchmark kami jalankan di satu laptop dengan computing unit yang jauh lebih kuat dibanding perangkat IoT atau mikrokontroler sesungguhnya. Jadi environment pengujian kami tidak setara — sama-sama diuji di hardware kelas laptop, bukan dibandingkan laptop versus perangkat IoT asli. Kami cuma mensimulasikan kondisi "tanpa AES-NI" dengan mematikan akselerasi hardware-nya di laptop yang sama, bukan menjalankan langsung di chip IoT. Ini kami sebutkan biar hasil dan rekomendasi kami tidak disalahartikan sebagai pengujian lintas platform yang sebenarnya.

---

**Slide 7 — Arsitektur Sistem**

Ini arsitektur sistem yang kami bangun untuk benchmark. Alurnya dimulai dari `main.py` sebagai orkestrator pipeline. Kalau data belum ada, `data_prep.py` akan generate dataset JSON dan PNG ke folder `data/`. Data itu dibaca oleh `benchmark.py`, yang menjalankan proses enkripsi-dekripsi lewat dua modul cipher: `cipher_aes.py` untuk AES-GCM, dan `cipher_ascon.py` yang memanggil DLL Ascon-C via ctypes, dengan fallback ke Python murni kalau DLL tidak tersedia. Hasil benchmark diproses `report.py` untuk hitung latensi dan overhead, disimpan sebagai CSV, lalu divisualisasikan lewat `visualize.py` dan dashboard interaktif `dashboard.py`.

---

**Slide 8 — Ruang Lingkup & Batasan**

Supaya penelitian ini fokus dan hasilnya bisa dipertanggungjawabkan, kami tetapkan enam batasan jelas.

Pertama, dari sisi bahasa dan library: implementasi kami pakai Python 3.x, dengan pycryptodome untuk AES-GCM dan library ascon untuk Ascon-128 — Ascon-nya sendiri kami jalankan lewat binding ke DLL native Ascon-C untuk performa maksimal, dengan fallback ke implementasi Python murni kalau DLL-nya tidak tersedia di sistem.

Kedua, jenis data yang diuji kami batasi cuma dua tipe: file JSON sebagai representasi data teks terstruktur, dan file gambar sebagai representasi data multimedia. Masing-masing tipe diuji dalam beberapa kategori ukuran, dari kecil sampai besar, biar kelihatan tren performanya seiring ukuran naik.

Ketiga, sumber dataset kami sintetis, bukan data asli atau data produksi. JSON di-generate pakai library Faker — isinya nama, ID, dan nominal transaksi yang semuanya palsu. Gambar dibuat programatik pakai Pillow. Kami pilih data sintetis supaya hasil benchmark bisa direproduksi dan tidak ada isu privasi data.

Keempat, metrik yang kami ukur cuma dua, sengaja kami sempitkan. Satu, latensi eksekusi dalam milidetik — untuk proses enkripsi dan dekripsi terpisah. Dua, overhead ukuran — ini istilah yang akan sering muncul, maksudnya adalah selisih ukuran ciphertext dibanding plaintext, dilaporkan dalam persen dan byte. Overhead ini terjadi karena AEAD menambahkan authentication tag, semacam "segel digital" berukuran tetap yang ditempel di akhir ciphertext untuk membuktikan data tidak diubah — jadi ciphertext selalu sedikit lebih besar dari plaintext aslinya.

Kelima, lingkungan uji kami single-machine benchmark: satu unit PC atau laptop dengan spesifikasi tetap selama seluruh sesi pengujian. Ini bukan pengujian terdistribusi, bukan juga pengujian lintas platform atau lintas arsitektur CPU yang berbeda-beda.

Keenam, dan ini penting: yang di luar cakupan penelitian kami. Kami tidak menguji keamanan dari sisi serangan — tidak ada side-channel attack, tidak ada brute-force, tidak ada kriptanalisis. Fokus penelitian kami murni ke performa komputasi dan efisiensi ukuran data, bukan analisis kekuatan kriptografi. Jadi kalau ditanya "mana yang lebih aman", itu di luar scope kami — yang kami jawab adalah "mana yang lebih efisien".

---

**Slide 9 — Alur Pengujian**

Ini alur pengujian kami secara menyeluruh, dari data mentah sampai kesimpulan.

Semua diawali dari operasi enkripsi data. File JSON atau gambar plaintext dienkripsi dua kali secara paralel — sekali pakai AES-GCM, sekali pakai Ascon-128 — dengan input yang identik, supaya perbandingannya adil. Di tahap ini juga authentication tag digenerate dan ditempel ke ciphertext masing-masing algoritma.

Dari situ alurnya bercabang dua, sesuai mekanisme masing-masing algoritma. Jalur AES-GCM masuk ke tahap operasi dekripsi dengan mekanisme fail-safe, dan jalur Ascon-128 masuk ke tahap operasi dekripsi dengan verifikasi integritas. Perlu kami perjelas, dua istilah ini sebenarnya menggambarkan hal yang sama secara fungsional — keduanya sama-sama AEAD, jadi keduanya sama-sama mengecek authentication tag sebelum mengembalikan plaintext. Bedanya cuma di penyebutan, mengikuti istilah yang lazim dipakai tiap library.

Untuk AES-GCM, kami sebut "fail-safe" karena mekanismenya lewat GMAC — pas dekripsi, library menghitung ulang tag dari ciphertext yang diterima, lalu dibandingkan dengan tag yang menyertainya. Kalau tidak cocok, pycryptodome langsung melempar exception dan proses berhenti total, tidak ada plaintext parsial yang sempat keluar — makanya disebut "gagal dengan aman".

Untuk Ascon-128, kami sebut "verifikasi integritas" karena mekanismenya lewat proses sponge — saat fase finalization, permutasi Ascon menghasilkan tag dari seluruh state internal yang sudah menyerap ciphertext dan associated data. Verifikasinya dilakukan dengan cara yang sama: tag dihitung ulang lalu dicocokkan, dan kalau beda, plaintext ditolak.

Jadi intinya, dua-duanya menolak data yang sudah diubah — cuma penamaan di diagram kami beda supaya sesuai istilah dokumentasi masing-masing library yang kami pakai. Hasil akhirnya identik: tidak ada plaintext yang bocor kalau ciphertext atau tag-nya tidak valid.

Kedua jalur itu lalu bertemu lagi di tahap pengukuran latensi eksekusi. Di sini kami catat waktu proses enkripsi dan dekripsi masing-masing algoritma, biasanya dengan beberapa kali pengulangan atau warm-up run biar hasilnya stabil dan tidak bias oleh noise sistem di run pertama.

Terakhir, hasil dari kedua algoritma itu dibawa ke tahap pengukuran rasio pembengkakan, atau overhead ratio — kami bandingkan ukuran ciphertext akhir terhadap ukuran plaintext awal. Karena authentication tag punya ukuran tetap, biasanya 16 byte, pengaruhnya ke overhead ini paling terasa di file kecil, dan makin tidak terasa di file besar — nanti kelihatan jelas di slide hasil.

Seluruh alur ini kami jalankan otomatis lewat pipeline `benchmark.py`, dan hasilnya langsung disimpan ke CSV supaya bisa dianalisis dan divisualisasikan di tahap berikutnya.

---

**Slide 10 — Demonstrasi (transisi)**

Sekarang kami akan masuk ke sesi demonstrasi langsung dari dashboard yang kami bangun.

---

**Slide 11 — Dashboard Benchmark File**

Ini tampilan dashboard benchmark kami. User bisa upload file JSON atau gambar, lalu klik "Jalankan Benchmark" untuk menjalankan AES-GCM dan Ascon-128 pada file yang sama. Contoh di sini, kami upload gambar 41.763 KB berukuran besar. Hasilnya: rata-rata enkripsi 333,432 milidetik, rata-rata dekripsi 394,414 milidetik, overhead rata-rata 0% — karena di file sebesar ini, tambahan 16 byte authentication tag praktis tidak berarti apa-apa dibanding ukuran totalnya — dan lolos uji tamper 2 dari 2, alias 100%. Di bawahnya ada tiga grafik: latensi enkripsi, latensi dekripsi — sudah termasuk waktu verifikasi authentication tag di dalamnya — dan overhead ciphertext dalam persen. Dan di tabel hasil benchmark, kelihatan detailnya: AES-GCM encrypt 249,9 ms, Ascon-128 encrypt 416,9 ms, dan kolom overhead sama-sama cuma 16 byte — pas dengan ukuran authentication tag-nya.

---

**Slide 12 — Pengujian: Skenario mengubah 1 bit**

Sekarang kami masuk ke pengujian keamanan fungsional.

Skenario pertama: uji tamper. Tamper artinya data diubah atau dirusak secara sengaja oleh pihak luar setelah dienkripsi — misalnya diserang di tengah jalan pas dikirim, atau file-nya diotak-atik sebelum sampai ke penerima. Kami simulasikan ini dengan membalik satu bit saja di ciphertext, perubahan sekecil mungkin, lalu coba dekripsi.

Nah, kenapa perubahan sekecil itu bisa langsung ketahuan? Karena AES-GCM dan Ascon-128 sama-sama algoritma AEAD — Authenticated Encryption with Associated Data, yang tadi sempat kami singgung di latar belakang. AEAD itu enkripsi yang punya dua fungsi sekaligus: merahasiakan data, dan membuktikan data itu asli, tidak diubah siapa pun. Pembuktian keasliannya lewat authentication tag — semacam segel digital kecil, biasanya 16 byte, yang dihitung dari seluruh isi ciphertext saat proses enkripsi, lalu ditempel di ujungnya. Segel ini sifatnya sangat sensitif: ubah walau cuma satu bit di ciphertext, hasil perhitungan ulang tag-nya pasti beda total, dan tidak akan cocok lagi dengan tag yang menyertainya.

Jadi begitu kami balik satu bit dan coba dekripsi, algoritma AEAD harusnya menolak, karena authentication tag yang sudah ditempel tidak akan cocok lagi dengan ciphertext yang sudah diubah. Dan benar, hasilnya ditolak: integritas terjaga, plaintext tidak dikembalikan sama sekali — bukan dikembalikan tapi salah isinya, tapi memang tidak dikembalikan sama sekali.

Skenario kedua di sebelah kanan: enkripsi lalu dekripsi balik, untuk membuktikan data kembali utuh kalau tidak ada gangguan sama sekali — jadi ini kebalikan dari skenario pertama, membuktikan jalur normalnya benar. Kami bandingkan hash SHA-256 sebelum dan sesudah proses — hasilnya sama persis, artinya data benar-benar kembali utuh tanpa korupsi.

---

**Slide 13 — Pengujian: Nonce reuse & gambar ciphertext**

Skenario ketiga: bahaya nonce dipakai ulang.

Nonce itu singkatan dari "number used once" — angka acak yang wajib beda setiap kali kita enkripsi pakai key yang sama. Fungsinya supaya dua pesan yang isinya sama pun hasil ciphertext-nya beda total. Analoginya seperti nomor seri sekali pakai: kalau nomor ini dipakai ulang dengan key yang sama, lapisan pelindung yang dihasilkan algoritma jadi sama persis untuk dua pesan berbeda — dan itu yang bahaya.

Kami simulasikan bahayanya: dua pesan dienkripsi dengan key dan nonce yang sama, lalu ciphertext-nya di-XOR dan dibandingkan dengan XOR plaintext-nya. XOR di sini maksudnya operasi bit-per-bit yang, kalau nonce-nya sama, bisa "mencoret" lapisan pelindung dari kedua ciphertext sehingga yang tersisa adalah hasil XOR dari plaintext aslinya — jadi penyerang bisa dapat informasi plaintext tanpa perlu tahu key sama sekali, cukup dengan membandingkan dua ciphertext yang nonce-nya kebetulan sama.

Hasil demo kami: AES-GCM bocor 35 dari 35 byte, alias 100% bocor. "Bocor" di sini maksudnya berapa byte dari plaintext asli yang berhasil kami pulihkan lewat trik XOR tadi, tanpa perlu key — jadi 100% bocor artinya seluruh isi pesan berhasil ditebak balik. Dan benar, plaintext B berhasil dipulihkan dari A. Ascon-128 sedikit lebih baik, bocor 16 dari 35 byte, sekitar 46% — jadi hampir separuh isi pesannya tetap bisa ditebak, tapi tidak selengkap AES-GCM. Intinya, reuse nonce itu fatal di kedua algoritma, cuma beda tingkat separahnya — dan ini terjadi di luar mekanisme authentication tag, karena tag cuma melindungi dari perubahan ciphertext, bukan dari kesalahan pemakaian nonce.

Skenario keempat, di sebelah kanan: gambar asli vs ciphertext. Piksel gambar yang diupload dienkripsi, lalu ciphertext-nya dirender sebagai gambar. Hasilnya jelas — foto asli berubah total jadi noise acak, membuktikan enkripsi menghilangkan semua pola visual yang bisa dikenali.

---

**Slide 15 — Titik Potong Latensi**

Ini grafik titik potong latensi Ascon versus AES-GCM. Grafik atas menunjukkan median latensi enkripsi terhadap ukuran data dalam skala log. Grafik bawah menunjukkan rasio Ascon dibagi AES — kalau di bawah 1, artinya Ascon lebih cepat. Kami temukan titik potongnya ada di sekitar 19 KB untuk data biner, dan sekitar 37 KB untuk JSON. Jadi di bawah titik itu Ascon lebih unggul, di atasnya AES-GCM yang unggul. Catatan: overhead ukuran tidak kami plot di grafik ini karena, seperti dijelaskan sebelumnya, kontribusi authentication tag terhadap overhead relatif konstan di semua ukuran — yang berubah signifikan justru latensinya, itu makanya ini fokus grafiknya.

---

**Slide 16 — Skenario Realistis: pesan kecil & AES-NI**

Angka-angka di slide sebelumnya itu abstrak — sekarang kami turunkan ke dua skenario yang lebih kebayang di dunia nyata.

Yang pertama, di kiri: "ribuan pesan JSON kecil, gaya komunikasi API." Maksudnya kami simulasikan pola trafik yang umum di aplikasi nyata — misalnya server yang terus-menerus menerima request kecil dari banyak client, tiap request dienkripsi sendiri-sendiri dengan nonce baru per pesan, bukan satu file besar yang dienkripsi sekali. Ukuran pesannya kami variasikan dari 64 byte sampai 4 KB — kira-kira seukuran satu baris JSON transaksi atau satu event log.

Kenapa hasilnya beda jauh dari slide sebelumnya? Karena di pesan sekecil ini, biaya "buka-tutup" enkripsi — inisialisasi cipher, setup nonce, generate authentication tag — jadi porsi dominan dari total waktu, bukan proses enkripsi datanya sendiri. Dan ingat, authentication tag ukurannya tetap 16 byte — di pesan 64 byte, itu sama dengan 25% dari ukuran pesan, jadi bebannya terasa jauh lebih berat dibanding di file besar tadi. Metrik yang kami pakai di grafik ini "pesan per detik" — makin tinggi batangnya, makin banyak pesan yang bisa diproses algoritma itu dalam satu detik, alias makin baik throughput-nya. Hasilnya Ascon-128 unggul jauh, bisa proses sampai 50 ribu pesan per detik di ukuran 256 byte — jauh di atas AES-GCM biasa.

Yang kedua, di kanan grafik yang sama: ada bar ketiga bernama "AES-GCM-noNI." AES-NI itu instruksi khusus di prosesor modern yang mempercepat operasi AES lewat hardware — hampir semua laptop dan server sekarang punya ini. Kami sengaja matikan fitur ini untuk AES-GCM, supaya hasilnya meniru kondisi perangkat yang tidak punya AES-NI, seperti kebanyakan mikrokontroler IoT. Ini penting karena banyak literatur IoT membandingkan Ascon dengan AES-GCM yang justru berjalan tanpa AES-NI di perangkat aslinya — jadi grafik ini menjelaskan kenapa temuan kami, yang pakai laptop ber-AES-NI, bisa terlihat berbeda dari literatur tersebut: begitu AES-NI dimatikan, keunggulan AES-GCM di data besar langsung hilang, karena dia kembali ke kecepatan software murni seperti Ascon.

---

**Slide 17 — Skenario Realistis: total waktu batch**

Masih skenario realistis, kali ini kami balik cara bacanya. Slide sebelumnya jawab pertanyaan "berapa pesan per detik yang sanggup diproses". Slide ini jawab pertanyaan yang lebih kebayang buat pemakai sistem: "berapa lama total waktu yang dibutuhkan untuk mengirim seluruh batch pesan sampai habis" — misalnya kalau ada 10 ribu pesan kecil yang harus dienkripsi berurutan, berapa detik total yang dihabiskan.

Konteksnya kami sebut "skenario IoT atau API burst" — burst artinya lonjakan trafik dalam waktu singkat, semacam saat banyak sensor IoT kirim data bersamaan, atau saat API menerima ratusan-ribuan request dalam hitungan detik. Ini kondisi yang lebih realistis dibanding "satu file besar dienkripsi sekali" seperti demo di slide 11 — di dunia nyata, sistem IoT dan API justru lebih sering berurusan dengan banyak pesan kecil yang datang terus-menerus, bukan satu file raksasa.

Sumbu Y di grafik ini pakai skala log, karena rentang waktunya lebar sekali. Hasilnya konsisten dengan slide sebelumnya: Ascon-128 jauh lebih cepat menyelesaikan seluruh batch pesan kecil dibanding AES-GCM, baik dengan atau tanpa AES-NI. Jadi kalau sistemnya berupa banyak pesan kecil yang harus diproses cepat berurutan, gap keunggulan Ascon ini yang paling terasa dampaknya secara nyata — bukan cuma beda di kertas.

---

**Slide 18 — Skenario Realistis: overhead per chunk**

Terakhir dari sesi skenario realistis. Skenario ini beda dari dua slide sebelumnya — kalau tadi kami uji banyak pesan kecil terpisah, di sini kami uji satu file besar yang sama, tapi dipecah-pecah jadi potongan atau "chunk" berukuran tertentu sebelum dienkripsi — ini pola yang umum dipakai kalau streaming file besar, misalnya upload video atau backup data, di mana file tidak dienkripsi sekaligus tapi per-potongan supaya hemat memori.

Grafik atas: overhead persen per ukuran chunk. Ini pelurusan konsep overhead yang sudah kami singgung sejak slide 8 — sekarang kelihatan jelas pola turunnya. Di chunk 4 KB, overhead-nya hampir 5%, tapi begitu chunk-nya diperbesar ke 64 KB, 1 MB, sampai file utuh, overhead-nya turun drastis ke di bawah 0,01%. Penyebabnya sama seperti yang kami jelaskan di slide 8: authentication tag ukurannya tetap 16 byte per chunk, jadi kalau chunk-nya kecil, 16 byte itu jadi porsi besar dari total data; kalau chunk-nya besar, 16 byte itu jadi nyaris tidak berasa — sama seperti nambah 1 sendok gula ke segelas air, rasanya kentara, tapi ke seember air, nyaris tidak terasa manisnya. Konsekuensi praktisnya: kalau sistem kalian mengenkripsi file dengan memecahnya jadi chunk kecil-kecil, pertimbangkan trade-off ini — chunk kecil boros overhead, chunk besar lebih hemat tapi butuh memori lebih banyak sekaligus.

Grafik bawah: median latensi enkripsi terhadap ukuran chunk yang sama. Di chunk kecil seperti 4 KB, ketiga varian — AES-GCM, Ascon-128, dan AES-GCM tanpa AES-NI — waktunya berdekatan, karena biaya inisialisasi per chunk masih dominan, mirip pola di slide 16. Begitu chunk-nya membesar ke 64 KB ke atas, urutannya menetap: AES-GCM konsisten paling cepat, disusul Ascon, lalu AES-GCM tanpa AES-NI paling lambat — ini konsisten dengan titik potong sekitar 19-37 KB yang sudah kami temukan di slide 15 tadi, di atas titik itu AES-GCM dengan AES-NI memang selalu unggul untuk data yang lebih besar.

---

**Slide 19 — Kesimpulan**

Sampai ke kesimpulan. Dari sisi latensi: AES-GCM lebih cepat untuk data sedang sampai besar, di atas 16 sampai 64 KB, bahkan 2,6 sampai 4 kali lebih cepat di data besar. Sebaliknya, Ascon-128 lebih cepat untuk data kecil, di bawah 16 KB. Dari sisi overhead ukuran: keduanya hampir sama, sama-sama cuma menambah 16 byte untuk authentication tag — jenis file dan algoritma tidak berpengaruh besar ke overhead ini, karena authentication tag memang ukurannya tetap, tidak tergantung ukuran atau jenis file yang dienkripsi. Jadi rekomendasi kami: AES-GCM cocok untuk sistem yang mengolah data besar dan masif di platform PC atau server modern yang punya AES-NI. Sementara Ascon-128 cocok untuk pesan kecil, atau perangkat dengan sumber daya terbatas seperti IoT dan mikrokontroler yang tidak punya AES-NI — dengan catatan, seperti sudah kami sampaikan di slide 6, rekomendasi untuk IoT ini berdasarkan karakteristik desain algoritma dan simulasi tanpa AES-NI, bukan pengujian langsung di perangkat IoT sungguhan.

---

**Slide 20 — Penutup**

Demikian presentasi dari Kelompok 1. Terima kasih atas perhatiannya, kami buka sesi tanya jawab.
