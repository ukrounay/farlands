class BaseServer:
    def __init__(self):
        self.players = {}
        self.game_state = {}

    def update(self, delta_time):
        """Update game logic."""
        pass

    def add_player(self, player_id, data):
        self.players[player_id] = data

    def handle_input(self, player_id, input_data):
        """Update player based on input."""
        pass

    def get_state(self):
        return self.game_state
