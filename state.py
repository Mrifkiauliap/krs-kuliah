import streamlit as st
import pickle
import sqlite3
from datetime import datetime

DB_FILE = "sessions.sqlite"

def _get_conn():
    """Get SQLite connection."""
    return sqlite3.connect(DB_FILE)

def init_db():
    try:
        conn = _get_conn()
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY DEFAULT 'default',
                data BLOB,
                updated_at TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"DB Init Error: {e}")

def _load_from_db():
    """Load the single session from SQLite."""
    try:
        conn = _get_conn()
        c = conn.cursor()
        c.execute("SELECT data FROM sessions WHERE id = 'default'")
        row = c.fetchone()
        conn.close()
        if row:
            return pickle.loads(row[0])
    except Exception as e:
        print(f"DB Load Error: {e}")
    return None

def _save_to_db(data: dict):
    """Save session data to the single SQLite row."""
    try:
        conn = _get_conn()
        c = conn.cursor()
        blob = pickle.dumps(data)
        now = datetime.now().isoformat()
        c.execute("""
            INSERT INTO sessions (id, data, updated_at)
            VALUES ('default', ?, ?)
            ON CONFLICT(id) DO UPDATE SET
            data=excluded.data, updated_at=excluded.updated_at
        """, (blob, now))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"DB Save Error: {e}")

def _clear_db():
    """Delete the single session row."""
    try:
        conn = _get_conn()
        c = conn.cursor()
        c.execute("DELETE FROM sessions WHERE id = 'default'")
        conn.commit()
        conn.close()
    except Exception:
        pass

def init_state():
    """Initialize session state, restoring from SQLite if available."""
    init_db()

    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False
        st.session_state["krs_data"] = None
        st.session_state["http_session"] = None
        st.session_state["selected"] = set()
        st.session_state["chat_history"] = []

        # Try restoring from DB
        data = _load_from_db()
        if data:
            # Restore persistent user data
            st.session_state["selected"] = data.get("selected", set())
            st.session_state["chat_history"] = data.get("chat_history", [])

            # Restore login state
            st.session_state["logged_in"] = data.get("logged_in", False)

            if st.session_state["logged_in"]:
                st.session_state["http_session"] = data.get("http_session")
                st.session_state["krs_data"] = data.get("krs_data")

def set_logged_in(http_session, krs_data):
    st.session_state["logged_in"] = True
    st.session_state["http_session"] = http_session
    st.session_state["krs_data"] = krs_data
    if "selected" not in st.session_state:
        st.session_state["selected"] = set()
    save_session()

def save_session():
    """Persist current session state to SQLite."""
    _save_to_db({
        "logged_in": st.session_state.get("logged_in", False),
        "http_session": st.session_state.get("http_session"),
        "krs_data": st.session_state.get("krs_data"),
        "selected": st.session_state.get("selected", set()),
        "chat_history": st.session_state.get("chat_history", []),
    })

def logout():
    """Logout but keep user data (selected, chat) in DB."""
    # Clear session/auth data
    st.session_state["logged_in"] = False
    st.session_state["http_session"] = None
    st.session_state["krs_data"] = None

    # Save the 'logged_out' state but keep 'selected' and 'chat_history'
    save_session()

def hard_reset():
    """Hard reset: clear ALL data and delete from DB."""
    for key in ["logged_in", "krs_data", "http_session", "selected", "chat_history"]:
        if key in st.session_state:
            del st.session_state[key]
    st.session_state["logged_in"] = False
    _clear_db()

def is_logged_in() -> bool:
    return st.session_state.get("logged_in", False)

def get_http_session():
    return st.session_state.get("http_session")

def get_krs_data():
    return st.session_state.get("krs_data")

def get_selected() -> set:
    return st.session_state.get("selected", set())

def toggle_selection(index):
    selected = get_selected()
    if index in selected:
        selected.discard(index)
    else:
        selected.add(index)
    st.session_state["selected"] = selected
    save_session()
