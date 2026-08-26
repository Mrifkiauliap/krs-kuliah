import pandas as pd
import requests
from io import BytesIO
from config import KRS_URL, HARI_ORDER


def fetch_krs(session: requests.Session) -> list[dict]:
    """Fetch raw KRS data from the mahasiswa API."""
    r = session.get(KRS_URL, timeout=30)
    r.raise_for_status()

    try:
        payload = r.json()
    except ValueError:
        raise Exception("Respons dari server bukan JSON. Sesi mungkin kadaluarsa, silakan login ulang.")

    data = payload.get("data")
    if not isinstance(data, list):
        raise Exception("Format data KRS tidak dikenali. API mungkin berubah.")

    return data


def build_dataframe(data: list[dict], jam_desc: bool = False) -> pd.DataFrame:
    """Convert raw KRS data into a sorted DataFrame."""
    if not data:
        return pd.DataFrame()

    df = pd.DataFrame(data)

    # Kolom wajib minimum
    required = ["hari", "jam_mulai"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise Exception(f"Data KRS tidak lengkap — kolom hilang: {', '.join(missing)}")

    # hari harus string dulu — API bisa kirim angka (mis. 1/2) yang bikin .str crash
    df["hari"] = df["hari"].astype(str).str.strip()
    df["hari_order"] = df["hari"].str.lower().map(HARI_ORDER).fillna(99)
    df["jam_mulai"] = pd.to_datetime(df["jam_mulai"], format="mixed", errors="coerce")

    # Parse jam_akhir
    if "jam_akhir" in df.columns:
        df["jam_akhir"] = pd.to_datetime(df["jam_akhir"], format="mixed")

    # Ensure sks is numeric
    if "sks_mata_kuliah" in df.columns:
        df["sks_mata_kuliah"] = pd.to_numeric(df["sks_mata_kuliah"], errors="coerce").fillna(0).astype(int)

    if "id_kelas_kuliah" in df.columns:
        df["id_kelas_kuliah"] = df["id_kelas_kuliah"].astype(str)

    df = df.sort_values(
        by=["hari_order", "jam_mulai"],
        ascending=[True, not jam_desc],
    )

    return df


def export_excel(df: pd.DataFrame) -> bytes:
    """Export DataFrame to Excel bytes."""
    buffer = BytesIO()
    drop_cols = [c for c in ["hari_order"] if c in df.columns]
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.drop(columns=drop_cols).to_excel(writer, index=False)
    return buffer.getvalue()


def search_dataframe(df: pd.DataFrame, query: str) -> pd.DataFrame:
    """Filter DataFrame rows that contain the search query (case-insensitive)."""
    if not query or df.empty:
        return df
    q = query.lower()
    # Gabungkan semua sel per baris jadi satu string.
    # str() eksplisit: aman untuk NaN, NaT, float, datetime (yang bikin join crash).
    text = df.apply(lambda row: " ".join(str(v) for v in row).lower(), axis=1)
    return df[text.str.contains(q, na=False)]


def filter_krs_data(df: pd.DataFrame, semesters: list = None, dosens: list = None) -> pd.DataFrame:
    """Filter DataFrame by specific Semester and Dosen values."""
    filtered = df.copy()

    if semesters and "semester" in filtered.columns:
        # Convert semester column to string just in case
        filtered = filtered[filtered["semester"].astype(str).isin(semesters)]

    if dosens and "nama_dosen" in filtered.columns:
        filtered = filtered[filtered["nama_dosen"].astype(str).isin(dosens)]

    return filtered


def get_courses_by_ids(df: pd.DataFrame, ids: list) -> pd.DataFrame:
    """Get rows where id_kelas_kuliah matches the given list of IDs."""
    if "id_kelas_kuliah" not in df.columns:
        return pd.DataFrame()
    return df[df["id_kelas_kuliah"].isin(ids)]
