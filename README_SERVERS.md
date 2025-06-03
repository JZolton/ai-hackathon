# Health Data MCP Servers Architecture

This project now uses separate MCP servers for each data source, allowing for better isolation and specialized agent connections.

## Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   CDC EPHT      │    │  CDC Open Data   │    │ Healthcare.gov  │
│   Server        │    │     Server       │    │    Server       │
│  Port: 8889     │    │   Port: 8890     │    │   Port: 8891    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────────┐
                    │   Agent System      │
                    │                     │
                    │ ┌─────────────────┐ │
                    │ │ Orchestrator    │ │
                    │ │ Agent           │ │
                    │ └─────────────────┘ │
                    │ ┌─────────────────┐ │
                    │ │ CDC EPHT Agent  │ │
                    │ └─────────────────┘ │
                    │ ┌─────────────────┐ │
                    │ │ CDC Open Data   │ │
                    │ │ Agent           │ │
                    │ └─────────────────┘ │
                    │ ┌─────────────────┐ │
                    │ │ Healthcare.gov  │ │
                    │ │ Agent           │ │
                    │ └─────────────────┘ │
                    │ ┌─────────────────┐ │
                    │ │ Report Writer   │ │
                    │ │ Agent           │ │
                    │ └─────────────────┘ │
                    └─────────────────────┘
```

## Server Files

### Individual Servers
- **`mcp_server_epht.py`** - CDC Environmental Public Health Tracking server (Port 8889)
- **`mcp_server_opendata.py`** - CDC Open Data server (Port 8890)  
- **`mcp_server_healthcare.py`** - Healthcare.gov server (Port 8891)

### Original Combined Server
- **`mcp_server.py`** - Original combined server (Port 8888) - still available for testing

## Quick Start

### 1. Setup API Key
First, you need to configure your Anthropic API key:

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your Anthropic API key
# ANTHROPIC_API_KEY=your_actual_api_key_here
```

**Get your API key from:** https://console.anthropic.com/

### 2. Start All Servers at Once (Recommended)
```bash
python start_servers.py
```

This will start all three specialized servers and monitor them. Press Ctrl+C to stop all servers.

### 3. Start Servers Individually (Alternative)
```bash
# Terminal 1 - CDC EPHT Server
python mcp_server_epht.py

# Terminal 2 - CDC Open Data Server  
python mcp_server_opendata.py

# Terminal 3 - Healthcare.gov Server
python mcp_server_healthcare.py
```

### 4. Run the Agent System
Once all servers are running and API key is configured:
```bash
python agent.py
```

**Note:** The agent system will check for the API key and provide helpful error messages if it's missing.

## Server Details

### CDC EPHT Server (Port 8889)
**Tools Available:**
- `get_measure_categories` - Get environmental health measure categories
- `search_measures_by_topic` - Search measures by health/environmental topic
- `get_air_quality_data` - Get air quality data (PM2.5, ozone, air toxics)
- `get_health_outcomes_by_environment` - Get health outcomes linked to environmental factors
- `get_community_health_profile` - Get comprehensive community health profiles

### CDC Open Data Server (Port 8890)
**Tools Available:**
- `search_open_data` - Search CDC Open Data repository
- `get_common_datasets` - Get list of commonly used CDC datasets
- `search_covid_data` - Search COVID-19 data
- `get_recent_datasets` - Get recent datasets with modification analysis
- `query_dataset_data` - Query actual data from specific datasets

### Healthcare.gov Server (Port 8891)
**Tools Available:**
- `test_healthcare_api` - Test connectivity to Healthcare.gov API
- `get_healthcare_categories` - Get healthcare data categories
- `get_api_status` - Get comprehensive API status

## Agent Specialization

Each agent connects to its specialized server:

- **CDC EPHT Agent** → CDC EPHT Server (8889)
- **CDC Open Data Agent** → CDC Open Data Server (8890)
- **Healthcare.gov Agent** → Healthcare.gov Server (8891)
- **Orchestrator Agent** → All servers (has access to all tools)
- **Report Writer Agent** → All servers (for comprehensive reporting)

## Environment Variables

You can customize server hosts and ports using environment variables:

```bash
# CDC EPHT Server
export MCP_EPHT_HOST=0.0.0.0
export MCP_EPHT_PORT=8889

# CDC Open Data Server
export MCP_OPENDATA_HOST=0.0.0.0
export MCP_OPENDATA_PORT=8890

# Healthcare.gov Server
export MCP_HEALTHCARE_HOST=0.0.0.0
export MCP_HEALTHCARE_PORT=8891
```

## Benefits of Separated Architecture

1. **Isolation** - Each data source runs independently
2. **Scalability** - Can scale individual servers based on load
3. **Maintenance** - Easier to update/restart individual services
4. **Debugging** - Easier to troubleshoot specific data source issues
5. **Security** - Can apply different security policies per data source
6. **Agent Specialization** - Each agent only has access to relevant tools

## Logs and Reports

- **Logs**: Created in `logs/` directory with timestamps
- **Reports**: Saved in `reports/` directory with timestamps
- **Format**: All logs and reports use markdown format

## Troubleshooting

### Server Connection Issues
1. Ensure all servers are running on their respective ports
2. Check firewall settings for ports 8889, 8890, 8891
3. Verify no other services are using these ports

### Agent Connection Issues
1. Check server logs for connection errors
2. Ensure agent.py is connecting to correct URLs
3. Verify MCP server tools are properly installed

### Tool Availability Issues
1. Check individual server logs for tool registration
2. Verify tool imports in each server file
3. Test individual servers with simple requests
