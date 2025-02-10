from os import getenv

import colorama
from dotenv import load_dotenv

from api_fetcher.WotClanDataFetcher import WotClanDataFetcher
from api_fetcher.utils import debug_print

#################################################
# NOTE: To run this bot you need to have a .env file in the root directory with the following variables:
# WG_API_KEY=YOUR_WG_API_KEY
# CLAN_ID=YOUR_CLAN_ID

if __name__ == "__main__":
    debug_print("INFO: Initializing...", colorama.Fore.CYAN)
    load_dotenv()

    wot_api_fetcher = WotClanDataFetcher(getenv("WG_API_KEY"), getenv("CLAN_ID"))
    wot_api_fetcher.print_members_data()
    wot_api_fetcher.print_roles_count()
    wot_api_fetcher.print_grouped_members_by_role()
