import pandas as pd
import requests
from io import BytesIO
from config import KRS_URL, HARI_ORDER


def fetch_krs(session: requests.Session) -> list[dict]:
    """Fetch raw KRS data from the mahasiswa API."""
    r = session.get(KRS_URL)
    r.raise_for_status()
    return r.json()["data"]


def build_dataframe(data: list[dict], jam_desc: bool = False) -> pd.DataFrame:
    """Convert raw KRS data into a sorted DataFrame."""
    df = pd.DataFrame(data)

    df["hari_order"] = df["hari"].str.lower().map(HARI_ORDER)
    df["jam_mulai"] = pd.to_datetime(df["jam_mulai"])

    # Parse jam_akhir
    if "jam_akhir" in df.columns:
        df["jam_akhir"] = pd.to_datetime(df["jam_akhir"])

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
    if not query:
        return df
    q = query.lower()
    # Vectorized: concat all string columns and check
    mask = df.astype(str).apply(lambda col: col.str.lower()).agg(' '.join, axis=1).str.contains(q, na=False)
    return df[mask]


def filter_krs_data(df: pd.DataFrame, semesters: list = None, dosens: list = None) -> pd.DataFrame:
    """Filter DataFrame by specific Semester and Dosen values."""
    filtered = df.copy()

    if semesters:
        # Convert semester column to string just in case
        filtered = filtered[filtered["semester"].astype(str).isin(semesters)]

    if dosens:
        filtered = filtered[filtered["nama_dosen"].isin(dosens)]

    return filtered


def get_courses_by_ids(df: pd.DataFrame, ids: list) -> pd.DataFrame:
    """Get rows where id_kelas_kuliah matches the given list of IDs."""
    if "id_kelas_kuliah" not in df.columns:
        return pd.DataFrame()
    return df[df["id_kelas_kuliah"].isin(ids)]
