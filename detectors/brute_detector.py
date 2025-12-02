import os
import asyncio
from datetime import datetime
from dotenv import load_dotenv
from collections import defaultdict, deque
from alert.anti_spam import can_alert
from alert.workers import alert_queue

load_dotenv()

THRESHOLD = int(os.getenv("NGINX_BRUTE_THRESHOLD", 50))
EXPIRE = int(os.getenv("NGINX_BRUTE_EXPIRE", 30))

# Mỗi IP có 1 deque để giữ timestamps của request gần nhất trong EXPIRE giây
REQUESTS = defaultdict(lambda: deque())

TARGET_URLS = {
    "/admin/login/",
    "/api/customers/login/",
}

def convert_time_local_to_vn(time_local: str) -> str:
    dt = datetime.strptime(time_local, "%d/%b/%Y:%H:%M:%S %z")
    return dt.strftime("Lúc %H:%M:%S Ngày %d/%m/%Y")


async def realtime_bruteforce_detector(streamer):
    loop = asyncio.get_event_loop()

    while True:
        async for log in streamer.stream_logs():

            ip = log.get("ip")
            method = log.get("method")
            url = log.get("url")
            user_agent = log.get("user_agent")
            time_local = log.get("time_local")
            vn_time = convert_time_local_to_vn(time_local)

            if not ip or not method or not url or not user_agent:
                continue

            # Chỉ POST request
            if method != "POST":
                continue

            # Chỉ những URL brute-force quan trọng
            if url not in TARGET_URLS:
                continue

            now = loop.time()
            dq = REQUESTS[ip]

            # Thêm timestamp của request hiện tại vào deque
            dq.append(now)

            # Loại bỏ request quá hạn EXPIRE giây
            while dq and now - dq[0] > EXPIRE:
                dq.popleft()

            count = len(dq)

            # Nếu vượt threshold thì cảnh báo
            if count >= THRESHOLD:
                if can_alert(ip):
                    msg = (
                        f"[Brute-Force ALERT] {vn_time}\n"
                        f" - IP: {ip}\n"
                        f" - URL: {url}\n"
                        f" - User-Agent: {user_agent}\n"
                        f" - Đã vượt ngưỡng brute-force với {count} requests trong {EXPIRE} giây."
                    )
                    await alert_queue.put({"content": msg, "threat_type": "bruteforce"})

        now = loop.time()
        expired_ips = [ip for ip, dq in REQUESTS.items() if dq and now - dq[-1] > EXPIRE]
        for ip in expired_ips:
            REQUESTS.pop(ip, None)

        await asyncio.sleep(0.05)
