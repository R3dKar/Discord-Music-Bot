import typing

from MusicSource import MusicSource
from FileCacheDict import FileCacheDict
from Downloader import Downloader


# базовый класс модуля MusicSoureceProvider
class MusicSourceProviderModule:
    def __init__(self, cache: FileCacheDict, downloader: Downloader):
        # кеш
        self.cache: FileCacheDict = cache
        # загрузчик
        self.downloader: Downloader = downloader

    # возвращает True, если запрос query может быть обработан
    def canProcessQuery(self, query: str) -> bool:
        return False

    # обрабатывает поступивший запрос
    async def processQuery(self, query: str) -> typing.AsyncIterator[MusicSource]:
        return
