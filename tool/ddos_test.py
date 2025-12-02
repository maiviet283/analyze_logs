import requests
import time
import random
import threading
import sys

HEADERS = {
    "User-Agent": "LoadBurstTester/1.0"
}

def worker(url, rps):
    """
    Worker tạo traffic HTTP nhanh → dùng để test hệ thống DDoS detector
    Đây KHÔNG phải tấn công DDoS thật.
    """
    session = requests.Session()
    interval = 1 / rps

    sent = 0

    while True:
        try:
            session.get(url, headers=HEADERS, timeout=0.5)
        except:
            pass

        sent += 1

        if sent % 50 == 0:
            print(f"[Worker] Sent {sent} requests (rps={rps})")

        time.sleep(interval)


def start_load_test(target_url, threads=5, min_rps=30, max_rps=80):
    print(f"\n=== Load Burst Test ===")
    print(f"Target: {target_url}")
    print(f"Threads: {threads}")
    print(f"RPS/Thread: {min_rps} → {max_rps}")
    print("Nhấn CTRL+C để dừng.\n")

    try:
        for i in range(threads):
            rps = random.randint(min_rps, max_rps)
            t = threading.Thread(target=worker, args=(target_url, rps), daemon=True)
            t.start()

        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n=== STOPPED ===\n")


def main():
    if len(sys.argv) < 2:
        print("Usage: python load_burst.py <IP> [threads]")
        sys.exit(1)

    ip = sys.argv[1]
    threads = int(sys.argv[2]) if len(sys.argv) > 2 else 5

    url = f"http://{ip}/"

    start_load_test(url, threads)


if __name__ == "__main__":
    main()
