import asyncio
import os
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass
from typing import List
from dotenv import load_dotenv

from autogen_core import AgentId, MessageContext, RoutedAgent, SingleThreadedAgentRuntime, message_handler
from autogen_core.models import ChatCompletionClient, SystemMessage, UserMessage
from autogen_ext.models.anthropic import AnthropicChatCompletionClient
from autogen_ext.tools.mcp import mcp_server_tools, SseServerParams

load_dotenv()

# Store report content
report_sections = defaultdict(list)

# Message Protocol for Parallel Agent Communication
@dataclass
class HealthDataTask:
    task: str
    data_source: str  # "epht", "opendata", or "healthcare"
    previous_results: List[str] = None

@dataclass
class HealthDataResult:
    result: str
    data_source: str

@dataclass
class UserHealthTask:
    task: str

@dataclass
class FinalHealthReport:
    result: str

class Logger:
    def __init__(self):
        self.log_dir = Path("logs")
        self.log_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = self.log_dir / f"health_data_agent_log_{timestamp}.md"
        
        # Initialize log file with header
        with open(self.log_file, "w") as f:
            f.write(f"# Health Data Agent Session Log - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
    
    def log(self, content: str, level: str = "info"):
        """Log content to file with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        with open(self.log_file, "a") as f:
            f.write(f"**[{timestamp}] {level.upper()}**\n\n{content}\n\n")

# CDC EPHT Worker Agent
class CDCEPHTAgent(RoutedAgent):
    def __init__(self, model_client: ChatCompletionClient, tools):
        super().__init__(description="CDC EPHT Agent")
        self._model_client = model_client
        self._tools = tools

    @message_handler
    async def handle_task(self, message: HealthDataTask, ctx: MessageContext) -> HealthDataResult:
        system_prompt = """You are a specialized CDC Environmental Public Health Tracking (EPHT) agent.
        Focus on environmental health data including:
        - Air quality measurements (PM2.5, ozone, air toxics)
        - Environmental health outcomes
        - Community health profiles
        - Geographic and temporal analysis of environmental factors
        
        Use the available EPHT tools to gather relevant data and provide insights."""
        
        # Create messages for the model
        messages = [SystemMessage(content=system_prompt)]
        if message.previous_results:
            context = "Previous analysis from other data sources:\n" + "\n\n".join(message.previous_results)
            messages.append(UserMessage(content=f"{context}\n\nTask: {message.task}", source="user"))
        else:
            messages.append(UserMessage(content=message.task, source="user"))
        
        model_result = await self._model_client.create(messages)
        assert isinstance(model_result.content, str)
        
        print(f"{'-'*80}\nCDC EPHT Agent:\n{model_result.content}")
        return HealthDataResult(result=model_result.content, data_source="epht")

# CDC Open Data Worker Agent  
class CDCOpenDataAgent(RoutedAgent):
    def __init__(self, model_client: ChatCompletionClient, tools):
        super().__init__(description="CDC Open Data Agent")
        self._model_client = model_client
        self._tools = tools

    @message_handler
    async def handle_task(self, message: HealthDataTask, ctx: MessageContext) -> HealthDataResult:
        system_prompt = """You are a specialized CDC Open Data agent.
        Focus on:
        - COVID-19 surveillance data
        - General health surveillance datasets
        - Disease outbreak and monitoring data
        - Public health statistics and trends
        
        Use the available CDC Open Data tools to gather relevant data and provide insights."""
        
        messages = [SystemMessage(content=system_prompt)]
        if message.previous_results:
            context = "Previous analysis from other data sources:\n" + "\n\n".join(message.previous_results)
            messages.append(UserMessage(content=f"{context}\n\nTask: {message.task}", source="user"))
        else:
            messages.append(UserMessage(content=message.task, source="user"))
        
        model_result = await self._model_client.create(messages)
        assert isinstance(model_result.content, str)
        
        print(f"{'-'*80}\nCDC Open Data Agent:\n{model_result.content}")
        return HealthDataResult(result=model_result.content, data_source="opendata")

# Healthcare.gov Worker Agent
class HealthcareGovAgent(RoutedAgent):
    def __init__(self, model_client: ChatCompletionClient, tools):
        super().__init__(description="Healthcare.gov Agent")
        self._model_client = model_client
        self._tools = tools

    @message_handler
    async def handle_task(self, message: HealthDataTask, ctx: MessageContext) -> HealthDataResult:
        system_prompt = """You are a specialized Healthcare.gov agent.
        Focus on:
        - Healthcare marketplace plans and coverage
        - Provider networks and facility data
        - Healthcare accessibility analysis
        - Insurance coverage patterns and trends
        
        Use the available Healthcare.gov tools to gather relevant data and provide insights."""
        
        messages = [SystemMessage(content=system_prompt)]
        if message.previous_results:
            context = "Previous analysis from other data sources:\n" + "\n\n".join(message.previous_results)
            messages.append(UserMessage(content=f"{context}\n\nTask: {message.task}", source="user"))
        else:
            messages.append(UserMessage(content=message.task, source="user"))
        
        model_result = await self._model_client.create(messages)
        assert isinstance(model_result.content, str)
        
        print(f"{'-'*80}\nHealthcare.gov Agent:\n{model_result.content}")
        return HealthDataResult(result=model_result.content, data_source="healthcare")

# Orchestrator Agent
class OrchestratorAgent(RoutedAgent):
    def __init__(self, model_client: ChatCompletionClient, num_layers: int = 2):
        super().__init__(description="Health Data Orchestrator Agent")
        self._model_client = model_client
        self._num_layers = num_layers

    @message_handler
    async def handle_task(self, message: UserHealthTask, ctx: MessageContext) -> FinalHealthReport:
        print(f"{'-'*80}\nOrchestrator:\nReceived task: {message.task}")
        
        # Create task for the first layer (parallel execution)
        worker_task = HealthDataTask(task=message.task, data_source="all", previous_results=[])
        
        # Execute multiple layers if specified
        for layer in range(self._num_layers - 1):
            print(f"{'-'*80}\nOrchestrator:\nDispatch to workers at layer {layer}")
            
            # Create worker agent IDs for parallel execution
            worker_ids = [
                AgentId("cdc_epht", f"layer_{layer}/epht"),
                AgentId("cdc_opendata", f"layer_{layer}/opendata"), 
                AgentId("healthcare_gov", f"layer_{layer}/healthcare")
            ]
            
            # Dispatch tasks to all workers in parallel
            results = await asyncio.gather(*[
                self.send_message(worker_task, worker_id) for worker_id in worker_ids
            ])
            
            print(f"{'-'*80}\nOrchestrator:\nReceived results from workers at layer {layer}")
            
            # Prepare task for next layer with previous results
            worker_task = HealthDataTask(
                task=message.task, 
                data_source="all",
                previous_results=[r.result for r in results]
            )
        
        # Perform final aggregation
        print(f"{'-'*80}\nOrchestrator:\nPerforming final aggregation")
        
        system_prompt = """You are a health data research orchestrator. You have received comprehensive analysis from specialized agents covering:
        1. CDC Environmental Public Health Tracking (EPHT) data
        2. CDC Open Data and surveillance information  
        3. Healthcare.gov marketplace and access data
        
        Your task is to synthesize these responses into a single, comprehensive health data report. 
        Critically evaluate the information, identify patterns and correlations across data sources, 
        and provide actionable insights. Structure your response with clear sections and recommendations.
        
        Analysis from specialized agents:"""
        
        system_prompt += "\n" + "\n\n".join([f"{i+1}. {r}" for i, r in enumerate(worker_task.previous_results)])
        
        model_result = await self._model_client.create([
            SystemMessage(content=system_prompt),
            UserMessage(content=message.task, source="user")
        ])
        
        assert isinstance(model_result.content, str)
        return FinalHealthReport(result=model_result.content)

async def main():
    # Initialize logger
    logger = Logger()
    
    # Connect to separate MCP servers for each data source
    logger.log("Connecting to CDC EPHT MCP server...")
    epht_server_params = SseServerParams(url="http://localhost:8889/sse")
    epht_tools = await mcp_server_tools(epht_server_params)
    
    logger.log("Connecting to CDC Open Data MCP server...")
    opendata_server_params = SseServerParams(url="http://localhost:8890/sse")
    opendata_tools = await mcp_server_tools(opendata_server_params)
    
    logger.log("Connecting to Healthcare.gov MCP server...")
    healthcare_server_params = SseServerParams(url="http://localhost:8891/sse")
    healthcare_tools = await mcp_server_tools(healthcare_server_params)
    
    # Check for API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        logger.log("ERROR: ANTHROPIC_API_KEY not found in environment variables!", "error")
        print("❌ ERROR: ANTHROPIC_API_KEY not found!")
        print("Please:")
        print("1. Copy .env.example to .env")
        print("2. Add your Anthropic API key to the .env file")
        print("3. Run the script again")
        return
    
    # Initialize LLM client with API key
    llm_client = AnthropicChatCompletionClient(
        model="claude-3-5-sonnet-latest",
        api_key=api_key,
        model_capabilities={
            "json_output": False,
            "vision": False,
            "function_calling": True,
            "structured_output": False
        },
    )
    
    logger.log(f"Initialized Anthropic client with model: claude-3-5-sonnet-latest")
    
    # Set up the runtime for parallel agent execution
    runtime = SingleThreadedAgentRuntime()
    
    # Register worker agents with their specialized tools
    await CDCEPHTAgent.register(
        runtime, 
        "cdc_epht", 
        lambda: CDCEPHTAgent(model_client=llm_client, tools=epht_tools)
    )
    
    await CDCOpenDataAgent.register(
        runtime,
        "cdc_opendata", 
        lambda: CDCOpenDataAgent(model_client=llm_client, tools=opendata_tools)
    )
    
    await HealthcareGovAgent.register(
        runtime,
        "healthcare_gov",
        lambda: HealthcareGovAgent(model_client=llm_client, tools=healthcare_tools)
    )
    
    # Register orchestrator agent
    await OrchestratorAgent.register(
        runtime,
        "orchestrator",
        lambda: OrchestratorAgent(model_client=llm_client, num_layers=2)
    )
    
    # Start the runtime
    runtime.start()
    
    # Example task - this can be customized based on research needs
    task = """Analyze environmental health data and public health trends for a comprehensive health assessment. 
    Include air quality data, COVID-19 trends, and healthcare access information. 
    Focus on identifying key health patterns and environmental factors affecting public health."""
    
    logger.log("Starting parallel health data research...")
    print("🚀 Starting Health Data Research with Parallel Agent Execution")
    print("=" * 80)
    
    # Send task to orchestrator which will coordinate parallel execution
    result = await runtime.send_message(
        UserHealthTask(task=task), 
        AgentId("orchestrator", "default")
    )
    
    # Stop the runtime
    await runtime.stop_when_idle()
    
    # Close the model client connection
    await llm_client.close()
    
    # Save the final report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)
    report_file = reports_dir / f"parallel_health_data_research_{timestamp}.md"
    
    with open(report_file, "w") as f:
        f.write(f"# Parallel Health Data Research Report\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**Task:** {task}\n\n")
        f.write("## Final Analysis\n\n")
        f.write(result.result)
    
    print(f"\n{'='*80}")
    print(f"📊 Final Report:")
    print(f"📁 Saved to: {report_file}")
    print(f"{'='*80}")
    print(result.result)
    
    logger.log("Parallel Health Data Research completed successfully!")
    logger.log(f"Report saved to: {report_file}")

if __name__ == "__main__":
    asyncio.run(main())
