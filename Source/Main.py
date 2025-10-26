"""
StarbaseSim Launch Control - Main Launcher
Starts server, flight software, and opens UI window
"""

import webview
import threading
import asyncio
import sys
import os
from pathlib import Path

# Import our modules
import Server
import FlightSoftware

class LaunchControlApp:
    def __init__(self):
        self.server_running = False
        self.flight_software_running = False
        self.html_path = None
        
    def get_html_content(self):
        """Load HTML file content"""
        # When running as .exe, files are in _MEIPASS temp directory
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
        
        html_file = os.path.join(base_path, 'LaunchControl.html')
        
        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"Error loading HTML: {e}")
            return "<h1>Error loading LaunchControl.html</h1>"
    
    def start_server(self):
        """Start the WebSocket server in background thread"""
        def run_server():
            try:
                print("Starting Server...")
                asyncio.run(Server.main())
            except Exception as e:
                print(f"Server error: {e}")
        
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        self.server_running = True
        print("Server started")
    
    def start_flight_software(self):
        """Start flight software in background thread"""
        def run_flight_software():
            try:
                print("Starting Flight Software...")
                # Give server time to start
                import time
                time.sleep(2)
                asyncio.run(FlightSoftware.main())
            except Exception as e:
                print(f"Flight Software error: {e}")
        
        flight_thread = threading.Thread(target=run_flight_software, daemon=True)
        flight_thread.start()
        self.flight_software_running = True
        print("Flight Software started")
    
    def run(self):
        """Main application entry point"""
        print("=" * 60)
        print("StarbaseSim Launch Control")
        print("=" * 60)
        
        # Start server first
        self.start_server()
        
        # Start flight software
        self.start_flight_software()
        
        # Small delay to let server initialize
        import time
        time.sleep(1)
        
        # Get HTML content
        html_content = self.get_html_content()
        
        # Create window with PyWebView
        print("Opening Launch Control window...")
        window = webview.create_window(
            title='StarbaseSim Launch Control',
            html=html_content,
            width=1920,
            height=1080,
            resizable=True,
            fullscreen=False,
            min_size=(1280, 720),
            background_color='#1e1e1e'
        )
        
        # Start webview (this blocks until window is closed)
        webview.start(debug=False)  # Set debug=True if YOU need to debug
        
        print("Launch Control closed")

def main():
    """Entry point"""
    app = LaunchControlApp()
    app.run()

if __name__ == '__main__':
    main()
