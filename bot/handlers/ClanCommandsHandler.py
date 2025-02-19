import datetime
from os import getenv

import discord
from discord.ext.commands import Context
from singleton_decorator import singleton

from api_fetcher.WotClanDataFetcher import WotClanDataFetcher
from database.DatabaseConnector import DatabaseConnector, DatabaseResultCode


@singleton
class ClanCommandsHandler:
    def __init__(self):
        self.wot_clan_data_fetcher = WotClanDataFetcher(getenv("WG_API_KEY"), getenv("CLAN_ID"))
        self.databaseConnector = DatabaseConnector()

    async def show_members(self, context: Context):
        playersData = self.wot_clan_data_fetcher.players
        mess = "# MEMBERS IN CLAN\n"
        for player in playersData:
            messBuff = f"### player `{player.account_name}` with `{player.role}`\n"
            if len(mess) + len(messBuff) > 2000:
                await context.send(mess)
                mess = ""
            mess += messBuff

    async def rank_check(self, context: Context, wot_nick: str):
        for player in self.wot_clan_data_fetcher.players:
            wot_nick = wot_nick.strip("`")
            if player.account_name == wot_nick:
                await context.send(f"Player `{player.account_name}` was found in the clan with rank `{player.role}`")
                return
        await context.send(
            f"Player was not found in the clan.\n(if you are sure that `{wot_nick}` is in clan try running !clanRefresh command)")

    async def clan_refresh(self, context: Context):
        players = await self.wot_clan_data_fetcher.fetch_clan_members()

        if len(players) == 0 or players is None:
            await context.send("I got no results!\nSomething may gone wrong! Check my logs.")
            return

        skipped_players = 0
        updated_players = 0
        added_players = 0
        for player in players:
            if self.databaseConnector.is_player_in_db(player.account_name):
                dbError = await self.databaseConnector.update_rank(player)
                if dbError == DatabaseResultCode.OK:
                    updated_players += 1
            else:
                dbError = await self.databaseConnector.add_clan_member(player)
                added_players += 1
            if dbError != DatabaseResultCode.OK:
                skipped_players += 1

        await context.send(
            f"## Ok!\n" +
            f"Got {len(players)} players.\n" +
            f"Updated {updated_players} players.\n" +
            f"Added {added_players} players.\n" +
            f"Skipped {skipped_players} players.")

    async def register(self, context: Context, wot_nick: str, discord_user: discord.User):
        wot_nick = wot_nick.strip("`")
        player = self.wot_clan_data_fetcher.find_player_data(wot_nick)
        if player is None:
            await context.send(f"Player `{wot_nick}` not found in clan.")
            return

        dbError = await self.databaseConnector.add_discord_user_ref(wot_nick, discord_user)
        if dbError != DatabaseResultCode.OK:
            if dbError == DatabaseResultCode.ALREADY_EXISTS:
                await context.send(f"User `{discord_user.name}` was already registered!")
            if dbError == DatabaseResultCode.NOT_FOUND:
                await context.send(f"Player `{wot_nick}` not found in database.\n Run !clanRefresh command manually.")
            return

        await context.send(f"Player `{wot_nick}` registered!")

    async def add_advance(self, context: Context, invoker_discord_id: discord.User):
        dbError = await self.databaseConnector.add_advance(str(invoker_discord_id.id))
        if dbError != DatabaseResultCode.OK:
            if dbError == DatabaseResultCode.FORBIDDEN:
                await context.send("You are not allowed to add advance!")
            return
        await context.send(f"Advance registered at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}!")

    async def register_user_for_adv(self, context: Context, discord_user: discord.User):
        dbError = await self.databaseConnector.register_discord_user_to_adv(discord_user)
        if dbError != DatabaseResultCode.OK:
            if dbError == DatabaseResultCode.ALREADY_EXISTS:
                await context.send("You are already registered to the newest advance.")
            if dbError == DatabaseResultCode.NOT_FOUND:
                await context.send("You are not linked to any player.")
            return
        await context.send("Registered to the newest advance!")

    async def whoami(self, context: Context, discord_user: discord.User):
        nick = await self.databaseConnector.get_wot_nick_from_discord_id(str(discord_user.id))
        if nick is None:
            await context.send("You are not linked to any player.")
            return
        await context.send(f"You are linked to player `{nick}`.")
