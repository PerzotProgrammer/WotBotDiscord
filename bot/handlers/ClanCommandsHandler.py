import datetime
from os import getenv

import discord
from discord.ext import commands
from discord.ext.commands import Context
from singleton_decorator import singleton

from api_fetcher.WotClanDataFetcher import WotClanDataFetcher
from database.DatabaseConnector import DatabaseConnector, DatabaseResultCode
from globals import clan_roles_to_discord_roles, clan_staff_ranks
from utils import debug_print, LogType


@singleton
class ClanCommandsHandler(commands.Cog, name="Clan Commands"):
    def __init__(self, bot):
        self.wot_clan_data_fetcher = WotClanDataFetcher(getenv("WG_API_KEY"), getenv("CLAN_ID"))
        self.databaseConnector = DatabaseConnector()
        self.bot = bot

    @commands.command(name="showMembers")
    async def show_members(self, context: Context):
        playersData = self.wot_clan_data_fetcher.players
        mess = "# MEMBERS IN CLAN\n"
        for player in playersData:
            messBuff = f"### player `{player.wot_name}` with `{player.role}`\n"
            if len(mess) + len(messBuff) > 2000:
                await context.send(mess)
                mess = ""
            mess += messBuff

    @commands.command(name="rankCheck")
    async def rank_check(self, context: Context, wot_nick: str):
        for player in self.wot_clan_data_fetcher.players:
            wot_nick = wot_nick.strip("`")
            if player.wot_name == wot_nick:
                await context.send(f"Player `{player.wot_name}` was found in the clan with rank `{player.role}`")
                return
        await context.send(
            f"Player was not found in the clan.\n(if you are sure that `{wot_nick}` is in clan try running !clanRefresh command)")

    @commands.command(name="clanRefresh")
    async def clan_refresh(self, context: Context):
        players = await self.wot_clan_data_fetcher.fetch_clan_members()

        if len(players) == 0 or players is None:
            await context.send("I got no results!\nSomething may gone wrong! Check my logs.")
            return

        skipped_players = 0
        updated_players = 0
        added_players = 0
        for player in players:
            if self.databaseConnector.is_player_in_db(player.wot_name):
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

    @commands.command(name="register")
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

    @commands.command(name="addAdvance")
    async def add_advance(self, context: Context, invoker_discord_id: discord.User):
        dbError = await self.databaseConnector.add_advance(str(invoker_discord_id.id))
        if dbError != DatabaseResultCode.OK:
            if dbError == DatabaseResultCode.FORBIDDEN:
                await context.send("You are not allowed to add advance!")
            return
        await context.send(f"Advance registered at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}!")

    @commands.command(name="optForAdv")
    async def register_user_for_adv(self, context: Context, discord_user: discord.User):
        dbError = await self.databaseConnector.register_discord_user_to_adv(discord_user)
        if dbError != DatabaseResultCode.OK:
            if dbError == DatabaseResultCode.ALREADY_EXISTS:
                await context.send("You are already registered to the newest advance.")
            if dbError == DatabaseResultCode.NOT_FOUND:
                await context.send("You are not linked to any player.")
            if dbError == DatabaseResultCode.FORBIDDEN:
                await context.send("You can't register to advance. Newest advance is older than 15 minutes.")
            return
        await context.send("Registered to the newest advance!")

    @commands.command(name="whoami")
    async def whoami(self, context: Context, discord_user: discord.User):
        nick = await self.databaseConnector.get_wot_nick_from_discord_id(str(discord_user.id))
        if nick is None:
            await context.send("You are not linked to any player.")
            return
        await context.send(f"You are linked to player `{nick}`.")

    @commands.command(name="giveMeRole")
    async def give_me_role(self, context: Context):
        uid = context.author.id
        pid = self.databaseConnector.uid_to_pid(str(uid))
        if pid is None:
            await context.send("You are not linked to any player.")
            return
        role = self.databaseConnector.get_role_from_pid(pid)
        if role is None:
            await context.send("You are not in the clan (or database is not refreshed).")
            return
        try:
            for user_roles in context.author.roles:
                if user_roles.name in clan_roles_to_discord_roles.values():
                    await context.author.remove_roles(user_roles)
            role_discord_id = discord.utils.get(context.guild.roles, name=clan_roles_to_discord_roles[role])
            await context.author.add_roles(role_discord_id)
        except Exception as e:
            debug_print(f"Error while giving role to user: {e}", LogType.ERROR)
            await context.send(f"Woah! Something went wrong! Check my logs!")
            return
        await context.send(f"Role `{clan_roles_to_discord_roles[role]}` given!")

    @commands.command(name="giveHimRole")
    async def give_him_role(self, context: Context, discord_user: discord.User):
        if self.databaseConnector.get_role_from_pid(
                self.databaseConnector.uid_to_pid(str(context.author.id))) not in clan_staff_ranks:
            await context.send("You are not allowed to use this command!")
            return

        pid = self.databaseConnector.uid_to_pid(str(discord_user.id))
        if pid is None:
            await context.send(f"Player linked to `{discord_user}` not found in database.")
            return
        player = self.wot_clan_data_fetcher.find_player_data(pid)

        if player.role is None:
            await context.send(f"Player linked to `{player.wot_name}` not in the clan (or database is not refreshed).")
            return
        try:
            for user_roles in context.guild.get_member(discord_user.id).roles:
                if user_roles.name in clan_roles_to_discord_roles.values():
                    await context.author.remove_roles(user_roles)
            role_discord_id = discord.utils.get(context.guild.roles, name=clan_roles_to_discord_roles[player.role])
            await context.author.add_roles(role_discord_id)
        except Exception as e:
            debug_print(f"Error while giving role to user: {e}", LogType.ERROR)
            await context.send(f"Woah! Something went wrong! Check my logs!")
            return
        await context.send(f"Role `{clan_roles_to_discord_roles[player.role]}` given to `{player.wot_name}`!")
