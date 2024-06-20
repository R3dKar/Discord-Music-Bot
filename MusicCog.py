import asyncio
import discord
from discord import app_commands
from discord.ext import commands

from LoopedQueue import LoopedQueue, LoopType
from MusicSource import MusicSource
from YouTubeMusicSource import createMusicSource


class MusicCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot: commands.Bot = bot
        self.queues: dict[discord.Guild, LoopedQueue[MusicSource]] = {}
        self.voiceClients: dict[discord.Guild, discord.VoiceClient] = {}
        self.infoMessages: dict[discord.Guild, discord.Message] = {}

    def ensureQueueExists(self, interaction: discord.Interaction) -> None:
        if interaction.guild not in self.queues:
            self.queues[interaction.guild] = LoopedQueue()
            self.voiceClients[interaction.guild] = None
            self.infoMessages[interaction.guild] = None

    def checkProcessingMusic(self, interaction: discord.Interaction) -> bool:
        self.ensureQueueExists(interaction)
        return self.voiceClients[interaction.guild] != None and self.voiceClients[interaction.guild].is_connected() and not self.queues[interaction.guild].empty

    def getQueueEmbed(self, interaction: discord.Interaction) -> discord.Embed | None:
        self.ensureQueueExists(interaction)

        if not self.checkProcessingMusic(interaction):
            return None

        current_queue = self.queues[interaction.guild]

        embed = discord.Embed()
        playing_music: MusicSource = current_queue.get()
        embed.set_author(name="Сейчас играет:")
        embed.title = f"{playing_music.title} [{playing_music.getDurationString()}]"
        embed.url = playing_music.url
        embed.set_thumbnail(url=playing_music.cover_url)

        embed.add_field(name=" ", value="Очередь:", inline=False)
        for i, music in enumerate(current_queue.queue[:23]):
            name = f"**{i+1}. {music.title} [{music.getDurationString()}]**" if music == playing_music else f"{i+1}. {music.title} [{music.getDurationString()}]"
            embed.add_field(name=name, value=" ", inline=False)

        if len(current_queue.queue) == 24:
            i = 23
            music = current_queue.queue[i]
            name = f"**{i+1}. {music.title} [{music.getDurationString()}]**" if music == playing_music else f"{i+1}. {music.title} [{music.getDurationString()}]"
            embed.add_field(name=name, value=" ", inline=False)
        elif len(current_queue.queue) > 24:
            number = len(current_queue.queue) - 23
            track_ending = "ов" if number % 100 in range(10, 20) else "" if number % 10 == 1 else "а" if number % 10 in range(2, 5) else "ов"
            embed.add_field(name=f"и ещё {number} трек{track_ending}...", value=" ", inline=False)

        return embed

    def getSimpleEmbed(self, message: str) -> discord.Embed:
        return discord.Embed(description=message)

    @app_commands.command(description="Добавить музыку в очередь")
    @app_commands.describe(url="Ссылка на музыку")
    @app_commands.guild_only()
    async def play(self, interaction: discord.Interaction, url: str) -> None:
        self.ensureQueueExists(interaction)

        await interaction.response.defer()

        if not self.queues[interaction.guild].empty:
            new_music_list: list[MusicSource] = None
            try:
                new_music_list = await createMusicSource(url)
            except ValueError as e:
                print(str(e))
                return await interaction.edit_original_response(embed=self.getSimpleEmbed("Не могу воспроизвести этот трек :/"))
            self.queues[interaction.guild].add(new_music_list)
            await self.infoMessages[interaction.guild].edit(embed=self.getQueueEmbed(interaction))

            if len(new_music_list) == 1:
                return await interaction.edit_original_response(embed=self.getSimpleEmbed(f"Добавлено в очередь: `{new_music_list[0].title} [{new_music_list[0].getDurationString()}]`"))
            else:
                return await interaction.edit_original_response(embed=self.getSimpleEmbed(f"Добавлено в очередь {len(new_music_list)} треков"))

        if not interaction.user.voice:
            return await interaction.edit_original_response(embed=self.getSimpleEmbed("Вы не находитесь ни в одном голосовом канале!"))

        try:
            self.voiceClients[interaction.guild] = await interaction.user.voice.channel.connect(self_deaf=True)
        except Exception as e:
            return await interaction.edit_original_response(embed=self.getSimpleEmbed("Не могу подключиться к вашему голосовому каналу :("))

        new_music_list: list[MusicSource] = None
        try:
            new_music_list = await createMusicSource(url)
        except ValueError as e:
            await self.voiceClients[interaction.guild].disconnect()
            print(str(e))
            return await interaction.edit_original_response(embed=self.getSimpleEmbed("Не могу воспроизвести этот трек :/"))
        self.queues[interaction.guild].add(new_music_list)

        if len(new_music_list) == 1:
            await interaction.edit_original_response(embed=self.getSimpleEmbed(f"Добавлено в очередь: `{new_music_list[0].title} [{new_music_list[0].getDurationString()}]`"))
        else:
            await interaction.edit_original_response(embed=self.getSimpleEmbed(f"Добавлено в очередь {len(new_music_list)} треков"))

        info_message = await interaction.channel.send(embed=self.getQueueEmbed(interaction))
        self.infoMessages[interaction.guild] = info_message

        while not self.queues[interaction.guild].empty and self.voiceClients[interaction.guild].is_connected():
            current_music: MusicSource = self.queues[interaction.guild].get()
            await info_message.edit(embed=self.getQueueEmbed(interaction))

            current_music_source = current_music.getSource()
            await self._play(self.voiceClients[interaction.guild], current_music_source)
            current_music_source.cleanup()

            self.queues[interaction.guild].next()

        if not self.voiceClients[interaction.guild].is_connected():
            await info_message.edit(embed=self.getSimpleEmbed("Воспроизведение остановлено"))
        else:
            await self.voiceClients[interaction.guild].disconnect()
            await info_message.edit(embed=self.getSimpleEmbed("Очередь закончилась"))

        self.queues[interaction.guild].clear()
        self.voiceClients[interaction.guild].cleanup()
        self.voiceClients[interaction.guild] = None
        self.infoMessages[interaction.guild] = None

    async def _play(self, vc: discord.VoiceClient, source: discord.AudioSource) -> None:
        _next: asyncio.Event = asyncio.Event()
        vc.play(source, after=lambda e: self.bot.loop.call_soon_threadsafe(_next.set))

        while not _next.is_set() and vc.is_connected():
            await asyncio.sleep(0.01)

    @app_commands.command(description="Повтор очереди")
    @app_commands.describe(loop="Тип повтора")
    @app_commands.guild_only()
    async def loop(self, interaction: discord.Interaction, loop: LoopType) -> None:
        self.ensureQueueExists(interaction)

        self.queues[interaction.guild].loop = loop

        content: str = ""
        if loop == LoopType.All:
            content = "Зацикливание всей очереди включено"
        elif loop == LoopType.Single:
            content = "Зацикливание одного трека включено"
        elif loop == LoopType.Off:
            content = "Зацикливание выключено"
        await interaction.response.send_message(embed=self.getSimpleEmbed(content))

    @app_commands.command(description="Очистить очередь и остановить проигрывание")
    @app_commands.guild_only()
    async def stop(self, interaction: discord.Interaction) -> None:
        self.ensureQueueExists(interaction)

        if self.checkProcessingMusic(interaction):
            await self.voiceClients[interaction.guild].disconnect()
            await interaction.response.send_message(embed=self.getSimpleEmbed("Воспроизведение остановлено"))
        else:
            await interaction.response.send_message(embed=self.getSimpleEmbed("Очередь пуста"))

    @app_commands.command(description="Поставить воспроизведение на паузу")
    @app_commands.guild_only()
    async def pause(self, interaction: discord.Interaction) -> None:
        self.ensureQueueExists(interaction)

        if not self.checkProcessingMusic(interaction):
            return await interaction.response.send_message(embed=self.getSimpleEmbed("Нечего ставить на паузу"))

        if self.voiceClients[interaction.guild].is_paused():
            return await interaction.response.send_message(embed=self.getSimpleEmbed("Уже на паузе"))

        self.voiceClients[interaction.guild].pause()
        await interaction.response.send_message(embed=self.getSimpleEmbed("Поставлено на паузу"))

    @app_commands.command(description="Продолжить воспроизведение")
    @app_commands.guild_only()
    async def resume(self, interaction: discord.Interaction) -> None:
        self.ensureQueueExists(interaction)

        if not self.checkProcessingMusic(interaction):
            return await interaction.response.send_message(embed=self.getSimpleEmbed("Нечего возобновлять"))

        if self.voiceClients[interaction.guild].is_playing():
            return await interaction.response.send_message(embed=self.getSimpleEmbed("Уже играет"))

        self.voiceClients[interaction.guild].resume()
        await interaction.response.send_message(embed=self.getSimpleEmbed("Продолжаю воспроизведение"))

    @app_commands.command(description="Пропустить текущий трек")
    @app_commands.guild_only()
    async def skip(self, interaction: discord.Interaction) -> None:
        self.ensureQueueExists(interaction)

        if not self.checkProcessingMusic(interaction):
            return await interaction.response.send_message(embed=self.getSimpleEmbed("Очередь пуста"))

        self.voiceClients[interaction.guild].stop()
        await interaction.response.send_message(embed=self.getSimpleEmbed("Трек пропущен!"))
