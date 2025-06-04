#!/usr/bin/env python3
"""
Setup script for HealthGuard AI Web Application
This script helps set up the complete environment for running the web application.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    return True

def check_uv_installed():
    """Check if uv is installed"""
    try:
        result = subprocess.run(['uv', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ uv is installed: {result.stdout.strip()}")
            return True
    except FileNotFoundError:
        pass
    
    print("❌ uv is not installed")
    print("📥 Install uv with: curl -LsSf https://astral.sh/uv/install.sh | sh")
    return False

def setup_environment():
    """Set up the environment file"""
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if not env_file.exists() and env_example.exists():
        print("📝 Creating .env file from .env.example...")
        shutil.copy(env_example, env_file)
        print("⚠️  Please edit .env file and add your ANTHROPIC_API_KEY")
        return False
    elif env_file.exists():
        print("✅ .env file exists")
        
        # Check if ANTHROPIC_API_KEY is set
        with open(env_file, 'r') as f:
            content = f.read()
            if "ANTHROPIC_API_KEY=your_anthropic_api_key_here" in content:
                print("⚠️  Please update ANTHROPIC_API_KEY in .env file")
                return False
            elif "ANTHROPIC_API_KEY=" in content:
                print("✅ ANTHROPIC_API_KEY is configured")
                return True
    
    print("❌ No .env file found")
    return False

def check_dependencies():
    """Check if all dependencies are installed"""
    try:
        result = subprocess.run(['uv', 'pip', 'list'], capture_output=True, text=True)
        if result.returncode == 0:
            required_packages = ['fastapi', 'uvicorn', 'anthropic', 'httpx', 'fastmcp', 'aiohttp', 'pydantic']
            installed_packages = result.stdout.lower()
            
            missing = []
            for package in required_packages:
                if package not in installed_packages:
                    missing.append(package)
            
            if missing:
                print(f"❌ Missing packages: {', '.join(missing)}")
                print("📦 Run: uv pip install -r pyproject.toml")
                return False
            else:
                print("✅ All required packages are installed")
                return True
    except Exception as e:
        print(f"❌ Error checking dependencies: {e}")
        return False

def check_mcp_servers():
    """Check if all MCP server files exist"""
    required_servers = [
        "mcp_server_epht.py",
        "mcp_server_opendata.py", 
        "mcp_server_healthcare.py",
        "mcp_server_medlineplus.py",
        "mcp_server_openfda.py"
    ]
    
    missing = []
    for server in required_servers:
        if not Path(server).exists():
            missing.append(server)
    
    if missing:
        print(f"❌ Missing MCP servers: {', '.join(missing)}")
        return False
    else:
        print("✅ All MCP server files exist")
        return True

def check_tools():
    """Check if all tool files exist"""
    required_tools = [
        "tools/cdc_epht.py",
        "tools/cdc_open_data.py",
        "tools/healthcare_gov_fixed.py",
        "tools/medlineplus_connect.py",
        "tools/openfda_api.py"
    ]
    
    missing = []
    for tool in required_tools:
        if not Path(tool).exists():
            missing.append(tool)
    
    if missing:
        print(f"❌ Missing tool files: {', '.join(missing)}")
        return False
    else:
        print("✅ All tool files exist")
        return True

def test_mcp_server():
    """Test if we can import MCP server modules"""
    try:
        # Test importing the tools
        sys.path.append('.')
        from tools.medlineplus_connect import register_medlineplus_tools
        from tools.openfda_api import register_openfda_tools
        print("✅ New tool modules can be imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Error importing tools: {e}")
        return False

def print_startup_instructions():
    """Print instructions for starting the application"""
    print("\n" + "="*60)
    print("🚀 HEALTHGUARD AI - STARTUP INSTRUCTIONS")
    print("="*60)
    print()
    print("1. Start all MCP servers:")
    print("   python start_servers.py")
    print()
    print("2. In a new terminal, start the FastAPI server:")
    print("   python fastapi_server.py")
    print()
    print("3. Open the web application:")
    print("   open frontend_example.html")
    print("   (or open it in your web browser)")
    print()
    print("🌐 The application will be available at:")
    print("   Frontend: file:///.../frontend_example.html")
    print("   API: http://localhost:8000")
    print("   MCP Servers: ports 8889-8893")
    print()
    print("📊 Available Databases:")
    print("   🌍 CDC EPHT (Environmental Health) - Port 8889")
    print("   📊 CDC Open Data (Surveillance) - Port 8890") 
    print("   🏥 Healthcare.gov (Access) - Port 8891")
    print("   🩺 MedlinePlus Connect (Education) - Port 8892")
    print("   ⚠️  OpenFDA (Drug Safety) - Port 8893")
    print()
    print("💡 Example Queries:")
    print("   • 'What are the latest FDA recalls for blood pressure medications?'")
    print("   • 'Analyze fentanyl-related adverse events and patient education'")
    print("   • 'Compare air quality trends with respiratory health outcomes'")
    print("="*60)

def main():
    """Main setup function"""
    print("🏥 HealthGuard AI - Web Application Setup")
    print("="*50)
    
    checks = [
        ("Python Version", check_python_version),
        ("UV Package Manager", check_uv_installed),
        ("Environment Setup", setup_environment),
        ("Dependencies", check_dependencies),
        ("MCP Servers", check_mcp_servers),
        ("Tool Files", check_tools),
        ("Module Imports", test_mcp_server)
    ]
    
    all_passed = True
    for check_name, check_func in checks:
        print(f"\n🔍 Checking {check_name}...")
        if not check_func():
            all_passed = False
    
    print("\n" + "="*50)
    if all_passed:
        print("🎉 Setup completed successfully!")
        print_startup_instructions()
    else:
        print("❌ Setup incomplete. Please fix the issues above.")
        print("\n📚 Common fixes:")
        print("   • Install uv: curl -LsSf https://astral.sh/uv/install.sh | sh")
        print("   • Install dependencies: uv pip install -r pyproject.toml")
        print("   • Set up .env file with your ANTHROPIC_API_KEY")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
