import re
import os
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta

from service.django_logs import DjangoLogFetcher
from config.telegram import send_message
from config.env import  THRESHOLD_SQLI, SECONDS_WINDOW

load_dotenv()

SQLI_PATTERNS = [
    r"(\%27)|(\')|(\-\-)|(\%23)|(#)",
    r"(union(\s)+select)",
    r"(or(\s)+1=1)",
    r"(or(\s)+'1'='1')",
    r"(sleep\()",
    r"(benchmark\()",
    r"(information_schema)",
    r"(\bselect\b|\binsert\b|\bupdate\b|\bdelete\b|\bdrop\b|\bexec\b)",
]
SQLI_REGEX = re.compile("|".join(SQLI_PATTERNS), re.IGNORECASE)


def detect_sqli(body: str) -> bool:
    """
    Trả về True nếu body chứa dấu hiệu SQL injection.
    """
    if not body:
        return False
    return bool(SQLI_REGEX.search(body))


django_fetcher = DjangoLogFetcher()

def check_sqli_scanner():
    """
    Quét logs theo khoảng thời gian cố định và phát hiện SQL injection scanner.
    """

    logs = django_fetcher.fetch_logs(
        seconds=SECONDS_WINDOW + 20,  # bạn muốn rộng hơn để không miss
        methods=["POST"],
        paths=["/admin/login/", "/api/customers/login/"],
        fields=[
            "@timestamp", "timestamp", "path", "full_path",
            "body", "ip", "status_code", "user_agent"
        ],
    )
    print(f"[SQLI SCANNER] Lấy được {len(logs)} log trong {SECONDS_WINDOW} giây gần nhất.")

    if logs.empty:
        return

    suspicious = []
    counter_by_ip = {}

    for _, row in logs.iterrows():
        body = str(row.get("body") or "")

        if detect_sqli(body):
            suspicious.append(row)

            ip = row.get("ip")
            counter_by_ip[ip] = counter_by_ip.get(ip, 0) + 1

    if not suspicious:
        return

    # Gửi alert theo từng IP
    for ip, count in counter_by_ip.items():

        if count >= THRESHOLD_SQLI:

            now_vn = datetime.now(timezone.utc).astimezone(
                timezone(timedelta(hours=7))
            )
            time_str = now_vn.strftime("%d-%m-%Y %H:%M:%S")

            alert_msg = (
                f"[SQL Injection ALERT]\n"
                f"Thời gian: {time_str}\n"
                f"IP: {ip}\n"
                f"Số request nghi ngờ: {count}\n"
                f"Trong {SECONDS_WINDOW} giây\n"
            )

            for item in suspicious:
                if item.get("ip") != ip:
                    continue

                alert_msg += (
                    f"-------------------------------\n"
                    f"Time: {item.get('timestamp') or item.get('@timestamp')}\n"
                    f"Path: {item.get('path')}\n"
                    f"Full Path: {item.get('full_path')}\n"
                    f"Status: {item.get('status_code')}\n"
                    f"User-Agent: {item.get('user_agent')}\n"
                    f"Body: {item.get('body')}\n"
                )

            print("[ALERT SQLI] Phát hiện SQL Injection từ IP:", ip)
            send_message(alert_msg)