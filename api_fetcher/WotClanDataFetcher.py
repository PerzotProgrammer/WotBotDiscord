import asyncio

import aiohttp
import colorama

from data_models.ClanPlayerData import ClanPlayerData
from utils import handle_internal_status_codes, debug_print


class WotClanDataFetcher:
    def __init__(self, wg_api_key, clan_id):
        self.url = "https://api.worldoftanks.eu/wot/clans"
        self.wg_api_key = wg_api_key
        self.clan_id = clan_id
        self.players = list[ClanPlayerData]

        if self.clan_id == "":
            debug_print("WARN: No CLAN_ID found in .env file. Players will not be pre-fetched!",
                        colorama.Fore.YELLOW)
            debug_print("WARN: You must specify the clan_id when calling the fetch_clan_members method.",
                        colorama.Fore.YELLOW)
        else:
            self.players = asyncio.run(self.fetch_clan_members())
        debug_print("INFO: WotClanDataFetcher initialized.", colorama.Fore.CYAN)

    # region API fetching methods

    async def fetch_clan_members(self) -> list[ClanPlayerData] | None:
        async with aiohttp.ClientSession() as self.session:
            async with self.session.get(
                    f"{self.url}/info/?application_id={self.wg_api_key}&clan_id={self.clan_id}&fields=members") as response:

                code = await handle_internal_status_codes(response)
                if code != 200:
                    debug_print(f"ERROR: Could not fetch clan members. Response code: {code}", colorama.Fore.RED)
                    return None

                data = await response.json()

                members_list = data["data"][self.clan_id]["members"]
                self.players = []
                for member in members_list:
                    self.players.append(ClanPlayerData(member["account_name"],
                                                       member["account_id"],
                                                       member["role"]))
                debug_print(f"INFO: Clan members fetched, {len(self.players)} results.", colorama.Fore.CYAN)
        return self.players

    # endregion
    # region Get data methods

    def find_player_data(self, account_name) -> ClanPlayerData | None:
        for player in self.players:
            if player.account_name == account_name:
                return player
        debug_print("WARN: Player not found in players. Maybe the player is not in the clan?", colorama.Fore.YELLOW)
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
                f"DATA: Account Name: {player.account_name}\tAccount ID: {player.account_id}\tRole: {player.role}",
                colorama.Fore.BLUE)
        debug_print("INFO: Done printing all members data.", colorama.Fore.CYAN)

    def print_roles_count(self) -> None:
        roles = self.get_roles_count()
        for role, count in roles.items():
            debug_print(f"DATA: Role: {role}\tCount: {count}", colorama.Fore.BLUE)
        debug_print("INFO: Done printing all roles count.", colorama.Fore.CYAN)

    def print_grouped_members_by_role(self) -> None:
        roles = self.group_members_by_role()
        for role, players in roles.items():
            debug_print(f"DATA: Role: {role}", colorama.Fore.BLUE)
            for player in players:
                debug_print(f"DATA: Account Name: {player.account_name}", colorama.Fore.BLUE)
        debug_print("INFO: Done printing all members grouped by role.", colorama.Fore.CYAN)
    # endregion
