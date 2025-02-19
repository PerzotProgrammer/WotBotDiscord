import sqlite3
from datetime import datetime
from enum import Enum

import discord
from singleton_decorator import singleton

from data_models.ClanPlayerData import ClanPlayerData
from globals import clan_staff_ranks
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
            self.cursor.execute(
                f"SELECT role FROM wot_players INNER JOIN discord_users_ids ON wot_players.id = discord_users_ids.player_id WHERE discord_id = {invoker_discord_id}", )
            blob = self.cursor.fetchone()
            if blob is None or blob[0] not in clan_staff_ranks:
                return DatabaseResultCode(DatabaseResultCode.FORBIDDEN)

            self.cursor.execute(
                f"INSERT INTO wot_advances (date, invoked_by) VALUES ('{datetime.now().timestamp()}','{invoker_discord_id}')")
            self.connection.commit()
        except sqlite3.Error as e:
            debug_print(f"Could not add advance. {e}", LogType.ERROR)
            return DatabaseResultCode(DatabaseResultCode.INTERNAL_ERROR)
        return DatabaseResultCode(DatabaseResultCode.OK)

    async def add_clan_member(self, playerData: ClanPlayerData) -> DatabaseResultCode:
        try:
            self.cursor.execute(f"SELECT wot_id FROM wot_players WHERE wot_id = '{playerData.account_id}'")

            if self.cursor.fetchone() is not None:
                return DatabaseResultCode(DatabaseResultCode.ALREADY_EXISTS)

            self.cursor.execute(
                f"INSERT INTO wot_players (wot_id, wot_name, role) "
                f"VALUES ('{playerData.account_id}', '{playerData.account_name}', '{playerData.role}')")
            self.connection.commit()

        except sqlite3.Error as e:
            debug_print(f"Could not add clan member {playerData.account_name}. {e}", LogType.ERROR)
            return DatabaseResultCode(DatabaseResultCode.INTERNAL_ERROR)
        return DatabaseResultCode(DatabaseResultCode.OK)

    async def update_rank(self, playerData: ClanPlayerData) -> DatabaseResultCode:
        try:
            self.cursor.execute(f"SELECT role FROM wot_players WHERE wot_id = '{playerData.account_id}'")
            blob = self.cursor.fetchone()
            if blob is None:
                debug_print(f"Player not found in database. {playerData.account_name}", LogType.WARNING)
                return DatabaseResultCode(DatabaseResultCode.NOT_FOUND)

            if blob[0] == playerData.role:
                debug_print(f"Player {playerData.account_name} already has the same role.", LogType.INFO)
                return DatabaseResultCode(DatabaseResultCode.SKIPPED)

            self.cursor.execute(
                f"UPDATE wot_players SET role = '{playerData.role}' WHERE wot_id = '{playerData.account_id}'")
            self.connection.commit()

        except sqlite3.Error as e:
            debug_print(f"Could not update rank for {playerData.account_name}. {e}", LogType.ERROR)
            return DatabaseResultCode(DatabaseResultCode.INTERNAL_ERROR)

        return DatabaseResultCode(DatabaseResultCode.OK)

    async def add_discord_user_ref(self, wot_name: str, discord_user: discord.User) -> DatabaseResultCode:
        try:
            self.cursor.execute(f"SELECT discord_id FROM discord_users_ids WHERE discord_id = '{discord_user.id}'")

            if self.cursor.fetchone() is not None:
                debug_print(f"Discord user already registered. {discord_user.name}", LogType.WARNING)
                return DatabaseResultCode(DatabaseResultCode.ALREADY_EXISTS)

            blob = self.cursor.execute(f"SELECT player_id FROM wot_players WHERE wot_name = '{wot_name}'").fetchone()
            if blob is None:
                debug_print(f"Player not found in database. {wot_name}", LogType.WARNING)
                return DatabaseResultCode(DatabaseResultCode.NOT_FOUND)

            self.cursor.execute(
                f"Insert INTO discord_users_ids (discord_id, discord_name, player_id) VALUES ('{discord_user.id}' ,'{discord_user.name}','{blob[0]}')")
            self.connection.commit()

        except sqlite3.Error as e:
            debug_print(f"Could not add discord user reference. {e}", LogType.ERROR)
            return DatabaseResultCode(DatabaseResultCode.INTERNAL_ERROR)
        return DatabaseResultCode(DatabaseResultCode.OK)

    async def register_discord_user_to_adv(self, discord_user: discord.User) -> DatabaseResultCode:
        try:
            newestAdvId = self.cursor.execute("SELECT id FROM wot_advances ORDER BY date DESC LIMIT 1").fetchone()[0]

            player_id = \
                self.cursor.execute(
                    f"SELECT player_id FROM discord_users_ids WHERE discord_id = '{discord_user.id}'").fetchone()[0]

            if player_id is None:
                debug_print(f"{discord_user.name} is not linked to any player.", LogType.WARNING)
                return DatabaseResultCode(DatabaseResultCode.NOT_FOUND)

            blob = self.cursor.execute(
                f"SELECT id FROM wot_advances_players WHERE advance_id = '{newestAdvId}' AND player_id = '{player_id}'").fetchone()
            if blob is not None:
                debug_print(f"Player already registered to newest advance. {discord_user.name}", LogType.WARNING)
                return DatabaseResultCode(DatabaseResultCode.ALREADY_EXISTS)

            self.cursor.execute(
                f"INSERT INTO wot_advances_players (advance_id, player_id) VALUES ('{newestAdvId}','{player_id}')")
            self.connection.commit()

        except sqlite3.Error as e:
            debug_print(f"Could not add user to newest advance. {e}", LogType.ERROR)
            return DatabaseResultCode(DatabaseResultCode.INTERNAL_ERROR)
        return DatabaseResultCode(DatabaseResultCode.OK)

    async def get_wot_nick_from_discord_id(self, discord_id: str) -> str | None:
        try:
            self.cursor.execute(
                f"SELECT wot_name FROM wot_players INNER JOIN discord_users_ids ON wot_players.id = discord_users_ids.player_id WHERE discord_id = {discord_id}")
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
        self.cursor.execute(f"SELECT * FROM wot_players WHERE wot_name = '{wot_name}'")
        blob = self.cursor.fetchone()
        if blob is None:
            return None
        return ClanPlayerData(blob[1], blob[2], blob[3])
