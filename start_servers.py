#!/usr/bin/env python3
"""
Script to start all MCP servers for health data research.
Each server runs on a different port for specialized data sources.
"""

import asyncio
import subprocess
import sys
import time
from pathlib import Path

def start_server(script_name, server_name):
    """Start a single MCP server in a subprocess"""
    print(f"Starting {server_name}...")
    try:
        process = subprocess.Popen([
            sys.executable, script_name
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return process
    except Exception as e:
        print(f"Failed to start {server_name}: {e}")
        return None

def main():
    """Start all MCP servers"""
    print("🚀 Starting Health Data MCP Servers...")
    print("=" * 50)
    
    # Server configurations
    servers = [
        ("mcp_server_epht.py", "CDC EPHT Server (Port 8889)"),
        ("mcp_server_opendata.py", "CDC Open Data Server (Port 8890)"),
        ("mcp_server_healthcare.py", "Healthcare.gov Server (Port 8891)")
    ]
    
    processes = []
    
    # Start each server
    for script, name in servers:
        if Path(script).exists():
            process = start_server(script, name)
            if process:
                processes.append((process, name))
                time.sleep(2)  # Give each server time to start
        else:
            print(f"❌ {script} not found!")
    
    if not processes:
        print("❌ No servers could be started!")
        return
    
    print("\n✅ All servers started successfully!")
    print("\nServer URLs:")
    print("- CDC EPHT: http://localhost:8889/sse")
    print("- CDC Open Data: http://localhost:8890/sse") 
    print("- Healthcare.gov: http://localhost:8891/sse")
    print("\n📝 You can now run: python agent.py")
    print("\n⚠️  Press Ctrl+C to stop all servers")
    
    try:
        # Keep the script running and monitor processes
        while True:
            time.sleep(1)
            # Check if any process has died
            for process, name in processes:
                if process.poll() is not None:
                    print(f"❌ {name} has stopped!")
    except KeyboardInterrupt:
        print("\n🛑 Stopping all servers...")
        for process, name in processes:
            print(f"Stopping {name}...")
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
        print("✅ All servers stopped!")

if __name__ == "__main__":
    main()
