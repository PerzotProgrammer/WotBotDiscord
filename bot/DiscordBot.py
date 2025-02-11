import random

import colorama
from discord import Intents, Message
from discord.ext import commands

from api_fetcher.WotClanDataFetcher import WotClanDataFetcher
from utils import debug_print


class DiscordBot(commands.Bot):
    def __init__(self, intents: Intents, wot_api_fetcher: WotClanDataFetcher):
        super().__init__(command_prefix='!', intents=intents)
        self.arty_words = ["arta", "arty"]
        self.arty_respond = ["You sink!", "WTH", "💩", "...", "Bój ci w lufę!"]

        @self.command(name="test")
        async def test(context):
            await context.send("Everything is fine!")
            debug_print("INFO: Test command executed.", colorama.Fore.CYAN)

        @self.command(name="showMembers")
        async def show_all_clan_members(context):
            playersData = wot_api_fetcher.players
            mess = ""
            for player in playersData:
                mess += f"{player.account_name}\n"
            await context.send(mess)

        @self.command(name="arty")
        async def arty(context):
            await context.send(self.roll_arty_respond())

        @self.command(name="register")
        async def register(context, dc_nick, wot_nick):
            await context.send("This currently doesn't work")

        @self.command(name="rankCheck")
        async def rank_check(context, wot_nick):
            for player in wot_api_fetcher.players:
                if player.account_name == wot_nick:
                    await context.send(f"Player {wot_nick} was found in the clan with rank {player.role}")
                    return
            await context.send(f"Player was not found in the clan. (try running !clanRefresh command)")

        @self.command(name="clanRefresh")
        async def clan_refresh(context):
            wot_api_fetcher.fetch_clan_members()
            if len(wot_api_fetcher.players) == 0:
                await context.send("Something gone wrong!")
                return
            await context.send("Ok!")

        debug_print("INFO: Bot is running!...", colorama.Fore.CYAN)

    async def on_message(self, message: Message) -> None:
        if message.author == self.user:
            return

        for arty_word in self.arty_words:
            if arty_word in str(message.content):
                await message.channel.send(self.roll_arty_respond())

    def roll_arty_respond(self) -> str:
        return self.arty_respond[random.randint(0, len(self.arty_respond) - 1)]
