import os
import json
import http.client
import socket
from config.elastic import es_async_client


WEBSERVER_HOST = os.getenv("WEBSERVER_HOST")
WEBSERVER_PORT_API = int(os.getenv("WEBSERVER_PORT_API", "5002"))
METRICS_TOKEN = os.getenv("X-METRICS-TOKEN")


def fetch_webserver_metrics():
    """Call API http://host:port/metrics and return dict or None."""
    try:
        conn = http.client.HTTPConnection(
            WEBSERVER_HOST, WEBSERVER_PORT_API, timeout=3
        )

        headers = {
            "X-METRICS-TOKEN": METRICS_TOKEN,
        }

        conn.request("GET", "/metrics", headers=headers)
        resp = conn.getresponse()
        data = resp.read()
        conn.close()

        if resp.status != 200:
            return None
        
        return json.loads(data.decode("utf-8"))

    except (socket.timeout, ConnectionRefusedError, Exception):
        return None


def format_webserver_text(m):
    if not m:
        return "Webserver Không Phản Hồi (timeout hoặc lỗi mạng)\n"

    cpu = m["cpu"]
    ram = m["ram"]
    disk = m["disk"]

    load = cpu["load_avg"]

    return (
        f"Webserver: {m['host']}\n"
        f" --- CPU ---\n"
        f"   - Usage: {cpu['percent']}%\n"
        f"   - Cores: {cpu['cores']}\n"
        f"   - Load Avg: {load['1m']}/{load['5m']}/{load['15m']}\n"
        f" --- RAM ---\n"
        f"   - Tổng: {ram['total_gb']} GB\n"
        f"   - Đang dùng: {ram['used_gb']} GB ({ram['percent']}%)\n"
        f"   - Còn trống: {ram['free_gb']} GB\n"
        f" --- DISK (/) ---\n"
        f"   - Tổng: {disk['total_gb']} GB\n"
        f"   - Dùng: {disk['used_gb']} GB ({disk['percent']}%)\n"
        f"   - Trống: {disk['free_gb']} GB\n"
    )


async def get_system_health():
    metrics = fetch_webserver_metrics()
    web_text = format_webserver_text(metrics)

    return web_text
