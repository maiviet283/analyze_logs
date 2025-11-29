import time
import os
from dotenv import load_dotenv
from controller.zeek_logs import check_zeek_scanner
from controller.django_logs import check_sqli_scanner

load_dotenv()

SECONDS_WINDOW = int(os.getenv("SECONDS_WINDOW", 10))


if __name__ == "__main__":
    try:
        while True:
            
            # check_sqli_scanner()
            check_zeek_scanner()
            
            time.sleep(SECONDS_WINDOW)
    except KeyboardInterrupt:
        print("=== SYSTEM STOPPED ===")
