import os
import sys
from dotenv import load_dotenv
from elasticsearch import AsyncElasticsearch

load_dotenv()

ELASTIC_HOST = os.getenv("ELASTIC_HOST")
ELASTIC_USER = os.getenv("ELASTIC_USER")
ELASTIC_PASSWORD = os.getenv("ELASTIC_PASSWORD")


class AsyncElasticsearchSingleton:
    _instance: AsyncElasticsearch = None

    @classmethod
    def get_instance(cls) -> AsyncElasticsearch:
        if cls._instance is None:
            cls._instance = cls._create_client()
        return cls._instance

    @classmethod
    def _create_client(cls) -> AsyncElasticsearch:
        try:
            es = AsyncElasticsearch(
                hosts=[ELASTIC_HOST],
                basic_auth=(ELASTIC_USER, ELASTIC_PASSWORD),
                verify_certs=False,
                request_timeout=10
            )
            print("AsyncElasticsearch kết nối thành công")
            return es
        except Exception as e:
            print("Không thể khởi tạo AsyncElasticsearch:", e)
            sys.exit(1)


es_async_client = AsyncElasticsearchSingleton.get_instance()
