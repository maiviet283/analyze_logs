import requests
import random
import sys
import time

# Một số User-Agent để làm hành vi giống bot fuzzing
USER_AGENTS = [
    "Mozilla/5.0 (Dirbuster)",
    "Mozilla/5.0 (FFUF Scanner)",
    "Mozilla/5.0 (Gobuster Agent)",
    "curl/8.0 fuzz",
    "python-requests fuzz",
    "Wfuzz/3.0",
]

# Wordlist mẫu – tạo ra hàng loạt request 404/403
COMMON_PATHS = [
    "admin", "admin123", "administrator", "backup", "config",
    "login", "log", "logs", "hidden", "private", "test", "testing",
    "dashboard", "root", "secret", "secrets", "internal",
    "phpinfo", "phpmyadmin", "server-status",
    "wp-admin", "wp-login", "wp-content", "env", ".env",
    "api", "api/v1", "api/internal", "sql", "database",
    "dev", "development", "staging", "prod", "production",
]

def directory_fuzz_soft(base_url, rps=20):
    """
    Kiểu fuzzing nhẹ → tạo hành vi path scanning thực tế:
    - Mỗi vòng gửi 15 -> 40 request.
    - Random User-Agent.
    - Random sleep để không "quá đều".
    """
    session = requests.Session()

    print(f"\n=== SOFT DIRECTORY FUZZ STARTED ===")
    print(f"Base URL: {base_url}")
    print(f"Target rate: ~{rps} requests/sec (ngẫu nhiên 15→40 per cycle)")
    print("Nhấn CTRL + C để dừng.\n")

    total = 0

    try:
        while True:
            burst = random.randint(15, 40)

            for _ in range(burst):
                path = random.choice(COMMON_PATHS)
                ua = random.choice(USER_AGENTS)

                url = f"{base_url}/{path}"
                headers = {"User-Agent": ua}

                try:
                    session.get(url, headers=headers, timeout=1)
                except:
                    pass

                total += 1

            # Điều chỉnh thời gian nghỉ để sát rps
            sleep_time = max(0.01, burst / rps)
            time.sleep(sleep_time)

            if total % 100 == 0:
                print(f"[INFO] Sent {total} fuzzing requests...")

    except KeyboardInterrupt:
        print("\n=== STOPPED BY USER ===")
        print(f"Tổng request đã gửi: {total}\n")


def main():
    if len(sys.argv) < 2:
        print("Usage: python directory_fuzz_soft.py <IP>")
        sys.exit(1)

    ip = sys.argv[1]
    base_url = f"http://{ip}"

    directory_fuzz_soft(base_url, rps=20)


if __name__ == "__main__":
    main()
