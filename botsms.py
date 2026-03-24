import time
import requests
import re
import os
import json

# ==============================
# CONFIG
# ==============================

BASE = "https://www.ivasms.com"

LOGIN_URL = BASE + "/login"
SUMMARY_URL = BASE + "/portal/sms/received/getsms"
DETAILS_URL = BASE + "/portal/sms/received/getdetails"

EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

API_URL = "https://apiserver-37it.onrender.com/receive_sms"
API_KEY = "sk_cc1480ac..."

SENT_MESSAGES_FILE = "ivasms_sent_messages.json"
MAX_MESSAGES = 1000

session = requests.Session()

# ==============================
# DUPLICATES
# ==============================

def load_sent():
    if not os.path.exists(SENT_MESSAGES_FILE):
        return set()
    try:
        return set(json.load(open(SENT_MESSAGES_FILE)))
    except:
        return set()

def save_sent(data):
    data = list(data)[-MAX_MESSAGES:]
    json.dump(data, open(SENT_MESSAGES_FILE, "w"))

sent_messages = load_sent()

# ==============================
# LOGIN
# ==============================

def login():
    print("[LOGIN]...")

    session.get(LOGIN_URL)

    r = session.post(LOGIN_URL, data={
        "email": EMAIL,
        "password": PASSWORD
    })

    if r.status_code == 200:
        print("✔ Logged in")
        return True

    print("❌ Login failed")
    return False

# ==============================
# FETCH
# ==============================

def fetch_messages():
    messages = []

    try:
        r = session.post(SUMMARY_URL)

        # إذا خرج من الجلسة
        if "login" in r.text.lower():
            if not login():
                return []

            r = session.post(SUMMARY_URL)

        data = r.json()

        numbers = [x.get("number") for x in data.get("data", []) if x.get("number")]

        for number in numbers:
            sms_res = session.post(DETAILS_URL, data={"number": number})
            sms_data = sms_res.json()

            for sms in sms_data.get("data", []):
                messages.append({
                    "id": str(sms.get("id")),
                    "number": number,
                    "text": sms.get("message")
                })

    except Exception as e:
        print("ERROR:", e)

    return messages

# ==============================
# HELPERS
# ==============================

def extract_otp(text):
    m = re.search(r'\b\d{4,8}\b', text)
    return m.group() if m else None

def clean_number(n):
    return re.sub(r'\D', '', str(n))

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
    except:
        pass

# ==============================
# API SERVER
# ==============================

def send_api(number, sms):
    try:
        requests.post(
            API_URL,
            json={"number": number, "message": sms},
            headers={"X-API-Key": API_KEY},
            timeout=5
        )
    except:
        pass

# ==============================
# MAIN
# ==============================

def main():
    print("🚀 STARTED")

    login()

    while True:
        msgs = fetch_messages()

        print("📊", len(msgs))

        for m in msgs:

            if m["id"] in sent_messages:
                continue

            number = clean_number(m["number"])
            sms = m["text"]
            otp = extract_otp(sms)

            text = f"💬 {sms}"
            if otp:
                text += f"\n🔐 OTP: {otp}"

            print(text)

            send_telegram(text)
            send_api(number, sms)

            sent_messages.add(m["id"])
            save_sent(sent_messages)

        time.sleep(3)

# ==============================
# START
# ==============================

if __name__ == "__main__":
    main()