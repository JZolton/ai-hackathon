#!/usr/bin/env python3
"""
Script to start all MCP servers for health data research.
Each server runs on a different port for specialized data sources.
"""
import subprocess
import time
import sys
import signal
import os
from typing import List, Dict

class MCPServerManager:
    def __init__(self):
        self.processes: List[subprocess.Popen] = []
        self.servers = [
            {
                "script": "mcp_server_epht.py",
                "port": 8889,
                "name": "CDC EPHT (Environmental Health)"
            },
            {
                "script": "mcp_server_opendata.py",
                "port": 8890,
                "name": "CDC Open Data"
            },
            {
                "script": "mcp_server_healthcare.py",
                "port": 8891,
                "name": "Healthcare.gov"
            },
            # NEW: Your added servers
            {
                "script": "mcp_server_medlineplus.py",
                "port": 8892,
                "name": "MedlinePlus Connect"
            },
            {
                "script": "mcp_server_openfda.py",
                "port": 8893,
                "name": "OpenFDA"
            }
        ]
    
    def start_server(self, server_config: Dict[str, any]) -> subprocess.Popen:
        """Start a single MCP server"""
        script = server_config["script"]
        port = server_config["port"]
        name = server_config["name"]
        
        print(f"🚀 Starting {name} on port {port}...")
        
        try:
            # Check if script exists
            if not os.path.exists(script):
                print(f"❌ Error: Script {script} not found!")
                return None
            
            # Start the server process
            process = subprocess.Popen(
                [sys.executable, script, "--port", str(port)],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            # Give it a moment to start
            time.sleep(2)
            
            # Check if process is still running
            if process.poll() is None:
                print(f"✅ {name} started successfully on port {port}")
                return process
            else:
                print(f"❌ {name} failed to start")
                # Print any error output
                output, _ = process.communicate()
                if output:
                    print(f"Error output: {output}")
                return None
                
        except Exception as e:
            print(f"❌ Error starting {name}: {e}")
            return None
    
    def start_all_servers(self):
        """Start all MCP servers"""
        print("🏥 HealthGuard AI - Starting MCP Servers")
        print("=" * 50)
        
        for server_config in self.servers:
            process = self.start_server(server_config)
            if process:
                self.processes.append(process)
        
        if not self.processes:
            print("❌ No servers started successfully!")
            return False
        
        print("\n🎉 All servers started successfully!")
        print("\nServer Status:")
        print("-" * 30)
        
        for i, server_config in enumerate(self.servers):
            if i < len(self.processes) and self.processes[i].poll() is None:
                print(f"✅ {server_config['name']} - Port {server_config['port']}")
            else:
                print(f"❌ {server_config['name']} - Failed to start")
        
        print(f"\n📊 {len(self.processes)} servers running")
        print("\nNext steps:")
        print("1. Start FastAPI server: uv run fastapi_server.py")
        print("2. Open frontend: open frontend_example.html")
        print("\nPress Ctrl+C to stop all servers")
        
        return True
    
    def stop_all_servers(self):
        """Stop all running servers"""
        print("\n🛑 Stopping all MCP servers...")
        
        for process in self.processes:
            try:
                process.terminate()
                process.wait(timeout=5)
                print("✅ Server stopped gracefully")
            except subprocess.TimeoutExpired:
                print("⚠️ Server didn't respond, forcing stop...")
                process.kill()
                print("✅ Server force stopped")
            except Exception as e:
                print(f"❌ Error stopping server: {e}")
        
        self.processes.clear()
        print("🏁 All servers stopped")
    
    def signal_handler(self, signum, frame):
        """Handle Ctrl+C gracefully"""
        self.stop_all_servers()
        sys.exit(0)
    
    def monitor_servers(self):
        """Monitor server health and restart if needed"""
        try:
            while True:
                # Check if all processes are still running
                running_count = 0
                for i, process in enumerate(self.processes):
                    if process.poll() is None:
                        running_count += 1
                    else:
                        server_name = self.servers[i]["name"]
                        print(f"⚠️ {server_name} has stopped unexpectedly")
                
                if running_count == 0:
                    print("❌ All servers have stopped")
                    break
                
                time.sleep(5)  # Check every 5 seconds
                
        except KeyboardInterrupt:
            pass
        finally:
            self.stop_all_servers()

def main():
    """Main function to start and manage MCP servers"""
    manager = MCPServerManager()
    
    # Set up signal handler for graceful shutdown
    signal.signal(signal.SIGINT, manager.signal_handler)
    signal.signal(signal.SIGTERM, manager.signal_handler)
    
    # Start all servers
    if manager.start_all_servers():
        # Monitor servers
        manager.monitor_servers()
    else:
        print("Failed to start servers")
        sys.exit(1)

if __name__ == "__main__":
    main()