# 📋 Booking Validation — QA Technical Test

> **Studi Kasus:** Deteksi harga booking tidak sesuai & double booking pada sistem reservasi venue.

## 🐛 Bug yang Ditemukan

| Bug ID | Severity | Deskripsi |
|--------|----------|-----------|
| **BUG-001** | 🔴 Critical | Harga `BK/000001` tersimpan **Rp 1.200.000**, seharusnya **Rp 1.000.000** (slot 09:00–11:00) |
| **BUG-002** | 🔴 Critical | Double booking — `BK/000001` & `BK/000005` memakai venue 15 di slot waktu yang sama |

### Data Booking (Kondisi Buggy)

| id | Booking_id | venue_id | date | start_time | end_time | price (aktual) | price (seharusnya) | Status |
|----|------------|----------|------|------------|----------|----------------|--------------------|--------|
| 1001 | BK/000001 | 15 | 2022-12-10 | 09:00:00 | 11:00:00 | 1.200.000 | **1.000.000** | ❌ Harga Salah |
| 1005 | BK/000005 | 15 | 2022-12-10 | 09:00:00 | 11:00:00 | 1.000.000 | 1.000.000 | ❌ Double Booking |

### Data Venue Schedule (Referensi Harga yang Benar)

| id | venue_id | date | start_time | end_time | price |
|----|----------|------|------------|----------|-------|
| 11 | 15 | 2022-12-10 | 07:00:00 | 09:00:00 | 800.000 |
| **12** | **15** | **2022-12-10** | **09:00:00** | **11:00:00** | **1.000.000** |
| 13 | 15 | 2022-12-10 | 11:00:00 | 13:00:00 | 1.200.000 |

---

## 🧪 Test Suite

**Framework:** Python + pytest  
**Total Test Cases:** 12  

| Kategori | TC | Deskripsi | Hasil |
|----------|----|-----------|-------|
| Price Validation | TC-001 | Semua harga booking sesuai schedule | ❌ FAIL |
| Price Validation | TC-002 | Harga BK/000001 = Rp 1.000.000 | ❌ FAIL |
| Price Validation | TC-003 | Booking tidak pakai harga slot lain | ❌ FAIL |
| Double Booking | TC-004 | Tidak ada double booking (slot identik) | ❌ FAIL |
| Double Booking | TC-005 | Tidak ada overlap waktu | ❌ FAIL |
| Double Booking | TC-006 | Max 1 booking aktif per slot | ❌ FAIL |
| Schedule Integrity | TC-007 | Jadwal tidak ada gap waktu | ✅ PASS |
| Schedule Integrity | TC-008 | Jadwal tidak ada overlap | ✅ PASS |
| Schedule Integrity | TC-009 | Booking harus punya schedule valid | ✅ PASS |
| Edge Cases | TC-010 | Harga booking > 0 | ✅ PASS |
| Edge Cases | TC-011 | start_time < end_time | ✅ PASS |
| Edge Cases | TC-012 | Booking ID unik | ✅ PASS |

> **Hasil eksekusi:** `6 failed, 6 passed` — Bug berhasil terdeteksi otomatis ✅

---

## 🚀 Cara Menjalankan Test

### Prasyarat
- Python 3.9+

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Jalankan Semua Test

```bash
python -m pytest -v --tb=short
```

### Generate Laporan HTML

```bash
python -m pytest --html=report.html --self-contained-html
```

Buka `report.html` di browser untuk melihat hasil lengkap dengan visualisasi.

### Contoh Output

```
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

========================= 6 failed, 6 passed in 0.18s =========================
```

---

## 📁 Struktur Proyek

```
AyoIndonesiaTest/
├── docs/
│   ├── TEST_SCENARIO.md             ← Dokumen test scenario lengkap (TC-001~TC-012)
│   └── PANDUAN_PENGGUNAAN.md        ← Panduan instalasi & penggunaan detail
├── tests/
│   ├── conftest.py                  ← Konfigurasi global pytest
│   └── test_booking_validation.py   ← Script automation test utama
├── pytest.ini                       ← Konfigurasi test runner
├── requirements.txt                 ← Dependencies (pytest, pytest-html)
└── README.md                        ← Dokumen ini
```

📄 Dokumentasi lengkap tersedia di:
- [Test Scenario Document](docs/TEST_SCENARIO.md) — Detail setiap test case, pre-condition, steps, expected & actual result
- [Panduan Penggunaan](docs/PANDUAN_PENGGUNAAN.md) — Instalasi, perintah lengkap, adaptasi ke database nyata

---

## 🔧 Rekomendasi Perbaikan

| # | Area | Rekomendasi |
|---|------|-------------|
| 1 | **Backend Logic** | Perbaiki query pencarian harga: `WHERE venue_id=? AND date=? AND start_time=? AND end_time=?` |
| 2 | **Database Constraint** | Tambahkan `UNIQUE (venue_id, date, start_time, end_time)` di table bookings |
| 3 | **Validasi Aplikasi** | Cek ketersediaan slot sebelum menyimpan booking baru |
| 4 | **Data Correction** | Update harga BK/000001 → 1.000.000; investigasi booking mana yang valid |
| 5 | **Regression Test** | Integrasikan test ini ke CI/CD pipeline |
