import logging

from MusicSource import MusicSource
from YouTubeUrlMusicSourceProviderModule import YouTubeUrlMusicSourceProviderModule
from YouTubeSearchMusicSourceProviderModule import YouTubeSearchMusicSourceProviderModule
from FileCacheDict import FileCacheDict
from Downloader import Downloader


# класс, предоставляющий доступ к объектам MusicSource по строке запроса
class MusicSourceProvider:
    # логгер
    logger = logging.getLogger("music_source_provider")

    def __init__(self, cache_folder: str, max_downloaders: int) -> None:
        # кеш
        self.cache: FileCacheDict = FileCacheDict(cache_folder)
        # загрузчик
        self.downloader: Downloader = Downloader(max_downloaders)

        # модули для получения MusicSource разными методами
        self.modules = [YouTubeUrlMusicSourceProviderModule(self.cache, self.downloader)]
        self.modules += [YouTubeSearchMusicSourceProviderModule(self.modules[0])]

    # получить экземпляры MusicSource по текстовому запросу
    async def getMusicSources(self, query: str) -> list[MusicSource]:
        try:
            # пройтись по модулям
            for module in self.modules:
                # если модуль не может обработать запрос - пропустить
                if not module.canProcessQuery(query):
                    continue

                self.logger.info(f'Trying module "{module.__class__.__name__}" for "{query}".')

                # получить MusicSource при помощи модуля
                music_sources = [music_source async for music_source in module.processQuery(query)]

                # если удалось получить непустой список music_soureces, то вернуть результат
                if len(music_sources) > 0:
                    self.logger.info(f"Fethched {len(music_sources)} entries.")
                    return music_sources

        except Exception as e:
            raise ValueError(f"{e.__name__}: {str(e)}")

        # если ни один модуль не смог отработать - вызвать ошибку
        self.logger.error(f'Query "{query}" cannot be proceed.')
        raise ValueError("Невозможно обработать запрос")
