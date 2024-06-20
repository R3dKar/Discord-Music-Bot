import discord
from discord.ext import commands

from MusicCog import MusicCog
from config import HOME_GUILD_ID


class MusicBot(commands.Bot):
    def __init__(self) -> None:
        super().__init__(command_prefix="!", intents=discord.Intents.default())

    async def setup_hook(self) -> None:
        await self.add_cog(MusicCog(self))
        self.tree.copy_global_to(guild=discord.Object(id=HOME_GUILD_ID))
        await self.tree.sync()
