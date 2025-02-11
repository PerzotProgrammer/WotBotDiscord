import random

import colorama
from discord import Intents, Message
from discord.ext import commands

from api_fetcher.WotClanDataFetcher import WotClanDataFetcher
from utils import debug_print


class DiscordBot(commands.Bot):
    def __init__(self, intents: Intents, wot_api_fetcher: WotClanDataFetcher):
        super().__init__(command_prefix='!', intents=intents)
        self.wot_api_fetcher = wot_api_fetcher
        self.arty_words = ["arta", "arty"]
        self.arty_respond = ["You sink!", "WTH", "💩", "...", "Bój ci w lufę!"]
        debug_print("INFO: Bot is running!...", colorama.Fore.CYAN)

        # region Command registration

        @self.command(name="test")
        async def test(context, arg):
            await self.test(context, arg)

        @self.command(name="showMembers")
        async def show_members(context):
            await self.show_members(context)

        @self.command(name="arty")
        async def arty(context):
            await context.send(self.roll_arty_respond())

        @self.command(name="register")
        async def register(context, dc_nick, wot_nick):
            await context.send("This currently doesn't work")

        @self.command(name="rankCheck")
        async def rank_check(context, wot_nick):
            await self.rank_check(context, wot_nick)

        @self.command(name="clanRefresh")
        async def clan_refresh(context):
            await self.clan_refresh(context)

        # endregion

    async def on_message(self, message: Message) -> None:
        await super().on_message(message)
        await self.handle_arty_on_chat(message)

    # region Command implementations

    async def handle_arty_on_chat(self, message: Message) -> None:
        if message.author == self.user:
            return

        for arty_word in self.arty_words:
            if arty_word in str(message.content):
                await message.channel.send(self.roll_arty_respond())

    def roll_arty_respond(self) -> str:
        return self.arty_respond[random.randint(0, len(self.arty_respond) - 1)]

    @staticmethod
    async def test(context, arg: str):
        await context.send("Everything is fine!")
        myArg = arg.strip("`")
        debug_print(f"INFO: Test command executed. Arg was: {myArg}", colorama.Fore.CYAN)

    async def show_members(self, context):
        playersData = self.wot_api_fetcher.players
        mess = "#MEMBERS IN CLAN\n"
        for player in playersData:
            messBuff = f"### player `{player.account_name}` with `{player.role}`\n"
            if len(mess) + len(messBuff) > 2000:
                await context.send(mess)
                mess = ""
            mess += messBuff

    async def rank_check(self, context, wot_nick: str):
        for player in self.wot_api_fetcher.players:
            wot_nick = wot_nick.strip("`")
            if player.account_name == wot_nick:
                await context.send(f"Player `{player.account_name}` was found in the clan with rank `{player.role}`")
                return
        await context.send(
            f"Player was not found in the clan. (if you are sure that `{wot_nick}` is in clan try running !clanRefresh command)")

    async def clan_refresh(self, context):
        players = self.wot_api_fetcher.fetch_clan_members()
        if len(players) == 0:
            await context.send("I got no results! Something may gone wrong! Check my logs.")
            return
        await context.send(f"Ok! fetched {len(players)} players!")

    # endregion
