import time
import requests
import re
import os
import cloudscraper
from bs4 import BeautifulSoup

# ==============================
# CONFIG
# ==============================

BASE = "https://www.ivasms.com"

URLS = [
    BASE + "/portal/sms/received",
    BASE + "/portal/live/my_sms"
]

LOGIN_URL = BASE + "/login"

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")

API_URL = "https://apiserver-37it.onrender.com/receive_sms"
API_KEY = "sk_cc1480ac5e3a4818e07fb4b0674bc2a72228372220dba26ac4579cfd4eda903b"

scraper = cloudscraper.create_scraper()
seen = set()

# ==============================
# COOKIES
# ==============================

def apply_cookies():
    if os.getenv("CF_CLEARANCE"):
        scraper.cookies.set("cf_clearance", os.getenv("CF_CLEARANCE"))

    if os.getenv("IVAS_SESSION"):
        scraper.cookies.set("ivas_sms_session", os.getenv("IVAS_SESSION"))

    if os.getenv("XSRF_TOKEN"):
        scraper.cookies.set("XSRF-TOKEN", os.getenv("XSRF_TOKEN"))

# ==============================
# TELEGRAM
# ==============================

def send_telegram(msg):
    try:
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": msg},
            timeout=5
        )
    except Exception as e:
        print("Telegram error:", e)

# ==============================
# API
# ==============================

def send_to_api(number, message):
    try:
        requests.post(
            API_URL,
            json={
                "number": number,
                "message": message
            },
            headers={
                "X-API-Key": API_KEY
            },
            timeout=5
        )
    except Exception as e:
        print("API error:", e)

# ==============================
# LOGIN
# ==============================

def login():
    try:
        print("[LOGIN] trying...")

        scraper.get(LOGIN_URL)

        payload = {
            "email": EMAIL,
            "password": PASSWORD
        }

        r = scraper.post(LOGIN_URL, data=payload)

        if "dashboard" in r.text.lower() or r.status_code == 200:
            print("[LOGIN SUCCESS]")
            send_telegram("♻️ Login success")
            return True

        print("[LOGIN FAILED]")
        return False

    except Exception as e:
        print("LOGIN ERROR:", e)
        return False

# ==============================
# CHECK SESSION
# ==============================

def ensure_login(r):
    if "login" in r.url.lower() or "login" in r.text.lower():
        print("[!] Session expired → login...")

        if login():
            return True
        else:
            return False

    return True

# ==============================
# FETCH
# ==============================

def fetch_messages():
    messages = []

    for url in URLS:
        try:
            apply_cookies()

            r = scraper.get(url)

            if not ensure_login(r):
                continue

            # إعادة الطلب بعد login
            r = scraper.get(url)

            soup = BeautifulSoup(r.text, "html.parser")

            rows = soup.find_all("tr")

            for row in rows:
                cols = row.find_all("td")

                if not cols:
                    continue

                row_text = " ".join([c.get_text(strip=True) for c in cols])

                if len(row_text) < 10:
                    continue

                if not re.search(r'\d{4,8}', row_text):
                    continue

                messages.append(row_text)

        except Exception as e:
            print("FETCH ERROR:", e)

    return messages

# ==============================
# EXTRACT
# ==============================

def extract_otp(text):
    m = re.search(r'\b\d{4,8}\b', text)
    return m.group() if m else None

def extract_number(text):
    m = re.search(r'\d{10,15}', text)
    return m.group() if m else "unknown"

# ==============================
# MAIN
# ==============================

def main():
    print("🚀 BOT STARTED (COOKIE + LOGIN)")
    send_telegram("🚀 BOT STARTED")

    while True:
        messages = fetch_messages()

        print(f"[📊] messages: {len(messages)}")

        for text in messages:
            if text in seen:
                continue

            otp = extract_otp(text)
            if not otp:
                continue

            number = extract_number(text)

            msg = f"💬 {text}\n🔐 OTP: {otp}"

            print(msg)

            send_telegram(msg)
            send_to_api(number, text)

            seen.add(text)

        time.sleep(5)

# ==============================
# START
# ==============================

if __name__ == "__main__":
    main()