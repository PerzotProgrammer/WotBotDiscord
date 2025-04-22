from random import randint

from discord import Message
from discord.ext.commands import Cog
from singleton_decorator import singleton

from globals import do_not_print_chat_messages
from utils import debug_print, LogType


@singleton
class ChatInteractionsCog(Cog, name="Chat Interactions"):
    def __init__(self, bot):
        self.arty_words = ["arta", "arty", "olek"]
        self.arty_respond = ["You sink!", "WTH", "💩", "...", "Bój ci w lufę!"]
        self.bot = bot
        debug_print("ChatInteractionsCog initialized.", LogType.INFO)

    @Cog.listener()
    async def on_message(self, message: Message) -> None:
        if message.author == self.bot.user:
            return
        if not do_not_print_chat_messages:
            debug_print(f"Message received from user {message.author.name} "
                        f"on [{message.guild.name}]-[{message.channel.name}]: {message.content}",
                        LogType.INFO)
        await self.handle_arty_on_chat(message)

    async def handle_arty_on_chat(self, message: Message) -> None:
        for arty_word in self.arty_words:
            if arty_word in str(message.content):
                await message.reply(self.roll_arty_respond())

    def roll_arty_respond(self) -> str:
        return self.arty_respond[randint(0, len(self.arty_respond) - 1)]
