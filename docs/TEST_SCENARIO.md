# 📋 Test Scenario Document
## Booking Validation — QA Technical Test

| Item | Detail |
|------|--------|
| **Dokumen** | Test Scenario & Test Case |
| **Versi** | 1.0 |
| **Tanggal** | 2026-06-04 |
| **Dibuat oleh** | QA Tester |
| **Status** | Active |

---

## 1. Ringkasan Permasalahan (Bug Summary)

Ditemukan dua buah bug kritis pada data booking yang tersimpan di database:

| # | Bug ID | Severity | Deskripsi |
|---|--------|----------|-----------|
| 1 | **BUG-001** | 🔴 Critical | Harga booking `BK/000001` tidak sesuai dengan harga schedule. Tersimpan `1.200.000`, seharusnya `1.000.000` |
| 2 | **BUG-002** | 🔴 Critical | Double booking — `BK/000001` dan `BK/000005` sama-sama membook venue 15 pada tanggal 2022-12-10 jam 09:00–11:00 |

### Data Aktual di Table Bookings

| id | Booking_id | venue_id | user_id | date | start_time | end_time | price (aktual) | price (seharusnya) | Status |
|----|------------|----------|---------|------|------------|----------|----------------|--------------------|--------|
| 1001 | BK/000001 | 15 | 12 | 2022-12-10 | 09:00:00 | 11:00:00 | 1.200.000 | **1.000.000** | ❌ Harga Salah |
| 1005 | BK/000005 | 15 | 12 | 2022-12-10 | 09:00:00 | 11:00:00 | 1.000.000 | 1.000.000 | ❌ Double Booking |

### Data Referensi di Table Venue Schedules

| id | venue_id | date | start_time | end_time | price |
|----|----------|------|------------|----------|-------|
| 11 | 15 | 2022-12-10 | 07:00:00 | 09:00:00 | 800.000 |
| **12** | **15** | **2022-12-10** | **09:00:00** | **11:00:00** | **1.000.000** |
| 13 | 15 | 2022-12-10 | 11:00:00 | 13:00:00 | 1.200.000 |

> **Root Cause Analysis:** BK/000001 tampaknya menggunakan harga dari slot 11:00–13:00 (id=13, harga 1.200.000) alih-alih slot yang benar 09:00–11:00 (id=12, harga 1.000.000). Kemungkinan bug terjadi pada logika pencarian price di backend saat proses booking.

---

## 2. Test Scope

```
IN SCOPE:
  ✅ Validasi kesesuaian harga booking dengan venue schedule
  ✅ Deteksi double booking (exact same slot)
  ✅ Deteksi overlap waktu antar booking
  ✅ Validasi integritas data schedule (gap, overlap)
  ✅ Edge case: harga negatif, waktu tidak valid, booking_id duplikat

OUT OF SCOPE:
  ❌ Pengujian UI / frontend
  ❌ Pengujian performa / load test
  ❌ Pengujian autentikasi pengguna
  ❌ Proses pembayaran / refund
```

---

## 3. Test Cases Matrix

### 🟥 TC-001: Validasi Kesesuaian Semua Harga Booking

| Field | Detail |
|-------|--------|
| **Test Case ID** | TC-001 |
| **Nama** | Semua harga booking harus sesuai dengan venue schedule |
| **Modul** | Price Validation |
| **Priority** | P1 – High |
| **Jenis** | Negative Test |

**Pre-condition:**
- Data booking tersedia di table `bookings`
- Data jadwal tersedia di table `venue_schedules`

**Test Steps:**
1. Ambil semua data booking dari table `bookings`
2. Untuk setiap booking, cari schedule yang cocok berdasarkan `venue_id`, `date`, `start_time`, `end_time`
3. Bandingkan `price` pada booking dengan `price` pada schedule yang cocok
4. Catat semua ketidaksesuaian

**Expected Result:** Semua `booking.price == schedule.price`  
**Actual Result:** BK/000001 memiliki harga 1.200.000 (schedule: 1.000.000) → ❌ FAIL  
**Status:** ❌ FAIL

---

### 🟥 TC-002: Validasi Harga Spesifik BK/000001

| Field | Detail |
|-------|--------|
| **Test Case ID** | TC-002 |
| **Nama** | Harga booking BK/000001 sesuai dengan schedule slot 09:00–11:00 |
| **Modul** | Price Validation |
| **Priority** | P1 – High |
| **Jenis** | Negative Test |

