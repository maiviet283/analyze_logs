from config.elastic import es_async_client

async def fetch_log_type_counts_15min():
    query = {
        "size": 0,
        "query": {
            "range": {
                "@timestamp": {
                    "gte": "now-15m",
                    "lte": "now"
                }
            }
        },
        "aggs": {
            "by_type": {
                "terms": {
                    "field": "log_type.keyword",
                    "size": 10
                }
            }
        }
    }

    res = await es_async_client.search(
        index="*-logs-*",
        body=query
    )

    buckets = res["aggregations"]["by_type"]["buckets"]

    counts = {b["key"]: b["doc_count"] for b in buckets}

    # Ensure missing types = 0
    counts = {
        "django": counts.get("django", 0),
        "nginx": counts.get("nginx", 0),
        "zeek": counts.get("zeek", 0),
    }

    total = sum(counts.values())
    percentages = {
        k: (v / total * 100 if total else 0)
        for k, v in counts.items()
    }

    return counts, percentages
