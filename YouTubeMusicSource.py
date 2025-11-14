from discord.player import AudioSource
import pytubefix as pytube
import asyncio

from MusicSource import MusicSource
from CacheEntry import CacheEntry


# обёртка на треком, который был получен с YouTube
class YouTubeMusicSource(MusicSource):
    def __init__(self, filename: str, video: pytube.YouTube, download_task: asyncio.Task, cache_entry: CacheEntry) -> None:
        # инициализация базового класса
        super().__init__(filename, f"{video.title} - {video.author}", video.watch_url, video.thumbnail_url, video.length)

        # задача скачивания файла
        self.downloadTask = download_task

        # запись в кеше
        self.cacheEntry = cache_entry
        # обновить время жизни кеша
        self.cacheEntry.updateLifetime()
        # увеличить число использований кеша
        self.cacheEntry.useCounter += 1

    # деструктор
    def __del__(self) -> None:
        # обновить время жизни кеша
        self.cacheEntry.updateLifetime()
        # уменьшить число использований кеша
        self.cacheEntry.useCounter -= 1

    # получить объект, который дискорд использует для проигрывания музыки
    async def getAudioSource(self, volume=0.5) -> AudioSource:
        # предварительно подождать, пока файл с музыкой скачается в кеш
        if self.downloadTask:
            await self.downloadTask

        # вызвать метод базового класса с основной логикой
        return await super().getAudioSource(volume)
