import os
import time
from dotenv import load_dotenv

load_dotenv()

LAST_ALERT = {}
ALERT_COOLDOWN = int(os.getenv("ALERT_COOLDOWN", 30))

def can_alert(ip: str) -> bool:
    now = time.time()

    if ip not in LAST_ALERT:
        LAST_ALERT[ip] = now
        return True

    if now - LAST_ALERT[ip] >= ALERT_COOLDOWN:
        LAST_ALERT[ip] = now
        return True

    return False
