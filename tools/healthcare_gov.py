import logging
import aiohttp
import json
from typing import Dict, List, Optional, Any, Union
from fastmcp import FastMCP
from pydantic import Field
from urllib.parse import urlencode, quote

logger = logging.getLogger(__name__)

# Data.Healthcare.gov API base URL
BASE_URL = "https://data.healthcare.gov/api/1"

# Common healthcare dataset categories
HEALTHCARE_CATEGORIES = {
    "marketplace": "Health Insurance Marketplace data",
    "quality": "Healthcare quality measures",
    "costs": "Healthcare costs and pricing",
    "providers": "Healthcare provider information",
    "outcomes": "Health outcomes and statistics",
    "access": "Healthcare access and availability",
    "demographics": "Healthcare demographics",
    "insurance": "Insurance coverage data"
}



async def get_all_schemas() -> Dict[str, Any]:
    """Get list of all schemas available in the metastore"""
    
    url = f"{BASE_URL}/metastore/schemas"
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "status": "success",
                        "schemas": data,
                        "count": len(data) if isinstance(data, list) else None
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


async def get_schema_details(
    schema_id: str = Field(description="Schema ID (e.g., 'dataset', 'distribution')")
) -> Dict[str, Any]:
    """Get details for a specific schema"""
    
    url = f"{BASE_URL}/metastore/schemas/{schema_id}"
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "status": "success",
                        "schema": data,
                        "schema_id": schema_id
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


async def get_schema_items(
    schema_id: str = Field(description="Schema ID (e.g., 'dataset')"),
    limit: Optional[int] = None,
    offset: Optional[int] = None
) -> Dict[str, Any]:
    """Get all items for a specific schema (e.g., all datasets)"""
    
    url = f"{BASE_URL}/metastore/schemas/{schema_id}/items"
    params = {}
    
    if limit is not None:
        params["limit"] = limit
    if offset is not None:
        params["offset"] = offset
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "status": "success",
                        "items": data,
                        "schema_id": schema_id,
                        "count": len(data) if isinstance(data, list) else None,
                        "query_params": params
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


async def get_dataset(
    identifier: str = Field(description="Dataset identifier/ID")
) -> Dict[str, Any]:
    """Get a single dataset by its identifier"""
    
    url = f"{BASE_URL}/metastore/schemas/dataset/items/{identifier}"
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "status": "success",
                        "dataset": data,
                        "identifier": identifier
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


