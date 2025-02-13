from os import getenv

import colorama
import discord
from dotenv import load_dotenv

from bot.DiscordBot import DiscordBot
from utils import debug_print

#################################################
# NOTE: To run this bot you need to have a .env file in the root directory with the following variables:
# WG_API_KEY=YOUR_WG_API_KEY
# CLAN_ID=YOUR_CLAN_ID

if __name__ == "__main__":
    debug_print("INFO: Initializing...", colorama.Fore.CYAN)
    load_dotenv()

    intents = discord.Intents.default()
    intents.message_content = True
    bot = DiscordBot(intents=intents)
    bot.run(getenv("DISCORD_BOT_TOKEN"))
