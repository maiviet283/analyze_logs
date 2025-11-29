import os
from dotenv import load_dotenv
import sys
from elasticsearch import Elasticsearch, ConnectionError, TransportError

load_dotenv()

ELASTIC_HOST = os.getenv("ELASTIC_HOST", "http://192.168.47.130:9200")
ELASTIC_USER = os.getenv("ELASTIC_USER", "elastic")
ELASTIC_PASSWORD = os.getenv("ELASTIC_PASSWORD", "Bigdreamer123@#.")


def get_es_client():
    try:
        es = Elasticsearch(
            [ELASTIC_HOST],
            basic_auth=(ELASTIC_USER, ELASTIC_PASSWORD),
            verify_certs=False,
            request_timeout=10
        )

        if not es.ping():
            print("Không thể ping đến Elasticsearch. Kiểm tra lại server!")
            sys.exit(1)

        print("Kết nối Elasticsearch thành công!")
        return es

    except ConnectionError:
        print("Lỗi kết nối: Không thể kết nối đến Elasticsearch.")
        print("Kiểm tra lại IP, port, hoặc server có đang chạy không.")
        sys.exit(1)

    except TransportError as e:
        print(f"Lỗi transport: {e}")
        sys.exit(1)

    except Exception as e:
        print(f"Lỗi không xác định: {type(e).__name__}: {e}")
        sys.exit(1)
