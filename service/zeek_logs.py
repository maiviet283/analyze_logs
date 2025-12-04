from .base_streamer import BaseStreamer
from config.elastic import es_async_client
import asyncio


class ZeekStreamer(BaseStreamer):
    def __init__(self):
        super().__init__(index_pattern="zeek-logs-*")

    async def fast_forward(self):
        """Zeek logs không có log.offset → fast-forward chỉ theo @timestamp"""
        try:
            res = await self.es.search(
                index=self.index_pattern,
                body={
                    "size": 1,
                    "sort": [
                        {"@timestamp": "desc"}
                    ],
                    "query": {"match_all": {}}
                }
            )

            hits = res["hits"]["hits"]
            if hits:
                self.search_after = hits[0]["sort"]
                print(f"[FAST-FORWARD] {self.index_pattern} bắt đầu từ log mới nhất")
            else:
                print(f"[FAST-FORWARD] {self.index_pattern} không có logs")

            self.fast_forward_done = True

        except Exception as e:
            print("[ERROR] fast_forward Zeek:", e)
            self.fast_forward_done = True

    async def stream_logs(self):
        """Streamer riêng của Zeek: chỉ sort theo timestamp"""
        if not self.fast_forward_done:
            await self.fast_forward()

        while True:
            query = {
                "size": 300,
                "sort": [
                    {"@timestamp": "asc"}
                ],
                "query": {"match_all": {}}
            }

            if self.search_after:
                query["search_after"] = self.search_after

            res = await self.es.search(
                index=self.index_pattern,
                body=query,
                request_timeout=20
            )

            hits = res["hits"]["hits"]

            if hits:
                for h in hits:
                    yield h["_source"]

                self.search_after = hits[-1]["sort"]

            else:
                await asyncio.sleep(0.2)
