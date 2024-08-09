import os
import logging
import asyncio
import datetime
import typing

from CacheEntry import CacheEntry


# класс системы кеширования файлов
class FileCacheDict:
    # логгер
    logger = logging.getLogger("file_cache_dict")

    def __init__(self, cache_folder: str) -> None:
        # флаг, запущен ли объект
        self.started: bool = False
        # папка с кешем
        self.cacheFolder: str = cache_folder
        # словарь кеша
        self.cache: dict[str, CacheEntry] = {}

    # запускает систему кеширования и добавляет все файлы, найденные в папке, в кеш
    async def start(self) -> None:
        if self.started:
            return

        self.started = True

        existing_files = [filename for filename in os.listdir(self.cacheFolder) if os.path.isfile(os.path.join(self.cacheFolder, filename))]

        for filename in existing_files:
            self.logger.info(f'Found file "{filename}". Added to cache.')
            await self.addFile(filename)

    # корутина отслеживания времени жизни одного файла
    async def fileLifetimeCheck(self, filename: str) -> None:
        # пока файл в кеше и время жизни его не истекло, либо он используется, уходить в ожидание
        while (filename in self.cache) and ((datetime.datetime.now() < self.cache[filename].expires) or (self.cache[filename].useCounter > 0)):
            await asyncio.sleep(max((self.cache[filename].expires - datetime.datetime.now()).total_seconds(), 1))

        # если файл удалён из кеша, то пропустить
        if filename not in self.cache:
            return

        # удалить файл
        self.removeFile(filename)

    # добавить файл в кеш и запустить корутину отслеживания времени жизни файла
    async def addFile(self, filename: str) -> None:
        self.cache[filename] = CacheEntry(filename)
        asyncio.create_task(self.fileLifetimeCheck(filename))
        self.logger.info(f'Added "{filename} to cache."')

    # получить файл
    def getFile(self, filename: str) -> typing.Optional[CacheEntry]:
        return self.cache.get(filename, None)

    # магический метод для in
    def __contains__(self, item: str) -> bool:
        return item in self.cache

    # удалить файл из кеша
    def removeFile(self, filename: str) -> None:
        if filename not in self.cache:
            return

        if self.cache[filename].useCounter > 0:
            return

        del self.cache[filename]
        os.remove(os.path.join(self.cacheFolder, filename))

        self.logger.info(f'Removed "{filename}" from cache.')