**Pre-condition:**
- Booking `BK/000001` tersedia
- Schedule id=12 (venue=15, date=2022-12-10, 09:00–11:00, price=1.000.000) tersedia

**Test Steps:**
1. Query booking dengan `booking_id = 'BK/000001'`
2. Dapatkan `venue_id=15`, `date=2022-12-10`, `start_time=09:00`, `end_time=11:00`
3. Query schedule berdasarkan data tersebut
4. Bandingkan `booking.price` dengan `schedule.price`

**Expected Result:** `booking.price == 1.000.000`  
**Actual Result:** `booking.price == 1.200.000` → ❌ FAIL  
**Status:** ❌ FAIL

---

### 🟨 TC-003: Booking Tidak Menggunakan Harga Slot Lain

| Field | Detail |
|-------|--------|
| **Test Case ID** | TC-003 |
| **Nama** | Harga booking tidak boleh menggunakan harga dari slot waktu yang berbeda |
| **Modul** | Price Validation |
| **Priority** | P2 – Medium |
| **Jenis** | Negative Test |

**Test Steps:**
1. Untuk setiap booking, ambil harga yang seharusnya dari schedule yang cocok
2. Verifikasi bahwa harga yang tersimpan bukan merupakan harga dari slot lain

**Expected Result:** Harga tidak berasal dari slot waktu yang berbeda  
**Actual Result:** BK/000001 menggunakan harga slot 11:00–13:00 → ❌ FAIL  
**Status:** ❌ FAIL

---

### 🟥 TC-004: Tidak Ada Double Booking (Slot Identik)

| Field | Detail |
|-------|--------|
| **Test Case ID** | TC-004 |
| **Nama** | Sistem tidak mengizinkan dua booking dengan venue, tanggal, dan slot waktu yang sama |
| **Modul** | Double Booking Detection |
| **Priority** | P1 – High |
| **Jenis** | Negative Test |

**Pre-condition:**
- Data booking tersedia di table `bookings`

**Test Steps:**
1. Group semua booking berdasarkan `(venue_id, date, start_time, end_time)`
2. Cek apakah ada grup yang memiliki lebih dari 1 booking
3. Catat semua pasangan booking yang konflik

**Expected Result:** Tidak ada slot dengan lebih dari 1 booking aktif  
**Actual Result:** Slot (venue=15, 2022-12-10, 09:00–11:00) memiliki 2 booking: BK/000001 & BK/000005 → ❌ FAIL  
**Status:** ❌ FAIL

---

### 🟥 TC-005: Tidak Ada Overlap Waktu Booking

| Field | Detail |
|-------|--------|
| **Test Case ID** | TC-005 |
| **Nama** | Tidak ada booking dengan waktu tumpang-tindih untuk venue yang sama |
| **Modul** | Double Booking Detection |
| **Priority** | P1 – High |
| **Jenis** | Negative Test |

**Test Steps:**
1. Untuk setiap pasangan booking dengan `venue_id` dan `date` yang sama
2. Cek apakah `a.start_time < b.end_time AND b.start_time < a.end_time` (kondisi overlap)

**Expected Result:** Tidak ada pasangan booking dengan waktu overlap  
**Actual Result:** BK/000001 dan BK/000005 memiliki waktu identik → ❌ FAIL  
**Status:** ❌ FAIL

---

### 🟥 TC-006: Maksimal 1 Booking Aktif Per Slot

| Field | Detail |
|-------|--------|
| **Test Case ID** | TC-006 |
| **Nama** | Setiap slot venue hanya boleh memiliki 1 booking aktif |
| **Modul** | Double Booking Detection |
| **Priority** | P1 – High |
| **Jenis** | Negative Test |

**Expected Result:** Count booking per slot ≤ 1  
**Actual Result:** Slot venue=15, 2022-12-10, 09:00–11:00 memiliki count = 2 → ❌ FAIL  
**Status:** ❌ FAIL

---

### 🟩 TC-007: Jadwal Tidak Memiliki Gap Waktu

| Field | Detail |
|-------|--------|
| **Test Case ID** | TC-007 |
| **Nama** | Slot jadwal dalam satu hari tidak boleh memiliki celah waktu |
| **Modul** | Schedule Integrity |
| **Priority** | P2 – Medium |
| **Jenis** | Positive Test |

**Test Steps:**
1. Sort semua schedule per venue per hari berdasarkan `start_time`
2. Cek apakah `slot[n].end_time == slot[n+1].start_time`

