import datetime
import logging

from config import MUSIC_CACHE_LIFETIME


# класс записи в кэше
class CacheEntry:
    # логгер
    logger = logging.getLogger("cache_entry")

    def __init__(self, filename: str) -> None:
        # имя файла, с которым связана текущая запись
        self.filename = filename
        # верменная метка, когда кончается срок хранения файла
        self.expires: datetime.datetime = None
        self.updateLifetime()
        # число серверов, на которых используется текущий файл
        self.useCounter: int = 0

    # обновить время жизни файла в кэше
    def updateLifetime(self) -> None:
        old = self.expires
        self.expires = datetime.datetime.now() + datetime.timedelta(seconds=MUSIC_CACHE_LIFETIME)
        self.logger.info(f'Lifetime of "{self.filename}" updated from {old} to {self.expires}.')
