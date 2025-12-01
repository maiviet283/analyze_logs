import httpx
from config.chat_box import generate_ai_recommendation
from config.telegram import send_telegram_message


async def process_alert(client: httpx.AsyncClient, content: str, threat_type: str):
    ai_action = await generate_ai_recommendation(content, threat_type)

    final_message = (
        f"{content}\n"
        f"Hành động đề xuất bởi AI: {ai_action}"
    )

    await send_telegram_message(client, final_message)
