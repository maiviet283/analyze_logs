import os
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from service.zeek_logs import ZeekLogFetcher
from config.tele import send_message
from alert.chat_box import chat_bot

load_dotenv()

SECONDS_WINDOW = int(os.getenv("SECONDS_WINDOW", 10))
THRESHOLD_REQUESTS = int(os.getenv("THRESHOLD_REQUESTS", 1000))

zeek_fetcher = ZeekLogFetcher()


def check_zeek_scanner():
    """
    Kiểm tra Zeek logs để phát hiện các IP có hành vi quét mạng (scanner)
    """
    
    results = zeek_fetcher.detect_scanner(
        seconds=SECONDS_WINDOW, 
        threshold_requests=THRESHOLD_REQUESTS
    )

    if results["status"] == "ok":
        suspicious = results.get("suspicious_ips", [])
        alert_times = results.get("alert_times", {})
        ip_col = results["ip_column"]

        if suspicious:
            for ip in suspicious:
                ip_addr = ip[ip_col]
                time_str = alert_times.get(ip_addr, "Không xác định")
                
                alert = f"[Scanner ALERT] {time_str} Phát hiện IP {ip_addr} gửi {ip['request_count']} requests trong {SECONDS_WINDOW} giây"
                
                result_alert = chat_bot(alert, "ddos")
                print(alert)
                
                alert_msg = (
                    f"[Scanner ALERT] {time_str}\n"
                    f" - IP: {ip_addr}\n"
                    f" - Số lần : {ip['request_count']}\n"
                    f" - Trong {SECONDS_WINDOW} giây\n"
                    f"Hành động đề xuất bởi AI: {result_alert}"
                )
                
                send_message(alert_msg)
        else:
            now_vn = datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=7)))
            time_str = now_vn.strftime("Ngày %d-%m-%Y, lúc %H:%M:%S")
    else:
        print(f"[INFO] Zeek: {results.get('message', 'Không có dữ liệu')}")
