import os
import asyncio
from datetime import datetime
from collections import defaultdict, deque
from dotenv import load_dotenv
from alert.anti_spam import can_alert
from alert.workers import alert_queue
from controller.topip import add_attack_ip

load_dotenv()

THRESHOLD = int(os.getenv("NGINX_DIRBRUTE_THRESHOLD", 40))
EXPIRE = int(os.getenv("NGINX_DIRBRUTE_EXPIRE", 20))
MAX_DIR_IPS = int(os.getenv("MAX_DIR_IPS", 5000))

REQUESTS = defaultdict(lambda: deque())

SUSPICIOUS_STATUS = {"404", "403", "401", "405"}

def convert_time_local_to_vn(time_local: str) -> str:
    dt = datetime.strptime(time_local, "%d/%b/%Y:%H:%M:%S %z")
    return dt.strftime("Lúc %H:%M:%S Ngày %d/%m/%Y")


async def realtime_directory_bruteforce(streamer):
    """
    Directory fuzzing detection.
    - Không đụng code brute force cũ
    - Không sửa streamer
    - Không sửa BaseStreamer
    """

    loop = asyncio.get_event_loop()

    while True:
        async for log in streamer.stream_logs():

            ip = log.get("ip")
            url = log.get("url")
            status = log.get("status")
            user_agent = log.get("user_agent")
            time_local = log.get("time_local")

            if not ip or not url or not status or not time_local or not user_agent:
                continue

            # Chỉ bắt status liên quan đến directory fuzzing
            if status not in SUSPICIOUS_STATUS:
                continue

            vn_time = convert_time_local_to_vn(time_local)
            now = loop.time()
            dq = REQUESTS[ip]

            dq.append(now)

            # Loại request cũ
            while dq and now - dq[0] > EXPIRE:
                dq.popleft()

            count = len(dq)

            if count >= THRESHOLD and can_alert(f"dir-{ip}"):
                msg = (
                    f"[Directory Bruteforce ALERT] {vn_time}\n"
                    f" - IP: {ip}\n"
                    f" - URL mẫu cuối: {url}\n"
                    f" - Status: {status}\n"
                    f" - User-Agent: {user_agent}\n"
                    f" - {count} requests bất thường (404/403/401/405) trong {EXPIRE} giây."
                )

                await alert_queue.put({
                    "content": msg,
                    "threat_type": "dir_bruteforce"
                })
                
                print(f"[Directory Bruteforce ALERT] IP: {ip} - ({vn_time})")
                
                add_attack_ip(ip)

        # Cleanup
        now = loop.time()
        expired_ips = [
            ip for ip, dq in REQUESTS.items()
            if not dq or (now - dq[-1] > EXPIRE)
        ]
        for ip in expired_ips:
            REQUESTS.pop(ip, None)

        if len(REQUESTS) > MAX_DIR_IPS:
            REQUESTS.clear()

        await asyncio.sleep(0.05)
