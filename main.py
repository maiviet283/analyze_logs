import asyncio

from service.nginx_logs import NginxStreamer
from service.django_logs import DjangoStreamer
from service.zeek_logs import ZeekStreamer

from detectors.sqli_detector import realtime_sqli_detector
from detectors.brute_detector import realtime_bruteforce_detector
from detectors.ddos_detector import realtime_ddos_detector

from alert.workers import alert_worker
from config.elastic import es_async_client

async def main():
    nginx = NginxStreamer()
    django = DjangoStreamer()
    zeek = ZeekStreamer()

    # Gọi fast-forward trước khi streaming → tránh replay log
    await nginx.fast_forward()
    await django.fast_forward()
    await zeek.fast_forward()

    tasks = [
        asyncio.create_task(alert_worker()),

        asyncio.create_task(realtime_sqli_detector(django)),
        asyncio.create_task(realtime_bruteforce_detector(nginx)),
        asyncio.create_task(realtime_ddos_detector(zeek)),
    ]


    try:
        await asyncio.gather(*tasks)
    except asyncio.CancelledError:
        pass
    finally:
        print("Đóng Elasticsearch client")
        await es_async_client.close()

        for t in tasks:
            t.cancel()

        print("Shutdown sạch sẽ")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("=== STOPPED BY USER ===")
