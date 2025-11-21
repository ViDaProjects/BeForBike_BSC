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
        
            
            
