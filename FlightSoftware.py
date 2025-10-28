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
        
        # Propellant filling tracking
        self.filling_active = False
        self.ship_fill_start_time = None
        self.booster_fill_start_time = None
        self.ship_target_propellant = 1500  # tons
        self.booster_target_propellant = 3400  # tons
        self.ship_fill_duration = 46 * 60 + 40  # 46 minutes 40 seconds
        self.booster_fill_duration = 38 * 60 + 25  # 38 minutes 25 seconds
        self.ship_initial_wait = 17 * 60  # 17 minutes
        self.booster_initial_wait = 33 * 60 + 15  # 33 minutes 15 seconds
        
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
                data = json.loads(message)  # Fixed: changed parse to loads
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
            max_fuel_kg = 739.160 * 1000  # Convert tons to kg
            fuel_kg = data.get('fuelMass', 0)
            return (fuel_kg / max_fuel_kg) * 100
        else:
            max_fuel_kg = 326.100 * 1000  # Convert tons to kg
            fuel_kg = data.get('fuelMass', 0)
            return (fuel_kg / max_fuel_kg) * 100

    def get_lox_percent(self, vehicle='booster'):
        """Get LOX percentage"""
        data = self.telemetry.get(vehicle)
        if not data:
            return 0
        
        if vehicle == 'booster':
            max_lox_kg = 2660.840 * 1000  # Convert tons to kg
            lox_kg = data.get('oxidizerMass', 0)
            return (lox_kg / max_lox_kg) * 100
        else:
            max_lox_kg = 1173.851 * 1000  # Convert tons to kg
            lox_kg = data.get('oxidizerMass', 0)
            return (lox_kg / max_lox_kg) * 100
    
    def get_total_propellant(self, vehicle='booster'):
        """Get total propellant mass (fuel + oxidizer) in TONS"""
        data = self.telemetry.get(vehicle)
        if not data:
            return 0
        # Convert from kg to tons by dividing by 1000
        fuel_kg = data.get('fuelMass', 0)
        oxidizer_kg = data.get('oxidizerMass', 0)
        total_kg = fuel_kg + oxidizer_kg
        return total_kg / 1000  # Convert to tons
    
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
    
    async def set_propellant(self, vehicle, mass_tons):
        """Set propellant mass in TONS (converts to kg for game)"""
        mass_kg = mass_tons * 1000  # Convert tons to kg for game
        await self.send_command({
            'command': int(GameCommand.Propellant),
            'target': vehicle,
            'value': mass_kg  # Game expects kg
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
    # PROPELLANT FILLING LOGIC
    # =========================================================================
    
    async def start_propellant_filling(self):
        """Start the propellant filling process for both vehicles"""
        if self.filling_active:
            print("Propellant filling already active!")
            return
        
        self.filling_active = True
        self.ship_fill_start_time = time.time()
        self.booster_fill_start_time = time.time()
        
        print("=" * 60)
        print("STARTING PROPELLANT FILLING SEQUENCE")
        print(f"Ship S0: {self.ship_target_propellant} tons over {self.ship_fill_duration}s")
        print(f"Booster B0: {self.booster_target_propellant} tons over {self.booster_fill_duration}s")
        print("=" * 60)
        
        # Start both filling tasks
        asyncio.create_task(self._fill_ship_propellant())
        asyncio.create_task(self._fill_booster_propellant())
    
    async def _fill_ship_propellant(self):
        """Fill ship propellant gradually over time"""
        print(f"Waiting {self.ship_initial_wait}s before starting ship fill...")
        await asyncio.sleep(self.ship_initial_wait)
        
        print("Starting ship propellant fill...")
        start_fill_time = time.time()
        
        while self.filling_active:
            current_time = time.time()
            elapsed_fill_time = current_time - start_fill_time
            
            if elapsed_fill_time >= self.ship_fill_duration:
                # Final fill to exact target
                await self.set_propellant('S0', self.ship_target_propellant)
                print(f"Ship propellant fill COMPLETE: {self.ship_target_propellant} tons")
                break
            
            # Calculate current target based on linear progression
            progress = elapsed_fill_time / self.ship_fill_duration
            current_target = progress * self.ship_target_propellant
            
            # Set propellant
            await self.set_propellant('S0', current_target)
            
            # Check if we've reached target early
            current_propellant = self.get_total_propellant('ship')
            if current_propellant >= self.ship_target_propellant:
                print(f"Ship propellant reached target early: {current_propellant} tons")
                break
            
            # Update every 5 seconds
            await asyncio.sleep(5)
    
    async def _fill_booster_propellant(self):
        """Fill booster propellant gradually over time"""
        print(f"Waiting {self.booster_initial_wait}s before starting booster fill...")
        await asyncio.sleep(self.booster_initial_wait)
        
        print("Starting booster propellant fill...")
        start_fill_time = time.time()
        
        while self.filling_active:
            current_time = time.time()
            elapsed_fill_time = current_time - start_fill_time
            
            if elapsed_fill_time >= self.booster_fill_duration:
                # Final fill to exact target
                await self.set_propellant('B0', self.booster_target_propellant)
                print(f"Booster propellant fill COMPLETE: {self.booster_target_propellant} tons")
                break
            
            # Calculate current target based on linear progression
            progress = elapsed_fill_time / self.booster_fill_duration
            current_target = progress * self.booster_target_propellant
            
            # Set propellant
            await self.set_propellant('B0', current_target)
            
            # Check if we've reached target early
            current_propellant = self.get_total_propellant('booster')
            if current_propellant >= self.booster_target_propellant:
                print(f"Booster propellant reached target early: {current_propellant} tons")
                break
            
            # Update every 5 seconds
            await asyncio.sleep(5)
    
    def stop_propellant_filling(self):
        """Stop the propellant filling process"""
        self.filling_active = False
        print("Propellant filling stopped")
    
    # =========================================================================
    # ASCENT SCRIPTS - FILL THESE IN!
    # =========================================================================
    
    async def ascent_script_1(self):
        """
        ASCENT SCRIPT 1 - No Roll, Downwards Flip
        
        Your flight control code goes here!
        Use the helper methods above to control the rocket.
        """
        print("Executing Ascent Script 1 (No Roll, Downwards Flip)")
        
        # Start propellant filling automatically
        await self.start_propellant_filling()
        
        # =====================================================================
        # YOUR CUSTOM ASCENT CODE GOES HERE!
        # =====================================================================
        
        # Example: Wait for propellant to be filled before continuing
        print("Waiting for propellant filling to complete...")
        await self.wait_for_condition(
            lambda: (self.get_total_propellant('ship') >= self.ship_target_propellant and 
                    self.get_total_propellant('booster') >= self.booster_target_propellant),
            timeout=3600  # 1 hour timeout
        )
        
        print("Propellant filled! Ready for launch sequence.")
        
        # ADD YOUR LAUNCH CODE HERE
        # Example:
        # await self.start_engines('booster')
        # await self.set_throttle('booster', 100)
        # await self.wait_for_condition(lambda: self.get_altitude('booster') > 1000)
        # ... etc
        
        pass
    
    async def ascent_script_2(self):
        """
        ASCENT SCRIPT 2 - Roll, Upwards Flip
        
        Your flight control code goes here!
        """
        print("Executing Ascent Script 2 (Roll, Upwards Flip)")
        
        # Start propellant filling automatically
        await self.start_propellant_filling()
        
        # =====================================================================
        # YOUR CUSTOM ASCENT CODE GOES HERE!
        # =====================================================================
        
        # Example: Wait for propellant to be filled before continuing
        print("Waiting for propellant filling to complete...")
        await self.wait_for_condition(
            lambda: (self.get_total_propellant('ship') >= self.ship_target_propellant and 
                    self.get_total_propellant('booster') >= self.booster_target_propellant),
            timeout=3600  # 1 hour timeout
        )
        
        print("Propellant filled! Ready for launch sequence.")
        
        # ADD YOUR LAUNCH CODE HERE
        # This script can have different behavior than script 1
        
        pass
    
    # =========================================================================
    # BOOSTER SCRIPTS - FILL THESE IN!
    # =========================================================================
    
    async def booster_script_1(self):
        """BOOSTER SCRIPT 1 - Catch"""
        print("Executing Booster Script 1 (Catch)")
        
        # =====================================================================
        # YOUR CUSTOM BOOSTER CODE GOES HERE!
        # =====================================================================
        
        # ADD YOUR BOOSTER LANDING CODE HERE
        
        pass
    
    async def booster_script_2(self):
        """BOOSTER SCRIPT 2 - B13 Profile"""
        print("Executing Booster Script 2 (B13 Profile)")
        
        # =====================================================================
        # YOUR CUSTOM BOOSTER CODE GOES HERE!
        # =====================================================================
        
        pass
    
    async def booster_script_3(self):
        """BOOSTER SCRIPT 3 - B14-2 Profile"""
        print("Executing Booster Script 3 (B14-2 Profile)")
        
        # =====================================================================
        # YOUR CUSTOM BOOSTER CODE GOES HERE!
        # =====================================================================
        
        pass
    
    async def booster_script_4(self):
        """BOOSTER SCRIPT 4 - B15-2 Profile"""
        print("Executing Booster Script 4 (B15-2 Profile)")
        
        # =====================================================================
        # YOUR CUSTOM BOOSTER CODE GOES HERE!
        # =====================================================================
        
        pass
    
    async def booster_script_5(self):
        """BOOSTER SCRIPT 5 - B16 Profile, Recommended"""
        print("Executing Booster Script 5 (B16 Profile, Recommended)")
        
        # =====================================================================
        # YOUR CUSTOM BOOSTER CODE GOES HERE!
        # =====================================================================
        
        pass
    
    # =========================================================================
    # SHIP SCRIPTS - FILL THESE IN!
    # =========================================================================
    
    async def ship_script_1(self):
        """SHIP SCRIPT 1 - Normal Reentry"""
        print("Executing Ship Script 1 (Normal Reentry)")
        
        # =====================================================================
        # YOUR CUSTOM SHIP CODE GOES HERE!
        # =====================================================================
        
        # ADD YOUR SHIP LANDING CODE HERE
        
        pass
    
    async def ship_script_2(self):
        """SHIP SCRIPT 2 - Hypersonic Drifting Reentry"""
        print("Executing Ship Script 2 (Hypersonic Drifting Reentry)")
        
        # =====================================================================
        # YOUR CUSTOM SHIP CODE GOES HERE!
        # =====================================================================
        
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
        
        # Start ascent (which includes propellant filling)
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
        print("  fill - Start propellant filling")
        print("  stopfill - Stop propellant filling")
        print("  quit - Exit")
        print("=" * 60)
        
        # Simple command handler
        while self.running:
            try:
                command = await asyncio.get_event_loop().run_in_executor(None, input, "Enter command: ")
                command = command.strip().lower()
                
                if command == 'ascent1':
                    self.ascent_script = 1
                    asyncio.create_task(self.execute_ascent())
                elif command == 'ascent2':
                    self.ascent_script = 2
                    asyncio.create_task(self.execute_ascent())
                elif command.startswith('booster'):
                    script_num = int(command[-1])
                    if 1 <= script_num <= 5:
                        self.booster_script = script_num
                        asyncio.create_task(self.execute_booster())
                elif command == 'ship1':
                    self.ship_script = 1
                    asyncio.create_task(self.execute_ship())
                elif command == 'ship2':
                    self.ship_script = 2
                    asyncio.create_task(self.execute_ship())
                elif command == 'launch':
                    asyncio.create_task(self.execute_full_launch())
                elif command == 'fill':
                    asyncio.create_task(self.start_propellant_filling())
                elif command == 'stopfill':
                    self.stop_propellant_filling()
                elif command == 'quit':
                    self.running = False
                else:
                    print("Unknown command")
                    
            except KeyboardInterrupt:
                print("\nShutting down...")
                self.running = False
                break
            except Exception as e:
                print(f"Error processing command: {e}")

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
