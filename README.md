# KRS Viewer

Aplikasi web untuk melihat, merencanakan, dan menganalisis jadwal akademik mahasiswa.

Dibuat menggunakan Python dan Streamlit, aplikasi ini memudahkan mahasiswa dalam menyusun KRS dengan fitur deteksi bentrok otomatis dan asisten AI cerdas.

## Fitur Unggulan

- Validasi Cerdas: Pengecekan otomatis batas SKS dan kuota kelas.
- Deteksi Konflik: Peringatan visual jika ada jadwal yang bertabrakan.
- Jadwal Visual: Tampilan grid mingguan yang mudah dibaca.
- Asisten AI: Konsultasi jadwal dan rekomendasi mata kuliah menggunakan DeepSeek/Gemini.
- Bandingkan Jadwal: Cari waktu kosong bersama teman untuk kegiatan kelompok.
- Format Fleksibel: Ekspor rencana ke Excel/JSON atau simpan ke Google Calendar (ICS).
- Mode Offline: Data tersimpan otomatis di perangkat lokal.

## Persyaratan Sistem

- Python 3.8 atau lebih baru.
- Koneksi internet untuk mengambil data KRS.

## Panduan Instalasi

1. Clone repository ini atau download kode sumbernya.

2. Buka terminal atau command prompt di folder project.

3. Install semua library yang dibutuhkan:
   pip install -r requirements.txt

## Konfigurasi AI Assistant

Fitur AI Assistant menggunakan API dari Sumopod (kompatibel dengan OpenAI).

1. Daftar atau login di https://sumopod.com
2. Masuk ke dashboard dan buat API Key baru.
3. Salin API Key tersebut.
4. Di folder project ini, buat file baru bernama .env
5. Isi file .env dengan format berikut:
   AI_API_KEY=sk-xxxxxx (tempel API Key kamu di sini)

Catatan: Setiap pengguna baru biasanya mendapatkan saldo gratis yang cukup untuk ribuan percakapan (pada model gratis).

## Cara Menjalankan

1. Pastikan semua langkah instalasi selesai.

2. Jalankan aplikasi dengan perintah:
   streamlit run app.py

3. Browser akan otomatis terbuka ke http://localhost:8501

4. Login menggunakan username dan password portal akademik (SSO) kamu.

Selamat merencanakan semestermu!

## ⚠️ PENTING: Disclaimer

Aplikasi ini dibuat semata-mata untuk **tujuan edukasi dan pembelajaran** pengembangan perangkat lunak (educational purpose only).

- **API Tidak Resmi**: Aplikasi ini menggunakan API internal dari sistem akademik kampus secara *unofficial*. Penggunaan API ini tidak memiliki dukungan resmi dari pihak kampus.
- **Batasan Tanggung Jawab**: Pembuat aplikasi **TIDAK bertanggung jawab** atas segala risiko yang mungkin timbul, termasuk namun tidak terbatas pada: pemblokiran akun, kesalahan data, atau gangguan pada sistem akademik kampus.
- **Penggunaan Personal**: Segala aktivitas yang dilakukan menggunakan aplikasi ini menjadi tanggung jawab penuh pengguna masing-masing.

Harap gunakan aplikasi ini dengan bijak dan etika yang baik. Jangan gunakan untuk tujuan yang melanggar aturan kampus.
