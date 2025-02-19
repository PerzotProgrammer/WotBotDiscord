import discord
from discord import Intents, Message
from discord.ext import commands
from discord.ext.commands import Context
from singleton_decorator import singleton

from bot.handlers.ChatInteractionsHandler import ChatInteractionsHandler
from bot.handlers.ClanCommandsHandler import ClanCommandsHandler
from bot.handlers.PlayerCommandsHandler import PlayerCommandsHandler
from utils import debug_print, LogType


@singleton
class DiscordBot(commands.Bot):
    def __init__(self, intents: Intents):
        super().__init__(command_prefix='!', intents=intents)

        self.player_commands = PlayerCommandsHandler()
        self.clan_commands = ClanCommandsHandler()
        self.chat_handler = ChatInteractionsHandler()

        debug_print("Bot is running!...", LogType.INFO)

        @self.command(name="test")
        async def test(context: Context):
            await self.chat_handler.chat_test(context)

        @self.command(name="playerInfo")
        async def player_info(context: Context, player_name: str):
            await self.player_commands.player_info(context, player_name)

        @self.command(name="whoami")
        async def whoami(context: Context):
            await self.clan_commands.whoami(context, context.message.author)

        @self.command(name="showMembers")
        async def show_members(context: Context):
            await self.clan_commands.show_members(context)

        @self.command(name="rankCheck")
        async def rank_check(context: Context, wot_nick: str):
            await self.clan_commands.rank_check(context, wot_nick)

        @self.command(name="register")
        async def register(context: Context, wot_nick: str, discord_user: discord.User):
            await self.clan_commands.register(context, wot_nick, discord_user)

        @self.command(name="clanRefresh")
        async def clan_refresh(context: Context):
            await self.clan_commands.clan_refresh(context)

        @self.command(name="addAdvance")
        async def add_advance(context: Context):
            await self.clan_commands.add_advance(context, context.message.author)

        @self.command(name="optForAdv")
        async def opt_for_adv(context: Context):
            await self.clan_commands.register_user_for_adv(context, context.message.author)

    async def on_message(self, message: Message) -> None:
        await super().on_message(message)
        if message.author != self.user.bot:
            await self.chat_handler.handle_chat(message)
