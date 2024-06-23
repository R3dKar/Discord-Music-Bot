import datetime
import logging

from config import MUSIC_CACHE_LIFETIME


class CacheEntry:
    logger = logging.getLogger("cache_entry")

    def __init__(self, filename: str) -> None:
        self.filename = filename
        self.expires: datetime.datetime = None
        self.updateLifetime()
        self.useCounter: int = 0

    def updateLifetime(self) -> None:
        old = self.expires

        self.expires = datetime.datetime.now() + datetime.timedelta(seconds=MUSIC_CACHE_LIFETIME)

        self.logger.info(f'Lifetime of "{self.filename}" updated from {old} to {self.expires}.')
