class PlayerDetailsData:
    def __init__(self, account_name, last_battle_time, created_at, global_rating):
        self.account_name = account_name
        self.last_battle_time = last_battle_time
        self.created_at = created_at
        self.global_rating = global_rating
        self.clan_tag = None
        self.role = None

    def set_clan_data(self, clan_tag, role):
        self.clan_tag = clan_tag
        self.role = role
