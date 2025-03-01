from discord import Intents
from discord.ext import commands
from singleton_decorator import singleton

from bot.cogs.ChatInteractionsCog import ChatInteractionsCog
from bot.cogs.ClanCommandsCog import ClanCommandsCog
from bot.cogs.PlayerSpecificCommandsCog import PlayerSpecificCommandsCog
from bot.cogs.StaffOnlyCommandsCog import StaffOnlyCommandsCog
from utils import debug_print, LogType


@singleton
class DiscordBot(commands.Bot):
    def __init__(self, intents: Intents):
        super().__init__(command_prefix='!', intents=intents)

        self.cogs_list = [PlayerSpecificCommandsCog(self),
                          ClanCommandsCog(self),
                          StaffOnlyCommandsCog(self),
                          ChatInteractionsCog(self)]
        self.loops = [StaffOnlyCommandsCog().clan_auto_refresh]

        debug_print("Bot is running!...", LogType.INFO)

        @self.event
        async def on_ready():
            await self.add_cogs()
            await self.start_loops()

    async def add_cogs(self) -> None:
        for cog in self.cogs_list:
            await self.add_cog(cog)

    async def start_loops(self) -> None:
        for loop in self.loops:
            loop.start()
