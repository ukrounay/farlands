import asyncio
import websockets
from base_server import BaseServer
import json

class RemoteDedicatedServer(BaseServer):
    async def handler(self, websocket, path):
        player_id = await websocket.recv()
        self.add_player(player_id, {})
        try:
            async for message in websocket:
                data = json.loads(message)
                self.handle_input(player_id, data)
                await websocket.send(json.dumps(self.get_state()))
        except websockets.exceptions.ConnectionClosed:
            print(f"Player {player_id} disconnected")

    async def run(self, host="localhost", port=8765):
        server = await websockets.serve(self.handler, host, port)
        print(f"Server running on ws://{host}:{port}")
        await server.wait_closed()
