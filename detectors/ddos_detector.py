import asyncio
from collections import defaultdict
from alert.workers import alert_queue

COUNTS = defaultdict(int)
LAST = defaultdict(float)

THRESHOLD = 300
EXPIRE = 10

async def realtime_ddos_detector(streamer):
    async for log in streamer.stream_logs():
        ip = log.get("orig_h") or log.get("ip")
        if not ip:
            continue

        COUNTS[ip] += 1
        LAST[ip] = asyncio.get_event_loop().time()

        if COUNTS[ip] >= THRESHOLD:
            msg = f"[DDoS/Scanner ALERT]\n - IP: {ip}\n - Requests: {COUNTS[ip]}"
            print("co dau hieu ddos")
            await alert_queue.put({"content": msg, "threat_type": "ddos"})

        # cleanup
        now = asyncio.get_event_loop().time()
        for k in list(COUNTS.keys()):
            if now - LAST[k] > EXPIRE:
                del COUNTS[k]
                del LAST[k]
