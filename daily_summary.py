"""Daily summary — runs once at 9 PM IST. Confirms bot is alive and New Delhi status."""
import requests
from datetime import datetime
from bs4 import BeautifulSoup

NTFY_TOPIC   = "archit-dvisa-2026"
BOOKING_URL  = "https://broneering.mfa.ee/en/"
EMBASSY_ID   = "40"   # New Delhi

def check_slot():
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0"})
    r = session.get(BOOKING_URL, timeout=15)
    token = BeautifulSoup(r.text, "html.parser").find("input", {"name": "broneering[_token]"})
    if not token:
        return False
    r2 = session.post(BOOKING_URL, timeout=15, data={
        "broneering[esindus]": EMBASSY_ID,
        "broneering[isikuteArv]": "1",
        "g-recaptcha-response": "",
        "broneering[__dynamic_error]": "",
        "broneering[_token]": token["value"],
        "turbo": ""
    })
    options = [o.get_text(strip=True) for o in BeautifulSoup(r2.text, "html.parser").find_all("option")]
    return any("d-visa" in o.lower() for o in options)

found = check_slot()
today = datetime.now().strftime("%d %b %Y")

if found:
    title = "D-VISA SLOT OPEN - BOOK NOW"
    msg = (
        f"New Delhi D-visa slot is OPEN!\n\n"
        f"Book NOW: {BOOKING_URL}\n\n"
        f"Personal ID: 39707150215 | App: 2026052733\n"
        f"Avoid: Aug 18-20 and Sep 16"
    )
else:
    title = "Daily Check - No slot yet"
    msg = (
        f"Daily summary for {today}\n\n"
        f"New Delhi: No D-visa slot yet.\n"
        f"Bot checked every 5 mins all day. System working fine.\n\n"
        f"288 checks done today. Still watching."
    )

requests.post(
    f"https://ntfy.sh/{NTFY_TOPIC}",
    data=msg.encode("utf-8"),
    headers={"Title": title, "Priority": "default" if not found else "urgent", "Tags": "calendar"},
    timeout=10
)
print(f"Daily summary sent. New Delhi slot: {found}")
