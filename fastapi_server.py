import asyncio
import json
import logging
from typing import Dict, List, Optional, AsyncGenerator
from dataclasses import dataclass
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from anthropic import Anthropic
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@dataclass
class AgentConfig:
    name: str
    server_url: str
    system_message: str
    description: str

# Updated AGENT_CONFIGS with your new databases
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
        description="🌍 Environmental health and air quality specialist"
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
        description="📊 CDC surveillance and public health data specialist"
    ),
    AgentConfig(
        name="HealthcareAccess_Agent",
        server_url="http://localhost:8891/sse", 
        system_message="""You are a specialized Healthcare Access agent focusing on Healthcare.gov data.
        Focus on:
        - Insurance coverage and accessibility data
        - Provider network information
        - Healthcare marketplace statistics
        - Geographic healthcare access patterns
        
        Use the available Healthcare.gov tools to gather relevant data and provide insights.""",
        description="🏥 Healthcare access and insurance coverage specialist"
    ),
    # NEW: Your MedlinePlus Connect Agent
    AgentConfig(
        name="MedlinePlus_Agent",
        server_url="http://localhost:8892/sse",
        system_message="""You are a Patient Education and Clinical Support specialist focusing on:
        - Patient education materials and health information
        - Clinical decision support and medical terminology
        - Drug information and medication guidance
        - Diagnostic code interpretation (ICD-10, SNOMED CT)
        
        Use MedlinePlus Connect tools to provide authoritative health information.""",
        description="🩺 Patient Education & Clinical Support"
    ),
    # NEW: Your OpenFDA Agent
    AgentConfig(
        name="OpenFDA_Agent",
        server_url="http://localhost:8893/sse",
        system_message="""You are a Drug Safety and FDA Monitoring specialist focusing on:
        - Drug adverse events and safety signals
        - FDA recalls and enforcement actions
        - Medical device safety reports
        - Food safety and contamination issues
        
        Use OpenFDA tools to analyze safety data and regulatory actions.""",
        description="⚠️ Drug Safety & FDA Monitoring"
    )
]

def select_relevant_agents(user_query: str) -> List[str]:
    """Intelligently select which agents are needed based on the query"""
    query_lower = user_query.lower()
    relevant_agents = []
    
    # Environmental health keywords
    if any(word in query_lower for word in ['air quality', 'environmental', 'pollution', 'water', 'climate', 'epht']):
        relevant_agents.append('EPHT_Agent')
    
    # Public health keywords  
    if any(word in query_lower for word in ['covid', 'disease', 'outbreak', 'surveillance', 'mortality', 'cdc']):
        relevant_agents.append('OpenData_Agent')
    
    # Healthcare access keywords
    if any(word in query_lower for word in ['insurance', 'coverage', 'access', 'provider', 'network', 'marketplace']):
        relevant_agents.append('HealthcareAccess_Agent')
    
    # Patient education keywords
    if any(word in query_lower for word in ['patient', 'education', 'treatment', 'symptoms', 'diagnosis', 'medication guide']):
        relevant_agents.append('MedlinePlus_Agent')
    
    # Drug safety keywords
    if any(word in query_lower for word in ['drug', 'adverse', 'recall', 'fda', 'medication', 'safety', 'enforcement']):
        relevant_agents.append('OpenFDA_Agent')
    
    # Fentanyl crisis - uses multiple agents
    if 'fentanyl' in query_lower:
        relevant_agents.extend(['OpenFDA_Agent', 'MedlinePlus_Agent', 'OpenData_Agent'])
    
    # Default: if no specific match, use core agents
    if not relevant_agents:
        relevant_agents = ['EPHT_Agent', 'OpenData_Agent', 'HealthcareAccess_Agent']
    
    # Remove duplicates while preserving order
    return list(dict.fromkeys(relevant_agents))

