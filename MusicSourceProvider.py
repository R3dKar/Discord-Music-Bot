import asyncio
import datetime
import os
import pytube
import re
import logging

from MusicSource import MusicSource
from YouTubeMusicSource import YouTubeMusicSource
from CacheEntry import CacheEntry


class MusicSourceProvider:
    logger = logging.getLogger("music_source_provider")

    def __init__(self, cache_folder: str, max_downloaders: int) -> None:
        self.cacheFolder: str = cache_folder
        self.downloadSemaphore: asyncio.Semaphore = asyncio.Semaphore(max_downloaders)
        self.started = False

        self.cached: dict[str, CacheEntry] = {}

        existing_files = [filename for filename in os.listdir(self.cacheFolder) if os.path.isfile(os.path.join(self.cacheFolder, filename))]
        for filename in existing_files:
            self.cached[filename] = CacheEntry(filename)
            self.logger.info(f'Found file "{filename}". Added to cache.')

    async def fileLifetimeCheck(self, filename: str) -> None:
        while (datetime.datetime.now() < self.cached[filename].expires) or (self.cached[filename].useCounter > 0):
            await asyncio.sleep(max((self.cached[filename].expires - datetime.datetime.now()).total_seconds(), 1))

        del self.cached[filename]
        os.remove(os.path.join(self.cacheFolder, filename))
        self.logger.info(f'Removed file "{filename}" from cache.')

    async def start(self) -> None:
        if self.started:
            return

        self.started = True

        for filename in self.cached.keys():
            asyncio.create_task(self.fileLifetimeCheck(filename))

    async def getMusicSources(self, url: str) -> list[MusicSource]:
        try:
            if re.search(r"(http(s)?:\/\/)?(www\.)?youtu(\.be|be\.com)\/", url):
                urls: list[str] = []
                if re.search(r"list=", url):
                    urls.extend(pytube.Playlist(url).video_urls)
                else:
                    urls = [url]

                music_sources: list[MusicSource] = []

                for url in urls:
                    video = pytube.YouTube(url)

                    filename = f"youtube.{video.video_id}"
                    download_task = None

                    if filename not in self.cached:
                        self.cached[filename] = CacheEntry(filename)
                        asyncio.create_task(self.fileLifetimeCheck(filename))

                        download_task = asyncio.create_task(self.downloadYouTubeVideo(video, filename))
                    else:
                        self.logger.info(f'Found file "{filename}" in cache. Reusing...')

                    music_sources.append(YouTubeMusicSource(os.path.join(self.cacheFolder, filename), video, download_task, self.cached[filename]))

                return music_sources
        except Exception as e:
            raise ValueError(f"{e.__class__}: {str(e)}")

        raise ValueError("Ссылка не может быть обработана!")

    async def downloadYouTubeVideo(self, video: pytube.YouTube, filename: str) -> None:
        self.logger.info(f'Downloading of "{video.watch_url}" to "{filename}" is queued.')
        await self.downloadSemaphore.acquire()

        try:
            self.logger.info(f'Downloading of "{video.watch_url}" to "{filename}" started.')
            await asyncio.to_thread(lambda: video.streams.filter(only_audio=True).first().download(self.cacheFolder, filename))
        finally:
            self.logger.info(f'Downloading of "{video.watch_url}" to "{filename}" finished.')
            self.downloadSemaphore.release()
