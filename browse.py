"""Battery rundown test.

Scrolls through a fixed set of websites in a loop until the laptop shuts
down. While running, it appends the battery level to results_battery.csv
every minute, so the total runtime and the discharge curve survive the
power loss and can be read after the laptop reboots.
"""

from __future__ import annotations

import os
import sys

# When packaged as an exe (PyInstaller), Chromium is bundled inside the app
# folder instead of the user's browser cache — point Playwright at it.
if getattr(sys, "frozen", False):
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = "0"

import csv
import ctypes
import platform
import socket
import subprocess
import threading
import time
from datetime import datetime
from pathlib import Path

import psutil
from playwright.sync_api import sync_playwright

# 🔗 List of sites (keep this fixed across all tests)
URLS = [
    "https://www.straitstimes.com",
    "https://www.channelnewsasia.com",
    "https://www.bbc.com",
    "https://www.reddit.com",
    "https://en.wikipedia.org/wiki/Main_Page",
    "https://www.amazon.com",
    "https://www.youtube.com"
]

# ⏱️ Time per page (seconds)
PAGE_DURATION = 30

# 🖱️ Scroll settings
SCROLL_STEP = 300
SCROLL_DELAY = 1  # seconds

# 📊 Battery logging
RESULTS_FILE = "results_battery.csv"
LOG_INTERVAL_S = 60

CSV_FIELDS = [
    "laptop_name",
    "session_start",
    "timestamp",
    "elapsed_s",
    "battery_percent",
    "power_plugged",
    "design_capacity_mwh",
    "full_charge_capacity_mwh",
]

IS_WINDOWS = platform.system() == "Windows"


def keep_awake() -> None:
    """Stop Windows from sleeping or turning the screen off while we run."""
    if not IS_WINDOWS:
        return
    ES_CONTINUOUS = 0x80000000
    ES_SYSTEM_REQUIRED = 0x00000001
    ES_DISPLAY_REQUIRED = 0x00000002
    # Applies to this thread for as long as it lives, i.e. the whole test.
    ctypes.windll.kernel32.SetThreadExecutionState(
        ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED
    )


def battery_status() -> tuple[float | None, bool | None]:
    """Return (percent, plugged_in), or (None, None) if there is no battery."""
    b = psutil.sensors_battery()
    if b is None:
        return None, None
    return b.percent, b.power_plugged


def battery_capacities() -> tuple[int | None, int | None]:
    """Return (design_capacity_mwh, full_charge_capacity_mwh), best effort.

    A worn battery holds less than its design capacity; recording both makes
    battery wear visible when comparing runtimes across laptops.
    """
    if not IS_WINDOWS:
        return None, None

    def query(class_name: str, prop: str) -> int:
        out = subprocess.run(
            [
                "powershell", "-NoProfile", "-Command",
                f"(Get-CimInstance -Namespace root/wmi -ClassName {class_name}).{prop}",
            ],
            capture_output=True, text=True, timeout=30,
        )
        return int(out.stdout.strip().splitlines()[0])

    try:
        design = query("BatteryStaticData", "DesignedCapacity")
        full = query("BatteryFullChargedCapacity", "FullChargedCapacity")
        return design, full
    except Exception:
        return None, None


def wait_until_ready() -> None:
    """Refuse to start while the charger is plugged in; warn on low charge."""
    percent, plugged = battery_status()

    if plugged is None:
        print("WARNING: No battery detected - runtime results will be meaningless.")
        return

    if plugged:
        print()
        print(">>> Please UNPLUG the charger to begin the test.")
        print(">>> The test will start by itself once the charger is removed...")
        while plugged:
            time.sleep(2)
            percent, plugged = battery_status()
        print(">>> Charger removed - starting.")

    if percent is not None and percent < 95:
        print()
        print(f"WARNING: Battery is at {percent:.0f}%, not full.")
        print("For comparable results, charge to 100% before testing.")
        print("Continuing anyway...")


def append_row(row: dict) -> None:
    """Append one row to the CSV and force it onto disk immediately.

    The laptop will lose power without warning, so every row is flushed and
    fsync'd — the file must be readable after an abrupt shutdown.
    """
    file_exists = Path(RESULTS_FILE).exists()
    with open(RESULTS_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)
        f.flush()
        os.fsync(f.fileno())


def format_elapsed(seconds: float) -> str:
    h, rem = divmod(int(seconds), 3600)
    m = rem // 60
    return f"{h}h {m:02d}m"


def battery_logger(session_start: str, start_time: float,
                   design_mwh: int | None, full_mwh: int | None) -> None:
    """Runs in a background thread: one CSV row + heartbeat every minute."""
    while True:
        percent, plugged = battery_status()
        elapsed = time.time() - start_time

        append_row({
            "laptop_name": socket.gethostname(),
            "session_start": session_start,
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "elapsed_s": int(elapsed),
            "battery_percent": percent if percent is not None else "",
            "power_plugged": plugged if plugged is not None else "",
            "design_capacity_mwh": design_mwh or "",
            "full_charge_capacity_mwh": full_mwh or "",
        })

        if percent is not None:
            state = "CHARGING - unplug!" if plugged else "on battery"
            print(f"[{format_elapsed(elapsed)}] battery {percent:.0f}% ({state})")

        time.sleep(LOG_INTERVAL_S)


def browse(page):
    for url in URLS:
        try:
            print(f"Visiting {url}")
            page.goto(url, timeout=60000)

            start_time = time.time()
            while time.time() - start_time < PAGE_DURATION:
                # Scroll down
                page.mouse.wheel(0, SCROLL_STEP)
                time.sleep(SCROLL_DELAY)

            time.sleep(2)  # small pause before next page
        except Exception as e:
            # One bad page load must not end a multi-hour rundown.
            print(f"  Skipping {url} ({type(e).__name__})")


def browse_forever() -> None:
    """Run the browser until power loss; relaunch it if it ever crashes."""
    while True:
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=False,
                    args=[
                        "--start-maximized",
                        "--disable-notifications",
                        "--disable-infobars"
                    ]
                )

                context = browser.new_context(
                    viewport={"width": 1920, "height": 1080}
                )

                page = context.new_page()

                # 🔁 Loop forever (until battery dies)
                while True:
                    browse(page)
        except Exception as e:
            print(f"Browser stopped ({type(e).__name__}). Restarting in 10 seconds...")
            time.sleep(10)


def run():
    keep_awake()

    design_mwh, full_mwh = battery_capacities()
    percent, plugged = battery_status()

    print("=" * 60)
    print("BATTERY RUNDOWN TEST")
    print(f"  Laptop:        {socket.gethostname()}")
    print(f"  OS:            {platform.platform()}")
    if percent is not None:
        print(f"  Battery now:   {percent:.0f}%")
    if design_mwh and full_mwh:
        wear = 100.0 * (1 - full_mwh / design_mwh)
        print(f"  Battery health: {full_mwh} / {design_mwh} mWh "
              f"({wear:.1f}% wear)")
    print(f"  Logging to:    {RESULTS_FILE} (every {LOG_INTERVAL_S}s)")
    print("  Sleep and screen-off are blocked while the test runs.")
    print("=" * 60)

    wait_until_ready()

    session_start = datetime.now().isoformat(timespec="seconds")
    start_time = time.time()

    threading.Thread(
        target=battery_logger,
        args=(session_start, start_time, design_mwh, full_mwh),
        daemon=True,
    ).start()

    browse_forever()


if __name__ == "__main__":
    run()
