import re
from urllib.parse import unquote
from alert.workers import alert_queue

SQLI_PATTERN = re.compile(
    r"(?i)(union.+select|or\s+1=1|sleep\(|updatexml|extractvalue|drop\s+table)"
)

async def realtime_sqli_detector(streamer):
    async for log in streamer.stream_logs():
        body = unquote(str(log.get("body", "")))
        if SQLI_PATTERN.search(body):
            ip = log.get("ip", "unknown")
            msg = f"[SQLi ALERT]\n - IP: {ip}\n - Payload: {body[:250]}"
            await alert_queue.put({"content": msg, "threat_type": "sqli"})
