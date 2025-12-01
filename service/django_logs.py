import re
import pandas as pd
from urllib.parse import unquote
from datetime import datetime, timedelta, timezone
from .base_logs import BaseLogFetcher


SQLI_PATTERN = re.compile(
    r"(?i)("
    r"(\bor\b|\band\b)\s+(\d+|'[^']*'|true|false)\s*=\s*(\d+|'[^']*'|true|false)"
    r"|(['\"]\s*--\s*$)"
    r"|(\bunion\b\s+\bselect\b)"
    r"|(\bdrop\b\s+\btable\b)"
    r"|(\binsert\b\s+into\b)"
    r"|(\bupdate\b\s+.+\bset\b)"
    r"|(\bdelete\b\s+\bfrom\b)"
    r"|(\bselect\b.+\bfrom\b)"
    r"|(\b1\s*=\s*1\b)"
    r"|(;?\s*shutdown\b)"
    r")"
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
        for ip in suspicious["ip"]:
            first = sqli_logs[sqli_logs["ip"] == ip]["@timestamp"].min()
            alert_times[ip] = first

        return {
            "status": "ok",
            "seconds_window": seconds,
            "threshold": threshold,
            "suspicious_ips": suspicious.to_dict(orient="records"),
            "alert_times": alert_times
        }
