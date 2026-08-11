"""Estonian D-Visa Slot Monitor — FULL VALIDATION across all embassies."""
import requests, sys
from datetime import datetime
from bs4 import BeautifulSoup

NTFY_TOPIC     = "archit-dvisa-2026"
BOOKING_URL    = "https://broneering.mfa.ee/en/"
TARGET_SERVICE = "D-visa"

# All 38 embassies
EMBASSIES = {
    "244": "Abu Dhabi", "7": "Ankara", "49": "Astana", "8": "Athens",
    "249": "Baku", "9": "Berlin", "10": "Brussels", "11": "Budapest",
    "243": "Bucharest", "239": "Canberra", "12": "Dublin", "13": "The Hague",
    "14": "Helsinki", "45": "Cairo", "15": "Kyiv", "16": "Copenhagen",
    "17": "Lisbon", "4": "London", "19": "Madrid", "21": "Moscow",
    "40": "New Delhi", "23": "Oslo", "24": "Ottawa", "25": "Paris",
    "26": "Beijing", "28": "Prague", "29": "Riga", "30": "Rome",
    "251": "Singapore", "250": "Seoul", "32": "Stockholm", "43": "Tbilisi",
    "44": "Tel Aviv", "33": "Tokyo", "34": "Warsaw", "35": "Vienna",
    "36": "Vilnius", "37": "Washington", "259": "Dubai"
}

def notify_phone(title, message):
    requests.post(
        f"https://ntfy.sh/{NTFY_TOPIC}",
        data=message.encode("utf-8"),
        headers={"Title": title, "Priority": "urgent", "Tags": "white_check_mark"},
        timeout=10
    )

def get_fresh_token(session):
    r = session.get(BOOKING_URL, timeout=15)
    token = BeautifulSoup(r.text, "html.parser").find("input", {"name": "broneering[_token]"})
    return token["value"] if token else None

def check_embassy(session, embassy_id, token):
    r = session.post(BOOKING_URL, timeout=15, data={
        "broneering[esindus]": embassy_id,
        "broneering[isikuteArv]": "1",
        "g-recaptcha-response": "",
        "broneering[__dynamic_error]": "",
        "broneering[_token]": token,
        "turbo": ""
    })
    soup = BeautifulSoup(r.text, "html.parser")
    new_token = soup.find("input", {"name": "broneering[_token]"})
    options = [o.get_text(strip=True) for o in soup.find_all("option")]
    has_slot = any(TARGET_SERVICE.lower() in o.lower() for o in options)
    return has_slot, new_token["value"] if new_token else None

# Run full scan
session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0"})

print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Scanning all {len(EMBASSIES)} embassies...\n")
token = get_fresh_token(session)
found_list = []
errors = []

for eid, name in EMBASSIES.items():
    print(f"  Checking {name}...", end=" ", flush=True)
    try:
        has_slot, token = check_embassy(session, eid, token)
        if not token:
            token = get_fresh_token(session)
        if has_slot:
            found_list.append(name)
            print("D-VISA SLOT FOUND")
        else:
            print("no slot")
    except Exception as e:
        errors.append(f"{name}: {e}")
        print(f"ERROR: {e}")
        token = get_fresh_token(session)

print(f"\n{'='*40}")
print(f"Scan complete. Embassies with D-visa slots: {len(found_list)}/{len(EMBASSIES)}")
if found_list:
    print("Slots found at:", ", ".join(found_list))
if errors:
    print("Errors:", errors)

# Send one notification with full results
msg = (
    f"FULL SCAN COMPLETE - {len(found_list)} embassies have D-visa slots:\n\n"
    + "\n".join(f"- {e}" for e in found_list) +
    f"\n\nNew Delhi: {'SLOT OPEN - BOOK NOW!' if 'New Delhi' in found_list else 'No slot yet'}"
    f"\n\nScanned {len(EMBASSIES)} embassies. Bot is fully verified."
    f"\n\nAvoid: Aug 18-20 and Sep 16"
)
notify_phone("VALIDATION COMPLETE - Bot verified", msg)
print("\nPhone notification sent. Check your phone!")

# Exit 1 only if New Delhi has a slot (triggers GitHub Actions failure email)
if "New Delhi" in found_list:
    sys.exit(1)
