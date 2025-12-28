#!/usr/bin/env python3
# /usr/local/bin/webserver_metrics_service.py

from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import time
import os
import subprocess

HOST = "0.0.0.0"
PORT = int(os.environ.get("METRICS_PORT", "5002"))
EXPECTED_TOKEN = os.environ.get("METRICS_TOKEN", "changeme")

def systemctl_action(service, action):
    """Thực hiện start/stop/restart/status systemd service."""
    if action not in ("start", "stop", "restart", "status"):
        return {"error": "invalid action"}

    try:
        out = subprocess.check_output(
            ["systemctl", action, service],
            stderr=subprocess.STDOUT,
            timeout=5
        )
        return {
            "service": service,
            "action": action,
            "result": out.decode().strip()
        }
    except subprocess.CalledProcessError as e:
        return {
            "service": service,
            "action": action,
            "error": e.output.decode().strip()
        }

def nginx_test():
    try:
        out = subprocess.check_output(
            ["nginx", "-t"],
            stderr=subprocess.STDOUT,
            timeout=5
        )
        return {"result": out.decode().strip()}
    except subprocess.CalledProcessError as e:
        return {"error": e.output.decode().strip()}


def service_status(service_name):
    """Kiểm tra trạng thái systemd service."""
    try:
        out = subprocess.check_output(["systemctl", "is-active", service_name], stderr=subprocess.STDOUT)
        status = out.decode().strip()
        return status  # active, inactive, failed, activating
    except:
        return "unknown"


def process_exists(keyword):
    """Fallback: kiểm tra process nếu service không khả dụng."""
    try:
        pgrep = subprocess.call(["pgrep", "-f", keyword])
        return pgrep == 0  # 0 = tìm thấy process
    except:
        return False