class HealthGuardOrchestrator:
    def __init__(self):
        self.anthropic = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.agents = {config.name: config for config in AGENT_CONFIGS}
        
    async def create_specialized_prompts(self, user_query: str, selected_agents: List[str]) -> Dict[str, str]:
        """Create specialized research prompts for each selected agent"""
        prompts = {}
        
        coordinator_prompt = f"""
        Given this user query: "{user_query}"
        
        Create specialized research prompts for the following health data agents:
        {', '.join(selected_agents)}
        
        For each agent, create a focused research prompt that:
        1. Directly relates to their data domain
        2. Helps answer the original user query
        3. Is specific and actionable
        
        Return a JSON object with agent names as keys and their specialized prompts as values.
        """
        
        try:
            response = self.anthropic.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1000,
                messages=[{"role": "user", "content": coordinator_prompt}]
            )
            
            # Extract JSON from response
            content = response.content[0].text
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0].strip()
            else:
                json_str = content
                
            prompts = json.loads(json_str)
            
        except Exception as e:
            logger.error(f"Error creating specialized prompts: {e}")
            # Fallback to using original query for all agents
            for agent_name in selected_agents:
                prompts[agent_name] = user_query
                
        return prompts

    async def stream_agent_research(self, agent_name: str, prompt: str) -> AsyncGenerator[str, None]:
        """Stream research results from a specific agent"""
        agent_config = self.agents[agent_name]
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                async with client.stream(
                    "POST",
                    agent_config.server_url,
                    json={"message": prompt},
                    headers={"Accept": "text/plain"}
                ) as response:
                    if response.status_code == 200:
                        async for chunk in response.aiter_text():
                            if chunk.strip():
                                yield f"data: {json.dumps({'agent': agent_name, 'content': chunk, 'type': 'research'})}\n\n"
                    else:
                        error_msg = f"Error from {agent_name}: HTTP {response.status_code}"
                        yield f"data: {json.dumps({'agent': agent_name, 'content': error_msg, 'type': 'error'})}\n\n"
                        
        except Exception as e:
            error_msg = f"Connection error to {agent_name}: {str(e)}"
            logger.error(error_msg)
            yield f"data: {json.dumps({'agent': agent_name, 'content': error_msg, 'type': 'error'})}\n\n"

    async def synthesize_results(self, agent_results: Dict[str, str], original_query: str) -> str:
        """Synthesize all agent results into a comprehensive report"""
        synthesis_prompt = f"""
        Original Query: "{original_query}"
        
        Research Results from Health Data Agents:
        
        {chr(10).join([f"{agent}: {result}" for agent, result in agent_results.items()])}
        
        Create a comprehensive synthesis that:
        1. Directly answers the original query
        2. Integrates findings from all agents
        3. Highlights key insights and correlations
        4. Provides actionable recommendations for public health officials
        5. Maintains scientific accuracy and cites data sources
        
        Format as a professional public health report.
        """
        
        try:
            response = self.anthropic.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2000,
                messages=[{"role": "user", "content": synthesis_prompt}]
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"Error in synthesis: {e}")
            return f"Error synthesizing results: {str(e)}"

orchestrator = HealthGuardOrchestrator()

@app.post("/chat")
async def chat_endpoint(request: Request):
    """Main chat endpoint with intelligent agent selection and parallel processing"""
    try:
        body = await request.json()
        user_query = body.get("message", "")
        
        if not user_query:
            return {"error": "No message provided"}
            
        async def generate_response():
            # Step 1: Select relevant agents based on query
            selected_agents = select_relevant_agents(user_query)
            
            yield f"data: {json.dumps({'type': 'agent_selection', 'agents': selected_agents})}\n\n"
            
            # Step 2: Create specialized prompts
            yield f"data: {json.dumps({'type': 'coordinator', 'content': 'Creating specialized research prompts...'})}\n\n"
            
            specialized_prompts = await orchestrator.create_specialized_prompts(user_query, selected_agents)
            
            # Step 3: Launch parallel agent research
            yield f"data: {json.dumps({'type': 'coordinator', 'content': 'Launching parallel research across selected databases...'})}\n\n"
            
            # Create tasks for parallel execution
            tasks = []
            for agent_name in selected_agents:
                prompt = specialized_prompts.get(agent_name, user_query)
                task = asyncio.create_task(
                    collect_agent_results(agent_name, prompt)
                )
                tasks.append((agent_name, task))
            
            # Stream results as they come in
            agent_results = {}
            completed_agents = set()
            
            while len(completed_agents) < len(selected_agents):
                for agent_name, task in tasks:
                    if agent_name not in completed_agents and task.done():
                        try:
                            result = await task
                            agent_results[agent_name] = result
                            completed_agents.add(agent_name)
                            
                            yield f"data: {json.dumps({'type': 'agent_complete', 'agent': agent_name, 'content': result})}\n\n"
                            
                        except Exception as e:
                            logger.error(f"Error from {agent_name}: {e}")
                            agent_results[agent_name] = f"Error: {str(e)}"
                            completed_agents.add(agent_name)
                
                await asyncio.sleep(0.1)  # Small delay to prevent busy waiting
            
            # Step 4: Synthesize results
            yield f"data: {json.dumps({'type': 'coordinator', 'content': 'Synthesizing comprehensive report...'})}\n\n"
            
            final_synthesis = await orchestrator.synthesize_results(agent_results, user_query)
            
            yield f"data: {json.dumps({'type': 'synthesis', 'content': final_synthesis})}\n\n"
            yield f"data: {json.dumps({'type': 'complete'})}\n\n"
        
        return StreamingResponse(
            generate_response(),
            media_type="text/plain",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
        )
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        return {"error": str(e)}

async def collect_agent_results(agent_name: str, prompt: str) -> str:
    """Collect full results from an agent"""
    full_result = ""
    async for chunk in orchestrator.stream_agent_research(agent_name, prompt):
        try:
            if chunk.startswith("data: "):
                data = json.loads(chunk[6:])
                if data.get('type') == 'research':
                    full_result += data.get('content', '')
        except json.JSONDecodeError:
            continue
    return full_result

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "agents": [config.name for config in AGENT_CONFIGS]}

@app.get("/agents")
async def get_agents():
    """Get available agents and their descriptions"""
    return {
        "agents": [
            {
                "name": config.name,
                "description": config.description,
                "server_url": config.server_url
            }
            for config in AGENT_CONFIGS
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)