from base_server import BaseServer

class LocalDedicatedServer(BaseServer):
    def __init__(self):
        super().__init__()

    def run_tick(self, delta_time):
        self.update(delta_time)
