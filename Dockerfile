# Gunakan image Python slim sebagai base image untuk efisiensi ukuran
FROM python:3.11-slim

# Set working directory di dalam container
WORKDIR /app

# Install system dependencies yang mungkin dibutuhkan oleh lxml atau packages lainnya
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Salin file requirements.txt terlebih dahulu agar Docker cache layer bekerja optimal
COPY requirements.txt .

# Install dependencies Python
RUN pip install --no-cache-dir -r requirements.txt

# Salin seluruh kode aplikasi ke dalam container
COPY . .

# Expose port yang digunakan oleh Streamlit
EXPOSE 8501

# Konfigurasi Streamlit agar berjalan dengan benar di dalam container
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_HEADLESS=true

# Healthcheck untuk memastikan Streamlit berjalan dengan baik
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Jalankan aplikasi Streamlit
CMD ["streamlit", "run", "app.py"]
