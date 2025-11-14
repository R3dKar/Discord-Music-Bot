import discord
from discord.ext import commands

from MusicCog import MusicCog

from config import HOME_GUILD_ID

if not discord.opus.is_loaded():
    discord.opus.load_opus('libopus.so.0')

# класс бота
class MusicBot(commands.Bot):
    def __init__(self) -> None:
        super().__init__(command_prefix="!", intents=discord.Intents.default())

    async def setup_hook(self) -> None:
        # добавить ког с основной логикой
        await self.add_cog(MusicCog(self))
        # скопировать slash команды на сервер, указанный в конфиге
        self.tree.copy_global_to(guild=discord.Object(id=HOME_GUILD_ID))
        # синхронизация slash команд с серверами дискорда
        await self.tree.sync()
