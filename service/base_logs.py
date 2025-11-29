import pandas as pd
from config.es import get_es_client
from datetime import datetime, timedelta, timezone


class BaseLogFetcher:
    def __init__(self, index_pattern, default_size=15000):
        self.es = get_es_client()
        self.index_pattern = index_pattern
        self.default_size = default_size

    
    def to_es_timestamp(self, dt: datetime) -> str:
        """
        Convert datetime object sang string format Elasticsearch nhận (UTC, Z)
        """
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)
        return dt.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


    def fetch_logs(self, seconds=10, size=None) -> pd.DataFrame:
        """
        Lấy logs trong X giây gần nhất
        """
        size = size or self.default_size

        now_local = datetime.now().astimezone()
        start_local = now_local - timedelta(seconds=seconds)

        now_utc = now_local.astimezone(timezone.utc)
        start_utc = start_local.astimezone(timezone.utc)

        gte_ts = self.to_es_timestamp(start_utc)
        lte_ts = self.to_es_timestamp(now_utc)

        query = {
            "sort": [{"@timestamp": {"order": "desc"}}],
            "size": size,
            "query": {
                "range": {
                    "@timestamp": {
                        "gte": gte_ts,
                        "lte": lte_ts
                    }
                }
            }
        }

        res = self.es.search(index=self.index_pattern, body=query)
        logs = [hit["_source"] for hit in res["hits"]["hits"]]
        
        return pd.DataFrame(logs)
    

    def head(self, n=10, drop_columns=None):
        """
        Lấy n logs mới nhất, hiển thị chi tiết, bỏ cột không cần thiết.
        drop_columns: list các tên cột muốn loại bỏ
        """
        df = self.fetch_logs(size=n)
        
        if drop_columns:
            df = df.drop(columns=[col for col in drop_columns if col in df.columns])
        
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', 200)
        pd.set_option('display.max_colwidth', None)
        return df.head(n)


    def print_sample_logs(self, n=10, drop_columns=None, flatten=True, json_path=None, csv_path=None):
        """
        Hiển thị n logs gần nhất, flatten dicts, bỏ cột không cần thiết,
        xuất ra file JSON và CSV nếu muốn.
        """
        df = self.fetch_logs(size=n)

        if drop_columns:
            df = df.drop(columns=[c for c in drop_columns if c in df.columns])

        if flatten:
            dict_columns = [c for c in df.columns if df[c].apply(lambda x: isinstance(x, dict)).any()]
            for col in dict_columns:
                normalized = pd.json_normalize(df[col]).add_prefix(f"{col}.")
                df = df.drop(columns=[col]).join(normalized)

        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', 200)
        pd.set_option('display.max_colwidth', None)

        print(df.head(n))

        if json_path:
            df.to_json(json_path, orient='records', force_ascii=False, indent=2)
            print(f"Đã xuất ra file JSON: {json_path}")

        if csv_path:
            df.to_csv(csv_path, index=False)
            print(f"Đã xuất ra file CSV: {csv_path}")

        return df.head(n)