async def search_catalog(
    query: Optional[str] = None,
    facets: Optional[List[str]] = None,
    limit: int = 20,
    offset: int = 0
) -> Dict[str, Any]:
    """Search the healthcare data catalog"""
    
    url = f"{BASE_URL}/search"
    params = {
        "limit": limit,
        "offset": offset
    }
    
    if query:
        params["query"] = query
    if facets:
        # Ensure facets is a list before joining
        if isinstance(facets, list):
            params["facets"] = ",".join(facets)
        else:
            params["facets"] = str(facets)
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "status": "success",
                        "results": data,
                        "query_info": {
                            "query": query,
                            "facets": facets,
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


async def get_search_facets() -> Dict[str, Any]:
    """Retrieve search facet information for filtering"""
    
    url = f"{BASE_URL}/search/facets"
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "status": "success",
                        "facets": data
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


async def query_datastore(
    distribution_id: Optional[str] = None,
    dataset_id: Optional[str] = None,
    index: Optional[int] = None,
    conditions: Optional[Dict[str, Any]] = None,
    limit: int = 100,
    offset: int = 0,
    format: str = "json"
) -> Dict[str, Any]:
    """Query datastore resources with flexible parameters"""
    
    # Determine the appropriate endpoint
    if distribution_id:
        url = f"{BASE_URL}/datastore/query/{distribution_id}"
    elif dataset_id and index is not None:
        url = f"{BASE_URL}/datastore/query/{dataset_id}/{index}"
    else:
        url = f"{BASE_URL}/datastore/query"
    
    # Build query parameters
    query_params = {
        "limit": limit,
        "offset": offset,
        "format": format
    }
    
    # Add conditions if provided
    if conditions and isinstance(conditions, dict):
        for key, value in conditions.items():
            query_params[key] = value
    
    async with aiohttp.ClientSession() as session:
        try:
            # Use GET request with parameters
            async with session.get(url, params=query_params, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status == 200:
                    if format.lower() == "json":
                        data = await response.json()
                    else:
                        data = await response.text()
                    
                    return {
                        "status": "success",
                        "data": data,
                        "query_info": {
                            "distribution_id": distribution_id,
                            "dataset_id": dataset_id,
                            "index": index,
                            "conditions": conditions,
                            "limit": limit,
                            "offset": offset,
                            "format": format,
                            "url": str(response.url)
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


async def sql_query_datastore(
    query: str = Field(description="SQL query to execute"),
    limit: int = 100
) -> Dict[str, Any]:
    """Execute SQL query against the datastore"""
    
    url = f"{BASE_URL}/datastore/sql"
    params = {
        "query": query,
        "limit": limit
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "status": "success",
                        "results": data,
                        "query": query,
                        "limit": limit
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


async def get_datastore_import_stats(
    identifier: str = Field(description="Import identifier")
) -> Dict[str, Any]:
    """Get datastore import statistics for a specific identifier"""
    
    url = f"{BASE_URL}/datastore/imports/{identifier}"
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "status": "success",
                        "import_stats": data,
                        "identifier": identifier
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


async def search_healthcare_topics(
    topic: str = Field(description="Healthcare topic to search for (e.g., 'marketplace', 'quality', 'costs')")
) -> Dict[str, Any]:
    """Search for datasets related to specific healthcare topics"""
    
    # Map topic to search terms
    topic_keywords = {
        "marketplace": ["marketplace", "insurance", "plans", "enrollment"],
        "quality": ["quality", "measures", "ratings", "performance"],
        "costs": ["cost", "price", "premium", "deductible", "copay"],
        "providers": ["provider", "hospital", "physician", "facility"],
        "outcomes": ["outcomes", "mortality", "readmission", "safety"],
        "access": ["access", "availability", "network", "coverage"],
        "demographics": ["demographics", "population", "age", "gender"],
        "insurance": ["insurance", "coverage", "benefits", "plans"]
    }
    
    search_terms = topic_keywords.get(topic.lower(), [topic])
    # Ensure search_terms is always a list
    if not isinstance(search_terms, list):
        search_terms = [str(search_terms)]
    
    query = " OR ".join(search_terms)
    
    # Call search_catalog directly with explicit parameters
    url = f"{BASE_URL}/search"
    params = {
        "query": query,
        "limit": 10,
        "offset": 0
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "status": "success",
                        "results": data,
                        "query_info": {
                            "topic": topic,
                            "search_terms": search_terms,
                            "query": query,
                            "limit": 10,
                            "offset": 0
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


async def get_healthcare_categories() -> Dict[str, Any]:
    """Get list of common healthcare data categories"""
    return {
        "status": "success",
        "categories": [
            {
                "name": category,
                "description": description
            }
            for category, description in HEALTHCARE_CATEGORIES.items()
        ],
        "note": "Use these categories with search_healthcare_topics"
    }


async def test_healthcare_api() -> Dict[str, Any]:
    """Test connectivity to the Data.Healthcare.gov API"""
    
    results = {}
    
    async with aiohttp.ClientSession() as session:
        # Test schemas endpoint
        try:
            async with session.get(f"{BASE_URL}/metastore/schemas", timeout=aiohttp.ClientTimeout(total=10)) as response:
                results["schemas"] = {
                    "status": "success" if response.status == 200 else "error",
                    "status_code": response.status,
                    "endpoint": f"{BASE_URL}/metastore/schemas"
                }
        except Exception as e:
            results["schemas"] = {
                "status": "error",
                "error": str(e),
                "endpoint": f"{BASE_URL}/metastore/schemas"
            }
        
        # Test search endpoint
        try:
            async with session.get(f"{BASE_URL}/search?limit=1", timeout=aiohttp.ClientTimeout(total=10)) as response:
                results["search"] = {
                    "status": "success" if response.status == 200 else "error",
                    "status_code": response.status,
                    "endpoint": f"{BASE_URL}/search"
                }
        except Exception as e:
            results["search"] = {
                "status": "error",
                "error": str(e),
                "endpoint": f"{BASE_URL}/search"
            }
        
        # Test facets endpoint
        try:
            async with session.get(f"{BASE_URL}/search/facets", timeout=aiohttp.ClientTimeout(total=10)) as response:
                results["facets"] = {
                    "status": "success" if response.status == 200 else "error",
                    "status_code": response.status,
                    "endpoint": f"{BASE_URL}/search/facets"
                }
        except Exception as e:
            results["facets"] = {
                "status": "error",
                "error": str(e),
                "endpoint": f"{BASE_URL}/search/facets"
            }
    
    # Summary
    working_endpoints = sum(1 for result in results.values() if result["status"] == "success")
    total_endpoints = len(results)
    
    return {
        "summary": f"{working_endpoints}/{total_endpoints} endpoints responding",
        "results": results,
        "base_url": BASE_URL
    }


async def get_api_documentation() -> Dict[str, Any]:
    """Get comprehensive API documentation and endpoint information"""
    return {
        "api_info": {
            "name": "Data.Healthcare.gov API",
            "base_url": BASE_URL,
            "version": "v1",
            "documentation": "https://data.healthcare.gov/api",
            "description": "API for accessing healthcare data from Data.Healthcare.gov"
        },
        "endpoints": {
            "metastore": {
                "schemas": f"{BASE_URL}/metastore/schemas",
                "schema_details": f"{BASE_URL}/metastore/schemas/{{schema_id}}",
                "schema_items": f"{BASE_URL}/metastore/schemas/{{schema_id}}/items",
                "dataset": f"{BASE_URL}/metastore/schemas/dataset/items/{{identifier}}"
            },
            "datastore": {
                "query": f"{BASE_URL}/datastore/query",
                "query_distribution": f"{BASE_URL}/datastore/query/{{distributionId}}",
                "query_dataset": f"{BASE_URL}/datastore/query/{{datasetId}}/{{index}}",
                "sql": f"{BASE_URL}/datastore/sql",
                "imports": f"{BASE_URL}/datastore/imports/{{identifier}}"
            },
            "search": {
                "catalog": f"{BASE_URL}/search",
                "facets": f"{BASE_URL}/search/facets"
            }
        },
        "data_categories": HEALTHCARE_CATEGORIES
    }


def register_healthcare_gov_tools(mcp: FastMCP) -> None:
    """Register all Healthcare.gov tools with the MCP server."""
    mcp.tool()(get_all_schemas)
    mcp.tool()(get_schema_details)
    mcp.tool()(get_schema_items)
    mcp.tool()(get_dataset)
    mcp.tool()(search_catalog)
    mcp.tool()(get_search_facets)
    mcp.tool()(query_datastore)
    mcp.tool()(sql_query_datastore)
    mcp.tool()(get_datastore_import_stats)
    mcp.tool()(search_healthcare_topics)
    mcp.tool()(get_healthcare_categories)
    mcp.tool()(test_healthcare_api)
    mcp.tool()(get_api_documentation)
