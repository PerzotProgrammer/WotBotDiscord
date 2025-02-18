import datetime
from enum import Enum

import aiohttp
import colorama
from aiohttp import ClientResponse

from globals import do_not_print_debug_messages


class LogType(Enum):
    UNDEFINED = 0
    DATA = 1
    INFO = 2
    WARNING = 3
    ERROR = 4


async def handle_internal_status_codes(response: ClientResponse) -> int:
    try:
        response.raise_for_status()
    except aiohttp.ClientResponseError as e:
        debug_print(f"{e}", LogType.ERROR)

    data = await response.json()
    status_code = data['error']["code"] if "error" in data else response.status

    if status_code != 200:
        debug_print(f"{data['error']['message']}", LogType.ERROR)
    return status_code


def debug_print(message: str, log_type: LogType = LogType.UNDEFINED) -> None:
    if do_not_print_debug_messages:
        return

    if log_type == LogType.DATA:
        fore_color = colorama.Fore.BLUE
        log_type_str = "DATA"
    elif log_type == LogType.INFO:
        fore_color = colorama.Fore.CYAN
        log_type_str = "INFO"
    elif log_type == LogType.WARNING:
        fore_color = colorama.Fore.YELLOW
        log_type_str = "WARN"
    elif log_type == LogType.ERROR:
        fore_color = colorama.Fore.RED
        log_type_str = "ERROR"
    else:
        fore_color = colorama.Fore.WHITE
        log_type_str = ""

    print(
        f"{fore_color}{datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")} - {log_type_str}: {message}{colorama.Style.RESET_ALL}")


def timestamp_to_date(timestamp: int) -> str:
    return datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
