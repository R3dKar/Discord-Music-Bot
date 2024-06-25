import discord
from LoopedQueue import LoopedQueue
from MusicSource import MusicSource


# класс состояния для сервера
class GuildMusicState:
    def __init__(self, guild: discord.Guild) -> None:
        # сервер
        self.guild = guild
        # очередь музыки
        self.queue: LoopedQueue[MusicSource] = LoopedQueue()
        # voiceClient (подключение к голосовому каналу)
        self.voiceClient: discord.VoiceClient = None
        # сообщение с очередью музыки
        self.infoMessage: discord.Message = None

    # возвращает True, если в данный момент проигрывается музыка (или стоит на паузе)
    def isProcessingMusic(self) -> bool:
        return self.voiceClient != None and self.voiceClient.is_connected() and not self.queue.empty

    # очистка состояния
    async def clear(self) -> None:
        # отключение от голосового
        if self.voiceClient != None and self.voiceClient.is_connected():
            await self.voiceClient.disconnect()

        # вызов для корректного отключения от голосового
        if self.voiceClient != None:
            self.voiceClient.cleanup()

        # очистака остального
        self.voiceClient = None
        self.infoMessage = None
        self.queue.clear()
