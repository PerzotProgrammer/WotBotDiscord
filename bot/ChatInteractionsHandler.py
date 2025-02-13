from random import randint

import colorama
from discord import Message

from utils import debug_print


class ChatInteractionsHandler:
    def __init__(self):
        self.arty_words = ["arta", "arty"]
        self.arty_respond = ["You sink!", "WTH", "💩", "...", "Bój ci w lufę!"]

    async def handle_chat(self, message: Message) -> None:
        debug_print(f"INFO: Message received: {message.content}", colorama.Fore.CYAN)
        await self.handle_arty_on_chat(message)

    async def handle_arty_on_chat(self, message: Message) -> None:
        for arty_word in self.arty_words:
            if arty_word in str(message.content):
                await message.channel.send(self.roll_arty_respond())

    def roll_arty_respond(self) -> str:
        return self.arty_respond[randint(0, len(self.arty_respond) - 1)]

    @staticmethod
    async def chat_test(context):
        await context.send("Everything is fine!")
        debug_print(f"INFO: Test command executed.", colorama.Fore.CYAN)
