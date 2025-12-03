import os
import matplotlib.pyplot as plt
from service.all_logs import fetch_log_type_counts_15min
from config.telegram import send_photo, send_to

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMAGE_DIR = os.path.join(BASE_DIR, "image")
os.makedirs(IMAGE_DIR, exist_ok=True)


def create_pie_chart(counts, percentages):
    labels = ["django", "nginx", "zeek"]
    values = [counts[k] for k in labels]

    colors = [
        "#3B82F6",
        "#EC4848",
        "#1EA751",
    ]

    plt.figure(figsize=(5.2, 5.2))

    # Custom autopct để hiển thị: django – 50.1%
    def label_function(pct, allvals):
        total = sum(allvals)
        index = label_function.idx
        label = labels[index]
        label_function.idx += 1
        return f"{label}: {pct:.1f}%" if pct > 0 else ""

    label_function.idx = 0

    wedges, texts, autotexts = plt.pie(
        values,
        colors=colors,
        labels=None,
        autopct=lambda pct: label_function(pct, values),
        pctdistance=0.75, # vị trí hiển thị %
        startangle=90,
        wedgeprops={"linewidth": 1, "edgecolor": "white"},
        textprops={"fontsize": 11},
    )

    # Làm text đẹp hơn
    for t in autotexts:
        t.set_weight("bold")
        t.set_color("#111827")  # Slate-900

    plt.axis("equal")  # tròn đều
    plt.tight_layout()

    chart_path = os.path.join(IMAGE_DIR, "chart.png")
    plt.savefig(chart_path, dpi=140, bbox_inches="tight")
    plt.clf()
    plt.close('all')

    return chart_path


async def handle_chart(client, chat_id):
    await send_to(client, chat_id, "Đang lấy dữ liệu vui lòng chờ trong vài giây…")

    counts, percentages = await fetch_log_type_counts_15min()

    if sum(counts.values()) == 0:
        await send_to(client, chat_id, "Không có logs trong 15 phút gần nhất.")
        return

    chart_path = create_pie_chart(counts, percentages)

    msg = (
        f"Toàn Bộ Logs của Hệ Thống trong 15 phút gần nhất \n"
        f" - Django có: {counts['django']} logs\n"
        f" - Nginx có: {counts['nginx']} logs\n"
        f" - Zeek có: {counts['zeek']} logs\n"
    )
    await send_to(client, chat_id, msg)
    await send_photo(client, chat_id, chart_path)
