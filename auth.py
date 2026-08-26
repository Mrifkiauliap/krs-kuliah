import requests
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from config import LOGIN_PAGE, CLIENT_ID, REDIRECT_URI

TIMEOUT = 30


def login_sso(username: str, password: str) -> requests.Session:
    """Login to UNSAM SSO and return an authenticated requests.Session."""
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0"})

    # 1. GET login page to obtain the form action URL
    r = session.get(
        LOGIN_PAGE,
        params={
            "client_id": CLIENT_ID,
            "redirect_uri": REDIRECT_URI,
            "response_type": "code",
            "scope": "openid",
        },
        timeout=TIMEOUT,
    )
    r.raise_for_status()

    soup = BeautifulSoup(r.text, "lxml")
    form = soup.find("form")

    if not form:
        raise Exception("Form login tidak ditemukan di halaman SSO")

    # Action bisa berupa URL relatif, jadi gabung dengan base URL
    action = urljoin(LOGIN_PAGE, form.get("action", ""))

    # 2. POST credentials
    payload = {
        "username": username,
        "password": password,
        "credentialId": "",
    }

    resp = session.post(action, data=payload, allow_redirects=True, timeout=TIMEOUT)

    # Periksa error yang terlihat (halaman error biasanya berisi "Invalid username")
    if resp.status_code == 401 or "invalid_username_or_password" in resp.text:
        raise Exception("Login gagal — username atau password salah")

    # ci_session cookie = main indicator of a successful login
    if "ci_session" not in session.cookies.get_dict():
        raise Exception("Login gagal — username atau password salah")

    return session
