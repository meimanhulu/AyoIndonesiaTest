"""
conftest.py - Konfigurasi global pytest
Berisi shared fixtures, markers, custom terminal summary,
auto-save result ke .md, dan auto-generate HTML report ke results/
"""

import os
import pytest
from datetime import datetime

# Timestamp dibuat sekali saat sesi dimulai, dipakai untuk .md dan .html
_RUN_TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")


# ============================================================
# MARKERS
# ============================================================

def pytest_configure(config):
    """Register custom markers dan set HTML report path secara otomatis."""
    config.addinivalue_line(
        "markers", "price_validation: Test validasi harga booking"
    )
    config.addinivalue_line(
        "markers", "double_booking: Test deteksi double booking"
    )
    config.addinivalue_line(
        "markers", "schedule_integrity: Test integritas data jadwal"
    )
    config.addinivalue_line(
        "markers", "edge_case: Test edge cases dan boundary conditions"
    )

    # Auto-set HTML report output ke results/ dengan timestamp
    # Hanya aktif jika plugin pytest-html terinstall
    if hasattr(config, "option") and hasattr(config.option, "htmlpath"):
        results_dir = os.path.normpath(
            os.path.join(os.path.dirname(__file__), "..", "results")
        )
        os.makedirs(results_dir, exist_ok=True)
        html_filename = f"result_{_RUN_TIMESTAMP}.html"
        config.option.htmlpath = os.path.join(results_dir, html_filename)
        config.option.self_contained_html = True


# ============================================================
# DIAGNOSTIC KNOWLEDGE BASE
# ============================================================

DIAGNOSTICS = {
    "test_TC001_all_booking_prices_match_schedule": {
        "root_cause": "Harga pada table bookings tidak sinkron dengan harga di table venue_schedules.",
        "fix": "Pastikan query pengambilan harga saat booking menggunakan filter: "
               "WHERE venue_id=? AND date=? AND start_time=? AND end_time=? (4 kolom, bukan sebagian).",
    },
    "test_TC002_booking_BK000001_price_is_correct": {
        "root_cause": "BK/000001 menyimpan harga 1.200.000 padahal slot 09:00–11:00 berharga 1.000.000. "
                      "Kemungkinan sistem mengambil harga dari row schedule yang salah (off-by-one).",
        "fix": "Periksa logika pencarian schedule_id saat booking dibuat. "
               "Harga harus diambil dari schedule yang time-nya PERSIS cocok, bukan terdekat.",
    },
    "test_TC003_booking_price_should_not_use_adjacent_slot_price": {
        "root_cause": "Harga BK/000001 (1.200.000) cocok dengan slot 11:00–13:00, bukan slot yang dibooking (09:00–11:00). "
                      "Indikasi bug: sistem mengambil slot berikutnya alih-alih slot yang sesuai.",
        "fix": "Tambahkan validasi: setelah harga diambil, verifikasi bahwa schedule_id yang digunakan "
               "memiliki start_time dan end_time yang identik dengan waktu booking.",
    },
    "test_TC004_no_double_booking_exact_same_slot": {
        "root_cause": "Dua booking (BK/000001 & BK/000005) memiliki venue_id, date, start_time, end_time yang sama. "
                      "Sistem tidak menolak booking kedua meskipun slot sudah terisi.",
        "fix": "Tambahkan pengecekan sebelum INSERT: "
               "SELECT COUNT(*) FROM bookings WHERE venue_id=? AND date=? AND start_time=? AND end_time=? "
               "Jika count > 0, tolak booking baru dengan error 'Slot sudah terisi'.",
    },
    "test_TC005_no_overlapping_bookings_for_same_venue": {
        "root_cause": "BK/000001 dan BK/000005 memiliki waktu yang tumpang-tindih (identik) pada venue yang sama. "
                      "Tidak ada mekanisme overlap check di sistem.",
        "fix": "Implementasikan overlap detection: tolak booking baru jika "
               "new.start_time < existing.end_time AND existing.start_time < new.end_time "
               "pada venue dan tanggal yang sama.",
    },
    "test_TC006_each_venue_slot_has_max_one_active_booking": {
        "root_cause": "Slot (venue=15, 2022-12-10, 09:00–11:00) memiliki 2 booking aktif sekaligus. "
                      "Tidak ada UNIQUE constraint di level database.",
        "fix": "Tambahkan UNIQUE constraint di database: "
               "ALTER TABLE bookings ADD CONSTRAINT uq_venue_slot "
               "UNIQUE (venue_id, date, start_time, end_time); "
               "Constraint ini mencegah double booking di level DB, bukan hanya di level aplikasi.",
    },
}


