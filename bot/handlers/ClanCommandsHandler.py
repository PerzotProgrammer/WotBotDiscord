from os import getenv

from singleton_decorator import singleton

from api_fetcher.WotClanDataFetcher import WotClanDataFetcher
from database.DatabaseConnector import DatabaseConnector, DatabaseResultCode


@singleton
class ClanCommandsHandler:
    def __init__(self):
        self.wot_clan_data_fetcher = WotClanDataFetcher(getenv("WG_API_KEY"), getenv("CLAN_ID"))
        self.databaseConnector = DatabaseConnector()

    async def show_members(self, context):
        playersData = self.wot_clan_data_fetcher.players
        mess = "# MEMBERS IN CLAN\n"
        for player in playersData:
            messBuff = f"### player `{player.account_name}` with `{player.role}`\n"
            if len(mess) + len(messBuff) > 2000:
                await context.send(mess)
                mess = ""
            mess += messBuff

    async def rank_check(self, context, wot_nick: str):
        for player in self.wot_clan_data_fetcher.players:
            wot_nick = wot_nick.strip("`")
            if player.account_name == wot_nick:
                await context.send(f"Player `{player.account_name}` was found in the clan with rank `{player.role}`")
                return
        await context.send(
            f"Player was not found in the clan.\n(if you are sure that `{wot_nick}` is in clan try running !clanRefresh command)")

    async def clan_refresh(self, context):
        players = await self.wot_clan_data_fetcher.fetch_clan_members()

        if len(players) == 0 or players is None:
            await context.send("I got no results!\nSomething may gone wrong! Check my logs.")
            return

        skipped_players = 0
        updated_players = 0
        added_players = 0
        for player in players:
            if self.databaseConnector.is_player_in_db(player.account_name):
                dbError = await self.databaseConnector.update_rank(player)
                updated_players += 1
            else:
                dbError = await self.databaseConnector.add_clan_member(player)
                added_players += 1
            if dbError != DatabaseResultCode.OK:
                skipped_players += 1

        await context.send(
            f"## Ok!\n" +
            f"Got {len(players)} players.\n" +
            f"Updated {updated_players} players.\n" +
            f"Added {added_players} players.\n" +
            f"Skipped {skipped_players} players.")

    async def register(self, context, wot_nick: str, discord_at_id: str):
        wot_nick = wot_nick.strip("`")
        player = self.wot_clan_data_fetcher.find_player_data(wot_nick)
        if player is None:
            await context.send(f"Player `{wot_nick}` not found in clan.")
            return

        dbError = await self.databaseConnector.add_discord_user_ref(wot_nick, discord_at_id, "")
        if dbError != DatabaseResultCode.OK:
            if dbError == DatabaseResultCode.ALREADY_EXISTS:
                await context.send(f"Player `{wot_nick}` was already registered!")
            if dbError == DatabaseResultCode.NOT_FOUND:
                await context.send(f"Player `{wot_nick}` not found in database.\n Run !clanRefresh command manually.")
            return

        await context.send(f"Player `{wot_nick}` registered!")
