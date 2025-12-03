import os
import time
from dotenv import load_dotenv

load_dotenv()

LAST_ALERT = {}
ALERT_COOLDOWN = int(os.getenv("ALERT_COOLDOWN", 30))
MAX_ALERT_IPS = int(os.getenv("MAX_ALERT_IPS", 5000))


def _prune_alert_cache(now: float) -> None:
    """
    Dọn bớt IP cũ khi bảng LAST_ALERT quá lớn để tránh phình RAM.
    Chiến lược:
      - Xoá các IP đã quá cooldown * 3
      - Nếu vẫn quá to thì clear toàn bộ.
    """
    if len(LAST_ALERT) <= MAX_ALERT_IPS:
        return

    cutoff = now - ALERT_COOLDOWN * 3
    stale_ips = [ip for ip, ts in LAST_ALERT.items() if ts < cutoff]

    for ip in stale_ips:
        LAST_ALERT.pop(ip, None)

    # Nếu vẫn quá lớn (trường hợp DDoS IP random), reset hẳn
    if len(LAST_ALERT) > MAX_ALERT_IPS:
        LAST_ALERT.clear()


def can_alert(ip: str) -> bool:
    now = time.time()

    # Dọn cache nếu cần
    _prune_alert_cache(now)

    last = LAST_ALERT.get(ip)
    if last is None:
        LAST_ALERT[ip] = now
        return True

    if now - last >= ALERT_COOLDOWN:
        LAST_ALERT[ip] = now
        return True

    return False
