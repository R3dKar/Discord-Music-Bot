from discord.player import AudioSource
import pytube
import asyncio

from MusicSource import MusicSource
from CacheEntry import CacheEntry


class YouTubeMusicSource(MusicSource):
    def __init__(self, filename: str, video: pytube.YouTube, download_task: asyncio.Task, cache_entry: CacheEntry) -> None:
        super().__init__(filename, f"{video.title} - {video.author}", video.watch_url, video.thumbnail_url, video.length)

        self.downloadTask = download_task
        self.cacheEntry = cache_entry
        self.cacheEntry.updateLifetime()
        self.cacheEntry.useCounter += 1

    def __del__(self) -> None:
        self.cacheEntry.updateLifetime()
        self.cacheEntry.useCounter -= 1

    async def getAudioSource(self, volume=0.5) -> AudioSource:
        if self.downloadTask:
            await self.downloadTask

        return await super().getAudioSource(volume)
