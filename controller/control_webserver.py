import json
import http.client
import os
import socket

HOST = os.getenv("WEBSERVER_HOST")
PORT = int(os.getenv("WEBSERVER_PORT_API", "5002"))
TOKEN = os.getenv("X-METRICS-TOKEN")

def call(path, method="GET"):
    try:
        conn = http.client.HTTPConnection(HOST, PORT, timeout=4)
        headers = {"X-METRICS-TOKEN": TOKEN}
        conn.request(method, path, headers=headers)
        resp = conn.getresponse()
        data = resp.read()
        conn.close()
        if resp.status != 200:
            return None
        return json.loads(data.decode())
    except (socket.timeout, Exception):
        return None

def nginx_cmd(action):
    if action == "test":
        return call("/nginx-test")
    return call(f"/nginx/{action}", "POST")

def gunicorn_cmd(action):
    return call(f"/gunicorn/{action}", "POST")

def format_result(title, data):
    if not data:
        return f"{title}: Không phản hồi"

    if "error" in data:
        return f"{title} ERROR:\n{data['error']}"

    if "result" in data:
        return f"{title}:\n{data['result']}"

    return f"{title}:\n{json.dumps(data, indent=2)}"

def uptime_cmd():
    return call("/uptime")

def process_top_cmd():
    return call("/process/top")

def ports_cmd():
    return call("/ports")

def format_uptime(data):
    if not data:
        return "Không lấy được uptime"

    uptime = data.get("uptime", "unknown")
    load = data.get("loadavg", (0, 0, 0))

    return (
        f"UPTIME: {uptime}\n"
        f"LOAD AVG: {load[0]} | {load[1]} | {load[2]}"
    )

def format_process_top(data):
    if not data:
        return "Không lấy được process list"

    header = data.get("header", "")
    processes = data.get("processes", [])

    body = "\n".join(processes)
    text = f"{header}\n{body}"

    return text[:3800]  # Telegram limit

def format_ports(data):
    if not data:
        return "Không lấy được danh sách port"

    if "error" in data:
        return f"Lỗi ports:\n{data['error']}"

    return data.get("result", "")[:3800]
