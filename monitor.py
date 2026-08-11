"""Estonian D-Visa Slot Monitor — cloud version for GitHub Actions."""
import requests, sys
from datetime import datetime
from bs4 import BeautifulSoup

NTFY_TOPIC     = "archit-dvisa-2026"
BOOKING_URL    = "https://broneering.mfa.ee/en/"
EMBASSY_ID     = "244"   # TEST: Abu Dhabi — change to "40" for New Delhi after test
TARGET_SERVICE = "D-visa"  # matches "Long-stay visa (D-visa) application"

def notify_phone(message):
    requests.post(
        f"https://ntfy.sh/{NTFY_TOPIC}",
        data=message.encode("utf-8"),
        headers={"Title": "🚨 D-VISA SLOT OPEN — BOOK NOW!", "Priority": "urgent", "Tags": "rotating_light"},
        timeout=10
    )

def check_slot():
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0"})
    r = session.get(BOOKING_URL, timeout=15)
    token = BeautifulSoup(r.text, "html.parser").find("input", {"name": "broneering[_token]"})
    if not token:
        print("CSRF token not found"); return False
    r2 = session.post(BOOKING_URL, timeout=15, data={
        "broneering[esindus]": EMBASSY_ID,
        "broneering[isikuteArv]": "1",
        "g-recaptcha-response": "",
        "broneering[__dynamic_error]": "",
        "broneering[_token]": token["value"],
        "turbo": ""
    })
    options = [o.get_text(strip=True) for o in BeautifulSoup(r2.text, "html.parser").find_all("option")]
    return any(TARGET_SERVICE.lower() in o.lower() for o in options)

ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
print(f"[{ts}] Checking Abu Dhabi (TEST)...", end=" ", flush=True)
found = check_slot()
if found:
    print("✅ Slot detected!")
    notify_phone(
        "✅ TEST PASSED — Bot is working!\n\n"
        "This was a test using Abu Dhabi embassy (which has slots).\n"
        "The bot will now be switched back to monitor New Delhi.\n"
        "You'll get a real alert like this when New Delhi slot opens."
    )
    sys.exit(0)
else:
    print("❌ No slot detected (check failed)")
    sys.exit(1)
