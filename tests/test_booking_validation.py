"""
========================================================
Booking Validation Automation Test Suite
========================================================
Framework : pytest
Author    : QA Tester
Date      : 2026-06-04
Studi Kasus: Deteksi harga booking tidak sesuai & double booking

Masalah yang dideteksi:
  [BUG-001] Harga booking BK/000001 tidak sesuai dengan schedule_price
             (tersimpan 1200000, seharusnya 1000000 untuk slot 09:00-11:00)
  [BUG-002] Double booking - BK/000001 & BK/000005 menggunakan venue & slot waktu yang sama
"""

import pytest
from datetime import datetime, time, date
from typing import List, Optional
from dataclasses import dataclass, field


# ============================================================
# DATA MODELS
# ============================================================

@dataclass
class Booking:
    id: int
    booking_id: str
    venue_id: int
    user_id: int
    date: date
    start_time: time
    end_time: time
    price: int


@dataclass
class VenueSchedule:
    id: int
    venue_id: int
    date: date
    start_time: time
    end_time: time
    price: int


# ============================================================
# FIXTURES - Simulasi data dari database
# ============================================================

@pytest.fixture
def booking_data() -> List[Booking]:
    """
    Simulasi data dari table 'bookings'.
    Merepresentasikan kondisi buggy yang ada di production.
    """
    return [
        Booking(
            id=1001,
            booking_id="BK/000001",
            venue_id=15,
            user_id=12,
            date=date(2022, 12, 10),
            start_time=time(9, 0, 0),
            end_time=time(11, 0, 0),
            price=1_200_000,  # BUG: seharusnya 1_000_000
        ),
        Booking(
            id=1005,
            booking_id="BK/000005",
            venue_id=15,
            user_id=12,
            date=date(2022, 12, 10),
            start_time=time(9, 0, 0),
            end_time=time(11, 0, 0),
            price=1_000_000,  # BUG: double booking dengan BK/000001
        ),
    ]


@pytest.fixture
def schedule_data() -> List[VenueSchedule]:
    """
    Simulasi data dari table 'venue_schedules'.
    Ini adalah data referensi harga yang benar.
    """
    return [
        VenueSchedule(
            id=11,
            venue_id=15,
            date=date(2022, 12, 10),
            start_time=time(7, 0, 0),
            end_time=time(9, 0, 0),
            price=800_000,
        ),
        VenueSchedule(
            id=12,
            venue_id=15,
            date=date(2022, 12, 10),
            start_time=time(9, 0, 0),
            end_time=time(11, 0, 0),
            price=1_000_000,
        ),
        VenueSchedule(
            id=13,
            venue_id=15,
            date=date(2022, 12, 10),
            start_time=time(11, 0, 0),
            end_time=time(13, 0, 0),
            price=1_200_000,
        ),
    ]


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def find_schedule(
    schedules: List[VenueSchedule],
    venue_id: int,
    booking_date: date,
    start_time: time,
    end_time: time,
) -> Optional[VenueSchedule]:
    """Cari jadwal yang cocok dengan kriteria booking."""
    for s in schedules:
        if (
            s.venue_id == venue_id
            and s.date == booking_date
            and s.start_time == start_time
            and s.end_time == end_time
        ):
            return s
    return None


def detect_double_bookings(bookings: List[Booking]) -> List[tuple]:
    """
    Deteksi double booking: dua booking atau lebih dengan
    venue_id, date, start_time, end_time yang sama.
    Mengembalikan list pasangan (booking_a, booking_b) yang konflik.
    """
    conflicts = []
    for i in range(len(bookings)):
        for j in range(i + 1, len(bookings)):
            a, b = bookings[i], bookings[j]
            if (
                a.venue_id == b.venue_id
                and a.date == b.date
                and a.start_time == b.start_time
                and a.end_time == b.end_time
            ):
                conflicts.append((a, b))
    return conflicts


def detect_time_overlap(bookings: List[Booking]) -> List[tuple]:
    """
    Deteksi overlap waktu (tidak harus persis sama, tapi tumpang-tindih)
    untuk venue dan tanggal yang sama.
    """
    conflicts = []
    for i in range(len(bookings)):
        for j in range(i + 1, len(bookings)):
            a, b = bookings[i], bookings[j]
            if a.venue_id != b.venue_id or a.date != b.date:
                continue
            # Cek overlap: a mulai sebelum b selesai DAN b mulai sebelum a selesai
            if a.start_time < b.end_time and b.start_time < a.end_time:
                conflicts.append((a, b))
    return conflicts


# ============================================================
# TEST SCENARIOS
# ============================================================

