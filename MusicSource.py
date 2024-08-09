import subprocess
import discord

from config import FFMPEG, FFPROBE


# класс-обёртка над файлом музыки, который содержит информацию о названии, картинке, длительности музыки,
# а также предоставляет доступ к объекту, который использует дискорд для проигрывания музыки
class MusicSource:
    # получает длительность файла музыки через FFPROBE
    @classmethod
    def getDuration(cls, filename) -> float:
        result = subprocess.run([FFPROBE, "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", filename], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        return float(result.stdout)

    def __init__(self, filename, title, url=None, cover_url=None, duration=None):
        # имя файла в кеше
        self.filename = filename
        # название трека
        self.title = title
        # ссылка на трек
        self.url = url
        # ссылка на картинку трека
        self.coverUrl = cover_url
        # длительность трека в секундах
        self.duration = duration or self.getDuration(self.filename)

    # деструктор
    def __del__(self) -> None:
        pass

    # строковое представление длительности трека
    def getDurationString(self) -> str:
        if self.duration >= 3600:
            return f"{self.duration // 3600:02.0f}:{self.duration % 3600 // 60:02.0f}:{self.duration % 60:02.0f}"
        else:
            return f"{self.duration // 60:02.0f}:{self.duration % 60:02.0f}"

    # получить объект, который дискорд использует для проигрывания музыки
    async def getAudioSource(self, volume=0.5) -> discord.AudioSource:
        return discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(self.filename, executable=FFMPEG, options="-vn"), volume)
