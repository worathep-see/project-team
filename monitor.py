import psutil
import time
import csv
from datetime import datetime

DURATION = 30 * 60   # 30 นาที
INTERVAL = 1        # วัดทุก 1 วินาที

with open("locust_smart_client.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow([
        "timestamp",
        "cpu_percent",
        "ram_used_mb",
        "ram_available_mb",
        "ram_percent"
    ])

    print("📊 Start monitoring CPU & RAM (Ctrl+C to stop)\n")

    try:
        start = time.time()
        while time.time() - start < DURATION:
            timestamp = datetime.now().strftime("%H:%M:%S")

            cpu = psutil.cpu_percent(interval=None)
            ram = psutil.virtual_memory()
            ram_used = ram.used / (1024 * 1024)
            ram_available = ram.available / (1024 * 1024)

            # ---- write CSV ----
            writer.writerow([
                datetime.now().isoformat(),
                cpu,
                round(ram_used, 2),
                round(ram_available, 2),
                ram.percent
            ])
            f.flush()

            # ---- print terminal ----
            print(
                f"[{timestamp}] "
                f"CPU: {cpu:5.1f}% | "
                f"RAM: {ram.percent:5.1f}% "
                f"({ram_used:7.1f} / {ram_available:7.1f} MB)"
            )

            time.sleep(INTERVAL)

    except KeyboardInterrupt:
        print("\n🛑 Monitoring stopped by user")

    finally:
        print("✅ Metrics saved to metrics_cpu_ram.csv")
