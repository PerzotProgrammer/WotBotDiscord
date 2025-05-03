from os import getenv

import discord
from discord import Member
from discord.ext.commands import Context, Cog, command
from singleton_decorator import singleton

from api_fetcher.WotClanDataFetcher import WotClanDataFetcher
from database.DatabaseConnector import DatabaseConnector, DatabaseResultCode
from globals import clan_roles_to_discord_roles, clan_roles_localized, base_clan_rank
from utils import debug_print, LogType


@singleton
class ClanCommandsCog(Cog, name="Clan Commands"):
    def __init__(self, bot):
        self.bot = bot
        self.clan_tag = getenv("CLAN_TAG")
        debug_print("ClanCommandsCog initialized.", LogType.INFO)

    @command(name="showAllMembers")
    async def show_members(self, context: Context):
        """
        Shows all members in clan.
        The data is fetched from the Wargaming API.
        """
        playersData = WotClanDataFetcher().players
        mess = "# MEMBERS IN CLAN\n"
        for player in playersData:
            messBuff = f"- player `{player.wot_name}` with `{clan_roles_localized[player.role]}`\n"
            if len(mess) + len(messBuff) > 2000:
                await context.send(mess)
                mess = ""
            mess += messBuff

    @command(name="optForAdv")
    async def register_user_for_adv(self, context: Context):
        """
        Registers user to the advance.
        User must be linked to the player in the database.
        Advance must be younger than 15 minutes, else it won't register your attendance.
        """
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
    async def whoami(self, context: Context, discord_user: Member):
        """
        Shows the player linked to the discord user.
        :param discord_user: Discord user to check the player (use @mention). If not provided, it will check the invoker.
        """
        nick = await DatabaseConnector().get_wot_nick_from_discord_id(str(discord_user.id))
        if nick is None:
            await context.send("You are not linked to any player.")
            return
        await context.send(f"You are linked to player `{nick}`.")

    @command(name="giveMeRole")
    async def give_me_role(self, context: Context):
        """
        Gives the clan role to the invoker.
        The invoker must be linked to the player in the database.
        In the future it will be merged with !register command.
        There is administrative version of this command called !giveHimRole. It can be used only by staff members.
        """
        await self.role_give(context, context.author)

    @staticmethod
    async def role_give(context: Context, discord_user: Member, silent=False, delete_mode=False) -> bool:
        pid = DatabaseConnector().uid_to_pid(str(discord_user.id))
        if pid is None and not delete_mode:
            if not silent:
                await context.send(f"Player linked to `{discord_user.name}` not found in database.")
            return False
        if delete_mode:
            for role in discord_user.roles:
                if role.is_assignable():
                    await discord_user.remove_roles(role)
            if not silent:
                debug_print(f"Removed ranks of `{discord_user.name}`.", LogType.INFO)
            return True

        player = WotClanDataFetcher().find_player_data_by_pid(pid)

        if player.role is None:
            if not silent:
                await context.send(
                    f"Player linked to `{player.wot_name}` not in the clan (or database is not refreshed).")
            return False
        try:
            for user_roles in context.guild.get_member(discord_user.id).roles:
                if user_roles.name in clan_roles_to_discord_roles.values():
                    await discord_user.remove_roles(user_roles)
            role_discord_id = discord.utils.get(context.guild.roles, name=clan_roles_to_discord_roles[player.role])
            base_clan_rank_id = discord.utils.get(context.guild.roles, name=base_clan_rank)
            await discord_user.add_roles(role_discord_id, base_clan_rank_id)

        except discord.errors.Forbidden:
            await context.send(f"I don't have permissions to give role to user {discord_user}")
            debug_print(f"Bot does not have permissions to give role to user: {player.wot_name}", LogType.ERROR)

        except Exception as e:
            await context.send(f"Woah! Something went wrong! Check my logs!")
            debug_print(f"Error while giving role to user: {e}", LogType.ERROR)
            return False
        if not silent:
            await context.send(
                f"Role `{clan_roles_to_discord_roles[player.role]}` given to `{discord_user.name} ({player.wot_name})`!")
        return True
