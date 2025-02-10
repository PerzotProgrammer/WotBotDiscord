import colorama
import requests

from api_fetcher.utils import handle_status_codes, debug_print
from data_models.ClanPlayerData import ClanPlayerData


class WotClanDataFetcher:
    def __init__(self, wg_api_key, clan_id):
        self.url = "https://api.worldoftanks.eu/wot/"
        self.wg_api_key = wg_api_key
        self.clan_id = clan_id
        self.players = list[ClanPlayerData]

        if self.wg_api_key == "":
            debug_print("ERROR: No WG_API_KEY found in .env file. THIS PROGRAM CANT RUN WITHOUT IT! Exiting...",
                        colorama.Fore.RED)
            exit(1)
        if self.clan_id == "":
            debug_print("WARNING: No CLAN_ID found in .env file. Players will not be pre-fetched!",
                        colorama.Fore.YELLOW)
            debug_print("WARNING: You must specify the clan_id when calling the fetch_clan_members method.",
                        colorama.Fore.YELLOW)
        else:
            self.players = self.fetch_clan_members()
        debug_print("INFO: WotClanDataFetcher initialized.", colorama.Fore.CYAN)

    # region API fetching methods
    ############################################################
    # Fetches the clan members from the WG API. If no clan_id is provided, it will use the clan_id from the .env file.
    # Returns a list of ClanPlayerData objects and makes a copy in self.players.
    # API CALL: https://api.worldoftanks.eu/wot/clans/info/?application_id=APP_ID_HERE&clan_id=CLAN_ID_HERE&fields=members
    ############################################################
    def fetch_clan_members(self) -> list[ClanPlayerData]:
        response = requests.get(
            f"{self.url}clans/info/?application_id={self.wg_api_key}&clan_id={self.clan_id}&fields=members")

        if handle_status_codes(response) != 200:
            return []

        members_list = response.json()["data"][self.clan_id]["members"]
        self.players = []
        for member in members_list:
            self.players.append(ClanPlayerData(member["account_name"],
                                               member["account_id"],
                                               member["role"]))
        return self.players

    # endregion
    # region Get data methods

    ############################################################
    # Finds a player in the players list by account_name.
    ############################################################
    def find_player_data(self, account_name) -> ClanPlayerData | None:
        for player in self.players:
            if player.account_name == account_name:
                return player
        debug_print("WARNING: Player not found in players. Maybe the player is not in the clan?", colorama.Fore.YELLOW)
        return None

    ############################################################
    # Tells how many of what rank players are in clan.
    ############################################################
    def get_roles_count(self) -> dict[str, int]:
        roles = {}
        for player in self.players:
            if player.role in roles:
                roles[player.role] += 1
            else:
                roles[player.role] = 1
        return roles

    ############################################################
    # Groups the players by role.
    ############################################################
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

    ############################################################
    # Prints all members data to console. (for debugging purposes)
    ############################################################
    def print_members_data(self) -> None:
        for player in self.players:
            print(f"Account Name: {player.account_name}\tAccount ID: {player.account_id}\tRole: {player.role}")
        debug_print("INFO: Done printing all members data.", colorama.Fore.CYAN)

    ############################################################
    # Prints all roles and their counts to console. (for debugging purposes)
    ############################################################
    def print_roles_count(self) -> None:
        roles = self.get_roles_count()
        for role, count in roles.items():
            debug_print(f"Role: {role}\tCount: {count}", colorama.Fore.BLUE)
        debug_print("INFO: Done printing all roles count.", colorama.Fore.CYAN)

    ############################################################
    # Prints all members grouped by role to console. (for debugging purposes)
    ############################################################
    def print_grouped_members_by_role(self) -> None:
        roles = self.group_members_by_role()
        for role, players in roles.items():
            debug_print(f"Role: {role}", colorama.Fore.BLUE)
            for player in players:
                debug_print(f"Account Name: {player.account_name}", colorama.Fore.BLUE)
        debug_print("INFO: Done printing all members grouped by role.", colorama.Fore.CYAN)
    # endregion
