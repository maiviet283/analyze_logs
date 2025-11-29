import asyncio
from config.telegram import send_message
from config.chat_box import chat_bot
import time

async def tesst(message: str = "hello ban"):
    start = time.time()

    r = await chat_bot(message, "ddos")
    send_message(r)

    end = time.time()
    print(end - start)

asyncio.run(tesst("1 ip gui 1000 request trong 10s"))
asyncio.run(tesst("1 ip gui 20000 request trong 10s"))
asyncio.run(tesst("1 ip gui 10 request trong 10s"))