# ============================================================
# HELPER: SIMPAN HASIL KE FILE MARKDOWN
# ============================================================

def _save_result_to_markdown(failed_tests, passed_tests, run_time: str):
    """Tulis hasil test ke file .md di folder results/."""

    # Buat folder results/ jika belum ada
    results_dir = os.path.join(
        os.path.dirname(__file__),  # direktori tests/
        "..",                       # naik ke root proyek
        "results",
    )
    results_dir = os.path.normpath(results_dir)
    os.makedirs(results_dir, exist_ok=True)

    # Nama file: result_YYYYMMDD_HHMMSS.md
    filename = f"result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    filepath = os.path.join(results_dir, filename)

    total = len(failed_tests) + len(passed_tests)
    passed_count = len(passed_tests)
    failed_count = len(failed_tests)
    status_icon = "✅ SEMUA LULUS" if failed_count == 0 else "❌ ADA BUG TERDETEKSI"

    lines = []

    # ── Header ──────────────────────────────────────────────
    lines.append("# Booking Validation - Test Result")
    lines.append("")
    lines.append(f"| Item | Detail |")
    lines.append(f"|------|--------|")
    lines.append(f"| **Tanggal & Waktu** | {run_time} |")
    overall = "[PASS] SEMUA LULUS" if failed_count == 0 else "[FAIL] ADA BUG TERDETEKSI"
    lines.append(f"| **Status Keseluruhan** | {overall} |")
    lines.append(f"| **Total Test** | {total} |")
    lines.append(f"| **Passed** | PASS {passed_count} |")
    lines.append(f"| **Failed** | {'FAIL ' + str(failed_count) if failed_count > 0 else str(failed_count)} |")
    lines.append("")

    # ── Tabel hasil per test ─────────────────────────────────
    lines.append("## Hasil Per Test Case")
    lines.append("")
    lines.append("| # | Test Case | Modul | Status |")
    lines.append("|---|-----------|-------|--------|")

    all_tests = [(r, "PASSED") for r in passed_tests] + [(r, "FAILED") for r in failed_tests]
    all_tests.sort(key=lambda x: x[0].nodeid)

    for idx, (report, status) in enumerate(all_tests, start=1):
        tc_name = report.nodeid.split("::")[-1]
        module = report.nodeid.split("::")[-2].replace("Test", "")
        icon = "PASS" if status == "PASSED" else "FAIL"
        lines.append(f"| {idx} | `{tc_name}` | {module} | {icon} |")

    lines.append("")

    # ── Root cause & rekomendasi (hanya untuk yang failed) ──
    if failed_tests:
        lines.append("## Root Cause and Rekomendasi Perbaikan")
        lines.append("")

        for i, report in enumerate(failed_tests, start=1):
            test_fn = report.nodeid.split("::")[-1]
            diag = DIAGNOSTICS.get(test_fn)

            lines.append(f"### [{i}] `{test_fn}`")
            lines.append("")

            if diag:
                lines.append(f"**Root Cause:**  ")
                lines.append(f"{diag['root_cause']}")
                lines.append("")
                lines.append(f"**Rekomendasi Perbaikan:**  ")
                lines.append(f"{diag['fix']}")
            else:
                lines.append("**Root Cause:** Lihat traceback pytest untuk detail.")

            lines.append("")
            lines.append("---")
            lines.append("")

        # ── Kesimpulan ───────────────────────────────────────
        lines.append("## Kesimpulan")
        lines.append("")
        lines.append(f"**{failed_count} bug kritis ditemukan** pada data booking. Prioritas perbaikan:")
        lines.append("")
        lines.append("1. Perbaiki logika pencarian harga (price lookup) di backend.")
        lines.append("2. Tambahkan `UNIQUE constraint` di database untuk mencegah double booking.")
        lines.append("3. Implementasikan overlap check sebelum booking disimpan.")
        lines.append("")

    else:
        lines.append("## Kesimpulan")
        lines.append("")
        lines.append("✅ Semua validasi lulus. Tidak ada masalah harga maupun double booking yang terdeteksi.")
        lines.append("")

    lines.append("---")
    lines.append(f"_Report di-generate otomatis oleh pytest pada {run_time}_")

    with open(filepath, "w", encoding="utf-8", errors="replace") as f:
        f.write("\n".join(lines))

    return filepath


