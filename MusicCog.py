import asyncio
import discord
from discord import app_commands
from discord.ext import commands

from LoopedQueue import LoopType
from MusicSource import MusicSource
from MusicSourceProvider import MusicSourceProvider
from GuildMusicState import GuildMusicState

from config import MUSIC_CACHE_FOLDER, MUSIC_MAX_DOWNLOADERS


# ког с основной логикой проигрывания музыки
class MusicCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot: commands.Bot = bot

        # инициализация кеширования
        self.musicSourceProvider: MusicSourceProvider = MusicSourceProvider(cache_folder=MUSIC_CACHE_FOLDER, max_downloaders=MUSIC_MAX_DOWNLOADERS)
        self.bot.loop.create_task(self.musicSourceProvider.cache.start())

        # словарь состояний для каждого известного сервера
        self.guildStates: dict[discord.Guild, GuildMusicState] = {}

    # вызывается, чтобы создать состояние для сервера, на котором был создан interaction
    def ensureQueueExists(self, interaction: discord.Interaction) -> None:
        if interaction.guild not in self.guildStates:
            self.guildStates[interaction.guild] = GuildMusicState(interaction.guild)

    # возвращает эмбед очереди музыки
    def getQueueEmbed(self, guildState: GuildMusicState) -> discord.Embed | None:
        # если музыка не проигрывается на сервере
        if not guildState.isProcessingMusic():
            return None

        current_queue = guildState.queue

        # основные параметры эмбеда
        embed = discord.Embed()
        playing_music: MusicSource = current_queue.get()
        embed.set_author(name="Сейчас играет:")
        embed.title = f"{playing_music.title} [{playing_music.getDurationString()}]"
        embed.url = playing_music.url
        embed.set_thumbnail(url=playing_music.coverUrl)

        # добавление полей с музыкой
        embed.add_field(name=" ", value="Очередь:", inline=False)
        for i, music in enumerate(current_queue.queue[:23], 1):
            name = f"**{i}. {music.title} [{music.getDurationString()}]**" if music == playing_music else f"{i}. {music.title} [{music.getDurationString()}]"
            embed.add_field(name=name, value=" ", inline=False)

        # если число треков 24 - поместятся все
        if len(current_queue.queue) == 24:
            i = 23
            music = current_queue.queue[i]
            name = f"**{i+1}. {music.title} [{music.getDurationString()}]**" if music == playing_music else f"{i+1}. {music.title} [{music.getDurationString()}]"
            embed.add_field(name=name, value=" ", inline=False)
        # если нет, то в последнем поле вывести информуцию "и ещё ..."
        elif len(current_queue.queue) > 24:
            number = len(current_queue.queue) - 23
            track_ending = "ов" if number % 100 in range(10, 20) else "" if number % 10 == 1 else "а" if number % 10 in range(2, 5) else "ов"
            embed.add_field(name=f"и ещё {number} трек{track_ending}...", value=" ", inline=False)

        return embed

    # возвращает эмбед с простым текстом
    def getSimpleEmbed(self, message: str) -> discord.Embed:
        return discord.Embed(description=message)

    # команда запуска проигрывания или добавления музыки в очередь
    @app_commands.command(description="Добавить музыку в очередь")
    @app_commands.describe(query="Текстовый запрос или ссылка")
    @app_commands.guild_only()
    async def play(self, interaction: discord.Interaction, query: str) -> None:
        self.ensureQueueExists(interaction)
        guildState = self.guildStates[interaction.guild]

        # думающий ответ, чтобы пользователь не паниковал
        await interaction.response.defer()

        # если музыка играет, то просто добавить треки в очередь
        if guildState.isProcessingMusic():
            return await self.addMusicToQueue(interaction, guildState, query)

        # если не играет и пользователь не в голосовом
        if not interaction.user.voice:
            return await interaction.edit_original_response(embed=self.getSimpleEmbed("Вы не находитесь ни в одном голосовом канале!"))

        # попытаться подключиться в голосовой канал с пользователем
        try:
            guildState.voiceClient = await interaction.user.voice.channel.connect(self_deaf=True)
        except Exception:
            return await interaction.edit_original_response(embed=self.getSimpleEmbed("Не могу подключиться к вашему голосовому каналу :("))

        # очистить очередь с музыкой (нужно из-за иногда возникающего бага скачивания с YouTube (актуально?))
        guildState.queue.clear()
        # если попытка добавить музыку неудачна - отключиться от голосового
        if not await self.addMusicToQueue(interaction, guildState, query):
            return await guildState.voiceClient.disconnect()

        # пока обрабатывается музыка
        while guildState.isProcessingMusic():
            # получить из очереди следующий MusicSource
            current_music: MusicSource = guildState.queue.get()
            # обновиться сообщение с очередью музыки
            await guildState.infoMessage.edit(embed=self.getQueueEmbed(guildState))

            # проиграть музыку в голосовой
            current_music_audiosource = await current_music.getAudioSource()
            await self.playAudioSource(guildState.voiceClient, current_music_audiosource)

            # сдвинуть очередь на следующий трек
            guildState.queue.next()

        # если бот не остался в голосовом - воспроизведение останавливали
        if not guildState.voiceClient.is_connected():
            await guildState.infoMessage.edit(embed=self.getSimpleEmbed("Воспроизведение остановлено"))
        # если бот остался в голосовом к этому моменту - очередь закончилась
        else:
            await guildState.infoMessage.edit(embed=self.getSimpleEmbed("Очередь закончилась"))

        # произвести очистку состояния сервера
        await guildState.clear()

    # метод добавления музыки в очередь. Возвращает True при успехе
    async def addMusicToQueue(self, interaction: discord.Interaction, guildState: GuildMusicState, query: str) -> bool:
        new_music_list: list[MusicSource] = None

        try:
            # получение списка MusciSource через систему кеширования
            new_music_list = await self.musicSourceProvider.getMusicSources(query)
        except ValueError:
            # при неудаче вернуть False
            await interaction.edit_original_response(embed=self.getSimpleEmbed("Не могу воспроизвести этот трек :/"))
            return False

        # добавить полученный список MusicSource
        guildState.queue.add(new_music_list)

        if not guildState.infoMessage:
            # отправить сообщение с очередью музыки и сохранить сообщение для изменения, если его нет
            guildState.infoMessage = await interaction.channel.send(embed=self.getQueueEmbed(guildState))
        else:
            # иначе просто обновить существующее
            await guildState.infoMessage.edit(embed=self.getQueueEmbed(guildState))

        # ответ с правильным окончанием
        if len(new_music_list) == 1:
            await interaction.edit_original_response(embed=self.getSimpleEmbed(f"Добавлено в очередь: `{new_music_list[0].title} [{new_music_list[0].getDurationString()}]`"))
        else:
            await interaction.edit_original_response(embed=self.getSimpleEmbed(f"Добавлено в очередь {len(new_music_list)} треков"))

        return True

    # запуск проигрывания музыки с асинхронным ожиданием оканчания проигрывания
    async def playAudioSource(self, voice_client: discord.VoiceClient, source: discord.AudioSource) -> None:
        # флаг конца проигрывания, устанавливается через callback
        finished: asyncio.Event = asyncio.Event()
        # запуск проигрывания в другом потоке
        voice_client.play(source, after=lambda _: self.bot.loop.call_soon_threadsafe(finished.set))

        # ожидаем конца проигрывания (костыльно, но voice_client.play не блокирует выполнение, поэтому ожидание делается через sleep асинхронный)
        while not finished.is_set() and voice_client.is_connected():
            await asyncio.sleep(0.01)

    # команда установки типа зацикливания
    @app_commands.command(description="Повтор очереди")
    @app_commands.describe(loop="Тип повтора")
    @app_commands.guild_only()
    async def loop(self, interaction: discord.Interaction, loop: LoopType) -> None:
        self.ensureQueueExists(interaction)
        guildState = self.guildStates[interaction.guild]

        guildState.queue.loop = loop

        messageDict: dict[LoopType, str] = {
            LoopType.All: "Зацикливание всей очереди включено",
            LoopType.Single: "Зацикливание одного трека включено",
            LoopType.Off: "Зацикливание выключено",
        }

        await interaction.response.send_message(embed=self.getSimpleEmbed(messageDict[loop]))

    # команда остановки проигрывания
    @app_commands.command(description="Очистить очередь и остановить проигрывание")
    @app_commands.guild_only()
    async def stop(self, interaction: discord.Interaction) -> None:
        self.ensureQueueExists(interaction)
        guildState = self.guildStates[interaction.guild]

        if guildState.isProcessingMusic():
            # если музыка играет, то выйти из голосового канала (проигрывание само обработается в play)
            await guildState.voiceClient.disconnect()
            await interaction.response.send_message(embed=self.getSimpleEmbed("Воспроизведение остановлено"))
        else:
            await interaction.response.send_message(embed=self.getSimpleEmbed("Очередь пуста"))

    # команда паузы музыки
    @app_commands.command(description="Поставить воспроизведение на паузу")
    @app_commands.guild_only()
    async def pause(self, interaction: discord.Interaction) -> None:
        self.ensureQueueExists(interaction)
        guildState = self.guildStates[interaction.guild]

        # если музыка играет
        if not guildState.isProcessingMusic():
            return await interaction.response.send_message(embed=self.getSimpleEmbed("Нечего ставить на паузу"))

        # если на паузе
        if guildState.voiceClient.is_paused():
            return await interaction.response.send_message(embed=self.getSimpleEmbed("Уже на паузе"))

        # поставить на паузу voiceClient
        guildState.voiceClient.pause()
        await interaction.response.send_message(embed=self.getSimpleEmbed("Поставлено на паузу"))

    # команда снятия трека с паузы
    @app_commands.command(description="Продолжить воспроизведение")
    @app_commands.guild_only()
    async def resume(self, interaction: discord.Interaction) -> None:
        self.ensureQueueExists(interaction)
        guildState = self.guildStates[interaction.guild]

        # если музыка не играется
        if not guildState.isProcessingMusic():
            return await interaction.response.send_message(embed=self.getSimpleEmbed("Нечего возобновлять"))

        # если музыка не на паузе
        if guildState.voiceClient.is_playing():
            return await interaction.response.send_message(embed=self.getSimpleEmbed("Уже играет"))

        # возобновить voiceClient
        guildState.voiceClient.resume()
        await interaction.response.send_message(embed=self.getSimpleEmbed("Продолжаю воспроизведение"))

    # команда пропуска текущего трека
    @app_commands.command(description="Пропустить текущий трек")
    @app_commands.guild_only()
    async def skip(self, interaction: discord.Interaction) -> None:
        self.ensureQueueExists(interaction)
        guildState = self.guildStates[interaction.guild]

        # если музыка не проигрывается
        if not guildState.isProcessingMusic():
            return await interaction.response.send_message(embed=self.getSimpleEmbed("Очередь пуста"))

        # если проигрывается, то остановить voiceClient
        # после остановки, цикл в play сам начнёт играть следующий трек
        guildState.voiceClient.stop()
        await interaction.response.send_message(embed=self.getSimpleEmbed("Трек пропущен!"))
