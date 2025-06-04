import asyncio
import os
import json
import tiktoken
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, AsyncGenerator
from dataclasses import dataclass
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.conditions import TextMessageTermination, MaxMessageTermination
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_ext.models.anthropic import AnthropicChatCompletionClient
from autogen_ext.tools.mcp import mcp_server_tools, SseServerParams
from autogen_core.models import UserMessage

load_dotenv()

app = FastAPI()

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request model
class ChatRequest(BaseModel):
    query: str

# Event types for streaming
class EventType:
    AGENT_MESSAGE = "agent_message"
    TOOL_CALL = "tool_call"
    TOOL_RESPONSE = "tool_response"
    PHASE_UPDATE = "phase_update"
    FINAL_REPORT = "final_report"
    ERROR = "error"

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

def create_event(event_type: str, agent: str, content: Any) -> str:
    """Create a server-sent event formatted string"""
    event_data = {
        "type": event_type,
        "agent": agent,
        "content": content,
        "timestamp": datetime.now().isoformat()
    }
    return f"data: {json.dumps(event_data)}\n\n"

def count_tokens(text: str) -> int:
    """Count tokens in text using tiktoken"""
    try:
        encoding = tiktoken.encoding_for_model("claude-3-5-sonnet-20241022")
        return len(encoding.encode(text))
    except Exception:
        # Fallback: rough estimate (1 token ≈ 4 characters)
        return len(text) // 4

def truncate_prompt(prompt: str, max_tokens: int = 180000) -> str:
    """Truncate prompt to stay under token limit with safety margin"""
    current_tokens = count_tokens(prompt)
    
    if current_tokens <= max_tokens:
        return prompt
    
    # Calculate rough character limit based on token ratio
    char_per_token = len(prompt) / current_tokens
    target_chars = int(max_tokens * char_per_token * 0.9)  # 10% safety margin
    
    # Truncate and add notice
    truncated = prompt[:target_chars]
    truncated += f"\n\n[Note: Prompt truncated from {current_tokens} to ~{max_tokens} tokens due to length limits]"
    
    return truncated

async def safe_llm_call(model_client, prompt: str, max_retries: int = 3) -> str:
    """Make LLM call with token checking and retries"""
    
    # Check and truncate if needed
    truncated_prompt = truncate_prompt(prompt)
    
    for attempt in range(max_retries):
        try:
            response = await model_client.create([UserMessage(content=truncated_prompt, source="user")])
            return response.content.strip()
        
        except Exception as e:
            error_msg = str(e).lower()
            
            if "too long" in error_msg or "token" in error_msg:
                # Further reduce token count
                current_tokens = count_tokens(truncated_prompt)
                new_limit = int(current_tokens * 0.8)  # Reduce by 20%
                truncated_prompt = truncate_prompt(truncated_prompt, new_limit)
                print(f"Attempt {attempt + 1}: Reducing prompt to ~{new_limit} tokens")
                
            elif attempt == max_retries - 1:
                # Last attempt failed
                raise e
            else:
                # Other error, wait and retry
                await asyncio.sleep(1)
                print(f"Attempt {attempt + 1} failed: {e}. Retrying...")
    
    raise Exception("Max retries exceeded")

async def create_specialized_prompt(user_query: str, model_client) -> str:
    """Create a specialized prompt for all agents based on the user query"""
    
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
    
    return await safe_llm_call(model_client, prompt)

async def create_agent_team(config: AgentConfig, model_client):
    """Create a single-agent team for a specific data source"""
    
    try:
        # Connect to MCP server
        server_params = SseServerParams(url=config.server_url)
        tools = await mcp_server_tools(server_params)
        
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
        
        return team, config
        
    except Exception as e:
        print(f"Failed to setup {config.name}: {e}")
        return None, config

async def run_agent_team_with_streaming(
    team, 
    config: AgentConfig, 
    task: str,
    event_queue: asyncio.Queue
) -> Dict[str, Any]:
    """Run a single agent team and stream events"""
    
    await event_queue.put(create_event(
        EventType.PHASE_UPDATE,
        config.name,
        f"{config.name} starting research..."
    ))
    
    messages = []
    tool_calls = []
    
    try:
        async for message in team.run_stream(task=task):
            # Handle different message types
            if hasattr(message, 'content'):
                if isinstance(message.content, str):
                    # Regular message
                    await event_queue.put(create_event(
                        EventType.AGENT_MESSAGE,
                        config.name,
                        message.content
                    ))
                    messages.append(message.content)
                elif isinstance(message.content, list):
                    # Tool calls or responses
                    for item in message.content:
                        if hasattr(item, 'name'):
                            # Tool call
                            await event_queue.put(create_event(
                                EventType.TOOL_CALL,
                                config.name,
                                {"tool": item.name, "args": getattr(item, 'args', {})}
                            ))
                            tool_calls.append(item.name)
                        elif hasattr(item, 'type') and item.type == 'text':
                            # Tool response
                            await event_queue.put(create_event(
                                EventType.TOOL_RESPONSE,
                                config.name,
                                item.text
                            ))
        
        await event_queue.put(create_event(
            EventType.PHASE_UPDATE,
            config.name,
            f"{config.name} completed research"
        ))
        
        return {
            "agent": config.name,
            "description": config.description,
            "messages": messages,
            "tool_calls": tool_calls,
            "success": True,
            "final_message": messages[-1] if messages else "No results"
        }
        
    except Exception as e:
        await event_queue.put(create_event(
            EventType.ERROR,
            config.name,
            str(e)
        ))
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
    
    return await safe_llm_call(model_client, prompt)

