import os
from dotenv import load_dotenv
import asyncio
from collections import defaultdict
from datetime import datetime, timedelta

from alert.anti_spam import can_alert
from alert.workers import alert_queue

load_dotenv()

COUNTS = defaultdict(int)
LAST = defaultdict(float)

THRESHOLD = int(os.getenv("THRESHOLD_REQUESTS", 500))
EXPIRE = int(os.getenv("SECONDS_WINDOW", 10))
MAX_DDOS_IPS = int(os.getenv("MAX_DDOS_IPS", 50000))


def convert_to_vietnam_time(ts: str):
    """Chuyển timestamp UTC → giờ Việt Nam (UTC+7)."""
    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    vn_time = dt + timedelta(hours=7)
    return vn_time.strftime("%d/%m/%Y lúc %H:%M")


async def realtime_ddos_detector(streamer):
    loop = asyncio.get_event_loop()

    while True:
        async for log in streamer.stream_logs():

            # Lấy IP
            ip = log.get("zeek", {}).get("orig_h") or log.get("ip")
            if not ip:
                continue

            # Lấy timestamp từ Zeek log
            ts = log.get("@timestamp")
            if not ts:
                continue

            # Chuyển về giờ Việt Nam
            vn_time = convert_to_vietnam_time(ts)

            now = loop.time()

            # Nếu đã quá EXPIRE giây thì reset counter của IP
            if now - LAST[ip] > EXPIRE:
                COUNTS[ip] = 0

            COUNTS[ip] += 1
            LAST[ip] = now

            # Nếu vượt ngưỡng → gửi cảnh báo
            if COUNTS[ip] >= THRESHOLD and can_alert(ip):
                msg = (
                    f"[ALERT DDoS Scanner] Ngày {vn_time}\n"
                    f" - IP: {ip} \n"
                    f" - Ngưỡng {THRESHOLD} requests trong {EXPIRE} giây đã bị vượt qua."
                )
                await alert_queue.put({"content": msg, "threat_type": "ddos"})

        # Cleanup để không leak RAM
        now = loop.time()
        expired = [ip for ip, ts in LAST.items() if now - ts > EXPIRE]
        for ip in expired:
            LAST.pop(ip, None)
            COUNTS.pop(ip, None)

        # Nếu số IP đang theo dõi quá lớn (DDoS IP random), reset cứng
        if len(LAST) > MAX_DDOS_IPS:
            LAST.clear()
            COUNTS.clear()

        await asyncio.sleep(0.05)
