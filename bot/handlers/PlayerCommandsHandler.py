from os import getenv

from discord.ext import commands
from singleton_decorator import singleton

from api_fetcher.WotPlayerDataFetcher import WotPlayerDataFetcher
from utils import timestamp_to_date


@singleton
class PlayerCommandsHandler(commands.Cog, name="Player Commands"):
    def __init__(self, bot):
        self.wot_player_data_fetcher = WotPlayerDataFetcher(getenv("WG_API_KEY"))
        self.bot = bot

    @commands.command(name="playerInfo")
    async def player_info(self, context, wot_nick: str):
        wot_nick = wot_nick.strip("`")
        player_data = await self.wot_player_data_fetcher.fetch_player_data(wot_nick)

        if player_data is None:
            await context.send(f"Player `{wot_nick}` not found.")
            return

        msgBuff = (f"# Stats of `{wot_nick}`.\n" +
                   f"Rating: `{player_data.global_rating}`\n" +
                   f"Last battle: `{timestamp_to_date(player_data.last_battle_time)}`\n" +
                   f"Created at: `{timestamp_to_date(player_data.created_at)}`\n")

        if player_data.clan_tag is not None:
            msgBuff += (f"Clan: `{player_data.clan_tag}`\n" +
                        f"Role: `{player_data.role}`\n")
        await context.send(msgBuff)
