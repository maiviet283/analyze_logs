import asyncio
import httpx
from config.alert_handler import process_alert

alert_queue = asyncio.Queue()

async def alert_worker():
    async with httpx.AsyncClient() as client:
        while True:
            try:
                job = await alert_queue.get()
            except asyncio.CancelledError:
                break

            try:
                await process_alert(client, job["content"], job["threat_type"])
            except Exception as e:
                print("[ERROR] Worker job failed:", e)
            finally:
                alert_queue.task_done()

        print("[INFO] Worker stopped cleanly.")
