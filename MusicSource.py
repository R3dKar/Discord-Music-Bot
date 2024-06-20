import subprocess
import discord

from config import FFMPEG, FFPROBE

FFMPEG_OPTIONS = {"options": "-vn"}


class MusicSource:
    def __init__(self, filename, title, url=None, cover_url=None, duration=None):
        self.filename = filename
        self.title = title
        self.url = url
        self.cover_url = cover_url
        self.duration = duration or self.getDuration(self.filename)

    @classmethod
    def getDuration(cls, filename) -> float:
        result = subprocess.run([FFPROBE, "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", filename], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        return float(result.stdout)

    def getDurationString(self) -> str:
        if self.duration >= 3600:
            return f"{self.duration // 3600:02.0f}:{self.duration % 3600 // 60:02.0f}:{self.duration % 60:02.0f}"
        else:
            return f"{self.duration // 60:02.0f}:{self.duration % 60:02.0f}"

    def getSource(self, volume=0.5) -> discord.AudioSource:
        return discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(self.filename, executable=FFMPEG, **FFMPEG_OPTIONS), volume)
