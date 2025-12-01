import asyncio
from collections import defaultdict
from alert.anti_spam import can_alert
from alert.workers import alert_queue

FAILED = defaultdict(int)
LAST = defaultdict(float)

THRESHOLD = 10     # ví dụ brute-force 10 lần
EXPIRE = 60        # reset sau 60s

async def realtime_bruteforce_detector(streamer):
    async for log in streamer.stream_logs():
        ip = log.get("ip")
        status = log.get("status_code")

        if not ip or status != 401:
            continue

        FAILED[ip] += 1
        LAST[ip] = asyncio.get_event_loop().time()

        if FAILED[ip] >= THRESHOLD:
            if can_alert(ip):
                msg = f"[Brute-Force ALERT]\n - IP: {ip}\n - Attempts: {FAILED[ip]}"
                await alert_queue.put({"content": msg, "threat_type": "bruteforce"})