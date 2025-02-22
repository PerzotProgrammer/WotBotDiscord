from discord import Intents
from discord.ext import commands
from singleton_decorator import singleton

from bot.handlers.ChatInteractionsHandler import ChatInteractionsHandler
from bot.handlers.ClanCommandsHandler import ClanCommandsHandler
from bot.handlers.PlayerCommandsHandler import PlayerCommandsHandler
from utils import debug_print, LogType


@singleton
class DiscordBot(commands.Bot):
    def __init__(self, intents: Intents):
        super().__init__(command_prefix='!', intents=intents)

        self.cogs_list = [PlayerCommandsHandler(self),
                          ClanCommandsHandler(self),
                          ChatInteractionsHandler(self)]

        debug_print("Bot is running!...", LogType.INFO)

        @self.event
        async def on_ready():
            await self.add_cogs()

    async def add_cogs(self) -> None:
        for cog in self.cogs_list:
            await self.add_cog(cog)
