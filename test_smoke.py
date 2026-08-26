"""Smoke test: pastikan pipeline data KRS tak crash pada data kotor (NaN, None, float, kolom hilang).

Jalankan: python test_smoke.py
"""
import pandas as pd

from krs_service import build_dataframe, search_dataframe, filter_krs_data
import conflict_checker, ics_tool, timetable_renderer, ai_assistant

RAW = [
    {"id_kelas_kuliah": "1", "hari": "Senin", "jam_mulai": "2026-01-01T08:00:00",
     "jam_akhir": "2026-01-01T09:40:00", "nama_mata_kuliah": "Matematika",
     "kode_mata_kuliah": "MAT101", "sks_mata_kuliah": 3, "nama_kelas_kuliah": "A",
     "nama_dosen": "Dr X", "semester": 3, "ruang": "R1", "kuota": None, "jumlah": None},
    {"id_kelas_kuliah": "2", "hari": "Senin", "jam_mulai": "2026-01-01T09:00:00",
     "jam_akhir": None, "nama_mata_kuliah": "Fisika", "kode_mata_kuliah": "FIS101",
     "sks_mata_kuliah": 3, "nama_kelas_kuliah": "B", "nama_dosen": "Dr Y",
     "semester": 3, "ruang": "R2", "kuota": 40.5, "jumlah": 0},
]

# Kolom wajib minimum (hari, jam_mulai) dan beberapa kolom opsional hilang
RAW_MIN = [
    {"id_kelas_kuliah": "1", "hari": "Senin", "jam_mulai": "2026-01-01T08:00:00",
     "nama_mata_kuliah": "Matematika", "sks_mata_kuliah": 3},
    {"id_kelas_kuliah": "2", "hari": "Rabu", "jam_mulai": "2026-01-01T10:00:00",
     "nama_mata_kuliah": "Kimia", "sks_mata_kuliah": 2},
]


def test_full_pipeline():
    df = build_dataframe(RAW)
    assert len(df) == 2
    assert search_dataframe(df, "fisika").__len__() == 1
    assert search_dataframe(df, "dr y").__len__() == 1
    assert search_dataframe(df, "").__len__() == 2
    assert search_dataframe(df, "zzz").empty

    sel = df[df["id_kelas_kuliah"] == "1"]
    assert conflict_checker.find_conflicts(sel) == []
    assert "VEVENT" in ics_tool.create_ics(df)
    assert "timetable-container" in timetable_renderer.render_timetable_html(df)
    assert "Matematika" in ai_assistant.build_catalog_summary(df)
    assert len(filter_krs_data(df, semesters=["3"])) == 2


def test_minimal_columns():
    df = build_dataframe(RAW_MIN)
    assert len(df) == 2
    # Kolom opsional hilang: semester, dosen, kode, jam_akhir, kuota, jumlah
    assert filter_krs_data(df, semesters=["1"], dosens=["X"]).__len__() == 2
    assert search_dataframe(df, "kimia").__len__() == 1
    assert conflict_checker.find_conflicts(df) == []
    assert "VEVENT" in ics_tool.create_ics(df)
    assert "Matematika" in ai_assistant.build_catalog_summary(df)


def test_numeric_day():
    df = build_dataframe([{"id_kelas_kuliah": "1", "hari": 1,
                           "jam_mulai": "2026-01-01T08:00:00",
                           "nama_mata_kuliah": "X", "sks_mata_kuliah": 2}])
    assert str(df.iloc[0]["hari"]) == "1"
    assert search_dataframe(df, "x").__len__() == 1


def test_empty():
    assert build_dataframe([]).empty
    assert search_dataframe(pd.DataFrame(), "x").empty
    assert conflict_checker.find_conflicts(pd.DataFrame()) == []
    assert ics_tool.create_ics(pd.DataFrame()) == ""
    assert ai_assistant.build_catalog_summary(pd.DataFrame()) == ""


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            fn()
            print(f"PASS {name}")
    print("ALL PASSED")
