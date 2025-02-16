import colorama
from discord import Intents, Message
from discord.ext import commands

from bot.handlers.ChatInteractionsHandler import ChatInteractionsHandler
from bot.handlers.ClanCommandsHandler import ClanCommandsHandler
from bot.handlers.PlayerCommandsHandler import PlayerCommandsHandler
from utils import debug_print


class DiscordBot(commands.Bot):
    def __init__(self, intents: Intents):
        super().__init__(command_prefix='!', intents=intents)

        self.player_commands = PlayerCommandsHandler()
        self.clan_commands = ClanCommandsHandler()
        self.chat_handler = ChatInteractionsHandler()

        debug_print("INFO: Bot is running!...", colorama.Fore.CYAN)

        @self.command(name="test")
        async def test(context):
            await self.chat_handler.chat_test(context)

        @self.command(name="arty")
        async def arty(context):
            await context.send(self.chat_handler.roll_arty_respond())

        # @self.command(name="register")
        # async def register(context, dc_nick, wot_nick):
        #     await context.send("This currently doesn't work")

        @self.command(name="playerInfo")
        async def player_info(context, player_name):
            await self.player_commands.player_info(context, player_name)

        @self.command(name="showMembers")
        async def show_members(context):
            await self.clan_commands.show_members(context)

        @self.command(name="rankCheck")
        async def rank_check(context, wot_nick):
            await self.clan_commands.rank_check(context, wot_nick)

        @self.command(name="clanRefresh")
        async def clan_refresh(context):
            await self.clan_commands.clan_refresh(context)

    async def on_message(self, message: Message) -> None:
        await super().on_message(message)
        if message.author != self.user:
            await self.chat_handler.handle_chat(message)
