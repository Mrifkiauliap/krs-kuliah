# Pembelajaran Eksperimen: Dockerisasi KRS Viewer

Dokumentasi eksperimen penambahan dukungan containerization menggunakan Docker dan Docker Compose pada project KRS Viewer.

## Eksperimen 1: Dockerisasi Aplikasi Streamlit

### Deskripsi
Membuat file konfigurasi Docker (`Dockerfile`, `docker-compose.yml`, dan `.dockerignore`) untuk menjalankan aplikasi Streamlit secara terisolasi dan persisten.

### Konfigurasi yang Dibuat

1. **[Dockerfile](file:///d:/Project/test_py/unsam_krs/Dockerfile)**
   - Menggunakan base image `python:3.11-slim` demi efisiensi ukuran image.
   - Menginstal `build-essential` dan `curl` untuk keperluan kompilasi package (misal `lxml`) serta healthcheck container.
   - Mengatur variabel lingkungan Streamlit (`STREAMLIT_SERVER_PORT=8501`, `STREAMLIT_SERVER_ADDRESS=0.0.0.0`, `STREAMLIT_SERVER_HEADLESS=true`).
   - Menambahkan healthcheck endpoint (`http://localhost:8501/_stcore/health`) untuk memantau status aplikasi.

2. **[docker-compose.yml](file:///d:/Project/test_py/unsam_krs/docker-compose.yml)**
   - Mendefinisikan service `krs-viewer`.
   - Melakukan port binding `8501:8501`.
   - Menggunakan mount volume untuk file database SQLite `sessions.sqlite` dan `.env` agar sesi login serta kunci API AI tetap persisten di host machine.

3. **[.dockerignore](file:///d:/Project/test_py/unsam_krs/.dockerignore)**
   - Mengabaikan virtual environment (`.venv`), temporary files, git folders, database lokal, dan file konfigurasi Docker itu sendiri dari build context untuk mempercepat proses build.

### Hasil & Cara Menjalankan
Aplikasi dapat dijalankan dengan perintah:
```bash
docker compose up -d --build
```
Aplikasi akan tersedia di `http://localhost:8501`. Sesi login dan data pilihan KRS akan tetap tersimpan di host pada file `sessions.sqlite`.
