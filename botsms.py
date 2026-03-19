import cloudscraper
import requests
import time
import json
import re
import os
import random

# ==============================
# CONFIG
# ==============================

BASE = "https://www.ivasms.com"
LOGIN_URL = BASE + "/login"
SMS_URL = BASE + "/portal/sms/received/getsms"

EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

scraper = cloudscraper.create_scraper()

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
# COOKIES
# ==============================

def load_cookies():
    scraper.cookies.set("cf_clearance", os.getenv("CF_CLEARANCE"))
    scraper.cookies.set("ivas_sms_session", os.getenv("IVAS_SESSION"))
    scraper.cookies.set("XSRF-TOKEN", os.getenv("XSRF_TOKEN"))

def save_cookies():
    cookies = scraper.cookies.get_dict()
    print("[+] Cookies refreshed")

# ==============================
# LOGIN
# ==============================

def login():
    print("[LOGIN] trying...")

    scraper.get(LOGIN_URL)

    payload = {
        "email": EMAIL,
        "password": PASSWORD
    }

    r = scraper.post(LOGIN_URL, data=payload)

    if r.status_code == 200:
        save_cookies()
        print("[LOGIN] success")
        return True

    print("[LOGIN] failed")
    return False

# ==============================
# FETCH
# ==============================

def fetch():
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json, text/plain, */*",
        "Referer": BASE + "/portal/live/my_sms",
        "X-Requested-With": "XMLHttpRequest"
    }

    try:
        r = scraper.get(SMS_URL, headers=headers, timeout=10)

        if "text/html" in r.headers.get("content-type", ""):
            return None

        return r.json().get("data", [])

    except:
        return None

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
    print("🚀 BOT STARTED")
    send("🚀 BOT STARTED (Railway Mode)")

    seen = set()

    load_cookies()

    while True:
        data = fetch()

        # 🔴 إذا فشل
        if data is None:
            print("[!] session broken → fixing")

            if login():
                send("♻️ session restored")
            else:
                send("❌ login failed")
                time.sleep(10)
                continue

        else:
            for m in data:
                mid = str(m.get("id"))
                text = m.get("text", "")
                number = m.get("number", "")

                otp = extract(text)

                if not otp:
                    continue

                key = f"{mid}_{otp}"

                if key in seen:
                    continue

                msg = f"🔐 OTP: {otp}\n📱 {number}"
                print(msg)
                send(msg)

                seen.add(key)

        time.sleep(random.randint(4, 7))

# ==============================
# START
# ==============================

if __name__ == "__main__":
    main()
