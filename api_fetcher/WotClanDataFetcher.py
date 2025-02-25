import asyncio

import aiohttp
from singleton_decorator import singleton

from data_models.ClanPlayerData import ClanPlayerData
from utils import handle_internal_status_codes, debug_print, LogType


@singleton
class WotClanDataFetcher:
    def __init__(self, wg_api_key, clan_id):
        self.url = "https://api.worldoftanks.eu/wot/clans"
        self.wg_api_key = wg_api_key
        self.clan_id = clan_id
        self.players = list[ClanPlayerData]

        if self.clan_id == "":
            debug_print("No CLAN_ID found in .env file. Players will not be pre-fetched!",
                        LogType.WARNING)
            debug_print("You must specify the clan_id when calling the fetch_clan_members method.",
                        LogType.WARNING)
        else:
            self.players = asyncio.run(self.fetch_clan_members())
        debug_print("WotClanDataFetcher initialized.", LogType.INFO)

    # region API fetching methods

    async def fetch_clan_members(self) -> list[ClanPlayerData] | None:
        async with aiohttp.ClientSession() as self.session:
            async with self.session.get(
                    f"{self.url}/info/?application_id={self.wg_api_key}&clan_id={self.clan_id}&fields=members") as response:

                code = await handle_internal_status_codes(response)
                if code != 200:
                    debug_print(f"Could not fetch clan members. Response code: {code}", LogType.ERROR)
                    return None

                data = await response.json()

                members_list = data["data"][self.clan_id]["members"]
                self.players = []
                for member in members_list:
                    self.players.append(ClanPlayerData(
                        member["account_id"],
                        member["account_name"],
                        member["role"]))
                debug_print(f"Clan members fetched, {len(self.players)} results.", LogType.INFO)
        return self.players

    # endregion
    # region Get data methods

    def find_player_data_by_pid(self, pid) -> ClanPlayerData | None:
        for player in self.players:
            if player.pid == pid:
                return player
        debug_print("Player not found in players. Maybe the player is not in the clan?", LogType.WARNING)
        return None

    def find_player_data_by_name(self, wot_name) -> ClanPlayerData | None:
        for player in self.players:
            if player.wot_name == wot_name:
                return player
        debug_print("Player not found in players. Maybe the player is not in the clan?", LogType.WARNING)
        return None

    def get_roles_count(self) -> dict[str, int]:
        roles = {}
        for player in self.players:
            if player.role in roles:
                roles[player.role] += 1
            else:
                roles[player.role] = 1
        return roles

    def group_members_by_role(self) -> dict[str, list[ClanPlayerData]]:
        roles = {}
        for player in self.players:
            if player.role in roles:
                roles[player.role].append(player)
            else:
                roles[player.role] = [player]
        return roles

    # endregion
