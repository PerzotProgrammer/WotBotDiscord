import aiohttp
from singleton_decorator import singleton

from data_models.PlayerDetailsData import PlayerDetailsData
from utils import debug_print, handle_internal_status_codes, LogType


@singleton
class WotPlayerDataFetcher:
    def __init__(self, wg_api_key):
        self.url = "https://api.worldoftanks.eu/wot/account"
        self.wg_api_key = wg_api_key

    debug_print("WotPlayerDataFetcher initialized.", LogType.INFO)

    async def fetch_player_data(self, player_name) -> PlayerDetailsData | None:
        async with aiohttp.ClientSession() as self.session:
            async with self.session.get(
                    f"{self.url}/list/?application_id={self.wg_api_key}&search={player_name}&limit=1") as response:
                code = await handle_internal_status_codes(response)
                if code != 200:
                    debug_print(f"Could not fetch player data. Response code: {code}", LogType.ERROR)
                    return None

                data = await response.json()
                account_id = data["data"][0]["account_id"]
                if account_id is None:
                    debug_print(f"Player not found: {player_name}", LogType.WARNING)
                    return None

            async with self.session.get(
                    f"{self.url}/info/?application_id={self.wg_api_key}&account_id={account_id}&fields=last_battle_time%2Ccreated_at%2Cupdated_at%2Cglobal_rating%2Cclan_id") as response:
                code = await handle_internal_status_codes(response)
                if code != 200:
                    debug_print(f"Could not fetch player data. Response code: {code}", LogType.ERROR)
                    return None

                data = await response.json()
                player_data = data["data"][str(account_id)]
                clan_id = str(player_data["clan_id"])

                player_data_obj = PlayerDetailsData(player_name,
                                                    player_data["last_battle_time"],
                                                    player_data["created_at"],
                                                    player_data["global_rating"])

            async with self.session.get(
                    f"https://api.worldoftanks.eu/wot/clans/info/?application_id={self.wg_api_key}&clan_id={clan_id}&fields=tag%2Cmembers&members_key=id") as response:
                code = await handle_internal_status_codes(response)
                if code == 407:  # Clan not found i.e. player is not in a clan
                    return player_data_obj

                if code != 200:
                    debug_print(f"Could not fetch player data. Response code: {code}", LogType.ERROR)
                    return None

                data = await response.json()
                clan_data = data["data"][clan_id]
                debug_print("Player data fetched.", LogType.INFO)

                player_data_obj.set_clan_data(clan_data["tag"], clan_data["members"][str(account_id)]["role"])
                return player_data_obj
