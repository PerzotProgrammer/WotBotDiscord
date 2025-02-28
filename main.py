from os import getenv

import discord
from dotenv import load_dotenv

from api_fetcher.WotClanDataFetcher import WotClanDataFetcher
from bot.DiscordBot import DiscordBot
from database.DatabaseConnector import DatabaseConnector
from utils import debug_print, LogType

#################################################
# NOTE: To run this bot you need to have a .env file in the root directory with the following variables:
# WG_API_KEY=YOUR_WG_API_KEY
# CLAN_ID=YOUR_CLAN_ID

if __name__ == "__main__":
    debug_print("Initializing...", LogType.INFO)
    load_dotenv()

    if getenv("WG_API_KEY") == "":
        debug_print("No WG_API_KEY found in .env file. THIS PROGRAM CANT RUN WITHOUT IT! Exiting...",
                    LogType.ERROR)
        exit(1)

    DatabaseConnector("./database/database.db")
    WotClanDataFetcher(getenv("WG_API_KEY"), getenv("CLAN_ID"))
    intents = discord.Intents.all()
    bot = DiscordBot(intents=intents)
    bot.run(getenv("DISCORD_BOT_TOKEN"))
