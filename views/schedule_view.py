import streamlit as st
import pandas as pd
from state import get_selected
from timetable_renderer import render_timetable_html
from ics_tool import create_ics

def render_schedule_view(df: pd.DataFrame):
    st.subheader("🗓️ Visual Timetable")

    selected_ids = get_selected()
    if not selected_ids:
        st.info("⚠️ Belum ada mata kuliah yang dipilih. Silakan pilih di menu **Pilih KRS**.")
    else:
        # Get Data
        my_df = df[df["id_kelas_kuliah"].isin(selected_ids)].copy()

        # Controls
        col_dl, col_blank = st.columns([2, 5])
        with col_dl:
            ics_str = create_ics(my_df)
            st.download_button(
                "📅 Download .ICS (Calendar)",
                data=ics_str,
                file_name="jadwal_krs.ics",
                mime="text/calendar",
                help="Import file ini ke Google Calendar atau Outlook"
            )

        st.divider()

        # Render HTML Grid
        html_code = render_timetable_html(my_df)
        st.components.v1.html(html_code, height=800, scrolling=True)
