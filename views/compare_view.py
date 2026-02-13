import streamlit as st
import pandas as pd
import json
import re

from state import get_selected
from krs_service import get_courses_by_ids, build_dataframe
from config import DAYS, SCHEDULE_START_HOUR, SCHEDULE_END_HOUR, MINUTES_PER_SKS

SLOT_MINUTES = 15  # Granularity for free time calculation
MIN_FREE_BLOCK = 60  # Minimum free block length (minutes) to display


def _collect_busy_slots(comparison_data: list, days: list, start_hour: int, end_hour: int) -> set:
    """Build a set of busy (day_idx, slot_idx) from all schedules."""
    busy = set()
    for item in comparison_data:
        for _, row in item["df"].iterrows():
            day_str = str(row.get("hari", "")).capitalize()
            if day_str not in days:
                continue
            d_idx = days.index(day_str)

            s_time = row["jam_mulai"]
            if pd.isna(s_time):
                continue

            e_time = row.get("jam_akhir")
            if pd.isna(e_time):
                sks = int(row.get("sks_mata_kuliah", 2))
                e_time = s_time + pd.Timedelta(minutes=sks * MINUTES_PER_SKS)

            start_min = (s_time.hour - start_hour) * 60 + s_time.minute
            end_min = (e_time.hour - start_hour) * 60 + e_time.minute

            for m in range(start_min, end_min, SLOT_MINUTES):
                busy.add((d_idx, m // SLOT_MINUTES))

    return busy


def _find_free_ranges(busy_slots: set, days: list, start_hour: int, end_hour: int) -> list[dict]:
    """Find contiguous free blocks >= MIN_FREE_BLOCK across all days."""
    total_slots = (end_hour - start_hour) * 60 // SLOT_MINUTES
    free_ranges = []

    for d_idx, day in enumerate(days):
        block_start = None
        duration = 0

        for s in range(total_slots):
            if (d_idx, s) not in busy_slots:
                if block_start is None:
                    block_start = s
                duration += SLOT_MINUTES
            else:
                if block_start is not None and duration >= MIN_FREE_BLOCK:
                    free_ranges.append(_make_range(day, block_start, duration, start_hour))
                block_start = None
                duration = 0

        # End-of-day leftover
        if block_start is not None and duration >= MIN_FREE_BLOCK:
            free_ranges.append(_make_range(day, block_start, duration, start_hour))

    return free_ranges


def _make_range(day: str, slot_start: int, duration: int, base_hour: int) -> dict:
    """Convert slot indices to a readable time range dict."""
    start_min = slot_start * SLOT_MINUTES
    end_min = start_min + duration
    return {
        "day": day,
        "start": f"{base_hour + start_min // 60:02d}:{start_min % 60:02d}",
        "end": f"{base_hour + end_min // 60:02d}:{end_min % 60:02d}",
        "duration": duration,
    }


def _render_schedule_card(row, badges_html: str):
    """Render a single course card with owner badges."""
    nama = row.get("nama_mata_kuliah", "-")
    kelas = row.get("nama_kelas_kuliah", "-")
    hari = row.get("hari", "").capitalize()
    jam_start = row["jam_mulai"].strftime("%H:%M")
    jam_end = row["jam_akhir"].strftime("%H:%M") if pd.notna(row.get("jam_akhir")) else "?"

    st.markdown(f"""
    <div style="background:#161b22; padding:10px 14px; border-radius:6px; margin-bottom:8px; border:1px solid #30363d">
        <div style="display:flex; justify-content:space-between; align-items:center">
            <div>
                <div style="font-weight:bold; color:#e6edf3">{nama}
                    <span style="font-weight:normal; color:#8b949e">({kelas})</span>
                </div>
                <div style="font-size:13px; color:#8b949e; margin-top:2px">
                    🗓️ {hari}, {jam_start}–{jam_end}
                </div>
            </div>
            <div style="text-align:right">{badges_html}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def _owner_badge(name: str) -> str:
    """Generate colored HTML badge for an owner."""
    if "SAYA" in name:
        color = "#1f6feb"
    elif "NIM" in name:
        color = "#238636"
    else:
        color = "#6e7681"
    return f"<span style='background:{color}; color:white; padding:2px 8px; border-radius:12px; font-size:11px; margin-right:4px'>{name}</span>"


# ─── Main View ───

def render_compare_view(df: pd.DataFrame):
    st.subheader("👥 Bandingkan Jadwal Teman")
    st.caption("Paste data KRS temanmu (format: `selectedKrs-NIM:\"[...]\"`).")

    input_text = st.text_area(
        "Input Data JSON", height=120,
        placeholder='selectedKrs-2301001:"["uuid1","uuid2"]"\nselectedKrs-2301002:"["uuidA","uuidB"]"'
    )

    if not input_text:
        return

    # ── Parse Input ──
    pattern = r'selectedKrs-(\w+):"(\[.*?\])"'
    matches = re.findall(pattern, input_text)

    if not matches:
        st.warning("Format tidak valid. Pastikan formatnya `selectedKrs-NIM:\"[...]\"`")
        return

    st.success(f"✅ Ditemukan **{len(matches)}** data mahasiswa.")

    # ── Build comparison_data ──
    comparison_data = []

    my_selected = get_selected()
    if my_selected and "id_kelas_kuliah" in df.columns:
        my_df = df[df["id_kelas_kuliah"].isin(my_selected)].copy()
        comparison_data.append({"name": "SAYA", "df": my_df})

    for nim, json_str in matches:
        try:
            course_ids = json.loads(json_str)
            if isinstance(course_ids, list):
                friend_df = get_courses_by_ids(df, course_ids)
                comparison_data.append({"name": f"NIM {nim}", "df": friend_df})
        except Exception as e:
            st.error(f"Gagal parse NIM {nim}: {e}")

    if not comparison_data:
        return

    # ── Combined Schedule ──
    st.divider()
    combined_rows = []
    for item in comparison_data:
        for _, row in item["df"].iterrows():
            row_dict = row.to_dict()
            row_dict["Owners"] = item["name"]
            combined_rows.append(row_dict)

    if not combined_rows:
        st.info("Belum ada mata kuliah yang dipilih.")
        return

    comp_df = pd.DataFrame(combined_rows)

    if "id_kelas_kuliah" in comp_df.columns:
        aggs = {
            "Owners": lambda x: list(x),
            "nama_mata_kuliah": "first",
            "kode_mata_kuliah": "first",
            "nama_kelas_kuliah": "first",
            "hari": "first",
            "jam_mulai": "first",
            "jam_akhir": "first",
            "nama_dosen": "first",
            "semester": "first",
            "hari_order": "first",
        }
        valid_aggs = {k: v for k, v in aggs.items() if k in comp_df.columns}
        grouped = comp_df.groupby("id_kelas_kuliah").agg(valid_aggs).reset_index()
    else:
        grouped = comp_df

    grouped = build_dataframe(grouped.to_dict("records"))

    st.write("#### 🗓️ Jadwal Gabungan")
    for _, row in grouped.iterrows():
        badges_html = "".join(_owner_badge(o) for o in row["Owners"])
        _render_schedule_card(row, badges_html)

    # ── Free Time Finder ──
    st.divider()
    st.markdown("### 🤝 Waktu Kosong Bersama")

    days = DAYS[:5]  # Mon-Fri
    busy_slots = _collect_busy_slots(comparison_data, days, SCHEDULE_START_HOUR, SCHEDULE_END_HOUR)
    free_ranges = _find_free_ranges(busy_slots, days, SCHEDULE_START_HOUR, SCHEDULE_END_HOUR)

    if free_ranges:
        st.write(f"Ditemukan **{len(free_ranges)}** blok waktu kosong (≥ 1 jam) dimana **SEMUA** orang free.")

        cols = st.columns(3)
        for i, slot in enumerate(free_ranges):
            hours = slot["duration"] // 60
            mins = slot["duration"] % 60
            dur_str = f"{hours} jam" + (f" {mins} menit" if mins else "")
            with cols[i % 3]:
                st.success(f"**{slot['day']}**\n\n🕒 {slot['start']} – {slot['end']}\n\n⏱️ {dur_str}")
    else:
        st.warning("Tidak ditemukan waktu kosong bersama ≥ 1 jam.")
