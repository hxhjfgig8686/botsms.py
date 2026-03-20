import time
import requests
import json
import re
import os
import cloudscraper
from bs4 import BeautifulSoup

BASE = "https://www.ivasms.com"
SMS_URL = BASE + "/portal/sms/received"

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

scraper = cloudscraper.create_scraper()

# ==============================
# LOAD COOKIES FROM RAILWAY
# ==============================

def apply_cookies():
    scraper.cookies.set("cf_clearance", os.getenv("CF_CLEARANCE"))
    scraper.cookies.set("ivas_sms_session", os.getenv("IVAS_SESSION"))
    scraper.cookies.set("XSRF-TOKEN", os.getenv("XSRF_TOKEN"))

# ==============================
# FETCH
# ==============================

def fetch():
    try:
        apply_cookies()

        r = scraper.get(SMS_URL)

        print("STATUS:", r.status_code)

        if "login" in r.url:
            print("[!] cookies expired")
            return []

        soup = BeautifulSoup(r.text, "html.parser")

        text = soup.get_text(separator="\n")
        lines = text.split("\n")

        data = []

        for i, line in enumerate(lines):
            line = line.strip()

            if not line:
                continue

            if re.search(r'\d{4,8}', line):
                data.append({
                    "id": i,
                    "text": line
                })

        return data

    except Exception as e:
        print("ERROR:", e)
        return []

# ==============================
# OTP
# ==============================

def extract(text):
    m = re.search(r'\d{4,8}', text)
    return m.group() if m else None

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
# MAIN
# ==============================

def main():
    print("🚀 BOT STARTED (RAILWAY COOKIE MODE)")
    send("🚀 BOT STARTED (COOKIE MODE)")

    seen = set()

    while True:
        data = fetch()

        print(f"[📊] Messages: {len(data)}")

        for m in data:
            text = m["text"]
            mid = m["id"]

            otp = extract(text)

            if not otp:
                continue

            if mid in seen:
                continue

            msg = f"💬 {text}\n🔐 OTP: {otp}"

            print(msg)
            send(msg)

            seen.add(mid)

        time.sleep(5)

# ==============================
# START
# ==============================

if __name__ == "__main__":
    main()