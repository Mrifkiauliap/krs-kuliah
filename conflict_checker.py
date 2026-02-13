import pandas as pd
from datetime import timedelta
from config import MINUTES_PER_SKS


def _get_end_time(row: pd.Series) -> pd.Timestamp:
    """Get the end time for a course. Uses jam_selesai if available,
    otherwise estimates from jam_mulai + (sks * MINUTES_PER_SKS)."""
    if "jam_akhir" in row.index and pd.notna(row.get("jam_akhir")):
        return row["jam_akhir"]

    sks = int(row.get("sks_mata_kuliah", 2))
    return row["jam_mulai"] + timedelta(minutes=sks * MINUTES_PER_SKS)


def _times_overlap(start_a, end_a, start_b, end_b) -> bool:
    """Check if two time ranges overlap."""
    return start_a < end_b and start_b < end_a


def find_conflicts(selected_courses_df: pd.DataFrame) -> list[dict]:
    """Find schedule conflicts among selected courses.

    Returns a list of dicts: {
        'course_a': str,
        'course_b': str,
        'day': str,
        'time_a': str,
        'time_b': str,
    }
    """
    if len(selected_courses_df) < 2:
        return []

    selected = selected_courses_df.copy()
    conflicts = []

    rows = list(selected.iterrows())

    for i in range(len(rows)):
        idx_a, row_a = rows[i]
        day_a = str(row_a["hari"]).lower()
        start_a = row_a["jam_mulai"]
        end_a = _get_end_time(row_a)

        for j in range(i + 1, len(rows)):
            idx_b, row_b = rows[j]
            day_b = str(row_b["hari"]).lower()

            # Different day = no conflict
            if day_a != day_b:
                continue

            start_b = row_b["jam_mulai"]
            end_b = _get_end_time(row_b)

            if _times_overlap(start_a, end_a, start_b, end_b):
                # Get a display name for the course
                name_col = None
                for col in ["nama_mata_kuliah", "nama_mk", "matakuliah"]:
                    if col in row_a.index:
                        name_col = col
                        break

                name_a = row_a[name_col] if name_col else f"Matkul #{idx_a}"
                name_b = row_b[name_col] if name_col else f"Matkul #{idx_b}"

                fmt = "%H:%M"
                conflicts.append({
                    "course_a": str(name_a),
                    "course_b": str(name_b),
                    "day": str(row_a["hari"]).capitalize(),
                    "time_a": f"{start_a.strftime(fmt)}–{end_a.strftime(fmt)}",
                    "time_b": f"{start_b.strftime(fmt)}–{end_b.strftime(fmt)}",
                })

    return conflicts
