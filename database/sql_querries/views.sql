create view if not exists discord_users_to_wot_players as
select discord_users.discord_name, wot_players.wot_name, wot_players.role
from wot_players
         left join discord_users on discord_users.pid = wot_players.pid;


create view if not exists wot_advances_count_by_players_in_date as
select wot_name, count(wot_advances_players.id) as advances_count, wot_advances.date
from wot_players
         inner join wot_advances_players on wot_players.pid = wot_advances_players.pid
         inner join wot_advances on wot_advances.id = wot_advances_players.advance_id
group by wot_name, date(wot_advances.date);


create view if not exists wot_advances_count_by_players_last_week as
select wot_name, wot_players.pid, count(wot_advances_players.id) as advances_count
from wot_players
         inner join wot_advances_players on wot_players.pid = wot_advances_players.pid
         inner join wot_advances on wot_advances.id = wot_advances_players.advance_id
where julianday('now') - unixepoch(wot_advances.date) <= 7
group by wot_name;


create view if not exists advances_creators as
select wot_advances.id      as advance_id,
       wot_players.wot_name as added_by,
       wot_advances.date    as added_at
from wot_advances
         inner join discord_users
                    on wot_advances.invoker_uid = discord_users.uid
         inner join wot_players on wot_players.pid = discord_users.pid;

create view if not exists wot_players_count_by_role as
select role, count(pid) as players_count
from wot_players
group by role;


create view if not exists wot_pid_to_discord_uid as
select discord_users.uid, wot_players.pid
from discord_users
         inner join wot_players on discord_users.pid = wot_players.pid;