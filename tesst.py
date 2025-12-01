import asyncio
import json
from datetime import datetime, timedelta, timezone
from config.elastic import es_async_client

OUTPUT_FILE = "sample/django_sample.json"
INDEX = "django-logs-*"


async def fetch_nginx_sample(seconds=100, size=200):
    now_utc = datetime.now(timezone.utc)
    start_utc = now_utc - timedelta(seconds=seconds)

    print(f"=== Querying Elasticsearch for last {seconds} seconds ===")

    query = {
        "query": {
            "range": {
                "@timestamp": {
                    "gte": start_utc.isoformat(),
                    "lte": now_utc.isoformat()
                }
            }
        },
        "sort": [{"@timestamp": {"order": "asc"}}],
        "size": size
    }

    # Sửa cách truyền request_timeout để tránh warning
    res = await es_async_client.options(request_timeout=20).search(
        index=INDEX,
        body=query
    )

    hits = res["hits"]["hits"]
    print(f"=== Received {len(hits)} Nginx logs ===")

    # Lấy dữ liệu raw
    data = [h["_source"] for h in hits]

    # Xuất ra file JSON
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"=== Saved sample logs to {OUTPUT_FILE} ===")

    if not data:
        print("=== NO LOGS FOUND ===")
        await es_async_client.close()
        return

    # Tổng hợp danh sách cột
    all_keys = set()
    for entry in data:
        all_keys.update(entry.keys())

    print("\n=== ALL FIELDS FOUND IN NGINX LOGS ===")
    for k in sorted(all_keys):
        print(k)

    # In mẫu 3 record đầu tiên để xem cấu trúc chi tiết
    print("\n=== SAMPLE RECORDS (first 3) ===")
    for i, entry in enumerate(data[:3], start=1):
        print(f"\n--- Record #{i} ---")
        for key, value in entry.items():
            print(f"{key}: {value}")

    await es_async_client.close()


if __name__ == "__main__":
    asyncio.run(fetch_nginx_sample())
