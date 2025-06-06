import sqlite3
import time
from datetime import datetime
from enum import Enum
from typing import Any

from discord import Member
from singleton_decorator import singleton

from data_models.ClanPlayerData import ClanPlayerData
from utils import debug_print, LogType


class DatabaseResultCode(Enum):
    OK = 0
    INTERNAL_ERROR = 1
    FORBIDDEN = 2
    ALREADY_EXISTS = 3
    NOT_FOUND = 4
    SKIPPED = 5


@singleton
class DatabaseConnector:
    def __init__(self, database_path: str):
        self.connection = sqlite3.connect(database_path)
        self.cursor = self.connection.cursor()

    async def add_advance(self, invoker_discord_id: str) -> DatabaseResultCode:
        try:
            # self.cursor.execute(
            #     f"SELECT role FROM wot_players INNER JOIN discord_users ON wot_players.pid = discord_users.pid WHERE uid = {invoker_discord_id}", )
            # blob = self.cursor.fetchone()
            # if blob is None or blob[0] not in clan_staff_ranks:
            #     return DatabaseResultCode(DatabaseResultCode.FORBIDDEN)

            self.cursor.execute(
                f"INSERT INTO wot_advances (date, invoker_uid) VALUES ('{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}','{invoker_discord_id}')")
            self.connection.commit()
        except sqlite3.Error as e:
            debug_print(f"Could not add advance. {e}", LogType.ERROR)
            return DatabaseResultCode(DatabaseResultCode.INTERNAL_ERROR)
        return DatabaseResultCode(DatabaseResultCode.OK)

    async def add_clan_member(self, playerData: ClanPlayerData) -> DatabaseResultCode:
        try:
            self.cursor.execute(f"SELECT pid FROM wot_players WHERE pid = '{playerData.pid}'")

            if self.cursor.fetchone() is not None:
                return DatabaseResultCode(DatabaseResultCode.ALREADY_EXISTS)

            self.cursor.execute(
                f"INSERT INTO wot_players (pid, wot_name, role) "
                f"VALUES ('{playerData.pid}', '{playerData.wot_name}', '{playerData.role}')")
            self.connection.commit()

        except sqlite3.Error as e:
            debug_print(f"Could not add clan member {playerData.wot_name}. {e}", LogType.ERROR)
            return DatabaseResultCode(DatabaseResultCode.INTERNAL_ERROR)
        return DatabaseResultCode(DatabaseResultCode.OK)

    async def update_rank(self, playerData: ClanPlayerData, silent=False) -> DatabaseResultCode:
        try:
            self.cursor.execute(f"SELECT role FROM wot_players WHERE pid = '{playerData.pid}'")
            blob = self.cursor.fetchone()
            if blob is None:
                if not silent:
                    debug_print(f"Player not found in database. {playerData.wot_name}", LogType.WARNING)
                return DatabaseResultCode(DatabaseResultCode.NOT_FOUND)

            if blob[0] == playerData.role:
                if not silent:
                    debug_print(f"Player {playerData.wot_name} already has the same role.", LogType.INFO)
                return DatabaseResultCode(DatabaseResultCode.SKIPPED)

            self.cursor.execute(
                f"UPDATE wot_players SET role = '{playerData.role}' WHERE pid = '{playerData.pid}'")
            self.connection.commit()

        except sqlite3.Error as e:
            debug_print(f"Could not update rank for {playerData.wot_name}. {e}", LogType.ERROR)
            return DatabaseResultCode(DatabaseResultCode.INTERNAL_ERROR)

        return DatabaseResultCode(DatabaseResultCode.OK)

    async def add_discord_user_ref(self, wot_name: str, discord_user: Member) -> DatabaseResultCode:
        try:
            self.cursor.execute(f"SELECT uid FROM discord_users WHERE uid = '{discord_user.id}'")

            if self.cursor.fetchone() is not None:
                debug_print(f"Discord user already registered. {discord_user.name}", LogType.WARNING)
                return DatabaseResultCode(DatabaseResultCode.ALREADY_EXISTS)

            blob = self.cursor.execute(f"SELECT pid FROM wot_players WHERE wot_name = '{wot_name}'").fetchone()
            if blob is None:
                debug_print(f"Player not found in database. {wot_name}", LogType.WARNING)
                return DatabaseResultCode(DatabaseResultCode.NOT_FOUND)

            self.cursor.execute(
                f"Insert INTO discord_users (uid, discord_name, pid) VALUES ('{discord_user.id}' ,'{discord_user.name}','{blob[0]}')")
            self.connection.commit()

        except sqlite3.Error as e:
            debug_print(f"Could not add discord user reference. {e}", LogType.ERROR)
            return DatabaseResultCode(DatabaseResultCode.INTERNAL_ERROR)
        return DatabaseResultCode(DatabaseResultCode.OK)

    async def register_discord_user_to_adv(self, discord_user: Member) -> DatabaseResultCode:
        try:
            blob = self.cursor.execute(
                "SELECT id, wot_advances.date FROM wot_advances ORDER BY id DESC LIMIT 1").fetchone()

            newestAdvId = blob[0]
            newestAdvDate = blob[1]

            advMaxAge = 60 * 15  # 15 minutes

            if (int(datetime.now().timestamp()) -
                    int(time.mktime(
                        datetime.strptime(newestAdvDate, '%Y-%m-%d %H:%M:%S')
                                .timetuple())) > advMaxAge):
                debug_print(f"Newest advance is older than {advMaxAge / 60} minutes.", LogType.WARNING)
                return DatabaseResultCode(DatabaseResultCode.FORBIDDEN)

            blob = \
                self.cursor.execute(
                    f"SELECT pid FROM discord_users WHERE uid = '{discord_user.id}'").fetchone()

            if blob is None:
                debug_print(f"{discord_user.display_name} is not linked to any player.", LogType.WARNING)
                return DatabaseResultCode(DatabaseResultCode.NOT_FOUND)
            player_id = blob[0]
            blob = self.cursor.execute(
                f"SELECT id FROM wot_advances_players WHERE advance_id = '{newestAdvId}' AND pid = '{player_id}'").fetchone()
            if blob is not None:
                debug_print(f"Player already registered to newest advance. `{discord_user.display_name}`",
                            LogType.WARNING)
                return DatabaseResultCode(DatabaseResultCode.ALREADY_EXISTS)

            self.cursor.execute(
                f"INSERT INTO wot_advances_players (advance_id, pid) VALUES ('{newestAdvId}','{player_id}')")
            self.connection.commit()

        except sqlite3.Error as e:
            debug_print(f"Could not add user to newest advance. {e}", LogType.ERROR)
            return DatabaseResultCode(DatabaseResultCode.INTERNAL_ERROR)
        return DatabaseResultCode(DatabaseResultCode.OK)

    async def get_wot_nick_from_discord_id(self, discord_id: str) -> str | None:
        try:
            self.cursor.execute(
                f"SELECT wot_name FROM wot_players INNER JOIN discord_users ON wot_players.pid = discord_users.pid WHERE uid = {discord_id}")
            blob = self.cursor.fetchone()
            if blob is None:
                return None
            return blob[0]
        except sqlite3.Error as e:
            debug_print(f"Could not get player by discord id. {e}", LogType.ERROR)
            return None

    def is_player_in_db(self, wot_nick: str) -> bool:
        self.cursor.execute(f"SELECT * FROM wot_players WHERE wot_name = '{wot_nick}'")
        return self.cursor.fetchone() is not None

    def get_player_as_object(self, wot_name: str) -> ClanPlayerData | None:
        self.cursor.execute(f"SELECT pid, wot_name, role FROM wot_players WHERE wot_name = '{wot_name}'")
        blob = self.cursor.fetchone()
        if blob is None:
            return None
        return ClanPlayerData(blob[0], blob[1], blob[2])

    def uid_to_pid(self, uid: str) -> str | None:
        self.cursor.execute(f"SELECT pid FROM wot_pid_to_discord_uid WHERE uid = '{uid}'")
        blob = self.cursor.fetchone()
        if blob is None:
            return None
        return blob[0]

    def pid_to_uid(self, pid: str) -> str | None:
        self.cursor.execute(f"SELECT uid FROM wot_pid_to_discord_uid WHERE pid = '{pid}'")
        blob = self.cursor.fetchone()
        if blob is None:
            return None
        return blob[0]

    def get_role_from_pid(self, pid: str) -> str | None:
        self.cursor.execute(f"SELECT role FROM wot_players WHERE pid = '{pid}'")
        blob = self.cursor.fetchone()
        if blob is None:
            return None
        return blob[0]

    async def add_pid_to_redundancy(self, pid: str) -> None:
        self.cursor.execute(f"INSERT INTO current_wot_players_pids (pid) VALUES ('{pid}')")
        self.connection.commit()

    async def clear_redundancy(self) -> None:
        self.cursor.execute(f"DELETE FROM current_wot_players_pids")
        self.connection.commit()

    async def delete_non_redundant_players(self) -> int:
        players_to_delete = self.cursor.execute(
            f"SELECT COUNT(pid) FROM wot_players WHERE pid NOT IN (SELECT pid FROM current_wot_players_pids);").fetchone()[
            0]
        self.cursor.execute("DELETE FROM wot_players WHERE pid NOT IN (SELECT pid FROM current_wot_players_pids)")
        self.connection.commit()
        return players_to_delete

    async def get_discord_users_ids_to_delete(self) -> list[str]:
        self.cursor.execute(f"SELECT uid FROM discord_users WHERE pid NOT IN (SELECT pid FROM wot_players)")
        blob = self.cursor.fetchall()
        if blob is None:
            return []
        return [str(x[0]) for x in blob]

    async def delete_discord_users_not_in_clan(self) -> None:
        self.cursor.execute(f"DELETE FROM discord_users WHERE pid NOT IN (SELECT pid FROM current_wot_players_pids)")
        self.connection.commit()

    async def get_advance_from_discord_id(self, discord_id: str) -> Any | None:
        try:
            blob = self.cursor.execute(
                f"SELECT pid FROM discord_users WHERE uid = '{discord_id}'").fetchone()
            if blob is None:
                debug_print(f"Player not found in database. {discord_id}", LogType.WARNING)
                return None
            player_id = blob[0]
            self.cursor.execute(
                f"SELECT advances_count FROM wot_advances_count_by_players_last_week WHERE pid = '{player_id}'")
            blob = self.cursor.fetchone()
            if blob is None:
                return None
            return blob[0]
        except sqlite3.Error as e:
            debug_print(f"Could not get advance by discord id. {e}", LogType.ERROR)
            return None

    async def get_absent_players(self) -> list[str]:
        self.cursor.execute(f"SELECT wot_name FROM wot_advances_absent_players_last_week")
        blob = self.cursor.fetchall()
        if blob is None:
            return []
        return [row[0] for row in blob]
