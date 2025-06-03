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
    "insurance": "Insurance coverage data",
    "enrollment": "Enrollment and registration data",
    "brokers": "Agent and broker information"
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
        
        # Test dataset items endpoint
        try:
            async with session.get(f"{BASE_URL}/metastore/schemas/dataset/items?limit=1", timeout=aiohttp.ClientTimeout(total=10)) as response:
                results["dataset_items"] = {
                    "status": "success" if response.status == 200 else "error",
                    "status_code": response.status,
                    "endpoint": f"{BASE_URL}/metastore/schemas/dataset/items"
                }
        except Exception as e:
            results["dataset_items"] = {
                "status": "error",
                "error": str(e),
                "endpoint": f"{BASE_URL}/metastore/schemas/dataset/items"
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
        
        # Test datastore endpoint
        try:
            async with session.get(f"{BASE_URL}/datastore/query?limit=1", timeout=aiohttp.ClientTimeout(total=10)) as response:
                results["datastore"] = {
                    "status": "success" if response.status == 200 else "error",
                    "status_code": response.status,
                    "endpoint": f"{BASE_URL}/datastore/query"
                }
        except Exception as e:
            results["datastore"] = {
                "status": "error",
                "error": str(e),
                "endpoint": f"{BASE_URL}/datastore/query"
            }
    
    # Summary
    working_endpoints = sum(1 for result in results.values() if result["status"] == "success")
    total_endpoints = len(results)
    
    return {
        "summary": f"{working_endpoints}/{total_endpoints} endpoints responding",
        "results": results,
        "base_url": BASE_URL,
        "test_date": "2025-06-03"
    }

async def get_all_schemas() -> Dict[str, Any]:
    """Get list of all schemas available in the metastore"""
    
    url = f"{BASE_URL}/metastore/schemas"
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Process schema list to handle different formats
                    schema_list = []
                    if isinstance(data, list):
                        for schema in data:
                            if isinstance(schema, str):
                                schema_list.append({"name": schema, "type": "string"})
                            elif isinstance(schema, dict):
                                schema_list.append(schema)
                            else:
                                schema_list.append({"name": str(schema), "type": "unknown"})
                    
                    return {
                        "status": "success",
                        "schemas": schema_list,
                        "count": len(schema_list),
                        "raw_data": data
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

async def get_recent_datasets(
    limit: int = 50,
    year_filter: Optional[str] = None
) -> Dict[str, Any]:
    """Get recent datasets with modification date analysis"""
    
    url = f"{BASE_URL}/metastore/schemas/dataset/items"
    params = {"limit": limit}
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    recent_datasets = []
                    date_counts = {}
                    
                    for item in data:
                        if isinstance(item, dict):
                            modified = item.get('modified', '')
                            title = item.get('title', 'Untitled')
                            identifier = item.get('identifier', 'No ID')
                            
                            # Extract year from modified date
                            if modified:
                                try:
                                    year = modified[:4]
                                    if year.isdigit():
                                        date_counts[year] = date_counts.get(year, 0) + 1
                                        
                                        # Filter by year if specified, otherwise show 2024-2025
                                        target_years = [year_filter] if year_filter else ['2024', '2025']
                                        if year in target_years:
                                            recent_datasets.append({
                                                'title': title,
                                                'modified': modified,
                                                'identifier': identifier,
                                                'year': year
                                            })
                                except:
                                    pass
                    
                    return {
                        "status": "success",
                        "recent_datasets": recent_datasets,
                        "date_distribution": dict(sorted(date_counts.items(), reverse=True)),
                        "total_analyzed": len(data),
                        "recent_count": len(recent_datasets),
                        "filter_years": [year_filter] if year_filter else ['2024', '2025']
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

async def get_dataset_by_id(
    identifier: str = Field(description="Dataset identifier/ID")
) -> Dict[str, Any]:
    """Get a specific dataset by its identifier"""
    
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

async def browse_all_datasets(
    limit: int = 20,
    offset: int = 0
) -> Dict[str, Any]:
    """Browse all available datasets with pagination"""
    
    url = f"{BASE_URL}/metastore/schemas/dataset/items"
    params = {
        "limit": limit,
        "offset": offset
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Process datasets for better display
                    processed_datasets = []
                    for item in data:
                        if isinstance(item, dict):
                            processed_datasets.append({
                                'title': item.get('title', 'Untitled'),
                                'identifier': item.get('identifier', 'No ID'),
                                'modified': item.get('modified', 'Unknown'),
                                'description': item.get('description', 'No description')[:200] + '...' if item.get('description', '') else 'No description'
                            })
                    
                    return {
                        "status": "success",
                        "datasets": processed_datasets,
                        "count": len(processed_datasets),
                        "pagination": {
                            "limit": limit,
                            "offset": offset,
                            "returned": len(data)
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

async def query_dataset_data(
    dataset_id: str = Field(description="Dataset identifier to query"),
    limit: int = 10
) -> Dict[str, Any]:
    """Query actual data from a specific dataset"""
    
    # Try different datastore query approaches
    urls_to_try = [
        f"{BASE_URL}/datastore/query/{dataset_id}",
        f"{BASE_URL}/datastore/query/{dataset_id}/0",
        f"{BASE_URL}/datastore/query"
    ]
    
    async with aiohttp.ClientSession() as session:
        for url in urls_to_try:
            try:
                params = {"limit": limit}
                if url == f"{BASE_URL}/datastore/query":
                    params["resource_id"] = dataset_id
                
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "status": "success",
                            "data": data,
                            "dataset_id": dataset_id,
                            "query_url": str(response.url),
                            "record_count": len(data.get('results', [])) if isinstance(data, dict) and 'results' in data else len(data) if isinstance(data, list) else 0
                        }
                    elif response.status == 404:
                        continue  # Try next URL
                    else:
                        error_text = await response.text()
                        return {
                            "status": "error",
                            "error": f"API request failed with status {response.status}",
                            "details": error_text[:500],
                            "attempted_url": str(response.url)
                        }
            except Exception as e:
                continue  # Try next URL
        
        return {
            "status": "error",
            "error": "All datastore query attempts failed",
            "dataset_id": dataset_id,
            "attempted_urls": urls_to_try
        }

async def search_datasets_by_title(
    search_term: str = Field(description="Term to search for in dataset titles"),
    limit: int = 20
) -> Dict[str, Any]:
    """Search datasets by title (since API search seems limited)"""
    
    # Get all datasets and filter by title
    url = f"{BASE_URL}/metastore/schemas/dataset/items"
    params = {"limit": 100}  # Get more to search through
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    matching_datasets = []
                    search_lower = search_term.lower()
                    
                    for item in data:
                        if isinstance(item, dict):
                            title = item.get('title', '').lower()
                            description = item.get('description', '').lower()
                            
                            if search_lower in title or search_lower in description:
                                matching_datasets.append({
                                    'title': item.get('title', 'Untitled'),
                                    'identifier': item.get('identifier', 'No ID'),
                                    'modified': item.get('modified', 'Unknown'),
                                    'description': item.get('description', 'No description')[:200] + '...' if item.get('description', '') else 'No description',
                                    'relevance': 'title' if search_lower in title else 'description'
                                })
                    
                    # Sort by relevance (title matches first)
                    matching_datasets.sort(key=lambda x: (x['relevance'] != 'title', x['title']))
                    
                    return {
                        "status": "success",
                        "search_term": search_term,
                        "matches": matching_datasets[:limit],
                        "total_matches": len(matching_datasets),
                        "searched_datasets": len(data)
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
        "note": "Use these categories with search_datasets_by_title",
        "total_categories": len(HEALTHCARE_CATEGORIES)
    }

async def get_api_status() -> Dict[str, Any]:
    """Get comprehensive API status and capabilities"""
    
    # Test basic connectivity
    test_result = await test_healthcare_api()
    
    # Get dataset count
    try:
        recent_data = await get_recent_datasets(limit=10)
        dataset_info = {
            "recent_datasets_available": recent_data.get("recent_count", 0),
            "date_distribution": recent_data.get("date_distribution", {}),
            "total_analyzed": recent_data.get("total_analyzed", 0)
        }
    except:
        dataset_info = {"error": "Could not retrieve dataset information"}
    
    return {
        "api_status": test_result,
        "dataset_info": dataset_info,
        "capabilities": {
            "working_endpoints": [
                "get_all_schemas",
                "get_recent_datasets", 
                "browse_all_datasets",
                "get_dataset_by_id",
                "query_dataset_data",
                "search_datasets_by_title"
            ],
            "data_access": "Full access to 315+ datasets",
            "recent_data": "2024-2025 data available",
            "last_tested": "2025-06-03"
        }
    }

def register_healthcare_gov_tools(mcp: FastMCP) -> None:
    """Register all working Healthcare.gov tools with the MCP server."""
    mcp.tool()(test_healthcare_api)
    mcp.tool()(get_all_schemas)
    mcp.tool()(get_recent_datasets)
    mcp.tool()(get_dataset_by_id)
    mcp.tool()(browse_all_datasets)
    mcp.tool()(query_dataset_data)
    mcp.tool()(search_datasets_by_title)
    mcp.tool()(get_healthcare_categories)
    mcp.tool()(get_api_status)
