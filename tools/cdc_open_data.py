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
    "open_data": "https://data.cdc.gov",
    "phin_vads": "http://phinvads.cdc.gov/vocabService/v2",
    "wonder": "https://wonder.cdc.gov/controller/datarequest",
    "content_syndication": "https://tools.cdc.gov/api/v2",
    "tracking_network": "https://ephtracking.cdc.gov/apigateway/api/v1"
}

# Common dataset identifiers for Open Data API
COMMON_DATASETS = {
    "covid_cases": "9mfq-cb36",
    "covid_deaths": "r8kw-7aab", 
    "flu_surveillance": "pk7k-8jbr",
    "chronic_disease": "g4ie-h725",
    "behavioral_risk": "dttw-5yxu",
    "birth_data": "3h58-x6cd",
    "mortality_data": "bi63-dtpu",
    "cancer_statistics": "hiyb-xunq",
    "diabetes_surveillance": "37jh-ykv3",
    "heart_disease": "6x7h-usvx"
}

# Content syndication topic IDs
SYNDICATION_TOPICS = {
    "diseases_conditions": 1,
    "emergency_preparedness": 2,
    "environmental_health": 3,
    "healthy_living": 4,
    "injury_violence": 5,
    "life_stages": 6,
    "workplace_safety": 7,
    "travelers_health": 8
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


async def search_vocabularies(
    search_term: str = Field(description="Term to search for in vocabularies"),
    vocabulary_oid: Optional[str] = Field(default=None, description="Specific vocabulary OID to search within"),
    max_results: int = Field(default=50, description="Maximum number of results to return")
) -> Dict[str, Any]:
    """Search PHIN VADS vocabulary service for standard terms"""
    
    url = f"{ENDPOINTS['phin_vads']}/vocabulary"
    params = {
        "searchText": search_term,
        "maxResults": max_results
    }
    
    if vocabulary_oid:
        params["vocabularyOid"] = vocabulary_oid
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status == 200:
                    xml_data = await response.text()
                    try:
                        root = ET.fromstring(xml_data)
                        vocabularies = []
                        
                        for vocab in root.findall('.//vocabulary'):
                            vocab_info = {
                                "name": vocab.findtext('name', ''),
                                "oid": vocab.findtext('oid', ''),
                                "description": vocab.findtext('description', ''),
                                "version": vocab.findtext('version', ''),
                                "status": vocab.findtext('status', '')
                            }
                            
                            # Extract concepts if available
                            concepts = []
                            for concept in vocab.findall('.//concept'):
                                concept_info = {
                                    "code": concept.findtext('code', ''),
                                    "display_name": concept.findtext('displayName', ''),
                                    "definition": concept.findtext('definition', '')
                                }
                                concepts.append(concept_info)
                            
                            if concepts:
                                vocab_info["concepts"] = concepts
                            
                            vocabularies.append(vocab_info)
                        
                        return {
                            "status": "success",
                            "vocabularies": vocabularies,
                            "search_term": search_term,
                            "total_found": len(vocabularies)
                        }
                    
                    except ET.ParseError as e:
                        return {
                            "status": "error",
                            "error": f"Failed to parse XML response: {str(e)}",
                            "raw_response": xml_data[:500]
                        }
                else:
                    return {
                        "status": "error",
                        "error": f"API request failed with status {response.status}"
                    }
        except Exception as e:
            return {
                "status": "error",
                "error": f"Request failed: {str(e)}"
            }


async def get_syndicated_content(
    topic_id: Optional[int] = Field(default=None, description="Topic ID (1-8, see get_syndication_topics)"),
    media_type: str = Field(default="Html", description="Media type: Html, Json, Xml"),
    max_items: int = Field(default=20, description="Maximum number of items to return"),
    sort: str = Field(default="date", description="Sort by: date, title, or relevance")
) -> Dict[str, Any]:
    """Get syndicated content from CDC Content Syndication API"""
    
    url = f"{ENDPOINTS['content_syndication']}/resources/media"
    params = {
        "mediatype": media_type,
        "max": max_items,
        "sort": sort
    }
    
    if topic_id:
        params["topicid"] = topic_id
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status == 200:
                    if media_type.lower() == "json":
                        data = await response.json()
                    else:
                        data = await response.text()
                    
                    return {
                        "status": "success",
                        "content": data,
                        "query_info": {
                            "topic_id": topic_id,
                            "media_type": media_type,
                            "max_items": max_items,
                            "sort": sort
                        }
                    }
                else:
                    return {
                        "status": "error",
                        "error": f"API request failed with status {response.status}"
                    }
        except Exception as e:
            return {
                "status": "error",
                "error": f"Request failed: {str(e)}"
            }


async def get_syndication_topics() -> Dict[str, Any]:
    """Get available content syndication topics"""
    return {
        "status": "success",
        "topics": [
            {
                "id": topic_id,
                "name": name.replace("_", " ").title()
            }
            for name, topic_id in SYNDICATION_TOPICS.items()
        ],
        "note": "Use these topic IDs with get_syndicated_content"
    }


async def query_tracking_network(
    measure_id: str = Field(description="Measure ID (e.g., '296' for air quality)"),
    temporal_type: str = Field(default="annual", description="Temporal type: annual, monthly, daily"),
    geographic_type: str = Field(default="state", description="Geographic type: state, county, city"),
    year_filter: Optional[str] = Field(default=None, description="Year or year range (e.g., '2020' or '2018-2020')"),
    state_filter: Optional[str] = Field(default=None, description="State FIPS code or abbreviation")
) -> Dict[str, Any]:
    """Query CDC Environmental Public Health Tracking Network API"""
    
    url = f"{ENDPOINTS['tracking_network']}/getCoreHolder"
    params = {
        "measureId": measure_id,
        "temporalTypeId": temporal_type,
        "geographicTypeId": geographic_type
    }
    
    if year_filter:
        params["yearFilter"] = year_filter
    if state_filter:
        params["stateFilter"] = state_filter
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "status": "success",
                        "data": data,
                        "query_info": {
                            "measure_id": measure_id,
                            "temporal_type": temporal_type,
                            "geographic_type": geographic_type,
                            "year_filter": year_filter,
                            "state_filter": state_filter
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


async def get_tracking_measures() -> Dict[str, Any]:
    """Get available measures from CDC Environmental Public Health Tracking Network"""
    
    url = f"{ENDPOINTS['tracking_network']}/getMeasures"
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "status": "success",
                        "measures": data,
                        "note": "Use measure IDs with query_tracking_network"
                    }
                else:
                    return {
                        "status": "error",
                        "error": f"API request failed with status {response.status}"
                    }
        except Exception as e:
            return {
                "status": "error",
                "error": f"Request failed: {str(e)}"
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
    """Test connectivity to all CDC API endpoints"""
    
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
        
        # Test Content Syndication API
        try:
            async with session.get(f"{ENDPOINTS['content_syndication']}/resources/media?max=1", timeout=aiohttp.ClientTimeout(total=10)) as response:
                results["content_syndication"] = {
                    "status": "success" if response.status == 200 else "error",
                    "status_code": response.status,
                    "endpoint": ENDPOINTS['content_syndication']
                }
        except Exception as e:
            results["content_syndication"] = {
                "status": "error",
                "error": str(e),
                "endpoint": ENDPOINTS['content_syndication']
            }
        
        # Test Tracking Network API
        try:
            async with session.get(f"{ENDPOINTS['tracking_network']}/getMeasures", timeout=aiohttp.ClientTimeout(total=10)) as response:
                results["tracking_network"] = {
                    "status": "success" if response.status == 200 else "error",
                    "status_code": response.status,
                    "endpoint": ENDPOINTS['tracking_network']
                }
        except Exception as e:
            results["tracking_network"] = {
                "status": "error",
                "error": str(e),
                "endpoint": ENDPOINTS['tracking_network']
            }
        
        # Test PHIN VADS (may be slower)
        try:
            async with session.get(f"{ENDPOINTS['phin_vads']}/vocabulary?searchText=test&maxResults=1", timeout=aiohttp.ClientTimeout(total=15)) as response:
                results["phin_vads"] = {
                    "status": "success" if response.status == 200 else "error",
                    "status_code": response.status,
                    "endpoint": ENDPOINTS['phin_vads']
                }
        except Exception as e:
            results["phin_vads"] = {
                "status": "error",
                "error": str(e),
                "endpoint": ENDPOINTS['phin_vads']
            }
    
    # Summary
    working_apis = sum(1 for result in results.values() if result["status"] == "success")
    total_apis = len(results)
    
    return {
        "summary": f"{working_apis}/{total_apis} APIs responding",
        "results": results,
        "timestamp": "2025-06-02T18:19:00Z"
    }


async def get_api_documentation() -> Dict[str, Any]:
    """Get documentation links and information for all CDC APIs"""
    return {
        "apis": [
            {
                "name": "Open Data",
                "endpoint": ENDPOINTS['open_data'],
                "documentation": "https://dev.socrata.com/docs/endpoints.html",
                "description": "Repository of all available CDC datasets with Socrata Open Data API",
                "formats": ["json", "xml", "csv"],
                "architecture": "REST"
            },
            {
                "name": "PHIN VADS",
                "endpoint": ENDPOINTS['phin_vads'],
                "documentation": "http://phinvads.cdc.gov/vads/developersGuide.action",
                "description": "Standard vocabularies for CDC and public health partners",
                "formats": ["xml"],
                "architecture": "REST"
            },
            {
                "name": "WONDER",
                "endpoint": ENDPOINTS['wonder'],
                "documentation": "https://wonder.cdc.gov/wonder/help/WONDER-API.html",
                "description": "Access WONDER online databases with automated data queries",
                "formats": ["xml"],
                "architecture": "REST"
            },
            {
                "name": "Content Syndication",
                "endpoint": ENDPOINTS['content_syndication'],
                "documentation": "https://tools.cdc.gov/api/docs/info.aspx#response",
                "description": "CDC web content syndication for other sites and applications",
                "formats": ["json", "xml"],
                "architecture": "REST"
            },
            {
                "name": "Environmental Public Health Tracking Network",
                "endpoint": ENDPOINTS['tracking_network'],
                "documentation": "https://ephtracking.cdc.gov/apihelp",
                "description": "Query environmental public health tracking data",
                "formats": ["json"],
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
    """Register all CDC Open Data tools with the MCP server."""
    mcp.tool()(search_open_data)
    mcp.tool()(get_common_datasets)
    mcp.tool()(search_vocabularies)
    mcp.tool()(get_syndicated_content)
    mcp.tool()(get_syndication_topics)
    mcp.tool()(query_tracking_network)
    mcp.tool()(get_tracking_measures)
    mcp.tool()(search_covid_data)
    mcp.tool()(test_api_endpoints)
    mcp.tool()(get_api_documentation)
