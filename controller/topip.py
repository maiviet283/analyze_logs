import csv
import os

TOPIP_PATH = "data/topip.csv"


def load_topip():
    """Đọc file CSV thành dict {ip: count}."""
    data = {}

    if not os.path.exists(TOPIP_PATH):
        with open(TOPIP_PATH, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["ip", "count"])
        return data

    with open(TOPIP_PATH, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            ip = row["ip"]
            count = int(row["count"])
            data[ip] = count

    return data


def save_topip(data: dict):
    """Ghi dict {ip: count} trở lại CSV."""
    with open(TOPIP_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["ip", "count"])
        for ip, count in data.items():
            writer.writerow([ip, count])


def add_attack_ip(ip: str):
    """Tăng số lượng tấn công của IP hoặc thêm mới."""
    data = load_topip()
    if ip in data:
        data[ip] += 1
    else:
        data[ip] = 1
    save_topip(data)


def get_topip_list(limit=None):
    """
    Lấy danh sách IP theo yêu cầu.
    limit=None  -> lấy 10 IP
    limit="all" -> lấy toàn bộ
    limit=n     -> lấy n IP
    """
    data = load_topip()

    sorted_data = sorted(data.items(), key=lambda x: x[1], reverse=True)

    if limit is None:
        sorted_data = sorted_data[:10]
    elif isinstance(limit, int):
        sorted_data = sorted_data[:limit]
    elif isinstance(limit, str) and limit.lower() == "all":
        pass  # giữ nguyên toàn bộ danh sách
    else:
        return None

    return sorted_data


def format_topip_message(data):
    """
    Format danh sách IP thành chuỗi có thứ tự để gửi Telegram.
    """
    if not data:
        return "Không có dữ liệu IP tấn công nào."

    lines = ["Top IP tấn công nhiều nhất:"]
    for i, (ip, count) in enumerate(data, start=1):
        lines.append(f"{i}. {ip} - {count} lần")

    return "\n".join(lines)
