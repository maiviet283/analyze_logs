import asyncio
from config.elastic import es_async_client

class BaseStreamer:
    def __init__(self, index_pattern: str):
        self.es = es_async_client
        self.index_pattern = index_pattern
        self.search_after = None
        self.fast_forward_done = False

    async def fast_forward(self):
        """
        Khi hệ thống khởi động: skip toàn bộ log quá khứ.
        Lấy log mới nhất làm search_after → chỉ nhận log tương lai.
        """
        try:
            res = await self.es.search(
                index=self.index_pattern,
                body={
                    "size": 1,
                    "sort": [
                        {"@timestamp": "desc"},
                        {"log.offset": "desc"}
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
            print("[ERROR] fast_forward error:", e)
            self.fast_forward_done = True  # để tránh loop deadlock nếu lỗi

    async def stream_logs(self):
        # Đảm bảo fast-forward được gọi trước
        if not self.fast_forward_done:
            await self.fast_forward()

        while True:
            query = {
                "size": 300,
                "sort": [
                    {"@timestamp": "asc"},
                    {"log.offset": "asc"}
                ],
                "query": {"match_all": {}},
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
