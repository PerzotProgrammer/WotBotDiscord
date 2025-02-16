from os import getenv

from api_fetcher.WotClanDataFetcher import WotClanDataFetcher


class ClanCommandsHandler:
    def __init__(self):
        self.wot_clan_data_fetcher = WotClanDataFetcher(getenv("WG_API_KEY"), getenv("CLAN_ID"))

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
            f"Player was not found in the clan. (if you are sure that `{wot_nick}` is in clan try running !clanRefresh command)")

    async def clan_refresh(self, context):
        players = await self.wot_clan_data_fetcher.fetch_clan_members()
        if len(players) == 0 or players is None:
            await context.send("I got no results! Something may gone wrong! Check my logs.")
            return
        await context.send(f"Ok! fetched {len(players)} players!")
