import discord
from discord import User
from discord.ext import commands
from discord.ext.commands import Context, Cog, command
from singleton_decorator import singleton

from api_fetcher.WotClanDataFetcher import WotClanDataFetcher
from database.DatabaseConnector import DatabaseConnector, DatabaseResultCode
from globals import clan_roles_to_discord_roles, clan_roles_localized
from utils import debug_print, LogType


@singleton
class ClanCommandsCog(Cog, name="Clan Commands"):
    def __init__(self, bot):
        self.bot = bot
        debug_print("ClanCommandsCog initialized.", LogType.INFO)

    @command(name="showAllMembers")
    async def show_members(self, context: Context):
        playersData = WotClanDataFetcher().players
        mess = "# MEMBERS IN CLAN\n"
        for player in playersData:
            messBuff = f"- player `{player.wot_name}` with `{clan_roles_localized[player.role]}`\n"
            if len(mess) + len(messBuff) > 2000:
                await context.send(mess)
                mess = ""
            mess += messBuff

    @command(name="register")
    async def register(self, context: Context, wot_nick: str, discord_user: User):
        wot_nick = wot_nick.strip("`")

        player = WotClanDataFetcher().find_player_data_by_name(wot_nick)
        if player is None:
            await context.send(f"Player `{wot_nick}` not found in clan.")
            return

        dbError = await DatabaseConnector().add_discord_user_ref(wot_nick, discord_user)
        if dbError != DatabaseResultCode.OK:
            if dbError == DatabaseResultCode.ALREADY_EXISTS:
                await context.send(f"User `{discord_user.name}` was already registered!")
            if dbError == DatabaseResultCode.NOT_FOUND:
                await context.send(f"Player `{wot_nick}` not found in database.\n Run !clanRefresh command manually.")
            return

        await context.send(f"Player `{wot_nick}` registered!")

    @command(name="optForAdv")
    async def register_user_for_adv(self, context: Context):
        discord_user = context.author
        dbError = await DatabaseConnector().register_discord_user_to_adv(discord_user)
        if dbError != DatabaseResultCode.OK:
            if dbError == DatabaseResultCode.ALREADY_EXISTS:
                await context.send("You are already registered to the newest advance.")
            if dbError == DatabaseResultCode.NOT_FOUND:
                await context.send("You are not linked to any player.")
            if dbError == DatabaseResultCode.FORBIDDEN:
                await context.send("You can't register to advance. Newest advance is older than 15 minutes.")
            return
        await context.send("Registered to the newest advance!")

    @command(name="whoami")
    async def whoami(self, context: Context, discord_user: User):
        nick = await DatabaseConnector().get_wot_nick_from_discord_id(str(discord_user.id))
        if nick is None:
            await context.send("You are not linked to any player.")
            return
        await context.send(f"You are linked to player `{nick}`.")

    @command(name="giveMeRole")
    async def give_me_role(self, context: Context):
        await self.role_give(context, context.author)

    @staticmethod
    async def role_give(context: Context, discord_user: User, silent=False) -> bool:
        pid = DatabaseConnector().uid_to_pid(str(discord_user.id))
        if pid is None:
            if not silent:
                await context.send(f"Player linked to `{discord_user.name}` not found in database.")
            return False
        player = WotClanDataFetcher().find_player_data_by_pid(pid)

        if player.role is None:
            if not silent:
                await context.send(
                    f"Player linked to `{player.wot_name}` not in the clan (or database is not refreshed).")
            return False
        try:
            member = await commands.MemberConverter().convert(context, str(discord_user.id))
            for user_roles in context.guild.get_member(discord_user.id).roles:
                if user_roles.name in clan_roles_to_discord_roles.values():
                    await member.remove_roles(user_roles)
            role_discord_id = discord.utils.get(context.guild.roles, name=clan_roles_to_discord_roles[player.role])
            await member.add_roles(role_discord_id)
        except Exception as e:
            debug_print(f"Error while giving role to user: {e}", LogType.ERROR)
            await context.send(f"Woah! Something went wrong! Check my logs!")
            return False
        if not silent:
            await context.send(
                f"Role `{clan_roles_to_discord_roles[player.role]}` given to `{discord_user.name} ({player.wot_name})`!")
        return True