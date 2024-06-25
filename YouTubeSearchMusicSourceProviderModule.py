import typing
import pytube

from MusicSource import MusicSource
from MusicSourceProviderModule import MusicSourceProviderModule
from YouTubeUrlMusicSourceProviderModule import YouTubeUrlMusicSourceProviderModule


# модуль получения музыки при помощи текстового запроса из youtube
class YouTubeSearchMusicSourceProviderModule(MusicSourceProviderModule):
    def __init__(self, url_module: YouTubeUrlMusicSourceProviderModule):
        super().__init__(url_module.cache, url_module.downloader)

        # модуль, при помощи которого
        self.urlModule = url_module

    def canProcessQuery(self, query: str) -> bool:
        return True

    async def processQuery(self, query: str) -> typing.AsyncIterator[MusicSource]:
        # получить результаты поиска
        search_results = pytube.Search(query).results

        if len(search_results) == 0:
            return

        # если успешно, то получить MusicSourece через другой модуль по url
        async for music_source in self.urlModule.processQuery(search_results[0].watch_url):
            yield music_source
