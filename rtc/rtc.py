import os
from ds1302 import DS1302
from datetime import datetime

# --- Configuration ---
CLK_PIN = 17  # RTC_CLK -> GPIO17 (Pin 11)
DAT_PIN = 27  # RTC_DAT -> GPIO27 (Pin 13)
RST_PIN = 22  # RTC_RST -> GPIO22 (Pin 15)
# ---------------------

try:
    rtc = DS1302(CLK_PIN, DAT_PIN, RST_PIN)

    # 1. Get the time from the DS1302 module
    print("Reading local time from DS1302...")
    second = rtc.second()
    minute = rtc.minute()
    hour = rtc.hour()
    day = rtc.day()
    month = rtc.month()
    year = rtc.year() + 2000 

    # 2. Format it into a string
    new_system_time = f"{year:04d}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}:{second:02d}"

    print(f"Time from RTC (Local): {new_system_time}")

    # 3. Use 'os.system' to set the system time
    print("Setting system time from RTC...")
    os.system(f"sudo date -s '{new_system_time}'") # <<< MUDANÇA AQUI (removido --utc)
    print("System time updated successfully!")

except Exception as e:
    print(f"Error: {e}")
    print("Failed to sync time from RTC. Is it wired correctly?")

finally:
    if 'rtc' in locals():
        rtc.cleanupGPIO()