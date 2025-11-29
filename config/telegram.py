import os
import httpx
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

BASE_URL = f"https://api.telegram.org/bot{TOKEN}"


async def send_telegram_message(client: httpx.AsyncClient, text: str):
    try:
        r = await client.post(
            f"{BASE_URL}/sendMessage",
            data={"chat_id": CHAT_ID, "text": text},
            timeout=10
        )

        data = r.json()
        if not data.get("ok"):
            print("[ERROR] Telegram trả về lỗi:", data)

    except Exception as e:
        print("[ERROR] Lỗi Telegram:", e)
