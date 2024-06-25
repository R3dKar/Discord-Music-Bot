import re
import typing
import pytube
import functools
import asyncio
import os
import logging

from MusicSource import MusicSource
from MusicSourceProviderModule import MusicSourceProviderModule
from YouTubeMusicSource import YouTubeMusicSource
from FileCacheDict import FileCacheDict
from Downloader import Downloader


# модуль получения музыки при помощи ссылки youtube
class YouTubeUrlMusicSourceProviderModule(MusicSourceProviderModule):
    # логгер
    logger = logging.getLogger("youtube_music_source_provider_module")

    def __init__(self, cache: FileCacheDict, downloader: Downloader):
        super().__init__(cache, downloader)

    def canProcessQuery(self, query: str) -> bool:
        return re.search(r"(http(s)?:\/\/)?(www\.)?youtu(\.be|be\.com)\/", query)

    async def processQuery(self, query: str) -> typing.AsyncIterator[MusicSource]:
        # получить список ссылок youtube
        urls = pytube.Playlist(query).video_urls if re.search(r"list=", query) else [query]

        for url in urls:
            video: pytube.YouTube = pytube.YouTube(url)
            filename: str = f"youtube.{video.video_id}"
            download_task: typing.Optional[asyncio.Task] = None

            # если файл не в кеше, то в MusicSource добавить информацию о задаче скачивания
            if filename not in self.cache:
                await self.cache.addFile(filename)
                download_task = asyncio.create_task(self.downloader.downloadFile(filename, functools.partial(self.downloadVideo, video, filename)))
            else:
                self.logger.info(f'Found "{filename}" in cache! Reusing.')

            yield YouTubeMusicSource(os.path.join(self.cache.cacheFolder, filename), video, download_task, self.cache.getFile(filename))

    def downloadVideo(self, video: pytube.YouTube, filename: str) -> None:
        video.streams.filter(only_audio=True).first().download(self.cache.cacheFolder, filename)
