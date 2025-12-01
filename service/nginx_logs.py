import pandas as pd
from datetime import datetime, timedelta, timezone
from .base_logs import BaseLogFetcher


class NginxLogFetcher(BaseLogFetcher):
    def __init__(self):
        super().__init__(index_pattern="nginx-logs-*")

    async def fetch_logs(self, seconds=10):
        now_utc = datetime.now(timezone.utc)
        start_utc = now_utc - timedelta(seconds=seconds)

        query = {
            "query": {
                "bool": {
                    "must": [
                        {"term": {"method.keyword": "POST"}}
                    ],
                    "filter": [
                        {
                            "range": {
                                "@timestamp": {
                                    "gte": start_utc.isoformat(),
                                    "lte": now_utc.isoformat()
                                }
                            }
                        },
                        {
                            "bool": {
                                "should": [
                                    {"term": {"url.keyword": "/api/customers/login/"}},
                                    {"term": {"url.keyword": "/admin/login/"}}
                                ],
                                "minimum_should_match": 1
                            }
                        }
                    ]
                }
            },
            "sort": [{"@timestamp": {"order": "asc"}}],
            "size": 5000
        }

        res = await self.es.options(request_timeout=20).search(
            index=self.index_pattern,
            body=query,
        )

        logs = [h["_source"] for h in res["hits"]["hits"]]
        df = pd.DataFrame(logs)

        if "@timestamp" in df.columns:
            df["@timestamp"] = pd.to_datetime(df["@timestamp"], utc=True, errors="coerce")

        return df

    async def detect_bruteforce(self, seconds=10, threshold_requests=20):
        df = await self.fetch_logs(seconds=seconds)
        
        print(f"[DEBUG] Fetched {len(df)} nginx POST login logs in last {seconds} seconds")

        if df.empty:
            return {"status": "no_data", "message": f"Không có POST login trong {seconds} giây"}

        required = ["ip", "@timestamp"]
        for col in required:
            if col not in df.columns:
                return {"status": "missing_field", "message": f"Thiếu cột {col} trong logs"}

        # Đếm số POST login theo IP
        counter = df.groupby("ip").size().reset_index(name="request_count")
        suspicious = counter[counter["request_count"] >= threshold_requests]

        if suspicious.empty:
            return {"status": "safe", "message": "Không có dấu hiệu brute-force"}

        # Tính timestamp đầu tiên theo IP
        alert_times = {}
        for ip in suspicious["ip"]:
            first = df[df["ip"] == ip]["@timestamp"].min()
            vn_time = first.tz_convert("Asia/Ho_Chi_Minh")
            alert_times[ip] = vn_time.strftime("%d-%m-%Y %H:%M:%S")

        return {
            "status": "ok",
            "seconds_window": seconds,
            "threshold_requests": threshold_requests,
            "suspicious_ips": suspicious.to_dict(orient="records"),
            "alert_times": alert_times,
            "df": df 
        }
