import sqlite3
from enum import Enum

from singleton_decorator import singleton

from data_models.ClanPlayerData import ClanPlayerData
from utils import debug_print, LogType


class DatabaseResultCode(Enum):
    OK = 0
    INTERNAL_ERROR = 1
    FORBIDDEN = 2
    ALREADY_EXISTS = 3
    NOT_FOUND = 4


@singleton
class DatabaseConnector:
    def __init__(self, database_path: str):
        self.connection = sqlite3.connect(database_path)
        self.cursor = self.connection.cursor()

    async def add_advance(self, invoker_discord_id: str) -> bool:
        pass
        # try:
        #     self.cursor.execute("SELECT * FROM wot_players WHERE discord_id = ?", invoker_discord_id)
        #     blob = self.cursor.fetchone()
        #     if blob is None or blob["role"] != "commander" or blob["role"] != "executive_officer" or blob["role"] != "":
        #         return DatabaseResultCode(DatabaseResultCode.FORBIDDEN)
        # 
        #     self.cursor.execute(
        #         f"INSERT INTO wot_advances (date, invoked_by) VALUES ('{datetime.datetime.now().timestamp()}','{invoker_discord_id}')")
        #     self.connection.commit()
        # except sqlite3.Error:
        #     return DatabaseResultCode(DatabaseResultCode.INTERNAL_ERROR)
        # return DatabaseResultCode(DatabaseResultCode.OK)

    async def add_clan_member(self, playerData: ClanPlayerData) -> DatabaseResultCode:
        try:
            self.cursor.execute(f"SELECT * FROM wot_players WHERE wot_id = '{playerData.account_id}'")

            if self.cursor.fetchone() is not None:
                return DatabaseResultCode(DatabaseResultCode.ALREADY_EXISTS)

            self.cursor.execute(
                f"INSERT INTO wot_players (wot_id, wot_name, role) "
                f"VALUES ('{playerData.account_id}', '{playerData.account_name}', '{playerData.role}')")
            self.connection.commit()

        except sqlite3.Error:
            return DatabaseResultCode(DatabaseResultCode.INTERNAL_ERROR)
        return DatabaseResultCode(DatabaseResultCode.OK)

    async def update_rank(self, playerData: ClanPlayerData) -> DatabaseResultCode:
        try:
            self.cursor.execute(f"SELECT * FROM wot_players WHERE wot_id = '{playerData.account_id}'")

            if self.cursor.fetchone() is None:
                return DatabaseResultCode(DatabaseResultCode.NOT_FOUND)

            self.cursor.execute(
                f"UPDATE wot_players SET role = '{playerData.role}' WHERE wot_id = '{playerData.account_id}'")
            self.connection.commit()

        except sqlite3.Error as e:
            debug_print(f"Could not update rank for {playerData.account_name}. {e}", LogType.ERROR)
            return DatabaseResultCode(DatabaseResultCode.INTERNAL_ERROR)

        return DatabaseResultCode(DatabaseResultCode.OK)

    async def add_discord_user_ref(self, wot_name: str, discord_id: str, caller_discord_id: str) -> DatabaseResultCode:
        try:
            self.cursor.execute(f"SELECT * FROM discord_users_ids WHERE discord_id = '{discord_id}'")

            if self.cursor.fetchone() is not None:
                debug_print(f"Discord user already registered. {discord_id}", LogType.WARNING)
                return DatabaseResultCode(DatabaseResultCode.ALREADY_EXISTS)

            blob = self.cursor.execute(f"SELECT * FROM wot_players WHERE wot_name = '{wot_name}'").fetchone()
            if blob is None:
                debug_print(f"Player not found in database. {wot_name}", LogType.WARNING)
                return DatabaseResultCode(DatabaseResultCode.NOT_FOUND)

            self.cursor.execute(
                f"Insert INTO discord_users_ids (discord_id, discord_name, player_id) VALUES ('{discord_id}' ,'temp_name','{blob[0]}')")
            self.connection.commit()

        except sqlite3.Error as e:
            debug_print(f"Could not add discord user reference. {e}", LogType.ERROR)
            return DatabaseResultCode(DatabaseResultCode.INTERNAL_ERROR)
        return DatabaseResultCode(DatabaseResultCode.OK)

    def is_player_in_db(self, wot_nick: str) -> bool:
        self.cursor.execute(f"SELECT * FROM wot_players WHERE wot_name = '{wot_nick}'")
        return self.cursor.fetchone() is not None

    def get_player_as_object(self, wot_name: str) -> ClanPlayerData | None:
        self.cursor.execute(f"SELECT * FROM wot_players WHERE wot_name = '{wot_name}'")
        blob = self.cursor.fetchone()
        if blob is None:
            return None
        return ClanPlayerData(blob[1], blob[2], blob[3])
