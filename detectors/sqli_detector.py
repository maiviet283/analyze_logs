import re
from urllib.parse import unquote
from alert.anti_spam import can_alert
from alert.workers import alert_queue

SQLI_PATTERN = re.compile(
    r"(?i)(union.+select|or\s+1=1|sleep\(|updatexml|extractvalue|drop\s+table)"
)

async def realtime_sqli_detector(streamer):
    async for log in streamer.stream_logs():
        body = unquote(str(log.get("body", "")))
        ip = log.get("ip", "unknown")

        if SQLI_PATTERN.search(body):
            if not can_alert(ip):
                continue  # NGĂN SPAM ALERT

            msg = f"[SQLi ALERT]\n - IP: {ip}\n - Payload: {body[:250]}"
            await alert_queue.put({"content": msg, "threat_type": "sqli"})