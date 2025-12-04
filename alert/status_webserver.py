import os
import json
import http.client
import socket
from dotenv import load_dotenv

load_dotenv()

WEBSERVER_HOST = os.getenv("WEBSERVER_HOST")
WEBSERVER_PORT_API = int(os.getenv("WEBSERVER_PORT_API", "5002"))
METRICS_TOKEN = os.getenv("X-METRICS-TOKEN")

def fetch_nginx_status():
    """Call API /nginx-status để lấy trạng thái nginx."""
    try:
        conn = http.client.HTTPConnection(
            WEBSERVER_HOST, WEBSERVER_PORT_API, timeout=3
        )

        headers = {
            "X-METRICS-TOKEN": METRICS_TOKEN,
        }

        conn.request("GET", "/nginx-status", headers=headers)
        resp = conn.getresponse()
        data = resp.read()
        conn.close()

        if resp.status != 200:
            return None

        return json.loads(data.decode("utf-8"))

    except (socket.timeout, ConnectionRefusedError, Exception):
        return None

def fetch_gunicorn_status():
    """Call API /gunicorn-status để lấy trạng thái gunicorn."""
    try:
        conn = http.client.HTTPConnection(
            WEBSERVER_HOST, WEBSERVER_PORT_API, timeout=3
        )

        headers = {
            "X-METRICS-TOKEN": METRICS_TOKEN,
        }

        conn.request("GET", "/gunicorn-status", headers=headers)
        resp = conn.getresponse()
        data = resp.read()
        conn.close()

        if resp.status != 200:
            return None
        
        return json.loads(data.decode("utf-8"))

    except (socket.timeout, ConnectionRefusedError, Exception):
        return None

def format_nginx_text(data):
    if not data:
        return "NGINX: Không phản hồi (timeout hoặc lỗi mạng)\n"

    status = data.get("status", "unknown")

    return (
        f"NGINX Status:\n"
        f"   - Trạng thái: {status}\n"
    )

def format_gunicorn_text(data):
    if not data:
        return "Gunicorn: Không phản hồi (timeout hoặc lỗi mạng)\n"

    status = data.get("status", "unknown")

    return (
        f"Gunicorn Status:\n"
        f"   - Trạng thái: {status}\n"
    )

async def get_status_webserver():
    nginx = fetch_nginx_status()
    gunicorn = fetch_gunicorn_status()

    text = (
        format_nginx_text(nginx) +
        format_gunicorn_text(gunicorn)
    )

    return text
