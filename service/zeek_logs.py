import pandas as pd
import ipaddress
from datetime import datetime, timedelta, timezone
from .base_logs import BaseLogFetcher


class ZeekLogFetcher(BaseLogFetcher):
    def __init__(self):
        super().__init__(index_pattern="zeek-logs-*")
        self.last_timestamp = None


    async def fetch_logs(self, seconds=10):
        now_utc = datetime.now(timezone.utc)

        if self.last_timestamp is None:
            start_utc = now_utc - timedelta(seconds=seconds)
        else:
            start_utc = self.last_timestamp

        query = {
            "query": {
                "range": {
                    "@timestamp": {
                        "gt": start_utc.isoformat(),
                        "lte": now_utc.isoformat()
                    }
                }
            },
            "sort": [{"@timestamp": "asc"}]
        }

        all_hits = []
        search_after = None

        while True:
            if search_after:
                query["search_after"] = search_after

            res = await self.es.search(
                index=self.index_pattern,
                body=query,
                request_timeout=20
            )

            hits = res["hits"]["hits"]
            if not hits:
                break

            all_hits.extend(hits)
            search_after = hits[-1]["sort"]

        logs = [h["_source"] for h in all_hits]
        df = pd.DataFrame(logs)

        if not df.empty:
            df["@timestamp"] = pd.to_datetime(df["@timestamp"], utc=True, errors="coerce")
            self.last_timestamp = df["@timestamp"].max()

        return df


    async def detect_scanner(self, seconds=10, threshold_requests=50):
        df = await self.fetch_logs(seconds=seconds)

        if df.empty:
            return {"status": "no_data", "message": f"Không có logs trong {seconds} giây"}

        # Flatten dict
        dict_cols = [c for c in df.columns if df[c].apply(lambda x: isinstance(x, dict)).any()]
        for col in dict_cols:
            expanded = pd.json_normalize(df[col]).add_prefix(f"{col}.")
            df = df.drop(columns=[col]).join(expanded)

        # Tìm cột orig_h
        ip_candidates = [c for c in df.columns if c.endswith("orig_h")]
        if not ip_candidates:
            return {"status": "no_column", "message": "Không tìm thấy orig_h trong logs"}

        source_ip_col = ip_candidates[0]

        # Bắt buộc phải có timestamp
        if "@timestamp" not in df.columns:
            return {"status": "no_timestamp", "message": "Không có @timestamp"}

        df = df.dropna(subset=["@timestamp", source_ip_col])

        # Lọc IP hợp lệ
        def is_valid_ip(val):
            try:
                ipaddress.ip_address(str(val))
                return True
            except:
                return False

        df = df[df[source_ip_col].apply(is_valid_ip)]

        if df.empty:
            return {
                "status": "ok",
                "suspicious_ips": [],
                "alert_times": {},
                "ip_column": source_ip_col
            }

        # Đếm request
        counter = df.groupby(source_ip_col).size().reset_index(name="request_count")
        suspicious = counter[counter["request_count"] >= threshold_requests]

        if suspicious.empty:
            return {
                "status": "ok",
                "suspicious_ips": [],
                "alert_times": {},
                "ip_column": source_ip_col
            }

        # Lấy timestamp đầu tiên
        alert_times = {}
        for ip in suspicious[source_ip_col]:
            first_ts = df[df[source_ip_col] == ip]["@timestamp"].min()
            vn_time = first_ts.tz_convert("Asia/Ho_Chi_Minh")
            alert_times[ip] = vn_time.strftime("%d-%m-%Y %H:%M:%S")

        return {
            "status": "ok",
            "seconds_window": seconds,
            "threshold": threshold_requests,
            "suspicious_ips": suspicious.to_dict(orient="records"),
            "ip_column": source_ip_col,
            "alert_times": alert_times
        }
