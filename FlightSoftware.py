import asyncio
import websockets
import json
import time
import math
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

class FlightSoftware:
    def __init__(self):
        self.ws = None
        self.connected = False
        self.telemetry = {
            'booster': None,
            'ship': None
        }
        self.running = False
        
        # Script selections (can be changed via commands)
        self.ascent_script = 1
        self.booster_script = 1
        self.ship_script = 1
        
    async def connect(self):
        """Connect to the server WebSocket"""
        try:
            self.ws = await websockets.connect('ws://localhost:8765')
            self.connected = True
            print("Connected to server")
            return True
        except Exception as e:
            print(f"Failed to connect: {e}")
            self.connected = False
            return False
    
    async def send_command(self, command_data):
        """Send command to game through server"""
        if self.connected and self.ws:
            try:
                await self.ws.send(json.dumps({
                    'type': 'game_command',
                    'command': command_data
                }))
                return True
            except Exception as e:
                print(f"Error sending command: {e}")
                self.connected = False
        return False
    
    async def receive_telemetry(self):
        """Receive telemetry data from server"""
        try:
            async for message in self.ws:
                data = json.parse(message)
                if data.get('type') == 'telemetry':
                    telem = data.get('data', {})
                    objectname = telem.get('objectname', '')
                    
                    if objectname.startswith('B'):
                        self.telemetry['booster'] = telem
                    elif objectname.startswith('S'):
                        self.telemetry['ship'] = telem
                        
        except websockets.exceptions.ConnectionClosed:
            print("Connection closed")
            self.connected = False
        except Exception as e:
            print(f"Error receiving telemetry: {e}")
            self.connected = False
    
    # =========================================================================
    # HELPER METHODS - Use these in your flight scripts!
    # =========================================================================
    
    def get_booster_data(self):
        """Get current booster telemetry"""
        return self.telemetry['booster']
    
    def get_ship_data(self):
        """Get current ship telemetry"""
        return self.telemetry['ship']
    
    def get_altitude(self, vehicle='booster'):
        """Get altitude in meters"""
        data = self.telemetry.get(vehicle)
        if data and 'location' in data:
            return data['location'][2]
        return 0
    
    def get_velocity(self, vehicle='booster'):
        """Get velocity vector [vx, vy, vz] in m/s"""
        data = self.telemetry.get(vehicle)
        if data and 'velocity' in data:
            return data['velocity']
        return [0, 0, 0]
    
    def get_speed(self, vehicle='booster'):
        """Get total speed magnitude in m/s"""
        vel = self.get_velocity(vehicle)
        return math.sqrt(vel[0]**2 + vel[1]**2 + vel[2]**2)
    
    def get_fuel_percent(self, vehicle='booster'):
        """Get fuel percentage"""
        data = self.telemetry.get(vehicle)
        if not data:
            return 0
            
        if vehicle == 'booster':
            max_fuel = 739.160
            return (data.get('fuelMass', 0) / max_fuel) * 100
        else:
            max_fuel = 326.100
            return (data.get('fuelMass', 0) / max_fuel) * 100
    
    def get_lox_percent(self, vehicle='booster'):
        """Get LOX percentage"""
        data = self.telemetry.get(vehicle)
        if not data:
            return 0
            
        if vehicle == 'booster':
            max_lox = 2660.840
            return (data.get('oxidizerMass', 0) / max_lox) * 100
        else:
            max_lox = 1173.851
            return (data.get('oxidizerMass', 0) / max_lox) * 100
    
    async def start_engines(self, vehicle, engine_list=None):
        """
        Start engines on a vehicle
        vehicle: 'booster' or 'ship' (or full object name like 'B13')
        engine_list: list of engine numbers [1, 2, 3, ...] or None for all
        """
        if engine_list:
            for engine_num in engine_list:
                await self.send_command({
                    'command': int(GameCommand.Raptor),
                    'target': vehicle,
                    'value': engine_num,
                    'state': True
                })
                await asyncio.sleep(0.05)  # Small delay between engines
        else:
            await self.send_command({
                'command': int(GameCommand.Engines),
                'target': vehicle,
                'state': True
            })
    
    async def stop_engines(self, vehicle, engine_list=None):
        """Stop engines on a vehicle"""
        if engine_list:
            for engine_num in engine_list:
                await self.send_command({
                    'command': int(GameCommand.Raptor),
                    'target': vehicle,
                    'value': engine_num,
                    'state': False
                })
                await asyncio.sleep(0.05)
        else:
            await self.send_command({
                'command': int(GameCommand.Engines),
                'target': vehicle,
                'state': False
            })
    
    async def set_throttle(self, vehicle, percent):
        """Set throttle percentage (0-100)"""
        await self.send_command({
            'command': int(GameCommand.Throttle),
            'target': vehicle,
            'value': percent
        })
    
    async def set_attitude(self, vehicle, pitch, yaw, roll):
        """Set vehicle attitude target"""
        await self.send_command({
            'command': int(GameCommand.AttitudeTarget),
            'target': vehicle,
            'pitch': pitch,
            'yaw': yaw,
            'roll': roll
        })
    
    async def set_flaps(self, vehicle, angle):
        """Set flap angle"""
        await self.send_command({
            'command': int(GameCommand.Flaps),
            'target': vehicle,
            'value': angle
        })
    
    async def set_grid_fins(self, vehicle, angle):
        """Set grid fin angle"""
        await self.send_command({
            'command': int(GameCommand.GridFins),
            'target': vehicle,
            'value': angle
        })
    
    async def hot_stage(self):
        """Trigger hot staging"""
        await self.send_command({
            'command': int(GameCommand.HotStage),
            'target': 'ship'
        })
    
    async def detach_hsr(self):
        """Detach hot staging ring"""
        await self.send_command({
            'command': int(GameCommand.DetachHSR),
            'target': 'ship'
        })
    
    async def wait_for_condition(self, condition_func, timeout=None, check_interval=0.1):
        """
        Wait until a condition is met
        condition_func: a function that returns True when condition is met
        timeout: maximum time to wait in seconds (None = infinite)
        check_interval: how often to check the condition
        """
        start_time = time.time()
        while not condition_func():
            if timeout and (time.time() - start_time) > timeout:
                return False
            await asyncio.sleep(check_interval)
        return True
    
    # =========================================================================
    # ASCENT SCRIPTS - FILL THESE IN!
    # =========================================================================
    
    async def ascent_script_1(self):
        """
        ASCENT SCRIPT 1 - No Roll, Downwards Flip
        
        Your flight control code goes here!
        Use the helper methods above to control the rocket.
        
        Example:
            await self.start_engines('booster', [1, 2, 3])
            await self.set_throttle('booster', 100)
            await self.wait_for_condition(lambda: self.get_altitude('booster') > 1000)
            # ... etc
        """
        print("Executing Ascent Script 1 (No Roll, Downwards Flip)")
        
        # YOUR CODE HERE!
        pass
    
    async def ascent_script_2(self):
        """
        ASCENT SCRIPT 2 - Roll, Upwards Flip
        
        Your flight control code goes here!
        """
        print("Executing Ascent Script 2 (Roll, Upwards Flip)")
        
        # YOUR CODE HERE!
        pass
    
    # =========================================================================
    # BOOSTER SCRIPTS - FILL THESE IN!
    # =========================================================================
    
    async def booster_script_1(self):
        """BOOSTER SCRIPT 1 - Catch"""
        print("Executing Booster Script 1 (Catch)")
        
        # YOUR CODE HERE!
        pass
    
    async def booster_script_2(self):
        """BOOSTER SCRIPT 2 - B13 Profile"""
        print("Executing Booster Script 2 (B13 Profile)")
        
        # YOUR CODE HERE!
        pass
    
    async def booster_script_3(self):
        """BOOSTER SCRIPT 3 - B14-2 Profile"""
        print("Executing Booster Script 3 (B14-2 Profile)")
        
        # YOUR CODE HERE!
        pass
    
    async def booster_script_4(self):
        """BOOSTER SCRIPT 4 - B15-2 Profile"""
        print("Executing Booster Script 4 (B15-2 Profile)")
        
        # YOUR CODE HERE!
        pass
    
    async def booster_script_5(self):
        """BOOSTER SCRIPT 5 - B16 Profile, Recommended"""
        print("Executing Booster Script 5 (B16 Profile, Recommended)")
        
        # YOUR CODE HERE!
        pass
    
    # =========================================================================
    # SHIP SCRIPTS - FILL THESE IN!
    # =========================================================================
    
    async def ship_script_1(self):
        """SHIP SCRIPT 1 - Normal Reentry"""
        print("Executing Ship Script 1 (Normal Reentry)")
        
        # YOUR CODE HERE!
        pass
    
    async def ship_script_2(self):
        """SHIP SCRIPT 2 - Hypersonic Drifting Reentry"""
        print("Executing Ship Script 2 (Hypersonic Drifting Reentry)")
        
        # YOUR CODE HERE!
        pass
    
    # =========================================================================
    # SCRIPT EXECUTION
    # =========================================================================
    
    async def execute_ascent(self):
        """Execute selected ascent script"""
        if self.ascent_script == 1:
            await self.ascent_script_1()
        else:
            await self.ascent_script_2()
    
    async def execute_booster(self):
        """Execute selected booster script"""
        scripts = {
            1: self.booster_script_1,
            2: self.booster_script_2,
            3: self.booster_script_3,
            4: self.booster_script_4,
            5: self.booster_script_5
        }
        await scripts.get(self.booster_script, self.booster_script_1)()
    
    async def execute_ship(self):
        """Execute selected ship script"""
        if self.ship_script == 1:
            await self.ship_script_1()
        else:
            await self.ship_script_2()
    
    async def execute_full_launch(self):
        """Execute full launch sequence with all scripts"""
        print("=" * 60)
        print("STARTING FULL LAUNCH SEQUENCE")
        print("=" * 60)
        
        # Start ascent
        await self.execute_ascent()
        
        # Booster and ship scripts would be triggered by staging events
        # You can add logic here to detect staging and trigger the appropriate scripts
        
        print("=" * 60)
        print("LAUNCH SEQUENCE COMPLETE")
        print("=" * 60)
    
    # =========================================================================
    # MAIN LOOP
    # =========================================================================
    
    async def run(self):
        """Main run loop"""
        self.running = True
        
        # Connect to server
        if not await self.connect():
            print("Failed to connect to server. Make sure server.py is running!")
            return
        
        # Start telemetry receiver
        asyncio.create_task(self.receive_telemetry())
        
        print("=" * 60)
        print("Flight Software Ready!")
        print("=" * 60)
        print("Commands:")
        print("  ascent1/ascent2 - Execute ascent script")
        print("  booster1-5 - Execute booster script")
        print("  ship1/ship2 - Execute ship script")
        print("  launch - Execute full launch sequence")
        print("  quit - Exit")
        print("=" * 60)
        
        # Command loop
        while self.running:
            try:
                # In a real implementation, you'd want to listen for commands
                # For now, we'll just keep the connection alive
                await asyncio.sleep(1)
                
            except KeyboardInterrupt:
                print("\nShutting down...")
                self.running = False
                break

async def main():
    """Entry point"""
    flight_software = FlightSoftware()
    
    # You can manually trigger scripts here for testing:
    await flight_software.run()
    
    # Or trigger specific scripts:
    # await flight_software.execute_ascent()
    # await flight_software.execute_booster()
    # await flight_software.execute_ship()

if __name__ == "__main__":
    print("=" * 60)
    print("StarbaseSim Flight Software")
    print("=" * 60)
    print("Make sure server.py is running first!")
    print("=" * 60)
    asyncio.run(main())
