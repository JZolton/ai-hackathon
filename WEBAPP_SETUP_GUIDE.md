# HealthGuard AI - Web Application Setup Guide

## 🎯 Complete Setup for Running the Web Application

This guide will help you set up and run the complete HealthGuard AI web application with all 5 integrated databases.

## 📋 Prerequisites

- Python 3.8+ (✅ You have Python 3.13)
- An Anthropic API key for Claude

## 🚀 Quick Setup Steps

### 1. Install Dependencies

You can use either `pip` or `uv` (recommended):

**Option A: Using pip (Standard)**
```bash
pip install fastapi uvicorn anthropic httpx fastmcp aiohttp pydantic python-dotenv
```

**Option B: Using uv (Faster)**
```bash
# Install uv first (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv pip install fastapi uvicorn anthropic httpx fastmcp aiohttp pydantic python-dotenv
```

### 2. Set Up Environment Variables

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env file and add your Anthropic API key
# Replace 'your_anthropic_api_key_here' with your actual API key
```

Your `.env` file should look like:
```
ANTHROPIC_API_KEY=sk-ant-api03-your-actual-key-here
MCP_EPHT_HOST=0.0.0.0
MCP_EPHT_PORT=8889
MCP_OPENDATA_HOST=0.0.0.0
MCP_OPENDATA_PORT=8890
MCP_HEALTHCARE_HOST=0.0.0.0
MCP_HEALTHCARE_PORT=8891
MCP_MEDLINEPLUS_HOST=0.0.0.0
MCP_MEDLINEPLUS_PORT=8892
MCP_OPENFDA_HOST=0.0.0.0
MCP_OPENFDA_PORT=8893
```

### 3. Start the Application

**Step 1: Start all MCP servers (Terminal 1)**
```bash
python start_servers.py
```

This will start 5 specialized servers:
- 🌍 CDC EPHT (Environmental Health) - Port 8889
- 📊 CDC Open Data (Surveillance) - Port 8890
- 🏥 Healthcare.gov (Access) - Port 8891
- 🩺 MedlinePlus Connect (Education) - Port 8892
- ⚠️ OpenFDA (Drug Safety) - Port 8893

**Step 2: Start the FastAPI web server (Terminal 2)**
```bash
python fastapi_server.py
```

**Step 3: Open the web interface**
```bash
# Open the HTML file in your browser
open frontend_example.html
# Or double-click frontend_example.html in file explorer
```

## 🌐 Application URLs

- **Web Interface**: `file:///path/to/frontend_example.html`
- **API Server**: `http://localhost:8000`
- **Health Check**: `http://localhost:8000/health`
- **Available Agents**: `http://localhost:8000/agents`

## 🧪 Test the Setup

### Quick Test Commands

**Test individual MCP servers:**
```bash
# Test MedlinePlus server
curl "http://localhost:8892/sse" -X POST -H "Content-Type: application/json" -d '{"message": "test diabetes information"}'

# Test OpenFDA server  
curl "http://localhost:8893/sse" -X POST -H "Content-Type: application/json" -d '{"message": "test aspirin adverse events"}'
```

**Test the main API:**
```bash
curl "http://localhost:8000/health"
```

### Example Queries to Try

1. **Drug Safety Analysis**:
   ```
   "What are the latest FDA recalls for blood pressure medications and what patient education materials are available?"
   ```

2. **Fentanyl Crisis Research**:
   ```
   "Analyze fentanyl-related adverse events and provide patient education resources about opioid safety"
   ```

3. **Environmental Health**:
   ```
   "Compare air quality trends with respiratory health outcomes and provide patient guidance"
   ```

4. **Medication Safety**:
   ```
   "What are the current drug safety warnings for diabetes medications and related educational resources?"
   ```

## 🔧 Troubleshooting

### Common Issues

**1. Port Already in Use**
```bash
# Kill processes on specific ports
lsof -ti:8889 | xargs kill -9  # Replace 8889 with the problematic port
```

**2. Missing Dependencies**
```bash
# Install missing packages
pip install package_name
```

**3. API Key Issues**
- Make sure your `.env` file has the correct Anthropic API key
- Verify the key starts with `sk-ant-api03-`

**4. MCP Server Won't Start**
```bash
# Check if all tool files exist
ls tools/
# Should show: cdc_epht.py, cdc_open_data.py, healthcare_gov_fixed.py, medlineplus_connect.py, openfda_api.py
```

### Logs and Debugging

**Check server logs:**
```bash
# MCP servers log to console
# FastAPI server logs to console
# Check for any error messages in the terminal outputs
```

**Test individual components:**
```bash
# Test new integrations
python test_new_integrations.py
```

## 📊 Database Capabilities

### 🩺 MedlinePlus Connect (NEW)
- Health topic search in 11 languages
- ICD-10 diagnosis code lookup
- Medication information and interactions
- Symptom-based health search
- Patient education materials

### ⚠️ OpenFDA API (NEW)
- 800,000+ adverse event reports (FAERS)
- FDA drug labeling information
- Drug recalls and enforcement actions
- Medical device adverse events (MAUDE)
- Comprehensive drug safety analysis

### 🌍 CDC EPHT (Environmental Health)
- Air quality measurements
- Environmental health outcomes
- Community health profiles
- Geographic analysis

### 📊 CDC Open Data (Surveillance)
- COVID-19 surveillance data
- Disease outbreak monitoring
- Public health statistics
- Health trends analysis

### 🏥 Healthcare.gov (Access)
- Insurance coverage data
- Provider network information
- Healthcare marketplace statistics
- Access patterns analysis

## 🎉 Success Indicators

When everything is working correctly, you should see:

1. ✅ All 5 MCP servers started successfully
2. ✅ FastAPI server running on port 8000
3. ✅ Web interface loads and shows "5 Databases Connected"
4. ✅ Queries return results from multiple agents
5. ✅ Synthesis reports are generated

## 📞 Support

If you encounter issues:

1. Check that all dependencies are installed
2. Verify your `.env` file has the correct API key
3. Ensure all ports (8000, 8889-8893) are available
4. Check the console logs for error messages
5. Try the test commands above to isolate issues

---

**🏥 HealthGuard AI** - Comprehensive Public Health Decision Support System
