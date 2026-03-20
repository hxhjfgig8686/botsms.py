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

scraper = cloudscraper.create_scraper()

# ==============================
# COOKIES
# ==============================

def apply_cookies():
    scraper.cookies.set("cf_clearance", os.getenv("CF_CLEARANCE"))
    scraper.cookies.set("ivas_sms_session", os.getenv("IVAS_SESSION"))
    scraper.cookies.set("XSRF-TOKEN", os.getenv("XSRF_TOKEN"))

# ==============================
# TELEGRAM
# ==============================

def send(msg):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg})
    except:
        print("Telegram error")

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
            print("[LOGIN] success")
            send("♻️ Login success")
            return True

        print("[LOGIN] failed")
        return False

    except Exception as e:
        print("LOGIN ERROR:", e)
        return False

# ==============================
# FETCH FROM MULTIPLE PAGES
# ==============================

def fetch_all():
    data = []

    for url in URLS:
        try:
            r = scraper.get(url)

            # إذا مو مسجل دخول
            if "login" in r.url or "Login" in r.text:
                print("[!] Not logged in → login...")

                if login():
                    r = scraper.get(url)
                else:
                    continue

            soup = BeautifulSoup(r.text, "html.parser")

            text = soup.get_text(separator="\n")
            lines = text.split("\n")

            for line in lines:
                line = line.strip()

                if not line:
                    continue

                if re.search(r'\d{4,8}', line):
                    data.append(line)

        except Exception as e:
            print("FETCH ERROR:", e)

    return data

# ==============================
# OTP
# ==============================

def extract(text):
    m = re.search(r'\d{4,8}', text)
    return m.group() if m else None

# ==============================
# MAIN
# ==============================

def main():
    print("🚀 BOT STARTED (PRO MAX)")
    send("🚀 BOT STARTED (PRO MAX)")

    seen = set()

    while True:
        apply_cookies()

        messages = fetch_all()

        print(f"[📊] Total messages: {len(messages)}")

        for text in messages:
            otp = extract(text)

            if not otp:
                continue

            key = text

            if key in seen:
                continue

            msg = f"💬 {text}\n🔐 OTP: {otp}"

            print(msg)
            send(msg)

            seen.add(key)

        time.sleep(5)

# ==============================
# START
# ==============================

if __name__ == "__main__":
    main()