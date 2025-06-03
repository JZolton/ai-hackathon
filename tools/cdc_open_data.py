import logging
import aiohttp
import json
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Any, Union
from fastmcp import FastMCP
from pydantic import Field
from urllib.parse import urlencode, quote

logger = logging.getLogger(__name__)

# CDC API endpoints
ENDPOINTS = {
    "open_data": "https://data.cdc.gov"
}

# Common dataset identifiers for Open Data API
COMMON_DATASETS = {
    "nndss_weekly": "x9gk-5huc",
    "covid_deaths_provisional": "9bhg-hcku",
    "flu_surveillance": "pk7k-8jbr",
    "chronic_disease": "g4ie-h725",
    "behavioral_risk": "dttw-5yxu",
    "birth_data": "3h58-x6cd",
    "mortality_data": "bi63-dtpu",
    "cancer_statistics": "hiyb-xunq",
    "diabetes_surveillance": "37jh-ykv3",
    "heart_disease": "6x7h-usvx"
}




async def search_open_data(
    dataset_id: Optional[str] = Field(default=None, description="Specific dataset ID (e.g., '9mfq-cb36' for COVID cases)"),
    query: Optional[str] = Field(default=None, description="Search query text"),
    limit: int = Field(default=100, description="Maximum number of records to return"),
    offset: int = Field(default=0, description="Number of records to skip"),
    format: str = Field(default="json", description="Response format: json, xml, or csv")
) -> Dict[str, Any]:
    """Search CDC Open Data repository using Socrata API"""
    
    if dataset_id:
        # Query specific dataset
        url = f"{ENDPOINTS['open_data']}/resource/{dataset_id}.{format}"
        params = {
            "$limit": limit,
            "$offset": offset
        }
        if query:
            params["$q"] = query
    else:
        # Search across all datasets
        url = f"{ENDPOINTS['open_data']}/api/catalog/v1"
        params = {
            "limit": limit,
            "offset": offset
        }
        if query:
            params["q"] = query
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status == 200:
                    if format == "json":
                        data = await response.json()
                        return {
                            "status": "success",
                            "data": data,
                            "query_info": {
                                "dataset_id": dataset_id,
                                "query": query,
                                "limit": limit,
                                "offset": offset,
                                "url": str(response.url)
                            }
                        }
                    else:
                        text_data = await response.text()
                        return {
                            "status": "success",
                            "data": text_data,
                            "format": format,
                            "query_info": {
                                "dataset_id": dataset_id,
                                "query": query,
                                "limit": limit,
                                "offset": offset
                            }
                        }
                else:
                    error_text = await response.text()
                    return {
                        "status": "error",
                        "error": f"API request failed with status {response.status}",
                        "details": error_text[:500]
                    }
        except Exception as e:
            return {
                "status": "error",
                "error": f"Request failed: {str(e)}"
            }


async def get_common_datasets() -> Dict[str, Any]:
    """Get list of commonly used CDC datasets with their IDs"""
    return {
        "status": "success",
        "datasets": [
            {
                "id": dataset_id,
                "name": name.replace("_", " ").title(),
                "description": f"CDC {name.replace('_', ' ')} data"
            }
            for name, dataset_id in COMMON_DATASETS.items()
        ],
        "note": "Use these IDs with search_open_data to query specific datasets"
    }




async def search_covid_data(
    state: Optional[str] = Field(default=None, description="State name or abbreviation"),
    date_range: Optional[str] = Field(default=None, description="Date range in format 'YYYY-MM-DD/YYYY-MM-DD'"),
    data_type: str = Field(default="cases", description="Data type: cases, deaths, or hospitalizations"),
    limit: int = Field(default=1000, description="Maximum number of records")
) -> Dict[str, Any]:
    """Search COVID-19 data from CDC Open Data"""
    
    # Map data types to dataset IDs
    dataset_mapping = {
        "cases": "9mfq-cb36",
        "deaths": "r8kw-7aab",
        "hospitalizations": "g62h-syeh"
    }
    
    dataset_id = dataset_mapping.get(data_type, "9mfq-cb36")
    url = f"{ENDPOINTS['open_data']}/resource/{dataset_id}.json"
    
    params = {"$limit": limit}
    
    # Build query conditions
    where_conditions = []
    if state:
        where_conditions.append(f"state = '{state.upper()}'")
    if date_range and "/" in date_range:
        start_date, end_date = date_range.split("/")
        where_conditions.append(f"submission_date between '{start_date}T00:00:00.000' and '{end_date}T23:59:59.999'")
    
    if where_conditions:
        params["$where"] = " AND ".join(where_conditions)
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "status": "success",
                        "data": data,
                        "data_type": data_type,
                        "record_count": len(data),
                        "query_info": {
                            "state": state,
                            "date_range": date_range,
                            "dataset_id": dataset_id
                        }
                    }
                else:
                    error_text = await response.text()
                    return {
                        "status": "error",
                        "error": f"API request failed with status {response.status}",
                        "details": error_text[:500]
                    }
        except Exception as e:
            return {
                "status": "error",
                "error": f"Request failed: {str(e)}"
            }


async def test_api_endpoints() -> Dict[str, Any]:
    """Test connectivity to CDC Open Data API"""
    
    results = {}
    
    async with aiohttp.ClientSession() as session:
        # Test Open Data API
        try:
            async with session.get(f"{ENDPOINTS['open_data']}/api/catalog/v1?limit=1", timeout=aiohttp.ClientTimeout(total=10)) as response:
                results["open_data"] = {
                    "status": "success" if response.status == 200 else "error",
                    "status_code": response.status,
                    "endpoint": ENDPOINTS['open_data']
                }
        except Exception as e:
            results["open_data"] = {
                "status": "error",
                "error": str(e),
                "endpoint": ENDPOINTS['open_data']
            }
    
    # Summary
    working_apis = sum(1 for result in results.values() if result["status"] == "success")
    total_apis = len(results)
    
    return {
        "summary": f"{working_apis}/{total_apis} APIs responding",
        "results": results,
        "timestamp": "2025-06-03T15:15:00Z"
    }


async def get_api_documentation() -> Dict[str, Any]:
    """Get documentation links and information for CDC Open Data API"""
    return {
        "apis": [
            {
                "name": "Open Data",
                "endpoint": ENDPOINTS['open_data'],
                "documentation": "https://dev.socrata.com/docs/endpoints.html",
                "description": "Repository of all available CDC datasets with Socrata Open Data API",
                "formats": ["json", "xml", "csv"],
                "architecture": "REST"
            }
        ],
        "guidance": {
            "name": "API Guidance",
            "documentation": "https://publichealthsurveillance.atlassian.net/wiki/spaces/STA/pages/478969857/REST+API+Guidance+-+Version+1.1",
            "description": "CDC's Surveillance Data Platform program guidance on RESTful API design"
        }
    }


def register_cdc_open_data_tools(mcp: FastMCP) -> None:
    """Register CDC Open Data tools with the MCP server."""
    mcp.tool()(search_open_data)
    mcp.tool()(get_common_datasets)
    mcp.tool()(search_covid_data)
    mcp.tool()(test_api_endpoints)
    mcp.tool()(get_api_documentation)
