from config.elastic import es_async_client

async def get_elasticsearch_status():
    """Kiểm tra trạng thái thực tế của Elasticsearch."""
    try:
        # Lấy cluster health
        health = await es_async_client.cluster.health()
        status = health.get("status", "unknown")

        # Lấy bản build/version
        info = await es_async_client.info()
        version = info["version"]["number"]

        # Đếm tổng số index
        cat_indices = await es_async_client.cat.indices(format="json")
        index_count = len(cat_indices)

        # Tính tổng document
        total_docs = sum(int(idx.get("docs.count", 0)) for idx in cat_indices)

        # Ghép thông tin
        return (
            f"Hệ Thống Hoạt Động Ổn Định\n"
            f"Elastic hoạt động bình thường\n"
            f" - Trạng thái: {status}\n"
            f" - Version: {version}\n"
            f" - Số lượng index: {index_count}\n"
            f" - Tổng số documents: {total_docs}"
        )

    except Exception as e:
        return f"Elastic ERROR: {e}"
