from config.elastic import es_async_client

class BaseLogFetcher:
    """
    Base class for fetching logs from Elasticsearch.
    """
    def __init__(self, index_pattern: str):
        self.es = es_async_client
        self.index_pattern = index_pattern
