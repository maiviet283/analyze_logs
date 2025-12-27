import http.client
import json
import os

LOGSTASH_HOST = os.getenv("LOGSTASH_HOST", "192.168.47.130")
LOGSTASH_PORT = int(os.getenv("LOGSTASH_PORT", "9600"))

async def get_logstash_status():
    """Kiểm tra trạng thái thực tế của Logstash."""
    try:
        conn = http.client.HTTPConnection(LOGSTASH_HOST, LOGSTASH_PORT, timeout=3)
        conn.request("GET", "/_node/stats")
        resp = conn.getresponse()
        data = resp.read()
        conn.close()

        if resp.status != 200:
            return f"Logstash ERROR: HTTP {resp.status}"

        stats = json.loads(data.decode())

        # Thông tin cơ bản
        version = stats["version"]
        pipeline_count = len(stats.get("pipelines", {}))

        # Events
        events = stats["events"]
        in_events = events.get("in", 0)
        out_events = events.get("out", 0)
        duration = events.get("duration_in_millis", 0)

        # JVM
        jvm = stats["jvm"]["mem"]
        heap_used = round(jvm["heap_used_in_bytes"] / 1024 / 1024, 2)
        heap_max = round(jvm["heap_max_in_bytes"] / 1024 / 1024, 2)

        return (
            "Logstash hoạt động bình thường\n"
            f" - Version: {version}\n"
            f" - Pipelines: {pipeline_count}\n"
            f" - Events in: {in_events}\n"
            f" - Events out: {out_events}\n"
            f" - Event duration(ms): {duration}\n"
            f" - JVM Heap: {heap_used}MB / {heap_max}MB"
        )

    except Exception as e:
        return f"Logstash ERROR: {e}"
