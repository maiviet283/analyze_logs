import os
from dotenv import load_dotenv
from service.django_logs import DjangoLogFetcher
from alert.workers import alert_queue

load_dotenv()

django_fetcher = DjangoLogFetcher()

SECONDS_WINDOW = int(os.getenv("SECONDS_WINDOW", 10))
THRESHOLD_SQLI = int(os.getenv("THRESHOLD_SQLI", 5))

async def check_django_sqli():
    results = await django_fetcher.detect_sql_injection(
        seconds=SECONDS_WINDOW,
        threshold=THRESHOLD_SQLI
    )

    if results["status"] != "ok":
        print(f"[INFO] Django SQLi: {results.get('message')}")
        return

    for item in results["suspicious_ips"]:
        ip_addr = item["ip"]
        count = item["count"]
        time_str = results["alert_times"][ip_addr]

        detail = results["details"][ip_addr]

        ua = "".join(detail["user_agents"])
        paths = "\n    ".join(detail["full_paths"])
        bodies = "\n    ".join(detail["decoded_bodies"][:3])

        message = (
            f"[SQL Injection ALERT]\n"
            f" - IP: {ip_addr}\n"
            f" - Trong {results['seconds_window']} giây"
            f" - Lần xuất hiện đầu: {time_str}\n"
            f" - Tổng số lần: {count}\n"
            f" - User-Agents:\n    {ua}\n"
            f" - Full Paths:\n    {paths}\n"
            f" - Payload mẫu (decoded):\n    {bodies}"
        )

        await alert_queue.put({
            "content": message,
            "threat_type": "sqli"
        })

