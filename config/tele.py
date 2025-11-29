import os
from dotenv import load_dotenv
import requests
from threading import Thread

load_dotenv()

TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

BASE_URL = f"https://api.telegram.org/bot{TOKEN}"


def _send_request(url, data=None, files=None):
    try:
        r = requests.post(url, data=data, files=files, timeout=10)

        # Kiểm tra lỗi HTTP
        if r.status_code != 200:
            print(f"[ERROR] Telegram HTTP {r.status_code}: {r.text}")
            return None

        # Kiểm tra parse JSON
        try:
            result = r.json()
        except Exception as e:
            print(f"[ERROR] Không parse được JSON từ Telegram: {e}")
            return None

        # Kiểm tra Telegram API có trả về ok=false không
        if not result.get("ok", False):
            print(f"[ERROR] Telegram API báo lỗi: {result}")
            return None

        return result

    except requests.exceptions.Timeout:
        print("[ERROR] Telegram timeout (quá 10s).")
    except requests.exceptions.ConnectionError:
        print("[ERROR] Lỗi kết nối đến Telegram API.")
    except Exception as e:
        print(f"[ERROR] Gửi Telegram thất bại: {e}")

    return None


def send_message(text):
    """Gửi tin nhắn văn bản bất đồng bộ bằng thread"""
    def run():
        url = f"{BASE_URL}/sendMessage"
        data = {"chat_id": CHAT_ID, "text": text}
        result = _send_request(url, data=data)
        if result is None:
            print("[WARN] Gửi tin nhắn thất bại.")
    Thread(target=run).start()


def send_photo(photo_url_or_path, caption=None):
    """Gửi ảnh bất đồng bộ bằng thread"""
    def run():
        url = f"{BASE_URL}/sendPhoto"

        # Trường hợp gửi link ảnh
        if isinstance(photo_url_or_path, str) and photo_url_or_path.startswith("http"):
            data = {"chat_id": CHAT_ID, "photo": photo_url_or_path}
            if caption:
                data["caption"] = caption

            result = _send_request(url, data=data)
            if result is None:
                print("[WARN] Gửi ảnh qua URL thất bại.")
            return

        # Trường hợp gửi file local
        try:
            with open(photo_url_or_path, "rb") as f:
                files = {"photo": f}
                data = {"chat_id": CHAT_ID}
                if caption:
                    data["caption"] = caption

                result = _send_request(url, data=data, files=files)
                if result is None:
                    print("[WARN] Gửi ảnh file thất bại.")

        except FileNotFoundError:
            print(f"[ERROR] File không tồn tại: {photo_url_or_path}")
        except Exception as e:
            print(f"[ERROR] Lỗi khi mở hoặc gửi file ảnh: {e}")

    Thread(target=run).start()
