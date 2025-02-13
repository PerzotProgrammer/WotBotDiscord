import datetime

import aiohttp
import colorama
from aiohttp import ClientResponse

from globals import do_not_print_debug_messages


async def handle_internal_status_codes(response: ClientResponse) -> int:
    try:
        response.raise_for_status()
    except aiohttp.ClientResponseError as e:
        debug_print(f"ERROR: {e}", colorama.Fore.RED)

    data = await response.json()
    status_code = data['error']["code"] if "error" in data else response.status

    if status_code != 200:
        debug_print(f"ERROR: {data['error']['message']}", colorama.Fore.RED)
    return status_code


def debug_print(message: str, fore_color: colorama.Fore) -> None:
    if do_not_print_debug_messages:
        return
    print(f"{fore_color}{datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")} - {message}{colorama.Style.RESET_ALL}")
