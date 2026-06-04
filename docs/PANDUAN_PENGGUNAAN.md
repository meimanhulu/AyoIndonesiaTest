# 📖 Panduan Penggunaan — Booking Validation Automation Test

## Deskripsi

Script ini adalah automation test berbasis **Python + pytest** untuk memvalidasi integritas data booking di sistem reservasi venue. Dirancang untuk mendeteksi:

- ❌ **Harga booking tidak sesuai** dengan venue schedule
- ❌ **Double booking** pada slot waktu yang sama
- ❌ **Overlap waktu** antar booking
- ✅ **Integritas data** jadwal venue

---

## Prasyarat

| Kebutuhan | Versi Minimum |
|-----------|---------------|
| Python | 3.9+ |
| pip | 23.0+ |

Cek versi Python yang terinstal:
```bash
python --version
```

---

## Struktur Direktori

```
AyoIndonesiaTest/
├── docs/
│   ├── TEST_SCENARIO.md             # Dokumen test scenario & test cases
│   └── PANDUAN_PENGGUNAAN.md        # Panduan ini
├── tests/
│   ├── conftest.py                  # Konfigurasi global pytest
│   └── test_booking_validation.py   # Script utama automation test
├── pytest.ini                       # Konfigurasi pytest
├── requirements.txt                 # Daftar dependencies
└── README.md
```

---

## Langkah 1 — Buka Terminal di Direktori Proyek

Buka terminal (PowerShell / CMD) di VS Code, pastikan berada di:

```
c:\Users\GL\Documents\GitHub\AyoIndonesiaTest
```

> Di VS Code: gunakan menu **Terminal → New Terminal**, lalu terminal akan otomatis terbuka di direktori proyek yang aktif.

---

## Langkah 2 — (Opsional) Buat Virtual Environment

Disarankan menggunakan virtual environment agar dependencies terisolasi:

```powershell
# Buat virtual environment
python -m venv venv

# Aktifkan virtual environment (Windows PowerShell)
venv\Scripts\activate
```

Tanda berhasil: prompt berubah menjadi `(venv) PS C:\...>`

---

## Langkah 3 — Instalasi Dependencies

```powershell
pip install -r requirements.txt
```

Output yang diharapkan:
```
Successfully installed pytest-8.x.x pytest-html-4.x.x
```

---

## Langkah 4 — Menjalankan Test

> **Catatan:** Gunakan `python -m pytest` di Windows jika `pytest` tidak dikenali langsung.

### ▶ Jalankan Semua Test (Rekomendasi)

```powershell
python -m pytest -v --tb=short
```

### ▶ Hentikan di Kegagalan Pertama

```powershell
python -m pytest -x -v
```

### ▶ Jalankan Hanya Test Harga

```powershell
python -m pytest tests/test_booking_validation.py::TestPriceValidation -v
```

### ▶ Jalankan Hanya Test Double Booking

```powershell
python -m pytest tests/test_booking_validation.py::TestDoubleBookingDetection -v
```

### ▶ Generate Laporan HTML

```powershell
python -m pytest --html=report.html --self-contained-html
```

Laporan tersimpan di `report.html` — buka dengan browser untuk melihat hasil lengkap dengan visualisasi.

---

## Langkah 5 — Membaca Output

### Contoh Output saat Test GAGAL (kondisi bug saat ini):

```
========================= test session starts ==========================
platform win32 -- Python 3.x.x, pytest-8.x.x
collected 12 items

tests/test_booking_validation.py::TestPriceValidation::test_TC001 FAILED  [ 8%]
tests/test_booking_validation.py::TestPriceValidation::test_TC002 FAILED  [16%]
tests/test_booking_validation.py::TestPriceValidation::test_TC003 FAILED  [25%]
tests/test_booking_validation.py::TestDoubleBookingDetection::test_TC004 FAILED  [33%]
tests/test_booking_validation.py::TestDoubleBookingDetection::test_TC005 FAILED  [41%]
tests/test_booking_validation.py::TestDoubleBookingDetection::test_TC006 FAILED  [50%]
tests/test_booking_validation.py::TestScheduleIntegrity::test_TC007 PASSED  [58%]
tests/test_booking_validation.py::TestScheduleIntegrity::test_TC008 PASSED  [66%]
tests/test_booking_validation.py::TestScheduleIntegrity::test_TC009 PASSED  [75%]
tests/test_booking_validation.py::TestEdgeCases::test_TC010 PASSED  [83%]
tests/test_booking_validation.py::TestEdgeCases::test_TC011 PASSED  [91%]
tests/test_booking_validation.py::TestEdgeCases::test_TC012 PASSED  [100%]

====================== 6 failed, 6 passed in 0.17s =====================
```

### Contoh Pesan Error Detail:

```
AssertionError: [TC-001] GAGAL - Ditemukan ketidaksesuaian harga:
  • Booking BK/000001: harga tersimpan=1,200,000, harga seharusnya=1,000,000

AssertionError: [TC-004] GAGAL - Ditemukan 1 double booking:
  • BK/000001 ↔ BK/000005 (venue=15, 2022-12-10, 09:00:00-11:00:00)
```

### Output saat Semua Bug Diperbaiki:

```
========================= 12 passed in 0.10s ===========================
```

---

## Referensi Cepat

| Perintah | Fungsi |
|----------|--------|
| `python -m pytest -v` | Jalankan semua test dengan output verbose |
| `python -m pytest -x` | Berhenti di kegagalan pertama |
| `python -m pytest -k "price"` | Jalankan test yang mengandung kata "price" |
| `python -m pytest --html=report.html --self-contained-html` | Generate laporan HTML |
| `python -m pytest tests/test_booking_validation.py::TestDoubleBookingDetection` | Jalankan satu class test |

---

## Adaptasi ke Database Nyata

Saat ini, data di-*mock* langsung di dalam fixtures Python. Untuk menghubungkan ke database nyata:

1. Tambahkan library connector di `requirements.txt`:
   ```
   pymysql>=1.1.0      # untuk MySQL/MariaDB
   psycopg2>=2.9.0     # untuk PostgreSQL
   ```

2. Ganti fixtures di `conftest.py` dengan query database nyata:
   ```python
   import pymysql

   @pytest.fixture(scope="session")
   def db_connection():
       conn = pymysql.connect(
           host="localhost",
           user="your_user",
           password="your_password",
           database="your_db"
       )
       yield conn
       conn.close()

   @pytest.fixture
   def booking_data(db_connection):
       cursor = db_connection.cursor()
       cursor.execute("SELECT * FROM bookings")
       rows = cursor.fetchall()
       return [Booking(*row) for row in rows]
   ```

---

> **Tips CI/CD:** Jalankan automation test ini sebagai bagian dari pipeline (GitHub Actions, GitLab CI) untuk mendeteksi bug secara otomatis setiap kali ada perubahan kode.
