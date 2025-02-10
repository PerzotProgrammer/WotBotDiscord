import datetime

import colorama
import requests

from globals import do_not_print_debug_messages


def handle_status_codes(response) -> int:
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        debug_print(f"ERROR: {e}", colorama.Fore.RED)

    status_code = response.json()['error']["code"] if "error" in response.json() else response.status_code

    if status_code != 200:
        debug_print(f"ERROR: {response.json()['error']['message']}", colorama.Fore.RED)
    return status_code


def debug_print(message: str, fore_color: colorama.Fore) -> None:
    if do_not_print_debug_messages:
        return
    print(f"{fore_color}{datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")} - {message}{colorama.Style.RESET_ALL}")