class TestPriceValidation:
    """
    TC-001 ~ TC-003: Validasi kesesuaian harga booking dengan schedule
    """

    def test_TC001_all_booking_prices_match_schedule(
        self, booking_data, schedule_data
    ):
        """
        TC-001: Setiap booking harus memiliki harga yang sesuai
                dengan venue schedule yang berlaku.
        Expected: Semua harga booking == harga di schedule
        """
        mismatches = []
        for booking in booking_data:
            matched_schedule = find_schedule(
                schedule_data,
                booking.venue_id,
                booking.date,
                booking.start_time,
                booking.end_time,
            )
            assert matched_schedule is not None, (
                f"[TC-001] Tidak ditemukan schedule untuk booking {booking.booking_id} "
                f"(venue={booking.venue_id}, date={booking.date}, "
                f"{booking.start_time}-{booking.end_time})"
            )
            if booking.price != matched_schedule.price:
                mismatches.append(
                    f"Booking {booking.booking_id}: "
                    f"harga tersimpan={booking.price:,}, "
                    f"harga seharusnya={matched_schedule.price:,}"
                )

        assert not mismatches, (
            "[TC-001] GAGAL - Ditemukan ketidaksesuaian harga:\n"
            + "\n".join(f"  • {m}" for m in mismatches)
        )

    def test_TC002_booking_BK000001_price_is_correct(
        self, booking_data, schedule_data
    ):
        """
        TC-002: Validasi spesifik harga untuk booking BK/000001
        Expected: price = 1.000.000 (sesuai slot 09:00-11:00)
        """
        booking = next(
            (b for b in booking_data if b.booking_id == "BK/000001"), None
        )
        assert booking is not None, "Booking BK/000001 tidak ditemukan di database"

        matched = find_schedule(
            schedule_data,
            booking.venue_id,
            booking.date,
            booking.start_time,
            booking.end_time,
        )
        assert matched is not None, (
            f"Schedule untuk BK/000001 tidak ditemukan "
            f"(venue=15, date=2022-12-10, 09:00-11:00)"
        )
        assert booking.price == matched.price, (
            f"[TC-002] Harga BK/000001 tidak sesuai! "
            f"Tersimpan: {booking.price:,}, Seharusnya: {matched.price:,}"
        )

    def test_TC003_booking_price_should_not_use_adjacent_slot_price(
        self, booking_data, schedule_data
    ):
        """
        TC-003: Harga booking tidak boleh menggunakan harga slot lain
                (misal: slot 09:00-11:00 menggunakan harga slot 11:00-13:00)
        Expected: Tidak ada booking dengan harga slot yang salah
        """
        for booking in booking_data:
            matched = find_schedule(
                schedule_data,
                booking.venue_id,
                booking.date,
                booking.start_time,
                booking.end_time,
            )
            if matched is None:
                continue

            # Cari semua schedule lain (bukan slot booking ini) untuk venue yang sama
            other_schedules = [
                s for s in schedule_data
                if s.venue_id == booking.venue_id
                and s.date == booking.date
                and not (s.start_time == booking.start_time and s.end_time == booking.end_time)
            ]
            wrong_prices = [
                s for s in other_schedules if s.price == booking.price and matched.price != booking.price
            ]
            assert not wrong_prices, (
                f"[TC-003] Booking {booking.booking_id} menggunakan harga "
                f"dari slot yang salah! "
                f"Harga {booking.price:,} cocok dengan slot lain, bukan slot booking."
            )


class TestDoubleBookingDetection:
    """
    TC-004 ~ TC-006: Deteksi double booking dan konflik waktu
    """

    def test_TC004_no_double_booking_exact_same_slot(self, booking_data):
        """
        TC-004: Tidak boleh ada dua booking dengan venue_id, date,
                start_time, dan end_time yang persis sama (exact double booking).
        Expected: Tidak ada double booking
        """
        conflicts = detect_double_bookings(booking_data)
        conflict_details = [
            f"  • {a.booking_id} ↔ {b.booking_id} "
            f"(venue={a.venue_id}, {a.date}, {a.start_time}-{a.end_time})"
            for a, b in conflicts
        ]
        assert not conflicts, (
            f"[TC-004] GAGAL - Ditemukan {len(conflicts)} double booking:\n"
            + "\n".join(conflict_details)
        )

    def test_TC005_no_overlapping_bookings_for_same_venue(self, booking_data):
        """
        TC-005: Tidak boleh ada booking dengan waktu yang tumpang-tindih
                (overlap) untuk venue dan tanggal yang sama.
        Expected: Tidak ada overlap waktu
        """
        conflicts = detect_time_overlap(booking_data)
        conflict_details = [
            f"  • {a.booking_id} ({a.start_time}-{a.end_time}) ↔ "
            f"{b.booking_id} ({b.start_time}-{b.end_time})"
            for a, b in conflicts
        ]
        assert not conflicts, (
            f"[TC-005] GAGAL - Ditemukan {len(conflicts)} overlap waktu:\n"
            + "\n".join(conflict_details)
        )

    def test_TC006_each_venue_slot_has_max_one_active_booking(self, booking_data):
        """
        TC-006: Setiap slot waktu pada venue tertentu maksimal hanya
                boleh memiliki 1 booking aktif.
        Expected: Jumlah booking per slot <= 1
        """
        slot_count: dict = {}
        for b in booking_data:
            key = (b.venue_id, b.date, b.start_time, b.end_time)
            slot_count[key] = slot_count.get(key, []) + [b.booking_id]

        violations = {
            k: v for k, v in slot_count.items() if len(v) > 1
        }
        assert not violations, (
            "[TC-006] GAGAL - Slot yang memiliki lebih dari 1 booking:\n"
            + "\n".join(
                f"  • venue={k[0]}, date={k[1]}, {k[2]}-{k[3]}: {v}"
                for k, v in violations.items()
            )
        )