# ============================================================
# CUSTOM TERMINAL SUMMARY HOOK
# ============================================================

def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """
    Dijalankan otomatis setelah semua test selesai.
    1. Tampilkan diagnostic report di terminal
    2. Simpan hasil ke results/result_YYYYMMDD_HHMMSS.md
    """
    failed_tests = terminalreporter.stats.get("failed", [])
    passed_tests = terminalreporter.stats.get("passed", [])

    total = len(failed_tests) + len(passed_tests)
    passed_count = len(passed_tests)
    failed_count = len(failed_tests)
    run_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # ── Terminal: Header ─────────────────────────────────────
    terminalreporter.write_sep("=", "BOOKING VALIDATION — DIAGNOSTIC REPORT", bold=True)
    terminalreporter.write_line("")
    terminalreporter.write_line(f"  Total Test  : {total}")
    terminalreporter.write_line(f"  Passed      : {passed_count}  ✓", green=True)

    if failed_count > 0:
        terminalreporter.write_line(
            f"  Failed      : {failed_count}  ✗  ← Bug terdeteksi, perlu tindakan!", red=True
        )
    else:
        terminalreporter.write_line(
            f"  Failed      : {failed_count}  — Semua test lulus.", green=True
        )
    terminalreporter.write_line("")

    # ── Terminal: Root cause per kegagalan ───────────────────
    if failed_tests:
        terminalreporter.write_sep("-", "ROOT CAUSE & REKOMENDASI PERBAIKAN", bold=True)
        terminalreporter.write_line("")

        for i, report in enumerate(failed_tests, start=1):
            test_fn = report.nodeid.split("::")[-1]
            diag = DIAGNOSTICS.get(test_fn)

            terminalreporter.write_line(
                f"  [{i}] {report.nodeid.split('::')[-2]} › {test_fn}",
                bold=True, red=True,
            )
            if diag:
                terminalreporter.write_line(f"      Root Cause  : {diag['root_cause']}")
                terminalreporter.write_line(f"      Perbaikan   : {diag['fix']}")
            else:
                terminalreporter.write_line("      Root Cause  : Lihat traceback di atas.")
            terminalreporter.write_line("")

        terminalreporter.write_sep("-", "KESIMPULAN", bold=True)
        terminalreporter.write_line("")
        terminalreporter.write_line(f"  {failed_count} bug kritis ditemukan pada data booking.", red=True)
        terminalreporter.write_line("  Prioritas perbaikan:")
        terminalreporter.write_line("    1. Perbaiki logika pencarian harga (price lookup) di backend.")
        terminalreporter.write_line("    2. Tambahkan UNIQUE constraint di database.")
        terminalreporter.write_line("    3. Implementasikan overlap check sebelum booking disimpan.")
        terminalreporter.write_line("")
    else:
        terminalreporter.write_sep("-", "KESIMPULAN", bold=True)
        terminalreporter.write_line("")
        terminalreporter.write_line(
            "  ✓ Semua validasi lulus. Tidak ada bug terdeteksi.", green=True
        )
        terminalreporter.write_line("")

    # ── Simpan ke file .md ───────────────────────────────────
    try:
        saved_path = _save_result_to_markdown(failed_tests, passed_tests, run_time)
        terminalreporter.write_sep("-", "RESULT SAVED", bold=True)
        terminalreporter.write_line("")
        terminalreporter.write_line(f"  >> Hasil tersimpan di: {saved_path}", green=True)
        terminalreporter.write_line("")
    except Exception as e:
        terminalreporter.write_line(f"  ⚠ Gagal menyimpan result: {e}", yellow=True)

    terminalreporter.write_sep("=", "", bold=True)
