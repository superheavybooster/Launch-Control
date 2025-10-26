import asyncio
import websockets
import socket
import json
import threading
from enum import IntEnum, auto

class GameCommand(IntEnum):
    NONE = 0
    SendDataTick = auto()
    SetWhoSendsData = auto()
    SetRocketSetting = auto()
    SpawnAtLocation = auto()
    Engines = auto()
    Raptor = auto()
    Throttle = auto()
    RCS = auto()
    Flaps = auto()
    FoldFlaps = auto()
    GridFins = auto()
    Gimbals = auto()
    SetRCSManual = auto()
    SetDragManual = auto()
    SetGimbalManual = auto()
    Propellant = auto()
    CryotankPressure = auto()
    HotStage = auto()
    DetachHSR = auto()
    FTS = auto()
    OuterGimbalEngines = auto()
    BoosterClamps = auto()
    ControllerAltitude = auto()
    ControllerEastNorth = auto()
    ControllerAttitude = auto()
    AttitudeTarget = auto()
    ChillValve = auto()
    DumpFuel = auto()
    PopEngine = auto()
    BigFlame = auto()
    Chopsticks = auto()
    PadADeluge = auto()
    PadASQDQuickRetract = auto()
    PadAOLMQuickRetract = auto()
    PadABQDQuickRetract = auto()
    MasseyDeluge = auto()
    PadAOLMClampsExtend = auto()
    PadAOLMRQDExtend = auto()
    PadASpawnStack = auto()

class GameController:
    def __init__(self):
        self.game_socket = None
        self.connected = False
        self.buffer = ""
        self.websocket_clients = set()
        
    def connect_to_game(self):
        """Connect to StarbaseSim game server"""
        try:
            self.game_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.game_socket.connect(("localhost", 12345))
            self.game_socket.settimeout(0.1)
            self.connected = True
            print("Connected to StarbaseSim game server")
            
            # Request data updates
            self.send_to_game({
                "command": int(GameCommand.SendDataTick),
                "value": 0.1
            })
            return True
        except Exception as e:
            print(f"Failed to connect to game: {e}")
            self.connected = False
            return False
    
    def send_to_game(self, command_data):
        """Send command to game"""
        if self.connected and self.game_socket:
            try:
                self.game_socket.send((json.dumps(command_data) + "\n").encode())
                return True
            except Exception as e:
                print(f"Error sending to game: {e}")
                self.connected = False
        return False
    
    async def broadcast_to_clients(self, message):
        """Send data to all connected web clients"""
        if self.websocket_clients:
            await asyncio.gather(
                *[client.send(json.dumps(message)) for client in self.websocket_clients],
                return_exceptions=True
            )
    
    async def receive_from_game(self):
        """Receive data from game and broadcast to web clients"""
        while True:
            if not self.connected:
                if not self.connect_to_game():
                    await asyncio.sleep(1)
                    continue
            
            try:
                loop = asyncio.get_event_loop()
                data = await loop.run_in_executor(None, self.game_socket.recv, 4096)
                
                if not data:
                    raise ConnectionResetError("Game connection closed")
                
                self.buffer += data.decode('utf-8')
                
                while '\n' in self.buffer:
                    message, self.buffer = self.buffer.split('\n', 1)
                    if message and message != "Client still there?":
                        try:
                            json_data = json.loads(message)
                            # Broadcast to all web clients
                            await self.broadcast_to_clients({
                                "type": "telemetry",
                                "data": json_data
                            })
                        except json.JSONDecodeError:
                            pass
                            
            except socket.timeout:
                await asyncio.sleep(0.01)
            except Exception as e:
                print(f"Error receiving from game: {e}")
                self.connected = False
                await asyncio.sleep(1)

# Global controller instance
controller = GameController()

async def handle_websocket(websocket):
    """Handle WebSocket connections from web UI"""
    controller.websocket_clients.add(websocket)
    print(f"Web client connected (total: {len(controller.websocket_clients)})")
    
    try:
        # Send connection status
        await websocket.send(json.dumps({
            "type": "status",
            "connected": controller.connected
        }))
        
        async for message in websocket:
            try:
                data = json.loads(message)
                command_type = data.get("type")
                
                if command_type == "game_command":
                    # Forward command to game
                    controller.send_to_game(data.get("command"))
                    
            except json.JSONDecodeError:
                print(f"Invalid JSON from client: {message}")
                
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        controller.websocket_clients.discard(websocket)
        print(f"Web client disconnected (total: {len(controller.websocket_clients)})")

async def main():
    # Start game receiver task
    asyncio.create_task(controller.receive_from_game())
    
    # Start WebSocket server for web UI
    print("Starting WebSocket server on ws://localhost:8765")
    async with websockets.serve(handle_websocket, "localhost", 8765):
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    print("=" * 60)
    print("StarbaseSim WebSocket Proxy Server")
    print("=" * 60)
    print("1. Make sure StarbaseSim game is running")
    print("2. Open launch_control.html in your browser")
    print("=" * 60)
    asyncio.run(main())
