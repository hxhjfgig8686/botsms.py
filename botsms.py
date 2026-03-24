import time
import requests
import re
import os
import json
import urllib.parse

# ==============================
# CONFIG
# ==============================

BASE = "https://www.ivasms.com"

SUMMARY_URL = BASE + "/portal/sms/received/getsms"
DETAILS_URL = BASE + "/portal/sms/received/getdetails"

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

API_URL = "https://apiserver-37it.onrender.com/receive_sms"
API_KEY = os.getenv("API_KEY")

session = requests.Session()

SENT_FILE = "sent.json"
MAX = 1000

# ==============================
# COOKIES
# ==============================

def apply_cookies():
    session.cookies.set("cf_clearance", os.getenv("CF_CLEARANCE"))
    session.cookies.set("XSRF-TOKEN", os.getenv("XSRF_TOKEN"))
    session.cookies.set("ivas_sms_session", os.getenv("IVAS_SESSION"))

# ==============================
# HEADERS
# ==============================

def headers():
    xsrf = urllib.parse.unquote(os.getenv("XSRF_TOKEN"))
    return {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/x-www-form-urlencoded",
        "X-Requested-With": "XMLHttpRequest",
        "X-XSRF-TOKEN": xsrf,
        "Referer": "https://www.ivasms.com/portal/sms/received"
    }

# ==============================
# DUPLICATE
# ==============================

def load_sent():
    if not os.path.exists(SENT_FILE):
        return set()
    try:
        return set(json.load(open(SENT_FILE)))
    except:
        return set()

def save_sent(data):
    json.dump(list(data)[-MAX:], open(SENT_FILE, "w"))

sent = load_sent()

# ==============================
# SAFE JSON
# ==============================

def safe_json(r):
    try:
        if "application/json" not in r.headers.get("Content-Type", ""):
            print("❌ NOT JSON:")
            print(r.text[:300])
            return None
        return r.json()
    except Exception as e:
        print("JSON ERROR:", e)
        print(r.text[:300])
        return None

# ==============================
# FETCH
# ==============================

def fetch():
    msgs = []

    apply_cookies()

    r = session.post(SUMMARY_URL, headers=headers())

    print("STATUS:", r.status_code)

    data = safe_json(r)
    if not data:
        return []

    numbers = [x.get("number") for x in data.get("data", []) if x.get("number")]

    for num in numbers:

        sms_res = session.post(
            DETAILS_URL,
            data={"number": num},
            headers=headers()
        )

        sms_data = safe_json(sms_res)
        if not sms_data:
            continue

        for s in sms_data.get("data", []):
            msgs.append({
                "id": str(s.get("id")),
                "number": num,
                "text": s.get("message")
            })

    return msgs

# ==============================
# HELPERS
# ==============================

def otp(text):
    m = re.search(r'\d{4,8}', text)
    return m.group() if m else None

def clean(n):
    return re.sub(r'\D', '', str(n))

# ==============================
# TELEGRAM
# ==============================

def send_tg(msg):
    try:
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": msg},
            timeout=5
        )
    except:
        pass

# ==============================
# API
# ==============================

def send_api(n, m):
    try:
        requests.post(
            API_URL,
            json={"number": n, "message": m},
            headers={"X-API-Key": API_KEY},
            timeout=5
        )
    except:
        pass

# ==============================
# MAIN
# ==============================

def main():
    print("🚀 STARTED FINAL")

    while True:

        msgs = fetch()

        print("📊", len(msgs))

        for m in msgs:

            if m["id"] in sent:
                continue

            number = clean(m["number"])
            text = m["text"]

            code = otp(text)

            out = f"💬 {text}"
            if code:
                out += f"\n🔐 OTP: {code}"

            print(out)

            send_tg(out)
            send_api(number, text)

            sent.add(m["id"])
            save_sent(sent)

        time.sleep(3)

# ==============================
# START
# ==============================

if __name__ == "__main__":
    main()