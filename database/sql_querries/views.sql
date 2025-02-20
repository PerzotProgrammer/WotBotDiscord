create view if not exists discord_users_to_wot_players as
select discord_users_ids.discord_name, wot_players.wot_name, wot_players.role
from wot_players
         left join discord_users_ids on discord_users_ids.player_id = wot_players.id;


create view if not exists wot_advances_count_by_players_in_date as
select wot_name, count(wot_advances_players.id) as advances_count, date(wot_advances.date, 'unixepoch') as date
from wot_players
         inner join wot_advances_players on wot_players.id = wot_advances_players.player_id
         inner join wot_advances on wot_advances.id = wot_advances_players.advance_id
group by wot_name, date(wot_advances.date, 'unixepoch');


create view if not exists wot_advances_count_by_players_last_week as
select wot_name, count(wot_advances_players.id) as advances_count
from wot_players
         inner join wot_advances_players on wot_players.id = wot_advances_players.player_id
         inner join wot_advances on wot_advances.id = wot_advances_players.advance_id
where julianday('now') - julianday(wot_advances.date, 'unixepoch') <= 7
group by wot_name;


create view if not exists advances_creators as
select wot_advances.id                          as advance_id,
       wot_players.wot_name                     as added_by,
       datetime(wot_advances.date, 'unixepoch') as added_at
from wot_advances
         inner join discord_users_ids
                    on wot_advances.invoked_by = discord_users_ids.discord_id
         inner join wot_players on wot_players.id = discord_users_ids.player_id;

create view if not exists wot_players_count_by_role as
select role, count(id) as players_count
from wot_players
group by role;