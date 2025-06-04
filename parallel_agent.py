import asyncio
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass
from dotenv import load_dotenv

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.conditions import TextMessageTermination, MaxMessageTermination
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_ext.models.anthropic import AnthropicChatCompletionClient
from autogen_ext.tools.mcp import mcp_server_tools, SseServerParams
from autogen_core.models import UserMessage

load_dotenv()

@dataclass
class AgentConfig:
    name: str
    server_url: str
    system_message: str
    description: str

# Configuration for each specialized agent
AGENT_CONFIGS = [
    AgentConfig(
        name="EPHT_Agent",
        server_url="http://localhost:8889/sse",
        system_message="""You are a specialized CDC Environmental Public Health Tracking (EPHT) agent.
        Focus on environmental health data including:
        - Air quality measurements (PM2.5, ozone, air toxics)
        - Environmental health outcomes
        - Community health profiles
        - Geographic and temporal analysis of environmental factors
        
        Use the available EPHT tools to gather relevant data and provide comprehensive insights.""",
        description="Environmental health and air quality specialist"
    ),
    AgentConfig(
        name="OpenData_Agent", 
        server_url="http://localhost:8890/sse",
        system_message="""You are a specialized CDC Open Data agent.
        Focus on:
        - COVID-19 surveillance data
        - General health surveillance datasets
        - Disease outbreak and monitoring data
        - Public health statistics and trends
        
        Use the available CDC Open Data tools to gather relevant data and provide insights.""",
        description="CDC surveillance and public health data specialist"
    ),
    AgentConfig(
        name="Healthcare_Agent",
        server_url="http://localhost:8891/sse",
        system_message="""You are a specialized Healthcare.gov agent.
        Focus on:
        - Healthcare marketplace plans and coverage
        - Provider networks and facility data
        - Healthcare accessibility analysis
        - Insurance coverage patterns and trends
        
        Use the available Healthcare.gov tools to gather relevant data and provide insights.""",
        description="Healthcare marketplace and access specialist"
    )
]

async def create_specialized_prompt(user_query: str, model_client) -> str:
    """Create a specialized prompt for all agents based on the user query"""
    
    print("🎯 Creating specialized prompt from user query...")
    
    prompt = f"""
You are a health data research coordinator. Analyze this user query and create a single, focused research prompt that can be given to multiple specialized health data agents.

User Query: "{user_query}"

The prompt should:
1. Clearly state what data and insights are needed
2. Be specific enough to guide research but general enough for different data sources
3. Include any relevant geographic, temporal, or demographic parameters
4. Specify the type of analysis or correlations to look for

Create a prompt that each specialized agent (environmental health, CDC data, healthcare access) can interpret and act upon with their specific tools and data sources.

Respond with just the prompt text, no additional formatting or explanation.
"""
    
    response = await model_client.create([UserMessage(content=prompt, source="user")])
    
    specialized_prompt = response.content.strip()
    print(f"✅ Created specialized prompt: {specialized_prompt[:100]}...")
    return specialized_prompt

async def create_agent_team(config: AgentConfig, model_client, specialized_prompt: str):
    """Create a single-agent team for a specific data source"""
    
    print(f"\n🔧 Setting up {config.name}...")
    
    try:
        # Connect to MCP server
        server_params = SseServerParams(url=config.server_url)
        tools = await mcp_server_tools(server_params)
        print(f"  ✅ Connected to {config.server_url}")
        
        # Create the agent with tools
        agent = AssistantAgent(
            name=config.name,
            model_client=model_client,
            tools=tools,
            system_message=config.system_message
        )
        
        # Create termination conditions
        termination = TextMessageTermination(config.name) | MaxMessageTermination(10)
        
        # Create single-agent team
        team = RoundRobinGroupChat(
            participants=[agent],
            termination_condition=termination
        )
        
        print(f"  ✅ {config.name} team ready")
        return team, config
        
    except Exception as e:
        print(f"  ❌ Failed to setup {config.name}: {e}")
        return None, config

