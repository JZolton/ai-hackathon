# HealthGuard AI: Parallel Health Data Research Platform

AI-powered platform that empowers health officials with real-time parallel analysis across multiple CDC databases, providing comprehensive insights through intelligent agent coordination.

## Problem Statement

Public health officials and policymakers need rapid access to comprehensive health data to address critical challenges like the fentanyl crisis, environmental health disparities, and healthcare access gaps. Current systems require manual data gathering across multiple CDC databases, delaying evidence-based decision making.

## What We Built

**Parallel Agent Architecture**: 3 specialized AI agents working simultaneously across health databases
- **Environmental Health Agent** (CDC EPHT) - Air quality, environmental health tracking
- **Public Health Agent** (CDC Open Data) - Disease surveillance, COVID data, health statistics  
- **Healthcare Access Agent** (Healthcare.gov) - Insurance coverage, provider networks, accessibility

**Key Features:**
- **Real-time streaming interface** with live agent progress
- **Parallel execution** - all agents research simultaneously
- **Intelligent coordination** - coordinator creates specialized research prompts
- **Comprehensive synthesis** - final reports integrate all findings
- **Token-safe processing** - handles large prompts with automatic truncation

## Architecture

```
User Query → Coordinator → 3 Parallel Agents → Final Synthesis
                ↓              ↓
            Specialized    Real-time Tool
             Prompts       Execution
```

## How to Run

### Prerequisites
- Python 3.11+
- uv package manager
- Anthropic API key

### Setup

1. **Install dependencies**
   ```bash
   uv sync
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   # Add your ANTHROPIC_API_KEY to .env
   ```

3. **Start MCP servers** (Terminal 1)
   ```bash
   uv run start_servers.py
   ```
   This starts 3 MCP servers on ports 8889, 8890, 8891

4. **Start FastAPI backend** (Terminal 2)
   ```bash
   uv run fastapi_server.py
   ```
   API server runs on `http://localhost:8000`

5. **Open frontend** (Terminal 3)
   ```bash
   open frontend_example.html
   ```
   Or open the file in your browser

### Usage

1. Enter your health research query in the textarea
2. Click "Research" to start parallel agent execution
3. Watch real-time progress in 3 columns:
   - 🌍 Environmental Health (EPHT)
   - 📊 CDC Open Data  
   - 🏥 Healthcare Access
4. View synthesized final report with integrated findings

### Example Queries

- "What are the current air quality trends in California and how do they relate to respiratory health outcomes?"
- "Analyze COVID-19 vaccination rates and their correlation with healthcare access in rural areas"
- "Compare environmental health indicators with chronic disease rates across different states"

## API Endpoints

- `POST /chat` - Stream research responses (Server-Sent Events)
- `GET /health` - Health check

## Project Structure

```
├── fastapi_server.py          # Main API server with streaming
├── frontend_example.html      # React frontend with real-time UI
├── parallel_agent.py         # Original parallel agent implementation
├── start_servers.py          # MCP server startup script
├── mcp_server_*.py           # Individual MCP servers
├── tools/                    # Health data API integrations
├── reports/                  # Generated research reports
└── logs/                     # Agent execution logs
```

## Features

### Real-time Streaming Interface
- Live agent progress updates
- Tool call visualization
- Auto-scrolling columns
- Loading indicators during synthesis

### Intelligent Agent Coordination
- Coordinator creates specialized research prompts
- Each agent interprets prompts for their data domain
- Autonomous tool selection and execution
- Comprehensive result synthesis

### Robust Error Handling
- Token limit protection with automatic truncation
- Retry logic for failed requests
- Graceful degradation on API errors
- User-friendly error messages

## Development

### Adding New Data Sources
1. Create new MCP server in `mcp_server_*.py`
2. Add agent configuration to `AGENT_CONFIGS` in `fastapi_server.py`
3. Update `start_servers.py` to include new server

### Customizing Agents
- Modify system messages in `AGENT_CONFIGS`
- Adjust termination conditions in `create_agent_team()`
- Add new event types for specialized streaming

## Technical Details

- **Backend**: FastAPI with Server-Sent Events
- **Frontend**: React with real-time streaming
- **AI**: Claude 3.5 Sonnet via Anthropic API
- **Data**: MCP protocol for tool integration
- **Architecture**: Parallel agent execution with asyncio

## Demo

Perfect for hackathon demonstrations:
- Visual parallel processing
- Real-time streaming updates
- Professional UI with progress indicators
- Comprehensive final reports
- Handles complex health data queries

---

Built for rapid health data analysis and evidence-based decision making.
