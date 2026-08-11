"""Estonian D-Visa Slot Monitor — production, runs every 5 mins via GitHub Actions."""
import requests, sys
from datetime import datetime
from bs4 import BeautifulSoup

NTFY_TOPIC     = "archit-dvisa-2026"
BOOKING_URL    = "https://broneering.mfa.ee/en/"
EMBASSY_ID     = "40"        # New Delhi
TARGET_SERVICE = "D-visa"

def notify_phone(title, message, priority="urgent"):
    try:
        requests.post(
            f"https://ntfy.sh/{NTFY_TOPIC}",
            data=message.encode("utf-8"),
            headers={"Title": title, "Priority": priority, "Tags": "rotating_light"},
            timeout=10
        )
    except Exception:
        pass  # don't crash if ntfy fails

def check_slot():
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0"})
    r = session.get(BOOKING_URL, timeout=15)
    token = BeautifulSoup(r.text, "html.parser").find("input", {"name": "broneering[_token]"})
    if not token:
        raise ValueError("CSRF token not found — embassy site may have changed")
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
print(f"[{ts}] Checking New Delhi...", end=" ", flush=True)

try:
    found = check_slot()
except requests.exceptions.Timeout:
    print("Website timed out — skipping this check.")
    sys.exit(0)  # not a real failure, don't email
except requests.exceptions.ConnectionError:
    print("Connection error — skipping this check.")
    sys.exit(0)
except Exception as e:
    print(f"Unexpected error: {e}")
    sys.exit(0)  # still don't false-alarm on errors

if found:
    print("SLOT FOUND!")
    notify_phone(
        "D-VISA SLOT OPEN - BOOK NOW",
        "D-visa appointment slot is OPEN at Estonian Embassy New Delhi!\n\n"
        "Book NOW: https://broneering.mfa.ee/en/\n\n"
        "Personal ID: 39707150215\n"
        "Visa app number: 2026052733\n"
        "Description: Bolt Technology OU employee, STER 1066457755 (12.10-11.10.2027)\n\n"
        "AVOID: Aug 18-20 and Sep 16\n\n"
        f"Detected: {ts}"
    )
    sys.exit(1)  # only exit(1) for a REAL slot — triggers GitHub failure email
else:
    print("No slot yet.")
    sys.exit(0)
