import streamlit as st
import pandas as pd
import json
import re

from config import MAX_SKS
from krs_service import export_excel, filter_krs_data, search_dataframe, build_dataframe
from conflict_checker import find_conflicts
from state import get_selected, toggle_selection, save_session

def render_home_view(df: pd.DataFrame):
    col_title, col_sort = st.columns([8, 2])
    with col_title:
        st.subheader("📚 KRS UNSAM Selector")

    # Metrics
    selected_ids = get_selected()

    if "id_kelas_kuliah" in df.columns and len(selected_ids) > 0:
        selected_df_full = df[df["id_kelas_kuliah"].isin(selected_ids)]
        total_mk = len(selected_df_full)
        total_sks = int(selected_df_full["sks_mata_kuliah"].sum()) if "sks_mata_kuliah" in selected_df_full.columns else 0
    else:
        selected_df_full = pd.DataFrame()
        total_mk = 0
        total_sks = 0

    c1, c2, c3, c4 = st.columns([1, 1, 1, 2])
    c1.metric("Mata Kuliah", f"{total_mk}")
    delta_color = "normal" if total_sks <= MAX_SKS else "inverse"
    c2.metric("Total SKS", f"{total_sks}/{MAX_SKS}", delta=None, delta_color=delta_color)
    c3.metric("Sisa Kuota SKS", f"{max(MAX_SKS - total_sks, 0)}")
    with c4:
        st.progress(min(total_sks / MAX_SKS, 1.0))
        if total_mk > 0 and st.button("🔄 Reset Pilihan", use_container_width=True):
            st.session_state["selected"] = set()
            for key in list(st.session_state.keys()):
                if key.startswith("cb_"):
                    del st.session_state[key]
            save_session()
            st.rerun()

    # Peringatan over-SKS
    if total_sks > MAX_SKS:
        st.error(f"⚠️ Total SKS melebihi batas {MAX_SKS}! Hapus {total_sks - MAX_SKS} SKS atau lebih.")
    elif total_mk == 0:
        st.info("Belum ada mata kuliah dipilih. Centang kelas di daftar bawah.")

    st.divider()

    # Search & Filter
    with st.expander("🔍 Filter & Pencarian", expanded=True):
        col_filter1, col_filter2, col_filter3 = st.columns([1, 1, 2])
        semesters = sorted(df["semester"].astype(str).unique()) if "semester" in df.columns else []
        dosens = sorted(df["nama_dosen"].dropna().unique()) if "nama_dosen" in df.columns else []

        with col_filter1:
            sel_semester = st.multiselect("Semester", options=semesters, placeholder="Pilih Semester")
        with col_filter2:
            sel_dosen = st.multiselect("Dosen", options=dosens, placeholder="Pilih Dosen")
        with col_filter3:
            search_query = st.text_input("Search", placeholder="🔍 Cari...", label_visibility="visible")

        col_toggle = st.columns(1)[0]
        jam_desc = col_toggle.checkbox("Urutkan Jam (Sore → Pagi)", value=False, key="jam_toggle")

    # Export / Import Controls
    json_list_str = json.dumps(list(selected_ids)) if selected_ids else "[]"

    with st.expander("📤 Export / 📥 Import JSON & Excel", expanded=False):
        tab_export, tab_import = st.tabs(["📤 Export Data", "📥 Import JSON"])

        with tab_export:
            col_nim, col_actions = st.columns([1, 2])
            with col_nim:
                export_nim = st.text_input("Masukkan NIM (untuk format JSON)", value="NIM")

            formatted_json = f'selectedKrs-{export_nim}:"{json_list_str.replace(" ", "")}"'

            st.caption("Salin string di bawah ini untuk dibagikan:")
            st.code(formatted_json, language="text")

            if not selected_df_full.empty:
                excel_data = export_excel(selected_df_full)
                st.download_button(
                    "⬇️ Download Excel",
                    data=excel_data,
                    file_name=f"krs_{export_nim}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

        with tab_import:
            st.caption("Paste JSON (format `selectedKrs-NIM:\"[...]\"` atau raw `[\"...\"]`) untuk memuat pilihan.")
            import_str = st.text_area("Paste JSON String", height=100)

            if st.button("📥 Load Selection (Timpa Pilihan Saat Ini)"):
                if not import_str.strip():
                    st.warning("String kosong.")
                else:
                    try:
                        pattern = r'selectedKrs-.*:"(\[.*?\])"'
                        match = re.search(pattern, import_str)
                        if match:
                            raw_json = match.group(1)
                        else:
                            raw_json = import_str

                        imported_ids = json.loads(raw_json)
                        if isinstance(imported_ids, list):
                            imported_ids_str = set([str(x) for x in imported_ids])
                            st.session_state["selected"] = imported_ids_str

                            for key in list(st.session_state.keys()):
                                if key.startswith("cb_"):
                                    del st.session_state[key]
                            for cid in imported_ids_str:
                                st.session_state[f"cb_{cid}"] = True

                            st.success(f"Berhasil memuat {len(imported_ids_str)} mata kuliah! Checkbox otomatis diperbarui.")
                            save_session()
                            st.rerun()
                        else:
                            st.error("Format JSON tidak valid (harus berupa list).")
                    except Exception as e:
                        st.error(f"Gagal memuat JSON: {e}")

    # Apply Logic
    filtered_df = df.copy()
    filtered_df = filter_krs_data(filtered_df, semesters=sel_semester, dosens=sel_dosen)
    filtered_df = search_dataframe(filtered_df, search_query)
    if jam_desc:
        filtered_df = build_dataframe(filtered_df.to_dict('records'), jam_desc=True)

    # Conflicts
    if len(selected_ids) >= 2 and not selected_df_full.empty:
        conflicts = find_conflicts(selected_df_full)
        if conflicts:
            st.markdown(f"##### ⚠️ {len(conflicts)} Jadwal Bentrok")
            rows_html = ""
            for c in conflicts:
                rows_html += f"""<tr><td><b>{c['day']}</b></td><td><div style="font-weight:600; color:#ff7b7b">{c['course_a']}</div><div style="font-size:11px; opacity:0.8">{c['time_a']}</div></td><td style="color:#ff7b7b; text-align:center; vertical-align:middle">⚡</td><td><div style="font-weight:600; color:#ff7b7b">{c['course_b']}</div><div style="font-size:11px; opacity:0.8">{c['time_b']}</div></td></tr>"""
            st.markdown(f"""<table class="conflict-table"><thead><tr><th width="15%">Hari</th><th width="40%">Mata Kuliah A</th><th width="5%"></th><th width="40%">Mata Kuliah B</th></tr></thead><tbody>{rows_html}</tbody></table>""", unsafe_allow_html=True)

    # List
    st.write(f"#### 📋 Daftar Mata Kuliah ({len(filtered_df)})")

    def on_course_toggle(course_id):
        toggle_selection(course_id)

    for idx, row in filtered_df.iterrows():
        course_id = str(row["id_kelas_kuliah"])
        is_selected = course_id in selected_ids

        nama = row.get('nama_mata_kuliah', 'Unknown')
        kode = row.get('kode_mata_kuliah', '-')
        sks = row.get('sks_mata_kuliah', 0)
        kelas = row.get('nama_kelas_kuliah', '-')
        sem = row.get('semester', '-')
        dosen = row.get('nama_dosen', '-')
        hari = str(row.get('hari', '')).capitalize()
        jam_start = row["jam_mulai"].strftime("%H:%M") if pd.notna(row["jam_mulai"]) else "?"
        jam_end = row["jam_akhir"].strftime("%H:%M") if "jam_akhir" in row.index and pd.notna(row["jam_akhir"]) else "?"

        # None-safe: int(None) crash
        kuota = int(row.get('kuota') or 0)
        jumlah = int(row.get('jumlah') or 0)
        sisa = kuota - jumlah
        if sisa <= 0: quota_badge = "<span style='color:#f85149; font-weight:bold'>PENUH</span>"
        elif sisa <= 5: quota_badge = f"<span style='color:#d29922; font-weight:bold'>Sisa {sisa}</span>"
        else: quota_badge = f"<span style='color:#3fb950'>Sisa {sisa}</span>"

        c_check, c_details = st.columns([0.05, 0.95])
        with c_check:
            st.write("")
            st.checkbox("Select", value=is_selected, key=f"cb_{course_id}", label_visibility="collapsed", on_change=on_course_toggle, args=(course_id,))
        with c_details:
            st.markdown(f"""<div class="course-card"><div class="course-header">{nama} <span style="font-weight:400; color:#8b949e">({kode})</span> <span class="tag">SMT {sem}</span> <span class="tag">KLS {kelas}</span> <span class="tag">{sks} SKS</span></div><div class="course-meta"><span>🗓️ {hari}, {jam_start}–{jam_end}</span><span>👨‍🏫 {dosen}</span><span>{quota_badge}</span></div></div>""", unsafe_allow_html=True)

    # Summary
    if not selected_df_full.empty:
        st.divider()
        st.markdown("#### 📝 Ringkasan Pilihan")

        display_df = selected_df_full.copy()
        display_df['Mata Kuliah'] = display_df.apply(lambda x: f"{x.get('nama_mata_kuliah','')} ({x.get('kode_mata_kuliah','')})\nSMT {x.get('semester','')} - KLS {x.get('nama_kelas_kuliah','')}", axis=1)
        jam_akhir_ok = "jam_akhir" in display_df.columns
        display_df['Jadwal'] = display_df.apply(lambda x: f"{str(x.get('hari','')).capitalize()} {x['jam_mulai'].strftime('%H:%M')}-{x['jam_akhir'].strftime('%H:%M') if jam_akhir_ok and pd.notna(x.get('jam_akhir')) else ''}", axis=1)
        has_sks = "sks_mata_kuliah" in display_df.columns
        display_df['SKS'] = display_df['sks_mata_kuliah'] if has_sks else 0
        show_cols = ['Mata Kuliah', 'SKS', 'Jadwal'] if has_sks else ['Mata Kuliah', 'Jadwal']
        st.dataframe(display_df[show_cols], use_container_width=True, hide_index=True)

        # ── Beban SKS per hari (agar jadwal seimbang) ──
        st.markdown("##### ⚖️ Beban SKS per Hari")
        hari_order = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
        per_hari = display_df.groupby(display_df['hari'].astype(str).str.capitalize())['SKS'].sum().reindex(hari_order).dropna()
        if not per_hari.empty:
            chart_data = per_hari.reset_index()
            chart_data.columns = ["Hari", "SKS"]
            chart_data = chart_data.set_index("Hari")
            st.bar_chart(chart_data)
            cap = per_hari.max()
            st.caption(f"Hari terpadat: **{per_hari.idxmax()}** ({int(cap)} SKS)" if cap else "")
