import os
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from service.zeek_logs import ZeekLogFetcher
from alert.workers import alert_queue

load_dotenv()

SECONDS_WINDOW = int(os.getenv("SECONDS_WINDOW", 10))
THRESHOLD_REQUESTS = int(os.getenv("THRESHOLD_REQUESTS", 1000))

zeek_fetcher = ZeekLogFetcher()


async def check_zeek_scanner():
    results = await zeek_fetcher.detect_scanner(
        seconds=SECONDS_WINDOW,
        threshold_requests=THRESHOLD_REQUESTS
    )

    if results["status"] != "ok":
        print(f"[INFO] Zeek: {results.get('message')}")
        return

    suspicious = results["suspicious_ips"]
    alert_times = results["alert_times"]
    ip_col = results["ip_column"]

    for ip in suspicious:
        ip_addr = ip[ip_col]
        time_str = alert_times[ip_addr]

        base_message = (
            f"[Scanner ALERT] {time_str} "
            f"Phát hiện IP {ip_addr} gửi {ip['request_count']} requests "
            f"trong {SECONDS_WINDOW} giây"
        )

        await alert_queue.put({
            "content": base_message,
            "threat_type": "ddos"
        })
