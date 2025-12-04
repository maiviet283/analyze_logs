import os
import httpx
import asyncio
import traceback
from dotenv import load_dotenv
from .chat_box import generate_ai_recommendation
from alert.status_elastic import get_elasticsearch_status
from alert.status_webserver import get_status_webserver
from controller.topip import get_topip_list, format_topip_message

load_dotenv()

TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

BASE_URL = f"https://api.telegram.org/bot{TOKEN}"


async def send_telegram_message(client: httpx.AsyncClient, text: str):
    try:
        r = await client.post(
            f"{BASE_URL}/sendMessage",
            data={"chat_id": CHAT_ID, "text": text},
            timeout=17
        )

        data = r.json()
        if not data.get("ok"):
            print("[ERROR] Telegram trả về lỗi:", data)

    except Exception as e:
        print("[ERROR] Lỗi Telegram:", e)
        

async def send_photo(client, chat_id, photo_path: str):
    try:
        with open(photo_path, "rb") as f:
            await client.post(
                f"{BASE_URL}/sendPhoto",
                files={"photo": f},
                data={"chat_id": chat_id}
            )
    except Exception as e:
        print("Lỗi gửi ảnh:", e)


async def send_to(client, chat_id, text: str):
    try:
        await client.post(
            f"{BASE_URL}/sendMessage",
            data={"chat_id": chat_id, "text": text},
            timeout=10
        )
    except Exception as e:
        print("Lỗi gửi tin:", e)



async def listen_telegram():
    print("Bot đang lắng nghe tin nhắn Telegram...")

    offset = None

    async with httpx.AsyncClient(timeout=None) as client:
        while True:
            try:
                r = await client.get(
                    f"{BASE_URL}/getUpdates",
                    params={"offset": offset, "timeout": 15}
                )

                data = r.json()

                if not data.get("ok"):
                    print("Telegram error:", data)
                    await asyncio.sleep(1)
                    continue

                updates = data.get("result", [])

                for update in updates:
                    offset = update["update_id"] + 1

                    message = update.get("message")
                    if not message:
                        continue

                    chat = message["chat"]
                    chat_id = chat["id"]
                    text = message.get("text", "")

                    if text == "/logs":
                        from chart.export_chart import handle_chart
                        await handle_chart(client, chat_id)

                    elif text == "/help":
                        await send_to(client, chat_id,(
                            "Các lệnh khả dụng: \n"
                            "/logs : Xuất biểu đồ logs của toàn hệ thống và tính toán tỷ lệ \n"
                            "/elastic : Kiểm tra trạng thái thực tế của Elasticsearch. \n"
                            "/webserver : Kiểm tra trạng thái thực tế của Nginx + Gunicorn. \n"
                            "/health : Kiểm tra trạng thái của CPU, RAM, Disk của máy Ubuntu Server \n"
                            "/topip <số cụ thể | all> : Xem danh sách số lượng IP tấn công vào hệ thống nhiều nhất \n" 
                            "/chat <message> : Trao đổi với chatbot về hệ thống và kiến thức bảo mật"
                        ))
                        
                    elif text == "/elastic":
                        status_text = await get_elasticsearch_status()
                        await send_to(client, chat_id, status_text)
                        
                    elif text == "/webserver":
                        status_text = await get_status_webserver()
                        await send_to(client, chat_id, status_text)
                        
                    elif text.startswith("/topip"):
                        _, _, payload = text.partition(" ")
                        payload = payload.strip()

                        if payload == "":
                            list_data = get_topip_list(None)
                            msg = format_topip_message(list_data)
                            await send_to(client, chat_id, msg)

                        elif payload.lower() == "all":
                            list_data = get_topip_list("all")
                            msg = format_topip_message(list_data)
                            await send_to(client, chat_id, msg)

                        elif payload.isdigit():
                            n = int(payload)
                            list_data = get_topip_list(n)
                            msg = format_topip_message(list_data)
                            await send_to(client, chat_id, msg)

                        else:
                            await send_to(client, chat_id, "Sai cú pháp. Ví dụ: /topip 10 hoặc /topip all")

                    elif text == "/health":
                        from alert.health import get_system_health
                        reply = await get_system_health()
                        evaluate = await generate_ai_recommendation(reply, "evaluate")
                        result = reply + "Đánh Giá bởi AI :" + evaluate
                        await send_to(client, chat_id, result)
                        
                    elif text.startswith("/chat"):
                        _, _, payload = text.partition(" ")
                        if payload.strip():
                            ai_recommendation = await generate_ai_recommendation(payload, "chat")
                            await send_to(client, chat_id, ai_recommendation)
                        else:
                            await send_to(client, chat_id, "Vui lòng nhập nội dung sau /chat. Ví dụ: /chat hello")

                    else: 
                        await send_to(client, chat_id,(
                            "Nội Dung Không Hợp Lệ, vui lòng gõ /help để xem thêm thông tin"
                        ))

            except Exception as e:
                print("Lỗi polling:", repr(e))
                traceback.print_exc()
                await asyncio.sleep(3)