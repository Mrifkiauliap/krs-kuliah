import requests
from bs4 import BeautifulSoup
from config import LOGIN_PAGE, CLIENT_ID, REDIRECT_URI


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
    )

    soup = BeautifulSoup(r.text, "lxml")
    form = soup.find("form")

    if not form:
        raise Exception("Form login tidak ditemukan di halaman SSO")

    action = form["action"]

    # 2. POST credentials
    payload = {
        "username": username,
        "password": password,
        "credentialId": "",
    }

    session.post(action, data=payload, allow_redirects=True)

    # ci_session cookie = main indicator of a successful login
    if "ci_session" not in session.cookies.get_dict():
        raise Exception("Login gagal — username atau password salah")

    return session