class TestScheduleIntegrity:
    """
    TC-007 ~ TC-009: Validasi integritas data schedule
    """

    def test_TC007_schedule_has_no_time_gap(self, schedule_data):
        """
        TC-007: Jadwal untuk satu venue pada satu hari tidak boleh
                memiliki celah waktu (gap) antar slot.
        Expected: end_time slot sebelumnya == start_time slot berikutnya
        """
        venue_dates = set((s.venue_id, s.date) for s in schedule_data)
        gaps = []
        for vd in venue_dates:
            slots = sorted(
                [s for s in schedule_data if (s.venue_id, s.date) == vd],
                key=lambda s: s.start_time,
            )
            for i in range(len(slots) - 1):
                if slots[i].end_time != slots[i + 1].start_time:
                    gaps.append(
                        f"venue={vd[0]}, date={vd[1]}: "
                        f"gap antara {slots[i].end_time} dan {slots[i+1].start_time}"
                    )
        assert not gaps, "[TC-007] Ditemukan gap pada jadwal:\n" + "\n".join(f"  • {g}" for g in gaps)

    def test_TC008_schedule_has_no_overlap(self, schedule_data):
        """
        TC-008: Jadwal tidak boleh memiliki slot waktu yang tumpang-tindih.
        Expected: Tidak ada overlap antar slot jadwal
        """
        venue_dates = set((s.venue_id, s.date) for s in schedule_data)
        overlaps = []
        for vd in venue_dates:
            slots = sorted(
                [s for s in schedule_data if (s.venue_id, s.date) == vd],
                key=lambda s: s.start_time,
            )
            for i in range(len(slots)):
                for j in range(i + 1, len(slots)):
                    a, b = slots[i], slots[j]
                    if a.start_time < b.end_time and b.start_time < a.end_time:
                        overlaps.append(f"slot {a.id} ({a.start_time}-{a.end_time}) overlap dengan slot {b.id} ({b.start_time}-{b.end_time})")
        assert not overlaps, "[TC-008] Overlap pada jadwal:\n" + "\n".join(f"  • {o}" for o in overlaps)

    def test_TC009_booking_must_match_existing_schedule_slot(
        self, booking_data, schedule_data
    ):
        """
        TC-009: Setiap booking harus memiliki jadwal yang terdaftar.
                Booking tanpa jadwal yang valid tidak boleh ada.
        Expected: Semua booking memiliki schedule yang cocok
        """
        bookings_without_schedule = []
        for booking in booking_data:
            matched = find_schedule(
                schedule_data,
                booking.venue_id,
                booking.date,
                booking.start_time,
                booking.end_time,
            )
            if matched is None:
                bookings_without_schedule.append(
                    f"{booking.booking_id} (venue={booking.venue_id}, "
                    f"{booking.date}, {booking.start_time}-{booking.end_time})"
                )
        assert not bookings_without_schedule, (
            "[TC-009] Booking tanpa schedule yang valid:\n"
            + "\n".join(f"  • {b}" for b in bookings_without_schedule)
        )


class TestEdgeCases:
    """
    TC-010 ~ TC-012: Edge cases dan boundary conditions
    """

    def test_TC010_booking_price_must_be_positive(self, booking_data):
        """
        TC-010: Harga booking tidak boleh nol atau negatif.
        Expected: price > 0
        """
        invalid = [b for b in booking_data if b.price <= 0]
        assert not invalid, (
            "[TC-010] Booking dengan harga tidak valid (<=0):\n"
            + "\n".join(f"  • {b.booking_id}: price={b.price}" for b in invalid)
        )

    def test_TC011_booking_start_time_before_end_time(self, booking_data):
        """
        TC-011: start_time booking harus lebih awal dari end_time.
        Expected: start_time < end_time
        """
        invalid = [b for b in booking_data if b.start_time >= b.end_time]
        assert not invalid, (
            "[TC-011] Booking dengan waktu tidak valid:\n"
            + "\n".join(
                f"  • {b.booking_id}: {b.start_time} >= {b.end_time}"
                for b in invalid
            )
        )

    def test_TC012_booking_id_is_unique(self, booking_data):
        """
        TC-012: Setiap booking_id harus unik dalam sistem.
        Expected: Tidak ada booking_id yang duplikat
        """
        booking_ids = [b.booking_id for b in booking_data]
        duplicates = [bid for bid in set(booking_ids) if booking_ids.count(bid) > 1]
        assert not duplicates, (
            "[TC-012] booking_id yang duplikat: " + ", ".join(duplicates)
        )