**Expected Result:** Tidak ada gap antar slot  
**Actual Result:** 07:00–09:00, 09:00–11:00, 11:00–13:00 (berkesinambungan) → ✅ PASS  
**Status:** ✅ PASS

---

### 🟩 TC-008: Jadwal Tidak Memiliki Overlap

| Field | Detail |
|-------|--------|
| **Test Case ID** | TC-008 |
| **Nama** | Slot jadwal tidak boleh overlap satu sama lain |
| **Modul** | Schedule Integrity |
| **Priority** | P2 – Medium |
| **Jenis** | Positive Test |

**Expected Result:** Tidak ada overlap antar slot jadwal  
**Actual Result:** Schedule valid, tidak ada overlap → ✅ PASS  
**Status:** ✅ PASS

---

### 🟩 TC-009: Setiap Booking Memiliki Schedule yang Valid

| Field | Detail |
|-------|--------|
| **Test Case ID** | TC-009 |
| **Nama** | Booking hanya boleh dibuat untuk slot yang terdaftar di schedule |
| **Modul** | Schedule Integrity |
| **Priority** | P1 – High |
| **Jenis** | Positive Test |

**Expected Result:** Semua booking memiliki matching schedule  
**Actual Result:** Semua booking cocok dengan schedule yang ada → ✅ PASS  
**Status:** ✅ PASS

---

### 🟩 TC-010: Harga Booking Tidak Boleh Nol atau Negatif

| Field | Detail |
|-------|--------|
| **Test Case ID** | TC-010 |
| **Nama** | Validasi harga booking > 0 |
| **Modul** | Edge Cases |
| **Priority** | P2 – Medium |
| **Jenis** | Positive Test |

**Expected Result:** Semua `price > 0`  
**Actual Result:** Semua harga positif → ✅ PASS  
**Status:** ✅ PASS

---

### 🟩 TC-011: Start Time Harus Lebih Awal dari End Time

| Field | Detail |
|-------|--------|
| **Test Case ID** | TC-011 |
| **Nama** | Validasi urutan waktu booking |
| **Modul** | Edge Cases |
| **Priority** | P2 – Medium |
| **Jenis** | Positive Test |

**Expected Result:** `start_time < end_time`  
**Actual Result:** Semua booking memiliki urutan waktu valid → ✅ PASS  
**Status:** ✅ PASS

---

### 🟩 TC-012: Booking ID Harus Unik

| Field | Detail |
|-------|--------|
| **Test Case ID** | TC-012 |
| **Nama** | Tidak ada booking_id yang duplikat |
| **Modul** | Edge Cases |
| **Priority** | P1 – High |
| **Jenis** | Positive Test |

**Expected Result:** Semua `booking_id` unik  
**Actual Result:** BK/000001 dan BK/000005 berbeda → ✅ PASS  
**Status:** ✅ PASS

---

## 4. Ringkasan Hasil Test

| Status | Jumlah | Test Case ID |
|--------|--------|-------------|
| ❌ FAIL | 6 | TC-001, TC-002, TC-003, TC-004, TC-005, TC-006 |
| ✅ PASS | 6 | TC-007, TC-008, TC-009, TC-010, TC-011, TC-012 |
| **Total** | **12** | |

> ⚠️ **6 dari 12 test case GAGAL** — Semua kegagalan berstatus **P1 (Critical/High)** yang berpotensi menyebabkan kerugian finansial (overcharge pengguna) dan konflik reservasi venue.

---

## 5. Rekomendasi Perbaikan

| # | Area | Rekomendasi |
|---|------|-------------|
| 1 | **Backend Logic** | Perbaiki logika pencarian harga saat booking — gunakan `WHERE venue_id=? AND date=? AND start_time=? AND end_time=?` untuk matching yang presisi |
| 2 | **Database Constraint** | Tambahkan `UNIQUE constraint` pada kolom `(venue_id, date, start_time, end_time)` di table bookings |
| 3 | **Validasi Aplikasi** | Tambahkan pengecekan ketersediaan slot sebelum menyimpan booking baru |
| 4 | **Data Correction** | Update harga BK/000001 menjadi 1.000.000 dan lakukan investigasi untuk menentukan booking mana yang valid (BK/000001 atau BK/000005) |
| 5 | **Regression Test** | Jalankan automation test ini pada setiap deployment untuk mencegah regresi |
