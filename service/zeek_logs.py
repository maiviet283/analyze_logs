import pandas as pd
from .base_logs import BaseLogFetcher

class ZeekLogFetcher(BaseLogFetcher):
    """
    Async fetcher cho Zeek logs từ Elasticsearch.
    """
    def __init__(self):
        super().__init__(index_pattern="zeek-logs-*")

    async def detect_scanner(self, seconds=20, threshold_requests=50):
        df = await self.fetch_logs(seconds=seconds)

        if df.empty:
            return {"status": "no_data", "message": f"Không có logs trong {seconds} giây"}

        # Flatten các cột dict nếu có
        dict_columns = [c for c in df.columns if df[c].apply(lambda x: isinstance(x, dict)).any()]
        for col in dict_columns:
            df = df.drop(columns=[col]).join(pd.json_normalize(df[col]).add_prefix(f"{col}."))

        # Tìm cột IP nguồn
        ip_candidates = [c for c in df.columns if "orig" in c and "h" in c]
        if not ip_candidates:
            return {"status": "no_column", "message": "Không tìm thấy cột IP nguồn trong logs"}
        source_ip_col = ip_candidates[0]

        if "@timestamp" not in df.columns:
            return {"status": "no_timestamp", "message": "Không tìm thấy @timestamp trong logs"}

        # Giữ cột cần thiết và chuyển timestamp sang datetime
        df = df[["@timestamp", source_ip_col]].copy()
        df["@timestamp"] = pd.to_datetime(df["@timestamp"], utc=True)

        # Đếm request mỗi IP trong window
        counter = df.groupby(source_ip_col).size().reset_index(name="request_count")
        suspicious = counter[counter["request_count"] >= threshold_requests]

        # Lấy thời gian log đầu tiên của mỗi IP
        alert_times = {}
        for ip in suspicious[source_ip_col]:
            first_ts = df[df[source_ip_col] == ip]["@timestamp"].min()
            vn_time = first_ts.tz_convert("Asia/Ho_Chi_Minh")
            alert_times[ip] = vn_time.strftime("Ngày %d-%m-%Y, lúc %H:%M:%S")

        return {
            "status": "ok",
            "seconds_window": seconds,
            "threshold": threshold_requests,
            "suspicious_ips": suspicious.to_dict(orient="records"),
            "ip_column": source_ip_col,
            "alert_times": alert_times
        }
