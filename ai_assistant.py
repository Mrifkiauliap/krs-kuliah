import requests
import pandas as pd
from config import MAX_HISTORY, MAX_TOKENS, API_URL, AVAILABLE_MODELS

# Keywords that trigger catalog inclusion (user asking about available courses)
_CATALOG_KEYWORDS = [
    "rekomendasi", "saran", "rekomen", "pilih", "cari", "alternatif",
    "kelas lain", "mk apa", "mata kuliah apa", "tersedia", "available",
    "semester", "opsi", "ganti kelas", "pindah kelas", "bentrok",
    "yang bisa", "yang cocok", "yang pas", "suggest", "recommend",
]


def needs_catalog(prompt: str) -> bool:
    """Check if user's question needs the full course catalog."""
    p = prompt.lower()
    return any(kw in p for kw in _CATALOG_KEYWORDS)


def build_catalog_summary(df: pd.DataFrame) -> str:
    """Compress full course catalog into ultra-compact text.

    Format: Kalkulus (MAT101) 3SKS: A/Sen 08-10, B/Sel 10-12
    """
    if df.empty:
        return ""

    lines = []
    grouped = df.groupby(["nama_mata_kuliah", "kode_mata_kuliah"], sort=True)

    for (nama, kode), group in grouped:
        sks = group["sks_mata_kuliah"].iloc[0] if "sks_mata_kuliah" in group.columns else "?"

        parts = []
        for _, row in group.iterrows():
            kls = row.get("nama_kelas_kuliah", "?")
            hari = str(row.get("hari", "")).capitalize()[:3]
            js = row["jam_mulai"].strftime("%H:%M") if pd.notna(row["jam_mulai"]) else "?"
            je = row["jam_akhir"].strftime("%H:%M") if pd.notna(row.get("jam_akhir")) else "?"
            parts.append(f"{kls}/{hari} {js}-{je}")

        lines.append(f"{nama}({kode}){sks}SKS: {', '.join(parts)}")

    return "\n".join(lines)


def build_schedule_summary(df: pd.DataFrame, selected_ids: set) -> str:
    """Build compact summary of user's selected schedule."""
    if not selected_ids:
        return "Belum memilih MK."

    my_df = df[df["id_kelas_kuliah"].isin(selected_ids)]
    if my_df.empty:
        return "Belum memilih MK."

    parts = []
    for _, row in my_df.iterrows():
        nama = row.get("nama_mata_kuliah", "?")
        kls = row.get("nama_kelas_kuliah", "?")
        hari = str(row.get("hari", "")).capitalize()[:3]
        js = row["jam_mulai"].strftime("%H:%M") if pd.notna(row["jam_mulai"]) else "?"
        je = row["jam_akhir"].strftime("%H:%M") if pd.notna(row.get("jam_akhir")) else "?"
        sks = row.get("sks_mata_kuliah", "?")
        dosen = str(row.get("nama_dosen", "-"))
        parts.append(f"{nama}({kls}) {sks}SKS {hari} {js}-{je} [{dosen}]")

    return "\n".join(parts)


def trim_history(messages: list[dict], max_messages: int = MAX_HISTORY) -> list[dict]:
    """Keep only the last N messages to avoid exceeding context limits."""
    if len(messages) <= max_messages:
        return messages
    return messages[-max_messages:]


def ask_ai(api_key: str, messages: list[dict], model: str = AVAILABLE_MODELS[0][0], temperature: float = 0.7) -> str:
    """Send chat request to the custom AI API."""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": MAX_TOKENS,
        "temperature": temperature
    }

    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        result = response.json()

        if "choices" in result and len(result["choices"]) > 0:
            return result["choices"][0]["message"]["content"]
        else:
            return "Error: Tidak ada respon diterima."

    except requests.exceptions.HTTPError as e:
        return f"API Error: {e.response.status_code} - {e.response.text}"
    except requests.exceptions.Timeout:
        return "⏱️ Request timed out. Coba lagi atau gunakan model yang lebih cepat."
    except Exception as e:
        return f"Koneksi gagal: {str(e)}"
