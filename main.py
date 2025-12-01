import os
import time
import asyncio
from dotenv import load_dotenv

from controller.zeek_logs import check_zeek_scanner
from controller.nginx_logs import check_nginx_bruteforce

from alert.workers import alert_worker
from config.elastic import es_async_client

load_dotenv()

SECONDS_WINDOW = int(os.getenv("SECONDS_WINDOW", 10))


async def analysis_loop():
    next_run = time.time()

    while True:
        start = time.time()
        
        await check_zeek_scanner()
        await check_nginx_bruteforce()


        next_run += SECONDS_WINDOW
        sleep_time = next_run - time.time()

        if sleep_time > 0:
            await asyncio.sleep(sleep_time)

        end = time.time()
        print(f"=== Hoàn thành vòng phân tích trong {end - start:.2f} giây ===")


async def main():
    tasks = [
        asyncio.create_task(alert_worker()),
        asyncio.create_task(analysis_loop()),
    ]

    try:
        await asyncio.gather(*tasks)

    except asyncio.CancelledError:
        pass

    finally:
        print("=== Đang đóng Elasticsearch client ===")
        await es_async_client.close()

        print("=== Đóng background tasks ===")
        for t in tasks:
            t.cancel()

        print("=== Đã shutdown sạch sẽ ===")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("=== SYSTEM STOPPED BY USER ===")
