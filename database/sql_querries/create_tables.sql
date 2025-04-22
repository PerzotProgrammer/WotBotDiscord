PRAGMA foreign_keys = ON;

create table if not exists wot_players
(
    pid      integer primary key not null,
    wot_name text                not null,
    role     text                not null
);

create table if not exists discord_users
(
    uid          integer primary key not null,
    discord_name text                not null,
    pid          integer             not null,
    foreign key (pid) references wot_players (pid)
);


create table if not exists wot_advances
(
    id          integer primary key autoincrement not null,
    date        text                              not null,
    invoker_uid integer                           not null,
    foreign key (invoker_uid) references discord_users (uid)

);

create table if not exists wot_advances_players
(
    id         integer primary key autoincrement not null,
    pid        integer                           not null,
    advance_id integer                           not null,
    foreign key (pid) references wot_players (pid),
    foreign key (advance_id) references wot_advances (id)
);

create table if not exists current_wot_players_pids
(
    pid integer primary key not null
);