import pandas as pd
from datetime import datetime, timedelta
from config import DAYS_WEEKDAY, MINUTES_PER_SKS, SEMESTER_WEEKS


def create_ics(df: pd.DataFrame) -> str:
    """Generate an ICS (iCalendar) string from the selected courses DataFrame."""
    if df.empty:
        return ""

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//KRS UNSAM//ID",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
    ]

    today = datetime.now().date()

    for _, row in df.iterrows():
        hari_str = str(row.get("hari", "")).lower()
        if hari_str not in DAYS_WEEKDAY:
            continue

        target_weekday = DAYS_WEEKDAY[hari_str]
        current_weekday = today.weekday()

        # Calculate days until next occurrence
        days_ahead = target_weekday - current_weekday
        if days_ahead <= 0:
            days_ahead += 7

        start_date = today + timedelta(days=days_ahead)

        if pd.isna(row["jam_mulai"]):
            continue

        s_time = row["jam_mulai"].time()
        dt_start = datetime.combine(start_date, s_time)

        # End time
        if "jam_akhir" in row and pd.notna(row["jam_akhir"]):
            e_time = row["jam_akhir"].time()
            dt_end = datetime.combine(start_date, e_time)
        else:
            sks = int(row.get("sks_mata_kuliah", 2))
            dt_end = dt_start + timedelta(minutes=sks * MINUTES_PER_SKS)

        fmt = "%Y%m%dT%H%M%S"
        summary = f"{row.get('nama_mata_kuliah', 'Kuliah')} ({row.get('nama_kelas_kuliah', '?')})"
        description = f"Dosen: {row.get('nama_dosen', '-')}\\nSKS: {row.get('sks_mata_kuliah', '-')}"
        uid = f"{row.get('id_kelas_kuliah', dt_start.timestamp())}@krsunsam"

        lines.append("BEGIN:VEVENT")
        lines.append(f"DTSTART:{dt_start.strftime(fmt)}")
        lines.append(f"DTEND:{dt_end.strftime(fmt)}")
        lines.append(f"SUMMARY:{summary}")
        lines.append(f"DESCRIPTION:{description}")
        lines.append(f"RRULE:FREQ=WEEKLY;COUNT={SEMESTER_WEEKS}")
        lines.append(f"UID:{uid}")
        lines.append("END:VEVENT")

    lines.append("END:VCALENDAR")

    # ICS spec (RFC 5545) requires CRLF line endings
    return "\r\n".join(lines)