def get_uptime():
    try:
        with open("/proc/uptime") as f:
            uptime_seconds = float(f.readline().split()[0])

        days = int(uptime_seconds // 86400)
        hours = int((uptime_seconds % 86400) // 3600)
        minutes = int((uptime_seconds % 3600) // 60)

        return {
            "uptime": f"{days}d {hours}h {minutes}m",
            "loadavg": read_loadavg()
        }
    except:
        return {"uptime": "unknown"}


def process_top(limit=10):
    try:
        out = subprocess.check_output(
            ["ps", "-eo", "pid,comm,%cpu,%mem", "--sort=-%cpu"],
            text=True
        )
        lines = out.strip().splitlines()
        header = lines[0]
        body = lines[1:limit+1]

        return {
            "header": header,
            "processes": body
        }
    except Exception as e:
        return {"error": str(e)}


def ports_listen():
    try:
        out = subprocess.check_output(
            ["ss", "-lntup"],
            stderr=subprocess.STDOUT,
            text=True
        )
        return {"result": out.strip()}
    except Exception as e:
        return {"error": str(e)}


# ====================== CPU ======================
def read_cpu_percent():
    """Đo CPU % sử dụng thông qua /proc/stat (real-time, ổn định)."""
    try:
        with open("/proc/stat", "r") as f:
            a = f.readline().split()[1:]
        idle1 = int(a[3])
        total1 = sum(map(int, a))

        time.sleep(0.5)

        with open("/proc/stat", "r") as f:
            b = f.readline().split()[1:]
        idle2 = int(b[3])
        total2 = sum(map(int, b))

        idle_delta = idle2 - idle1
        total_delta = total2 - total1

        if total_delta == 0:
            return 0.0

        usage = 100.0 * (1 - idle_delta / total_delta)
        return round(usage, 2)

    except:
        return 0.0


def read_loadavg():
    """Load average (1,5,15 min)."""
    try:
        with open("/proc/loadavg", "r") as f:
            l1, l5, l15, *_ = f.readline().split()
        return float(l1), float(l5), float(l15)
    except:
        return 0.0, 0.0, 0.0


def cpu_cores():
    """Số lượng core vật lý / logical."""
    try:
        return os.cpu_count()
    except:
        return 1


# ====================== RAM ======================
def read_ram():
    """Trả về total/used/free (GB) + % used."""
    try:
        mem = {}
        with open("/proc/meminfo") as f:
            for line in f:
                parts = line.split()
                key = parts[0].rstrip(":")
                val = int(parts[1])  # kB
                mem[key] = val

        total = mem["MemTotal"] * 1024
        avail = mem["MemAvailable"] * 1024
        used = total - avail

        gb = 1024 * 1024 * 1024
        return {
            "total_gb": round(total / gb, 2),
            "used_gb": round(used / gb, 2),
            "free_gb": round(avail / gb, 2),
            "percent": round((used / total) * 100, 2),
        }

    except:
        return {"total_gb": 0, "used_gb": 0, "free_gb": 0, "percent": 0}


# ====================== DISK ======================
def read_disk():
    """Trả về total/used/free (GB) + % used."""
    try:
        st = os.statvfs("/")
        total = st.f_blocks * st.f_frsize
        free = st.f_bavail * st.f_frsize
        used = total - free

        gb = 1024 * 1024 * 1024

        return {
            "total_gb": round(total / gb, 2),
            "used_gb": round(used / gb, 2),
            "free_gb": round(free / gb, 2),
            "percent": round((used / total) * 100, 2),
        }
    except:
        return {"total_gb": 0, "used_gb": 0, "free_gb": 0, "percent": 0}


# ====================== HTTP Handler ======================
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):

        # ======== Validate token ========
        token = self.headers.get("X-METRICS-TOKEN", "m0n0t0n1c-s3cr3t-xxx")
        if token != EXPECTED_TOKEN:
            self.send_response(403)
            self.end_headers()
            self.wfile.write(b"Forbidden")
            return

        # ======== API: /metrics ========
        if self.path == "/metrics":
            cpu_percent = read_cpu_percent()
            load1, load5, load15 = read_loadavg()
            ram = read_ram()
            disk = read_disk()

            payload = {
                "host": os.uname().nodename,
                "timestamp": int(time.time()),
                "cpu": {
                    "percent": cpu_percent,
                    "load_avg": {"1m": load1, "5m": load5, "15m": load15},
                    "cores": cpu_cores(),
                },
                "ram": ram,
                "disk": disk,
            }

            body = json.dumps(payload).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        # ======== API: /nginx-status ========
        if self.path == "/nginx-status":
            status = service_status("nginx")
            if status == "unknown":  # fallback
                running = process_exists("nginx")
                status = "active" if running else "inactive"

            payload = {"service": "nginx", "status": status}
            body = json.dumps(payload).encode()

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        # ======== API: /gunicorn-status ========
        if self.path == "/gunicorn-status":
            status = service_status("gunicorn")
            if status == "unknown":
                running = process_exists("gunicorn")
                status = "active" if running else "inactive"

            payload = {"service": "gunicorn", "status": status}
            body = json.dumps(payload).encode()

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        
        # ======== API: /nginx/test ========
        if self.path == "/nginx-test":
            payload = nginx_test()
            body = json.dumps(payload).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        
        # ======== API: /uptime ========
        if self.path == "/uptime":
            payload = get_uptime()
            body = json.dumps(payload).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        
        # ======== API: /process/top ========
        if self.path == "/process/top":
            payload = process_top()
            body = json.dumps(payload).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        
        # ======== API: /ports ========
        if self.path == "/ports":
            payload = ports_listen()
            body = json.dumps(payload).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        # ======== Not found ========
        self.send_response(404)
        self.end_headers()
        
        
    def do_POST(self):
        token = self.headers.get("X-METRICS-TOKEN", "m0n0t0n1c-s3cr3t-xxx")
        if token != EXPECTED_TOKEN:
            self.send_response(403)
            self.end_headers()
            return

        if self.path.startswith("/nginx/"):
            action = self.path.split("/")[-1]
            payload = systemctl_action("nginx", action)

        elif self.path.startswith("/gunicorn/"):
            action = self.path.split("/")[-1]
            payload = systemctl_action("gunicorn", action)

        else:
            self.send_response(404)
            self.end_headers()
            return

        body = json.dumps(payload).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        return


def run():
    server = HTTPServer((HOST, PORT), Handler)
    print(f"Metrics service running at {HOST}:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    run()