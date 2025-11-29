import pandas as pd
from datetime import datetime, timedelta, timezone
from config.elastic import es_async_client


class BaseLogFetcher:
    def __init__(self, index_pattern: str):
        self.es = es_async_client
        self.index_pattern = index_pattern

    async def fetch_logs(self, seconds=10) -> pd.DataFrame:
        now_utc = datetime.now(timezone.utc)
        start_utc = now_utc - timedelta(seconds=seconds)

        query = {
            "query": {
                "range": {
                    "@timestamp": {
                        "gte": start_utc.isoformat(),
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
        return pd.DataFrame(logs)
