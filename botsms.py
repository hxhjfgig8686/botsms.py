import time
import requests
import re
import os
import json
from bs4 import BeautifulSoup

# ==============================
# CONFIG
# ==============================

URL = "https://www.ivasms.com/portal/live/my_sms"

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
    return {
        "User-Agent": "Mozilla/5.0",
        "Accept": "text/html",
        "Referer": "https://www.ivasms.com"
    }

# ==============================
# DUPLICATE SYSTEM
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
# FETCH LIVE SMS
# ==============================

def fetch():
    apply_cookies()

    r = session.get(URL, headers=headers())

    print("STATUS:", r.status_code)

    if "login" in r.text.lower():
        print("❌ session expired")
        return []

    soup = BeautifulSoup(r.text, "html.parser")

    messages = []

    # 👇 كل بلوك رسالة
    blocks = soup.find_all("div", class_="inner")

    for block in blocks:
        text = block.get_text("\n", strip=True)

        # استخراج OTP
        if not re.search(r'\b\d{4,8}\b', text):
            continue

        # استخراج الرقم من الصفحة كامل
        number_match = re.search(r'\d{10,15}', r.text)
        number = number_match.group() if number_match else "unknown"

        messages.append({
            "id": text,
            "number": number,
            "text": text
        })

    return messages

# ==============================
# OTP
# ==============================

def extract_otp(text):
    m = re.search(r'\b\d{4,8}\b', text)
    return m.group() if m else None

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

def send_api(number, message):
    try:
        requests.post(
            API_URL,
            json={"number": number, "message": message},
            headers={"X-API-Key": API_KEY},
            timeout=5
        )
    except:
        pass

# ==============================
# MAIN LOOP
# ==============================

def main():
    print("🚀 LIVE SMS BOT STARTED")

    while True:
        msgs = fetch()

        print("📊 messages:", len(msgs))

        for m in msgs:

            if m["id"] in sent:
                continue

            number = m["number"]
            text = m["text"]
            otp = extract_otp(text)

            output = f"📱 {number}\n💬 {text}"

            if otp:
                output += f"\n🔐 OTP: {otp}"

            print(output)

            send_telegram(output)
            send_api(number, text)

            sent.add(m["id"])
            save_sent(sent)

        time.sleep(5)

# ==============================
# START
# ==============================

if __name__ == "__main__":
    main()