async def run_agent_team(team, config: AgentConfig, task: str) -> Dict[str, Any]:
    """Run a single agent team and collect results"""
    
    print(f"\n🚀 {config.name} starting research...")
    
    messages = []
    tool_calls = []
    
    try:
        async for message in team.run_stream(task=task):
            # Log different message types
            if hasattr(message, 'content'):
                if isinstance(message.content, str):
                    print(f"  💬 {config.name}: {message.content[:100]}...")
                    messages.append(message.content)
                elif isinstance(message.content, list):
                    # Tool calls
                    for item in message.content:
                        if hasattr(item, 'name'):
                            print(f"  🔧 {config.name} calling tool: {item.name}")
                            tool_calls.append(item.name)
        
        print(f"✅ {config.name} completed research")
        
        return {
            "agent": config.name,
            "description": config.description,
            "messages": messages,
            "tool_calls": tool_calls,
            "success": True,
            "final_message": messages[-1] if messages else "No results"
        }
        
    except Exception as e:
        print(f"❌ {config.name} encountered error: {e}")
        return {
            "agent": config.name,
            "description": config.description,
            "messages": [],
            "tool_calls": [],
            "success": False,
            "error": str(e)
        }

async def synthesize_results(user_query: str, agent_results: List[Dict[str, Any]], model_client) -> str:
    """Synthesize all agent results into a final comprehensive report"""
    
    print("\n📊 Synthesizing results from all agents...")
    
    # Build results summary
    results_summary = ""
    for result in agent_results:
        results_summary += f"\n## {result['agent']} ({result['description']})\n"
        results_summary += f"**Success**: {result['success']}\n"
        if result['success']:
            results_summary += f"**Tools Used**: {len(result['tool_calls'])} - {', '.join(result['tool_calls'][:5])}\n"
            results_summary += f"**Key Findings**:\n{result['final_message']}\n"
        else:
            results_summary += f"**Error**: {result.get('error', 'Unknown error')}\n"
    
    prompt = f"""
You are a health data research coordinator. Synthesize the findings from multiple specialized agents into a comprehensive final report.

Original User Query: "{user_query}"

Agent Research Results:
{results_summary}

Create a comprehensive final report that:
1. Provides an executive summary answering the user's query
2. Integrates findings across all data sources
3. Identifies patterns and correlations between environmental, health, and healthcare data
4. Provides actionable insights and recommendations
5. Notes any data limitations or gaps
6. Includes specific data points and statistics from the agents' findings

Structure your response as a well-formatted markdown report with clear sections.
"""
    
    response = await model_client.create([UserMessage(content=prompt, source="user")])
    
    return response.content

async def main():
    # Check for API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ ERROR: ANTHROPIC_API_KEY not found!")
        return
    
    # Initialize model client
    model_client = AnthropicChatCompletionClient(
        model="claude-3-5-sonnet-latest",
        api_key=api_key,
    )
    
    # Example query
    user_query = "What are the current air quality trends in California and how do they relate to respiratory health outcomes and healthcare access?"
    
    print(f"\n{'='*80}")
    print(f"🎯 User Query: {user_query}")
    print(f"{'='*80}")
    
    # Phase 1: Create specialized prompt
    specialized_prompt = await create_specialized_prompt(user_query, model_client)
    
    # Phase 2: Create all agent teams
    print("\n📋 Setting up agent teams...")
    team_configs = []
    
    for config in AGENT_CONFIGS:
        team, agent_config = await create_agent_team(config, model_client, specialized_prompt)
        if team:
            team_configs.append((team, agent_config))
    
    if not team_configs:
        print("❌ No agent teams could be created")
        return
    
    print(f"\n✅ Created {len(team_configs)} agent teams")
    
    # Phase 3: Run all teams in parallel
    print("\n🚀 Running all agents in parallel...")
    print("="*80)
    
    # Create tasks for parallel execution
    tasks = [
        run_agent_team(team, config, specialized_prompt) 
        for team, config in team_configs
    ]
    
    # Run all agents simultaneously
    agent_results = await asyncio.gather(*tasks)
    
    print("\n" + "="*80)
    print("✅ All agents completed")
    
    # Phase 4: Synthesize results
    final_report = await synthesize_results(user_query, agent_results, model_client)
    
    # Save report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)
    report_file = reports_dir / f"parallel_team_research_{timestamp}.md"
    
    with open(report_file, "w") as f:
        f.write(f"# Parallel Agent Research Report\n\n")
        f.write(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**Query**: {user_query}\n\n")
        f.write(f"**Specialized Prompt**: {specialized_prompt}\n\n")
        f.write("---\n\n")
        f.write(final_report)
    
    print(f"\n{'='*80}")
    print(f"📁 Report saved to: {report_file}")
    print(f"{'='*80}\n")
    print("## Final Report Preview:\n")
    print(final_report[:500] + "...\n")
    
    # Cleanup
    await model_client.close()

if __name__ == "__main__":
    asyncio.run(main())
