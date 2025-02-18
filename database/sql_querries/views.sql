create view if not exists discord_users_to_wot_players as
select discord_users_ids.discord_name, wot_players.wot_name, wot_players.role
from wot_players
         left join discord_users_ids on discord_users_ids.player_id = wot_players.id;