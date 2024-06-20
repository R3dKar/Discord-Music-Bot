import yt_dlp
import asyncio
import re

from MusicSource import MusicSource

yt_dlp.utils.bug_reports_message = lambda: ""
YTDL_OPTIONS = {"format": "bestaudio/best", "outtmpl": "music/%(extractor)s-%(id)s-%(title)s.%(ext)s", "restrictfilenames": True, "noplaylist": True, "nocheckcertificate": True, "ignoreerrors": False, "logtostderr": False, "quiet": True, "no_warnings": True, "default_search": "auto", "source_address": "0.0.0.0"}


class YouTubeMusicSource(MusicSource):
    ytdl = yt_dlp.YoutubeDL(YTDL_OPTIONS)

    @classmethod
    async def create(cls, url, loop=None):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: YouTubeMusicSource.ytdl.extract_info(url, download=True))
        if "entries" in data:
            data = data["entries"][0]

        filename = YouTubeMusicSource.ytdl.prepare_filename(data)
        title = data.get("title")
        duration = data.get("duration")
        cover_url = data.get("thumbnail")
        return cls(filename=filename, title=title, url=url, duration=duration, cover_url=cover_url)

    @classmethod
    async def createList(cls, url, loop=None):
        loop = loop or asyncio.get_event_loop()
        data_list = await loop.run_in_executor(None, lambda: YouTubeMusicSource.ytdl.extract_info(url, download=True))
        if "entries" in data_list:
            data_list = data_list["entries"]
        else:
            data_list = [data_list]

        sources = []
        for data in data_list:
            filename = YouTubeMusicSource.ytdl.prepare_filename(data)
            title = data.get("title")
            duration = data.get("duration")
            cover_url = data.get("thumbnail")
            music_url = data.get("original_url")

            sources.append(cls(filename=filename, title=title, url=music_url, duration=duration, cover_url=cover_url))

        return sources


async def createMusicSource(url: str) -> list[MusicSource]:
    try:
        if re.search(r"(http(s)?:\/\/)?(www\.)?youtu(\.be|be\.com)\/", url):
            if re.search(r"list=", url):
                return await YouTubeMusicSource.createList(url)

            return [await YouTubeMusicSource.create(url)]
        # elif os.path.exists(os.path.join('music', url)):
        #    return MusicSource(os.path.join('music', url), 'Untitled')
    except Exception as e:
        raise ValueError(f"{e.__class__}: {str(e)}")

    raise ValueError("Invalid url pattern!")
