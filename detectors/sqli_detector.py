from urllib.parse import unquote
from alert.anti_spam import can_alert
from alert.workers import alert_queue
from enums.sqli_patern import SQLI_PATTERN


async def realtime_sqli_detector(streamer):
    async for log in streamer.stream_logs():
        body = unquote(str(log.get("body", "")))
        ip = log.get("ip", "unknown")
        time = log.get("timestamp", "unknown")
        user_agent = log.get("user_agent", "unknown")
        full_path = log.get("full_path", "unknown")
        method = log.get("method","unknown")

        if SQLI_PATTERN.search(body):
            if not can_alert(ip):
                continue

            msg = (
                f"[SQLi DETECTED ALERT] Lúc {time} \n"
                f" - IP: {ip} \n"
                f" - User-Agent: {user_agent} \n"
                f" - Method: {method} \n"
                f" - Path: {full_path} \n"
                f" - Payload: {body}"
            )
            await alert_queue.put({"content": msg, "threat_type": "sqli"})
            
            print(f"[SQLi DETECTED ALERT] IP: {ip} - (Lúc {time})")