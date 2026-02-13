import streamlit as st
from dotenv import load_dotenv

# Load env before anything else
load_dotenv()

from config import MAX_SKS
from auth import login_sso
from krs_service import fetch_krs, build_dataframe
from state import (
    init_state, set_logged_in, logout, hard_reset,
    is_logged_in, get_krs_data, get_http_session
)

# Views
from views.home_view import render_home_view
from views.schedule_view import render_schedule_view
from views.compare_view import render_compare_view
from views.ai_view import render_ai_view

# ================= PAGE CONFIG =================
st.set_page_config(page_title="KRS UNSAM", layout="wide", page_icon="📚")
init_state()

# ================= CUSTOM CSS =================
st.markdown("""
<style>
    /* Compact Table Styling */
    .dataframe { font-size: 13px !important; }

    /* Conflict Table */
    .conflict-table {
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
        margin-bottom: 1rem;
        background-color: #2d1117;
        border: 1px solid #7d2a33;
        border-radius: 6px;
        overflow: hidden;
    }
    .conflict-table th {
        background-color: #4c1d23;
        color: #ff7b7b;
        padding: 8px 12px;
        text-align: left;
        font-size: 13px;
        font-weight: 600;
        border-bottom: 1px solid #7d2a33;
    }
    .conflict-table td {
        padding: 8px 12px;
        color: #e6edf3;
        border-bottom: 1px solid #4c1d23;
        font-size: 13px;
        vertical-align: top;
    }
    .conflict-table tr:last-child td { border-bottom: none; }

    /* Course Row Styling */
    .course-card {
        padding: 8px 0;
        border-bottom: 1px solid #30363d;
    }
    .course-card:hover {
        background-color: #161b22;
    }
    .course-header {
        font-size: 15px;
        font-weight: 600;
        margin-bottom: 2px;
        color: #e6edf3;
    }
    .course-meta {
        font-size: 12px;
        color: #8b949e;
        display: flex;
        gap: 12px;
        align-items: center;
        flex-wrap: wrap;
    }
    .tag {
        background: #21262d;
        padding: 1px 6px;
        border-radius: 4px;
        font-size: 11px;
        border: 1px solid #30363d;
    }

    /* Comparison Badge */
    .badge-nim {
        background: #1f6feb;
        color: white;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 11px;
        font-weight: bold;
    }

    /* Metrics */
    div[data-testid="stMetricValue"] { font-size: 20px !important; }

    /* Chat Messages */
    .stChatMessage {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════
#  LOGIN LOGIC
# ═══════════════════════════════════════════════
if not is_logged_in():
    st.title("📚 KRS UNSAM Viewer")
    st.caption("Login dengan akun SSO UNSAM. Sesi akan disimpan secara lokal.")

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("🔐 Login", use_container_width=True)

    if submitted:
        if not username or not password:
            st.error("Username dan password harus diisi!")
        else:
            try:
                with st.spinner("🔄 Login ke SSO..."):
                    http_session = login_sso(username, password)

                with st.spinner("📥 Mengambil data KRS..."):
                    raw_data = fetch_krs(http_session)

                set_logged_in(http_session, raw_data)
                st.rerun()

            except Exception as e:
                st.error(f"❌ {e}")

    st.stop()


# ═══════════════════════════════════════════════
#  MAIN APPLICATION LAYOUT
# ═══════════════════════════════════════════════
raw_data = get_krs_data()
df = build_dataframe(raw_data)

# Sidebar Navigation
with st.sidebar:
    st.title("Navigasi")
    page = st.radio("Pilih Mode", ["🏠 Pilih KRS", "📅 Jadwal Saya", "👥 Bandingkan Jadwal", "🤖 AI Assistant"])
    st.divider()

    st.caption("Aksi Akun")
    if st.button("🔄 Refresh Data", help="Ambil ulang data terbaru"):
        try:
            session = get_http_session()
            if session:
                with st.spinner("Mengambil data terbaru..."):
                    new_data = fetch_krs(session)
                    set_logged_in(session, new_data)
                    st.success("Data diperbarui!")
                    st.rerun()
            else:
                st.error("Sesi kadaluarsa.")
        except Exception as e:
            st.error(f"Gagal: {e}")

    if st.button("🚪 Logout", use_container_width=True):
        logout()
        st.rerun()

    st.write("")
    if st.button("🔴 Hard Reset", use_container_width=True, help="Hapus SEMUA data & logout"):
        hard_reset()
        st.rerun()

# ================= PAGES =================
if page == "🏠 Pilih KRS":
    render_home_view(df)

elif page == "📅 Jadwal Saya":
    render_schedule_view(df)

elif page == "👥 Bandingkan Jadwal":
    render_compare_view(df)

elif page == "🤖 AI Assistant":
    render_ai_view(df)

