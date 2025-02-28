from os import getenv

from discord import Member
from discord.ext.commands import Cog, command, Context
from singleton_decorator import singleton

from api_fetcher.WotPlayerDataFetcher import WotPlayerDataFetcher
from database.DatabaseConnector import DatabaseConnector
from globals import clan_roles_localized
from utils import timestamp_to_date, LogType, debug_print


@singleton
class PlayerSpecificCommandsCog(Cog, name="Player Specific Commands"):
    def __init__(self, bot):
        self.wot_player_data_fetcher = WotPlayerDataFetcher(getenv("WG_API_KEY"))
        self.bot = bot
        debug_print("PlayerSpecificCommandsCog initialized.", LogType.INFO)

    @command(name="playerInfo")
    async def player_info(self, context, param: Member | str):
        """
        Shows player info.
        The data is fetched from the Wargaming API.
        Works only with clan players.
        :param param: World of Tanks nickname or @user.
        """
        if type(param) is Member:
            print("AWGGAWGAWg")
            wot_nick = await DatabaseConnector().get_wot_nick_from_discord_id(str(param.id))
        else:
            wot_nick = param.strip("`")
        player_data = await self.wot_player_data_fetcher.fetch_player_data(wot_nick)

        if player_data is None:
            await context.send(f"Player `{param.name}` (nick or @user link) not found.")
            return

        msgBuff = (f"# Stats of `{wot_nick}`.\n" +
                   f"Rating: `{player_data.global_rating}`\n" +
                   f"Last battle: `{timestamp_to_date(player_data.last_battle_time)}`\n" +
                   f"Created at: `{timestamp_to_date(player_data.created_at)}`\n")

        if player_data.clan_tag is not None:
            msgBuff += (f"Clan: `{player_data.clan_tag}`\n" +
                        f"Role: `{player_data.role}`\n")
        await context.send(msgBuff)

    @command(name="checkMyRank")
    async def rank_check(self, context: Context):
        """
        Shows player rank in the clan.
        The data is fetched from the Wargaming API (it could be different from data in database, if so, run !clanRefresh command).
        """
        wot_nick = await DatabaseConnector().get_wot_nick_from_discord_id(str(context.author.id))
        if wot_nick is None:
            await context.send("You are not linked to any wot account in database.")
            return

        player = await self.wot_player_data_fetcher.fetch_player_data(wot_nick)
        await context.send(
            f"Player `{player.account_name}` was found in the clan with rank `{clan_roles_localized[player.role]}`")
