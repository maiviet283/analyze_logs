import os
from dotenv import load_dotenv
from service.zeek_logs import ZeekLogFetcher
from alert.workers import alert_queue

load_dotenv()

SECONDS_WINDOW = int(os.getenv("SECONDS_WINDOW", 10))
THRESHOLD_REQUESTS = int(os.getenv("THRESHOLD_REQUESTS", 500))

zeek_fetcher = ZeekLogFetcher()


async def check_zeek_scanner():
    results = await zeek_fetcher.detect_scanner(
        seconds=SECONDS_WINDOW,
        threshold_requests=THRESHOLD_REQUESTS
    )

    if results["status"] != "ok":
        print(f"[INFO] Zeek: {results.get('message')}")
        return

    suspicious = results.get("suspicious_ips", [])
    alert_times = results.get("alert_times", {})
    ip_col = results.get("ip_column")

    if not suspicious:
        return

    for ip in suspicious:
        ip_addr = ip[ip_col]
        time_str = alert_times[ip_addr]

        base_message = (
            f"[Scanner ALERT] {time_str} \n"
            f" - IP {ip_addr} gửi {ip['request_count']} requests \n"
            f" - Số Lần : {ip['request_count']} requests \n"
            f" - Trong {SECONDS_WINDOW} giây"
        )

        await alert_queue.put({
            "content": base_message,
            "threat_type": "ddos"
        })
