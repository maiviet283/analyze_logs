import re
import pandas as pd
from .base_logs import BaseLogFetcher
from datetime import datetime, timedelta, timezone


class DjangoLogFetcher(BaseLogFetcher):
    def __init__(self):
        super().__init__(index_pattern="django-logs-*")
        
    
    def fetch_logs(self, seconds=30, size=None, fields=None, methods=None, paths=None) -> pd.DataFrame:
        """
        Lấy logs trong X giây gần nhất + lọc theo method + path nếu cung cấp.
        """

        size = size or self.default_size

        # Tính thời gian theo UTC
        now_utc = datetime.now(timezone.utc)
        start_utc = now_utc - timedelta(seconds=seconds)

        gte_ts = self.to_es_timestamp(start_utc)
        lte_ts = self.to_es_timestamp(now_utc)

        # Điều kiện MUST
        must_conditions = [
            {
                "range": {
                    "@timestamp": {
                        "gte": gte_ts,
                        "lte": lte_ts
                    }
                }
            }
        ]

        # Filter theo HTTP method
        if methods:
            must_conditions.append({
                "terms": {
                    "method.keyword": methods
                }
            })

        # Filter theo đường dẫn (path) — SỬA LẠI TOÀN BỘ Ở ĐÂY
        if paths:
            must_conditions.append({
                "bool": {
                    "should": [
                        {"match_phrase": {"path": p}} for p in paths
                    ],
                    "minimum_should_match": 1
                }
            })

        query = {
            "sort": [{"@timestamp": {"order": "desc"}}],
            "size": size,
            "query": {
                "bool": {
                    "must": must_conditions
                }
            }
        }

        # Lấy đúng các field bạn yêu cầu
        if fields:
            query["_source"] = fields

        # Truy vấn Elasticsearch
        res = self.es.search(index=self.index_pattern, body=query)
        logs = [hit["_source"] for hit in res["hits"]["hits"]]

        return pd.DataFrame(logs)


    def fetch_and_save_latest_logs(
        self,
        n=10,
        flatten=True,
        json_path="latest_logs.json",
        csv_path="latest_logs.csv"
    ):
        """
        Lấy n logs mới nhất, flatten dict nếu cần, và lưu ra JSON + CSV.
        """
        query = {
            "sort": [{"@timestamp": {"order": "desc"}}],
            "size": n,
            "query": {"match_all": {}}
        }

        res = self.es.search(index=self.index_pattern, body=query)
        logs = [hit["_source"] for hit in res["hits"]["hits"]]

        df = pd.DataFrame(logs)

        if flatten:
            dict_columns = [c for c in df.columns if df[c].apply(lambda x: isinstance(x, dict)).any()]
            for col in dict_columns:
                normalized = pd.json_normalize(df[col]).add_prefix(f"{col}.")
                df = df.drop(columns=[col]).join(normalized)

        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', 200)
        pd.set_option('display.max_colwidth', None)

        # xuất file JSON
        if json_path:
            df.to_json(json_path, orient='records', force_ascii=False, indent=2)
            print(f"Đã xuất ra file JSON: {json_path}")

        # xuất file CSV
        if csv_path:
            df.to_csv(csv_path, index=False)
            print(f"Đã xuất ra file CSV: {csv_path}")

        return df