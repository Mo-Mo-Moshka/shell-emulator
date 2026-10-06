"""Журнал вызовов команд в формате CSV.

Каждая строка журнала — одно событие вызова команды:
дата, время, имя команды, аргументы, статус и текст ошибки.
"""

import csv
import os
from datetime import datetime

LOG_FIELDS = ("date", "time", "command", "arguments", "status", "error")
DATE_FORMAT = "%Y-%m-%d"
TIME_FORMAT = "%H:%M:%S"
STATUS_OK = "ok"
STATUS_ERROR = "error"
ENCODING = "utf-8"


class CsvLogger:
    """Запись событий вызова команд в CSV-файл."""

    def __init__(self, path, clock=datetime.now):
        """Открыть журнал по пути path, при необходимости создав его.

        Отсутствующие папки создаются; заголовок пишется только
        в новый (пустой) файл. clock — источник текущего времени.
        Если файл нельзя открыть на запись, бросает OSError.
        """
        self.path = path
        self._clock = clock
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with self._open() as file:
            if file.tell() == 0:
                csv.writer(file).writerow(LOG_FIELDS)

    def log(self, command, arguments, error=""):
        """Записать событие вызова команды.

        arguments — строка аргументов, error — текст ошибки
        (пустая строка, если команда выполнилась успешно).
        """
        now = self._clock()
        status = STATUS_ERROR if error else STATUS_OK
        row = (now.strftime(DATE_FORMAT), now.strftime(TIME_FORMAT),
               command, arguments, status, error)
        with self._open() as file:
            csv.writer(file).writerow(row)

    def _open(self):
        """Открыть файл журнала на дозапись."""
        return open(self.path, "a", newline="", encoding=ENCODING)


class NullLogger:
    """Журнал-заглушка, когда лог-файл не задан."""

    def log(self, command, arguments, error=""):
        """Ничего не делать."""