async def process_query(query: str, event_queue: asyncio.Queue):
    """Process a user query and stream events"""
    
    # Check for API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        await event_queue.put(create_event(
            EventType.ERROR,
            "system",
            "ANTHROPIC_API_KEY not found in environment variables"
        ))
        return
    
    # Initialize model client
    model_client = AnthropicChatCompletionClient(
        model="claude-3-5-sonnet-latest",
        api_key=api_key,
    )
    
    try:
        # Phase 1: Create specialized prompt
        await event_queue.put(create_event(
            EventType.PHASE_UPDATE,
            "coordinator",
            "Creating specialized research prompt..."
        ))
        
        specialized_prompt = await create_specialized_prompt(query, model_client)
        
        await event_queue.put(create_event(
            EventType.AGENT_MESSAGE,
            "coordinator",
            f"Research prompt: {specialized_prompt}"
        ))
        
        # Phase 2: Create all agent teams
        await event_queue.put(create_event(
            EventType.PHASE_UPDATE,
            "system",
            "Setting up agent teams..."
        ))
        
        team_configs = []
        for config in AGENT_CONFIGS:
            team, agent_config = await create_agent_team(config, model_client)
            if team:
                team_configs.append((team, agent_config))
        
        if not team_configs:
            await event_queue.put(create_event(
                EventType.ERROR,
                "system",
                "No agent teams could be created"
            ))
            return
        
        # Phase 3: Run all teams in parallel
        await event_queue.put(create_event(
            EventType.PHASE_UPDATE,
            "system",
            "Running all agents in parallel..."
        ))
        
        # Create tasks for parallel execution
        tasks = [
            run_agent_team_with_streaming(team, config, specialized_prompt, event_queue) 
            for team, config in team_configs
        ]
        
        # Run all agents simultaneously
        agent_results = await asyncio.gather(*tasks)
        
        # Phase 4: Synthesize results
        await event_queue.put(create_event(
            EventType.PHASE_UPDATE,
            "coordinator",
            "Synthesizing results from all agents..."
        ))
        
        final_report = await synthesize_results(query, agent_results, model_client)
        
        # Send final report
        await event_queue.put(create_event(
            EventType.FINAL_REPORT,
            "coordinator",
            final_report
        ))
        
        # Save report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        reports_dir = Path("reports")
        reports_dir.mkdir(exist_ok=True)
        report_file = reports_dir / f"api_research_{timestamp}.md"
        
        with open(report_file, "w") as f:
            f.write(f"# Health Data Research Report\n\n")
            f.write(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"**Query**: {query}\n\n")
            f.write(f"**Specialized Prompt**: {specialized_prompt}\n\n")
            f.write("---\n\n")
            f.write(final_report)
        
    except Exception as e:
        await event_queue.put(create_event(
            EventType.ERROR,
            "system",
            f"System error: {str(e)}"
        ))
    finally:
        # Cleanup
        await model_client.close()

async def event_generator(query: str) -> AsyncGenerator[str, None]:
    """Generate server-sent events for the query processing"""
    
    # Create a queue for events
    event_queue = asyncio.Queue()
    
    # Start processing in background
    process_task = asyncio.create_task(process_query(query, event_queue))
    
    # Stream events as they come
    while True:
        try:
            # Wait for events with timeout
            event = await asyncio.wait_for(event_queue.get(), timeout=0.5)
            yield event
            
            # Check if this was the final report
            event_data = json.loads(event.split("data: ")[1].strip())
            if event_data["type"] == EventType.FINAL_REPORT:
                break
                
        except asyncio.TimeoutError:
            # Check if processing is done
            if process_task.done():
                break
            # Send keepalive
            yield ": keepalive\n\n"
    
    # Ensure task is complete
    await process_task

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """Stream chat responses for a user query"""
    
    return StreamingResponse(
        event_generator(request.query),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable Nginx buffering
        }
    )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
