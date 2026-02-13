import pandas as pd
from datetime import timedelta
from config import DAYS, SCHEDULE_START_HOUR, TIMETABLE_END_HOUR, TIMETABLE_CELL_HEIGHT, MINUTES_PER_SKS

def render_timetable_html(df: pd.DataFrame) -> str:
    """
    Generate an HTML string representing a weekly timetable grid.
    Expects df to have columns: 'hari', 'jam_mulai', 'jam_akhir', 'nama_mata_kuliah', 'nama_kelas_kuliah', 'nama_dosen', 'sks_mata_kuliah', 'id_kelas_kuliah'
    """

    # Configuration
    START_HOUR = SCHEDULE_START_HOUR
    END_HOUR = TIMETABLE_END_HOUR
    CELL_HEIGHT = TIMETABLE_CELL_HEIGHT

    # CSS
    css = f"""
    <style>
        .timetable-container {{
            display: grid;
            grid-template-columns: 50px repeat({len(DAYS)}, 1fr);
            grid-template-rows: 30px repeat({END_HOUR - START_HOUR}, {CELL_HEIGHT}px);
            gap: 1px;
            background-color: #30363d;
            border: 1px solid #30363d;
            border-radius: 6px;
            overflow-x: auto;
            margin-bottom: 20px;
        }}
        .tt-header {{
            background-color: #161b22;
            color: #e6edf3;
            font-weight: bold;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 13px;
            padding: 4px;
        }}
        .tt-time-col {{
            background-color: #161b22;
            color: #8b949e;
            font-size: 11px;
            display: flex;
            align-items: flex-start;
            justify-content: center;
            padding-top: 2px;
            grid-column: 1;
        }}
        .tt-cell {{
            background-color: #0d1117;
            /* Empty cells background */
        }}
        .tt-event {{
            position: relative;
            background-color: #1f6feb; /* Default Blue */
            color: white;
            border-radius: 4px;
            padding: 4px;
            font-size: 11px;
            overflow: hidden;
            display: flex;
            flex-direction: column;
            box-shadow: 0 1px 3px rgba(0,0,0,0.5);
            z-index: 10;
        }}
        .tt-event:hover {{
            z-index: 20;
            transform: scale(1.02);
            transition: all 0.1s;
        }}
        .tt-event-title {{
            font-weight: bold;
            line-height: 1.2;
            margin-bottom: 2px;
        }}
        .tt-event-meta {{
            font-size: 10px;
            opacity: 0.9;
        }}
    </style>
    """

    html = [css, '<div class="timetable-container">']

    # 1. Header Row (Day Names)
    html.append('<div class="tt-header" style="grid-column: 1; grid-row: 1">Jam</div>')
    for i, day in enumerate(DAYS):
        html.append(f'<div class="tt-header" style="grid-column: {i+2}; grid-row: 1">{day}</div>')

    # 2. Time Column (Left)
    for h in range(START_HOUR, END_HOUR):
        row_idx = h - START_HOUR + 2
        html.append(f'<div class="tt-time-col" style="grid-row: {row_idx}">{h:02d}:00</div>')

    # 3. Empty Grid Cells (Background)
    # We can omit this if the container bg is fine, but explicit cells might look better if we want borders.
    # For now, container bg handles the grid lines via gap.

    # 4. Events
    # We need to map Days to Column Indices (2 to 7)
    day_map = {d.lower(): i+2 for i, d in enumerate(DAYS)}

    if not df.empty:
        for idx, row in df.iterrows():
            day_str = str(row.get('hari', '')).capitalize()
            if day_str.lower() not in day_map:
                continue

            col_idx = day_map[day_str.lower()]

            start_time = row['jam_mulai'] # datetime
            if pd.isna(start_time): continue

            end_time = row.get('jam_akhir') # datetime
            # If end_time missing, assume SKS duration
            if pd.isna(end_time):
                sks = int(row.get('sks_mata_kuliah', 2))
                end_time = start_time + timedelta(minutes=sks * MINUTES_PER_SKS)

            # Calculate Grid Position
            start_hour = start_time.hour
            start_min = start_time.minute

            if start_hour < START_HOUR: start_hour = START_HOUR # Clamp

            base_row = start_hour - START_HOUR + 2
            minute_offset_px = (start_min / 60.0) * CELL_HEIGHT

            duration_minutes = (end_time - start_time).total_seconds() / 60
            height_px = (duration_minutes / 60.0) * CELL_HEIGHT

            # Generate style
            # Uses translation to shift down by minutes
            style = f"""
                grid-column: {col_idx};
                grid-row: {base_row};
                margin-top: {minute_offset_px}px;
                height: {height_px}px;
                background-color: {hash_color(row.get('nama_mata_kuliah', ''))};
            """

            # Content
            nama = row.get('nama_mata_kuliah', 'Unknown')
            kelas = row.get('nama_kelas_kuliah', '')
            ruang = row.get('ruang', '') # if avail
            time_str = f"{start_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}"

            html.append(f"""
            <div class="tt-event" style="{style}">
                <div class="tt-event-title">{nama}</div>
                <div class="tt-event-meta">{kelas} • {time_str}</div>
            </div>
            """)

    html.append('</div>')
    return "\n".join(html)

def hash_color(text):
    """Generate a consistent pastel color from text string."""
    hash_val = sum(ord(c) for c in text)
    # HSL: Hue based on hash, Saturation ~70%, Lightness ~35% (Dark mode friendly)
    hue = (hash_val * 137) % 360
    return f"hsl({hue}, 70%, 35%)"
