from random import randint

from discord import Message
from discord.ext import commands
from discord.ext.commands import Context
from singleton_decorator import singleton

from utils import debug_print, LogType


@singleton
class ChatInteractionsHandler(commands.Cog, name="Chat Interactions"):
    def __init__(self, bot):
        self.arty_words = ["arta", "arty"]
        self.arty_respond = ["You sink!", "WTH", "💩", "...", "Bój ci w lufę!"]
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: Message) -> None:
        if message.author == self.bot.user:
            return
        debug_print(f"Message received: {message.content}", LogType.INFO)
        await self.handle_arty_on_chat(message)

    async def handle_arty_on_chat(self, message: Message) -> None:
        for arty_word in self.arty_words:
            if arty_word in str(message.content):
                await message.reply(self.roll_arty_respond())

    def roll_arty_respond(self) -> str:
        return self.arty_respond[randint(0, len(self.arty_respond) - 1)]

    @commands.command(name="test", description="Test command.")
    async def chat_test(self, context: Context):
        await context.message.reply("# Everything is fine!")
        debug_print(f"Test command executed.", LogType.INFO)
