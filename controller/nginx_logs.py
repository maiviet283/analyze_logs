import os
from dotenv import load_dotenv
from service.nginx_logs import NginxLogFetcher
from alert.workers import alert_queue

load_dotenv()

SECONDS_WINDOW = int(os.getenv("SECONDS_WINDOW", 10))
NGINX_BRUTE_THRESHOLD = int(os.getenv("NGINX_BRUTE_THRESHOLD", 20))

nginx_fetcher = NginxLogFetcher()


async def check_nginx_bruteforce():
    results = await nginx_fetcher.detect_bruteforce(
        seconds=SECONDS_WINDOW,
        threshold_requests=NGINX_BRUTE_THRESHOLD
    )

    if results["status"] != "ok":
        print(f"[INFO] Nginx: {results.get('message')}")
        return

    suspicious = results["suspicious_ips"]
    alert_times = results["alert_times"]

    for item in suspicious:
        ip_addr = item["ip"]
        time_str = alert_times[ip_addr]

        base_message = (
            f"[Bruteforce ALERT] {time_str}\n"
            f"IP {ip_addr}\n"
            f"Gửi {item['request_count']} POST login trong {SECONDS_WINDOW} giây"
        )

        await alert_queue.put({
            "content": base_message,
            "threat_type": "bruteforce"
        })
