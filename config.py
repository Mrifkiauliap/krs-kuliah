# ===========================
# UNSAM Config
# ===========================
LOGIN_PAGE = "https://sso.unsam.ac.id/realms/Production/protocol/openid-connect/auth"
CLIENT_ID = "mahasiswa"
REDIRECT_URI = "https://mahasiswa.unsam.ac.id/home"
KRS_URL = "https://mahasiswa.unsam.ac.id/krs/datatable/20261"

MAX_SKS = 24

HARI_ORDER = {
    "senin": 1,
    "selasa": 2,
    "rabu": 3,
    "kamis": 4,
    "jumat": 5,
    "sabtu": 6,
    "minggu": 7,
}

# Duration per SKS in minutes (for conflict detection when jam_selesai is missing)
MINUTES_PER_SKS = 50

# ===========================
# Timetable & Schedule Config
# ===========================
DAYS = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu"]
DAYS_WEEKDAY = {  # Python weekday mapping (0=Monday)
    "senin": 0, "selasa": 1, "rabu": 2,
    "kamis": 3, "jumat": 4, "sabtu": 5, "minggu": 6,
}
SCHEDULE_START_HOUR = 7
SCHEDULE_END_HOUR = 20    # Free time finder range
TIMETABLE_END_HOUR = 21  # Visual timetable extends further
TIMETABLE_CELL_HEIGHT = 40  # px per hour in visual timetable

# ===========================
# ICS Export Config
# ===========================
SEMESTER_WEEKS = 16

# ===========================
# AI Assistant Config
# ===========================
API_URL = "https://ai.sumopod.com/v1/chat/completions"

# Available models (name, label)
AVAILABLE_MODELS = [
    ("kimi-k2-250905", "🆓 Kimi K2 (Free, Recommended)"),
    ("deepseek-v3-2-251201", "🆓 DeepSeek V3 (Free)"),
    ("deepseek-r1-250528", "🆓 DeepSeek R1 (Free, Reasoning)"),
    ("gemini/gemini-2.5-flash", "⚡ Gemini 2.5 Flash (Fast)"),
    ("gemini/gemini-2.0-flash-lite", "💸 Gemini 2.0 Flash Lite (Cheapest)"),
    ("gpt-4.1-mini", "🧠 GPT-4.1 Mini (Balanced)"),
    ("gpt-4o-mini", "🧠 GPT-4o Mini"),
    ("claude-haiku-4-5", "🧠 Claude Haiku 4.5"),
    ("gemini/gemini-2.5-pro", "🏆 Gemini 2.5 Pro (Best Quality)"),
]

# Max messages to keep in history (to manage token usage)
MAX_HISTORY = 20
MAX_TOKENS = 4096 # Bisa hingga 8192
