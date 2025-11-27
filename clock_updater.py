from PySide6.QtCore import QObject, QTimer, QDate, Signal, QDateTime, QLocale

import logging

class DateChangeWatcher(QObject):
    dateChanged = Signal(str)   # emits the date string yyyy-MM-dd

    def __init__(self, parent=None):
        self.locale = QLocale(QLocale.Portuguese)
        super().__init__(parent)
        #self._last_date = QDate.currentDate()
        self._last_date = QDateTime.currentDateTime()
        # Check once per minute (or more often if needed)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._check_date)
        self.timer.start(60 * 1000)  # 1 minute

    def emit_text(self):
        current = QDateTime.currentDateTime()
        month_name = self.locale.toString(current.date(), "MMM")
        day_hour_min = current.toString("dd HH:mm")

        formatted = f"{month_name}{day_hour_min}"

        logging.info(f"[DateChangeWatcher] Time changed to {formatted}")
        self.dateChanged.emit(formatted)

    def _check_date(self):
        current = QDateTime.currentDateTime()

        if current != self._last_date:
            self._last_date = current
            self.emit_text()

import os
#try:
#    from ds1302 import DS1302
#except:
#    logging.info("[CLOCK_UPDATER] Real time clock library does not exist")
from datetime import datetime
from datetime import datetime, timezone, timedelta
import logging

# --- Configuration ---
CLK_PIN = 17  # RTC_CLK -> GPIO17 (Pin 11)
DAT_PIN = 27  # RTC_DAT -> GPIO27 (Pin 13)
RST_PIN = 22  # RTC_RST -> GPIO22 (Pin 15)

            
class GPSClock:

    def __init__(self):
        self.rtc = None
        try:
            #from ds1302 import DS1302
            self.rtc = DS1302(CLK_PIN, DAT_PIN, RST_PIN)
            logging.info("[CLOCK_UPDATER] RTC DS1302 inicializado com sucesso.")
        except Exception as e:
            logging.error(f"[CLOCK_UPDATER] Falha ao inicializar o DS1302: {e}")
            #self.log.error("Verifique as permissões de GPIO ou se o hardware está conectado.")
        
    def update_time(self, real_time):

        dt_utc = real_time.replace(tzinfo=timezone.utc)
        fuso_local_desejado = timezone(timedelta(hours=-3))
        dt_local = dt_utc.astimezone(fuso_local_desejado)

        if dt_local:
            
            day_of_week_to_set = dt_local.isoweekday() # 1=Seg, ... 7=Dom

            date_list = [
                dt_local.second,
                dt_local.minute,
                dt_local.hour,
                dt_local.day,
                dt_local.month,
                day_of_week_to_set,
                dt_local.year - 2000
            ]
            
            try:
                #from ds1302 import DS1302
                rtc = DS1302(CLK_PIN, DAT_PIN, RST_PIN)
                rtc.setDateTime(date_list)
                logging.info("[CLOCK_UPDATER] Time updated correctly")
                logging.info("[GPS_CLOCK_UPDATER] Reading local time from DS1302...")
                second = rtc.second()
                minute = rtc.minute()
                hour = rtc.hour()
                day = rtc.day()
                month = rtc.month()
                year = rtc.year() + 2000

                # 2. Format it into a string
                new_system_time = f"{year:04d}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}:{second:02d}"

                logging.info(f"[CLOCK_UPDATER] Time from RTC (Local): {new_system_time}")

                # 3. Use 'os.system' to set the system time
                logging.info("[CLOCK_UPDATER] Setting system time from RTC...")
                status = os.system(f"sudo date -s '{new_system_time}'") # <<< MUDAN ^gA AQUI (removido --utc)
                logging.info("[CLOCK_UPDATER] {status}")
            except Exception as e:
                logging.error(f"[CLOCK_UPDATER] Erro ao tentar escrever no RTC: {e}")

            finally:
                if 'rtc' in locals():
                    self.rtc.cleanupGPIO()

        try:
            

            # 1. Get the time from the DS1302 module
            logging.info("[GPS_CLOCK_UPDATER] Reading local time from DS1302...")
            second = self.rtc.second()
            minute = self.rtc.minute()
            hour = self.rtc.hour()
            day = self.rtc.day()
            month = self.rtc.month()
            year = self.rtc.year() + 2000

            # 2. Format it into a string
            new_system_time = f"{year:04d}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}:{second:02d}"

            logging.info(f"[CLOCK_UPDATER] Time from RTC (Local): {new_system_time}")

            # 3. Use 'os.system' to set the system time
            logging.info("[CLOCK_UPDATER] Setting system time from RTC...")
            status = os.system(f"sudo date -s '{new_system_time}'") # <<< MUDAN ^gA AQUI (removido --utc)
            logging.info("[CLOCK_UPDATER] {status}")
            logging.info("[CLOCK_UPDATER] System time updated successfully!")

        except Exception as e:
            logging.info(f"[CLOCK_UPDATER] Error: {e}")
            logging.info("[CLOCK_UPDATER] Failed to sync time from RTC. Is it wired correctly?")

        finally:
            if 'rtc' in locals():
                self.rtc.cleanupGPIO()
