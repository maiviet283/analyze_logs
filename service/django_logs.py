import re
import pandas as pd
from urllib.parse import unquote
from datetime import datetime, timedelta, timezone
from .base_logs import BaseLogFetcher


SQLI_PATTERN = re.compile(
    r"(?i)("

    # Boolean-based
    r"\bor\b\s+\d+\s*=\s*\d+"
    r"|\bor\b\s+'[^']+'\s*=\s*'[^']+'"
    r"|\band\b\s+\d+\s*=\s*\d+"
    r"|\band\b\s+'[^']+'\s*=\s*'[^']+'"
    r"|\bor\s+true\b"
    r"|\bor\s+1=1\b"
    r"|\band\s+1=1\b"
    r"|\bor\s+'x'='x'"

    # Union-based
    r"|\bunion\b\s+(\ball\b\s+)?\bselect\b"
    r"|\bunion\b.*\bselect\b.*(from|version|user|database)"

    # Stacked queries
    r"|;.*\bdrop\b\s+\btable\b"
    r"|;.*\bshutdown\b"
    r"|;.*\bupdate\b"
    r"|;.*\binsert\b"
    r"|;.*\bdelete\b\s+from\b"

    # UPDATE/INSERT/DELETE patterns
    r"|\bupdate\b\s+\w+\s+\bset\b"
    r"|\binsert\b\s+into\b"
    r"|\bdelete\b\s+from\b"

    # SELECT patterns
    r"|\bselect\b.+\bfrom\b"
    r"|\bselect\b\s+\*?\s*from\b"

    # Error-based injections (MySQL)
    r"|\bextractvalue\s*\("
    r"|\bupdatexml\s*\("
    r"|\bgeometrycollection\s*\("
    r"|\bpolygon\s*\("
    r"|\bconvert\s*\("
    r"|\bconcat_ws\s*\("
    r"|\bbenchmark\s*\("
    r"|\brand\s*\("
    r"|\bif\s*\(.*sleep"

    # Time-based
    r"|\bsleep\s*\("
    r"|\bwaitfor\s+delay\b"

    # Comments (SQL)
    r"|--"
    r"|#"
    r"|/\*.*\*/"

    # Hex-based
    r"|0x[0-9a-fA-F]+"

    # SQL keywords unlikely in login
    r"|\border\b\s+by\b"
    r"|\bgroup\b\s+by\b"

    # Payload signs: `'='` trick
    r"|'[^']*'\s*=\s*'[^']*'"

    # URL encoded injections
    r"|%27"
    r"|%23"
    r"|%2F%2A"
    r"|%2D%2D"

    ")"
)

class DjangoLogFetcher(BaseLogFetcher):
    def __init__(self):
        super().__init__(index_pattern="django-logs-*")

    async def fetch_logs(self, seconds=30, size=5000, paths=None):
        now = datetime.now(timezone.utc)
        start = now - timedelta(seconds=seconds)

        must_conditions = [
            {"range": {"@timestamp": {"gte": start.isoformat(), "lte": now.isoformat()}}},
            {"term": {"method.keyword": "POST"}},
        ]

        if paths:
            must_conditions.append({
                "bool": {
                    "should": [{"match_phrase": {"full_path": p}} for p in paths],
                    "minimum_should_match": 1
                }
            })

        query = {
            "sort": [{"@timestamp": {"order": "desc"}}],
            "size": size,
            "_source": ["@timestamp", "ip", "method", "full_path", "body",
                        "user_agent", "status_code"],
            "query": {"bool": {"must": must_conditions}}
        }

        res = await self.es.search(index=self.index_pattern, body=query)
        hits = [h["_source"] for h in res["hits"]["hits"]]
        return pd.DataFrame(hits)


    async def detect_sql_injection(self, seconds=10, threshold=3):
        df = await self.fetch_logs(
            seconds=seconds,
            paths=["/api/customers/login/", "/admin/login/"]
        )
        
        print(f"[DEBUG] Django logs fetched: {len(df)} entries")

        if df.empty:
            return {"status": "no_data", "message": f"Không có dữ liệu POST trong {seconds} giây"}

        # Chỉ giữ những log có body
        df["decoded_body"] = df["body"].apply(lambda x: unquote(str(x)))

        # Kiểm tra SQL injection trong body
        df["is_sqli"] = df["decoded_body"].apply(
            lambda x: bool(SQLI_PATTERN.search(x))
        )

        sqli_logs = df[df["is_sqli"]]

        if sqli_logs.empty:
            return {"status": "safe", "message": "Không có SQL Injection phát hiện"}

        # Đếm theo IP
        counter = sqli_logs.groupby("ip").size().reset_index(name="count")
        suspicious = counter[counter["count"] >= threshold]

        if suspicious.empty:
            return {"status": "safe", "message": "SQLi có xuất hiện nhưng chưa vượt ngưỡng cảnh báo"}

        alert_times = {}
        alert_details = {}
        
        for ip in suspicious["ip"]:
            logs = sqli_logs[sqli_logs["ip"] == ip]
            
            first = sqli_logs[sqli_logs["ip"] == ip]["@timestamp"].min()
            alert_times[ip] = first
            
            alert_details[ip] = {
                "user_agents": logs["user_agent"].unique().tolist(),
                "full_paths": logs["full_path"].unique().tolist(),
                "bodies": logs["body"].tolist(),
                "decoded_bodies": logs["decoded_body"].tolist()
            }

        return {
            "status": "ok",
            "seconds_window": seconds,
            "threshold": threshold,
            "suspicious_ips": suspicious.to_dict(orient="records"),
            "alert_times": alert_times,
            "details": alert_details
        }
