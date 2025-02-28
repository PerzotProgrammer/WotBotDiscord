from datetime import datetime

from discord import Member
from discord.ext import commands
from discord.ext.commands import Cog, command, Context
from singleton_decorator import singleton

from api_fetcher.WotClanDataFetcher import WotClanDataFetcher
from bot.cogs.ClanCommandsCog import ClanCommandsCog
from database.DatabaseConnector import DatabaseConnector, DatabaseResultCode
from globals import clan_staff_ranks
from utils import LogType, debug_print


@singleton
class StaffOnlyCommandsCog(Cog, name="Staff only commands"):
    def __init__(self, bot):
        self.bot = bot
        debug_print("ChatInteractionsCog initialized.", LogType.INFO)

    @staticmethod
    async def can_call_command(context: Context) -> bool:
        pid = DatabaseConnector().uid_to_pid(str(context.author.id))
        if DatabaseConnector().get_role_from_pid(pid) not in clan_staff_ranks:
            return False
        return True

    @command(name="clanRefresh")
    async def clan_refresh(self, context: Context):
        """
        Refreshes the clan members in the database.
        The data is fetched from the Wargaming API and copied to database.
        The invoker must be a staff member (recruitment officer or higher).
        After running this command, the bot will have the most recent data about the clan members.
        You will be able to register new users and auto-give them roles.
        """

        if not await self.can_call_command(context):
            await context.send("You are not allowed to use this command!")
            return

        players = await WotClanDataFetcher().fetch_clan_members()

        if len(players) == 0 or players is None:
            await context.send("I got no results!\nSomething may gone wrong! Check my logs.")
            return

        skipped_players = 0
        updated_players = 0
        added_players = 0
        for player in players:
            if DatabaseConnector().is_player_in_db(player.wot_name):
                dbError = await DatabaseConnector().update_rank(player)
                if dbError == DatabaseResultCode.OK:
                    updated_players += 1
            else:
                dbError = await DatabaseConnector().add_clan_member(player)
                added_players += 1
            if dbError != DatabaseResultCode.OK:
                skipped_players += 1

        await context.send(
            f"## Ok!\n" +
            f"Got {len(players)} players.\n" +
            f"Updated {updated_players} players.\n" +
            f"Added {added_players} players.\n" +
            f"Skipped {skipped_players} players.")

    @command(name="addAdvance")
    async def add_advance(self, context: Context):
        """
        Adds advance to the database.
        The data is used to track attendance.
        The invoker must be a staff member (recruitment officer or higher).
        Use !optForAdv to register to the advance.
        """
        if not await self.can_call_command(context):
            await context.send("You are not allowed to add advance!")
            return
        invoker_discord_id = context.author.id
        dbError = await DatabaseConnector().add_advance(str(invoker_discord_id))
        if dbError != DatabaseResultCode.OK:
            await context.send("Could not add advance!")
            return

        await context.send(f"Advance registered at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}!")

        if context.author.voice is None:
            await context.send(
                "You are not connected to a voice channel. Users must be added manually with !optForAdv command.")
            return
        membersInVoiceChannel = context.author.voice.channel.members
        addedMembers = 0
        for member in membersInVoiceChannel:
            dbError = await DatabaseConnector().register_discord_user_to_adv(member)
            if dbError != DatabaseResultCode.OK:
                if dbError == DatabaseResultCode.NOT_FOUND:
                    await context.send(
                        f"User {member.name} is not linked to any player (run !register command on him).")
                else:
                    await context.send(f"Could not register {member.name} to the newest advance.")
                continue
            addedMembers += 1
        await context.send(f"Registered {addedMembers} players to advance.")

    @command(name="giveHimRole")
    async def give_him_role(self, context: Context, discord_user: Member):
        """
        Administrative version of !giveMeRole.
        Gives the clan role to the mentioned user.
        The invoker must be a staff member (recruitment officer or higher).
        :param discord_user: @mention of the user to give the role.
        """
        if not await self.can_call_command(context):
            await context.send("You are not allowed to use this command!")
            return
        await ClanCommandsCog().role_give(context, discord_user)

    @command(name="refreshAllRanks")
    async def refresh_all_roles_on_server(self, context: Context):
        """
        Refreshes all roles on the server.
        The invoker must be a staff member (recruitment officer or higher).
        It will automatically fetch data from the Wargaming API, update database and update roles on discord (!clanRefresh and !giveHimRole for @everyone).
        """
        if not await self.can_call_command(context):
            await context.send("You are not allowed to use this command!")
            return

        await context.send("This may take a while. Please wait.")
        allClanMembers = await WotClanDataFetcher().fetch_clan_members()
        success_count = 0
        skip_count = 0
        for player in allClanMembers:
            await DatabaseConnector().update_rank(player)
            uid = DatabaseConnector().pid_to_uid(player.pid)
            if uid is None:
                skip_count += 1
                continue
            user = await commands.MemberConverter().convert(context, str(uid))
            if await ClanCommandsCog().role_give(context, user, True):
                success_count += 1
            else:
                skip_count += 1
        await context.send(f"All roles refreshed (with {success_count} successfully and {skip_count} skipped).")
