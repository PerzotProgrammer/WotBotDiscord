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
        debug_print("wot_nameWotClanDataFetcher initialized.", LogType.INFO)

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
                    self.players.append(ClanPlayerData(member["account_name"],
                                                       member["account_id"],
                                                       member["role"]))
                debug_print(f"wot_nameClan members fetched, {len(self.players)} results.", LogType.INFO)
        return self.players

    # endregion
    # region Get data methods

    def find_player_data(self, wot_name) -> ClanPlayerData | None:
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
    # region Debugging methods

    def print_members_data(self) -> None:
        for player in self.players:
            debug_print(
                f"Account Name: {player.wot_name}\tAccount ID: {player.account_id}\tRole: {player.role}",
                LogType.DATA)
        debug_print("Done printing all members data.", LogType.INFO)

    def print_roles_count(self) -> None:
        roles = self.get_roles_count()
        for role, count in roles.items():
            debug_print(f"Role: {role}\tCount: {count}", LogType.DATA)
        debug_print("Done printing all roles count.", LogType.INFO)

    def print_grouped_members_by_role(self) -> None:
        roles = self.group_members_by_role()
        for role, players in roles.items():
            debug_print(f"Role: {role}", LogType.DATA)
            for player in players:
                debug_print(f"Account Name: {player.wot_name}", LogType.DATA)
        debug_print("Done printing all members grouped by role.", LogType.INFO)
    # endregion
