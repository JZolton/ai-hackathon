# HealthGuard AI: Public Health Decision Support System

AI-powered platform that empowers health officials with real-time CDC data analysis and evidence-based recommendations for America's pressing health challenges.

## Problem Statement

Public health officials and policymakers need rapid access to comprehensive health data to address critical challenges like the fentanyl crisis, environmental health disparities, and healthcare access gaps. Current systems require manual data gathering across multiple CDC databases, delaying evidence-based decision making.

## What We Have

**Unified MCP Server**: 37 tools across 4 major CDC/health databases
- **CDC WONDER** (6 tools) - Mortality, natality, disease surveillance  
- **CDC EPHT** (8 tools) - Environmental health tracking
- **CDC Open Data** (10 tools) - General public health datasets
- **Healthcare.gov** (13 tools) - Insurance and healthcare access data

**Key Capabilities:**
- Cross-database correlation analysis
- Real-time health data querying
- Environmental health + outcome linking
- Geographic hotspot identification

## TODOs

1. **Generate/find compelling problems** that health officials/policymakers care about
2. **Validate tools effectiveness** for answering those specific questions  
3. **Plug server into LibreChat frontend** for immediate deployment
4. **Build cleaner frontend UI** (time permitting)

## Quick Start

(requires uv)

```bash
# Install dependencies
uv sync

# Run MCP server
uv run mcp_server.py
```

Server runs on `localhost:8888` with 37 health data tools available via MCP protocol.
