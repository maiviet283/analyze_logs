import pandas as pd
from .base_logs import BaseLogFetcher


class NginxLogFetcher(BaseLogFetcher):
    def __init__(self):
        super().__init__(index_pattern="nginx-logs-*")

    async def detect_bruteforce(self, seconds=20, threshold_requests=20):
        df = await self.fetch_logs(seconds=seconds)

        if df.empty:
            return {"status": "no_data", "message": f"Không có logs trong {seconds} giây"}

        required = ["ip", "method", "url", "@timestamp"]
        for col in required:
            if col not in df.columns:
                return {"status": "missing_field", "message": f"Thiếu cột {col} trong logs"}

        # Chuyển timestamp
        df["@timestamp"] = pd.to_datetime(df["@timestamp"], utc=True)

        # Lọc POST login
        df = df[
            (df["method"] == "POST") &
            (
                (df["url"] == "/api/customers/login/") |
                (df["url"].str.startswith("/admin/login"))
            )
        ]

        if df.empty:
            return {"status": "no_login", "message": "Không có POST login nào trong window"}

        # Đếm số request theo IP
        counter = df.groupby("ip").size().reset_index(name="request_count")
        suspicious = counter[counter["request_count"] >= threshold_requests]

        if suspicious.empty:
            return {"status": "safe", "message": "Không có brute-force"}

        # Lấy timestamp đầu tiên theo IP
        alert_times = {}
        for ip in suspicious["ip"]:
            first_ts = df[df["ip"] == ip]["@timestamp"].min()
            vn_time = first_ts.tz_convert("Asia/Ho_Chi_Minh")
            alert_times[ip] = vn_time.strftime("Ngày %d-%m-%Y, lúc %H:%M:%S")

        return {
            "status": "ok",
            "seconds_window": seconds,
            "threshold": threshold_requests,
            "suspicious_ips": suspicious.to_dict(orient="records"),
            "alert_times": alert_times,
        }
