create table if not exists discord_users_ids
(
    id           integer primary key autoincrement not null,
    discord_id   integer                           not null,
    discord_name text                              not null,
    player_id    integer                           not null
);

create table if not exists wot_players
(
    id       integer primary key autoincrement not null,
    wot_id   integer                           not null,
    wot_name text                              not null,
    role     text                              not null
);

create table if not exists wot_advances
(
    id         integer primary key autoincrement not null,
    date       text                              not null,
    invoked_by integer                           not null
);

create table if not exists wot_advances_players
(
    id         integer primary key autoincrement not null,
    advance_id integer                           not null,
    player_id  integer                           not null
);