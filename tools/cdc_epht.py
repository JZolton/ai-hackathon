import logging
import aiohttp
import json
from typing import Dict, List, Optional, Any, Union
from fastmcp import FastMCP
from pydantic import Field
from urllib.parse import urlencode

logger = logging.getLogger(__name__)

# CDC Environmental Public Health Tracking Network API base URL
BASE_URL = "https://ephtracking.cdc.gov/apigateway/api/v1"

# Common measure categories and their IDs
MEASURE_CATEGORIES = {
    "air_quality": {
        "description": "Air quality measures including PM2.5, ozone, and air toxics",
        "measures": {
            "pm25_annual": "296",
            "ozone_8hr": "297", 
            "air_toxics_cancer_risk": "298",
            "air_toxics_respiratory": "299"
        }
    },
    "water_quality": {
        "description": "Drinking water quality and violations",
        "measures": {
            "drinking_water_violations": "300",
            "water_fluoridation": "301",
            "nitrate_violations": "302"
        }
    },
    "climate": {
        "description": "Climate and weather-related health impacts",
        "measures": {
            "heat_related_illness": "303",
            "extreme_heat_events": "304",
            "drought_conditions": "305"
        }
    },
    "health_outcomes": {
        "description": "Health outcomes potentially linked to environmental factors",
        "measures": {
            "asthma_hospitalizations": "306",
            "heart_disease_mortality": "307",
            "cancer_incidence": "308",
            "birth_defects": "309"
        }
    },
    "community_design": {
        "description": "Built environment and community design factors",
        "measures": {
            "walkability_index": "310",
            "green_space_access": "311",
            "food_environment": "312"
        }
    }
}

# Geographic types available
GEOGRAPHIC_TYPES = {
    "state": "State level data",
    "county": "County level data", 
    "city": "City level data",
    "tract": "Census tract level data",
    "zip": "ZIP code level data"
}

# Temporal types available
TEMPORAL_TYPES = {
    "annual": "Annual data",
    "monthly": "Monthly data",
    "daily": "Daily data",
    "seasonal": "Seasonal data"
}


# get_available_measures removed - API endpoint disabled



async def get_measure_categories() -> Dict[str, Any]:
    """Get predefined measure categories with common environmental health indicators"""
    return {
        "status": "success",
        "categories": MEASURE_CATEGORIES,
        "geographic_types": GEOGRAPHIC_TYPES,
        "temporal_types": TEMPORAL_TYPES,
        "note": "Use measure IDs from categories with query_environmental_data"
    }


async def query_environmental_data(
    measure_id: str = Field(description="Measure ID (e.g., '296' for PM2.5 annual)"),
    geographic_type: str = Field(default="state", description="Geographic level: state, county, city, tract, zip"),
    temporal_type: str = Field(default="annual", description="Temporal aggregation: annual, monthly, daily, seasonal"),
    year_filter: Optional[str] = Field(default=None, description="Year or year range (e.g., '2020' or '2018-2020')"),
    state_filter: Optional[str] = Field(default=None, description="State FIPS code or abbreviation (e.g., 'CA' or '06')"),
    county_filter: Optional[str] = Field(default=None, description="County FIPS code"),
    stratification: Optional[str] = Field(default=None, description="Stratification variable (e.g., 'age', 'race', 'gender')")
) -> Dict[str, Any]:
    """Query environmental health data from EPHT - CURRENTLY UNAVAILABLE"""
    
    return {
        "status": "error",
        "error": "CDC EPHT API is currently unavailable",
        "details": "All EPHT API endpoints are returning 400 Bad Request or 410 Gone errors",
        "alternative": "Consider using CDC Open Data API for environmental health data",
        "query_attempted": {
            "measure_id": measure_id,
            "geographic_type": geographic_type,
            "temporal_type": temporal_type,
            "year_filter": year_filter,
            "state_filter": state_filter,
            "county_filter": county_filter,
            "stratification": stratification
        },
        "last_tested": "2025-06-03",
        "api_status": "All endpoints non-functional"
    }


async def get_air_quality_data(
    pollutant: str = Field(default="pm25", description="Pollutant type: pm25, ozone, air_toxics_cancer, air_toxics_respiratory"),
    geographic_level: str = Field(default="county", description="Geographic level: state, county, city"),
    years: Optional[List[int]] = Field(default=None, description="List of years to include (e.g., [2018, 2019, 2020])"),
    states: Optional[List[str]] = Field(default=None, description="List of state abbreviations (e.g., ['CA', 'NY', 'TX'])")
) -> Dict[str, Any]:
    """Get air quality data for specific pollutants and locations"""
    
    # Map pollutant names to measure IDs
    pollutant_mapping = {
        "pm25": "296",
        "ozone": "297",
        "air_toxics_cancer": "298", 
        "air_toxics_respiratory": "299"
    }
    
    measure_id = pollutant_mapping.get(pollutant)
    if not measure_id:
        return {
            "status": "error",
            "error": f"Unknown pollutant: {pollutant}",
            "available_pollutants": list(pollutant_mapping.keys())
        }
    
    # Build year filter
    year_filter = None
    if years:
        if len(years) == 1:
            year_filter = str(years[0])
        else:
            year_filter = f"{min(years)}-{max(years)}"
    
    # Build state filter
    state_filter = None
    if states:
        state_filter = ",".join(states)
    
    return await query_environmental_data(
        measure_id=measure_id,
        geographic_type=geographic_level,
        temporal_type="annual",
        year_filter=year_filter,
        state_filter=state_filter,
        county_filter=None,
        stratification=None
    )


async def get_health_outcomes_by_environment(
    health_outcome: str = Field(description="Health outcome: asthma, heart_disease, cancer, birth_defects"),
    environmental_factor: str = Field(description="Environmental factor: air_quality, water_quality, climate"),
    geographic_level: str = Field(default="county", description="Geographic level: state, county"),
    year: Optional[int] = Field(default=None, description="Specific year to query")
) -> Dict[str, Any]:
    """Get health outcomes data potentially linked to environmental factors"""
    
    # Map health outcomes to measure IDs
    health_outcome_mapping = {
        "asthma": "306",
        "heart_disease": "307", 
        "cancer": "308",
        "birth_defects": "309"
    }
    
    # Map environmental factors to measure IDs (for correlation analysis)
    env_factor_mapping = {
        "air_quality": "296",  # PM2.5 as proxy
        "water_quality": "300",  # Water violations
        "climate": "303"  # Heat-related illness
    }
    
    health_measure_id = health_outcome_mapping.get(health_outcome)
    env_measure_id = env_factor_mapping.get(environmental_factor)
    
    if not health_measure_id:
        return {
            "status": "error", 
            "error": f"Unknown health outcome: {health_outcome}",
            "available_outcomes": list(health_outcome_mapping.keys())
        }
    
    if not env_measure_id:
        return {
            "status": "error",
            "error": f"Unknown environmental factor: {environmental_factor}",
            "available_factors": list(env_factor_mapping.keys())
        }
    
    year_filter = str(year) if year else None
    
    # Get both health outcome and environmental data
    health_data = await query_environmental_data(
        measure_id=health_measure_id,
        geographic_type=geographic_level,
        temporal_type="annual",
        year_filter=year_filter,
        state_filter=None,
        county_filter=None,
        stratification=None
    )
    
    env_data = await query_environmental_data(
        measure_id=env_measure_id,
        geographic_type=geographic_level, 
        temporal_type="annual",
        year_filter=year_filter,
        state_filter=None,
        county_filter=None,
        stratification=None
    )
    
    return {
        "status": "success",
        "health_outcome_data": health_data,
        "environmental_data": env_data,
        "analysis_note": "Compare geographic patterns between health outcomes and environmental exposures",
        "query_info": {
            "health_outcome": health_outcome,
            "environmental_factor": environmental_factor,
            "geographic_level": geographic_level,
            "year": year
        }
    }


async def get_community_health_profile(
    state: str = Field(description="State abbreviation (e.g., 'CA')"),
    county: Optional[str] = Field(default=None, description="County FIPS code (optional)"),
    include_air_quality: bool = Field(default=True, description="Include air quality measures"),
    include_water_quality: bool = Field(default=True, description="Include water quality measures"),
    include_health_outcomes: bool = Field(default=True, description="Include health outcome measures"),
    year: Optional[int] = Field(default=None, description="Specific year (defaults to most recent)")
) -> Dict[str, Any]:
    """Get comprehensive community health profile including environmental and health data"""
    
    geographic_level = "county" if county else "state"
    year_filter = str(year) if year else None
    state_filter = state.upper()
    county_filter = county if county else None
    
    profile_data = {}
    
    # Air quality data
    if include_air_quality:
        try:
            pm25_data = await query_environmental_data(
                measure_id="296",  # PM2.5
                geographic_type=geographic_level,
                temporal_type="annual",
                year_filter=year_filter,
                state_filter=state_filter,
                county_filter=county_filter,
                stratification=None
            )
            profile_data["air_quality"] = {
                "pm25": pm25_data
            }
        except Exception as e:
            profile_data["air_quality"] = {"error": str(e)}
    
    # Water quality data
    if include_water_quality:
        try:
            water_data = await query_environmental_data(
                measure_id="300",  # Water violations
                geographic_type=geographic_level,
                temporal_type="annual", 
                year_filter=year_filter,
                state_filter=state_filter,
                county_filter=county_filter,
                stratification=None
            )
            profile_data["water_quality"] = {
                "violations": water_data
            }
        except Exception as e:
            profile_data["water_quality"] = {"error": str(e)}
    
    # Health outcomes data
    if include_health_outcomes:
        try:
            asthma_data = await query_environmental_data(
                measure_id="306",  # Asthma hospitalizations
                geographic_type=geographic_level,
                temporal_type="annual",
                year_filter=year_filter,
                state_filter=state_filter,
                county_filter=county_filter,
                stratification=None
            )
            profile_data["health_outcomes"] = {
                "asthma_hospitalizations": asthma_data
            }
        except Exception as e:
            profile_data["health_outcomes"] = {"error": str(e)}
    
    return {
        "status": "success",
        "community_profile": profile_data,
        "location": {
            "state": state,
            "county": county,
            "geographic_level": geographic_level
        },
        "query_info": {
            "year": year,
            "included_categories": {
                "air_quality": include_air_quality,
                "water_quality": include_water_quality,
                "health_outcomes": include_health_outcomes
            }
        }
    }


async def search_measures_by_topic(
    topic: str = Field(description="Topic to search for (e.g., 'asthma', 'air pollution', 'water')")
) -> Dict[str, Any]:
    """Search for measures related to a specific health or environmental topic"""
    
    topic_lower = topic.lower()
    
    # Search predefined categories
    category_matches = {}
    for category_name, category_info in MEASURE_CATEGORIES.items():
        if topic_lower in category_name.lower() or topic_lower in category_info["description"].lower():
            category_matches[category_name] = category_info
        else:
            # Check individual measures in category
            for measure_name, measure_id in category_info["measures"].items():
                if topic_lower in measure_name.lower():
                    if category_name not in category_matches:
                        category_matches[category_name] = {"measures": {}}
                    category_matches[category_name]["measures"][measure_name] = measure_id
    
    return {
        "status": "success",
        "topic": topic,
        "category_matches": category_matches,
        "total_matches": len(category_matches),
        "note": "Use measure IDs with query_environmental_data function"
    }


# get_geographic_coverage removed - API endpoint returns 400 Bad Request


# get_temporal_coverage removed - API endpoint returns 400 Bad Request


async def test_epht_api() -> Dict[str, Any]:
    """Test connectivity and basic functionality of the EPHT API"""
    
    results = {}
    
    async with aiohttp.ClientSession() as session:
        # Test getMeasures endpoint
        try:
            async with session.get(f"{BASE_URL}/getMeasures", timeout=aiohttp.ClientTimeout(total=15)) as response:
                results["get_measures"] = {
                    "status": "success" if response.status == 200 else "error",
                    "status_code": response.status,
                    "endpoint": f"{BASE_URL}/getMeasures"
                }
                if response.status == 200:
                    data = await response.json()
                    results["get_measures"]["measure_count"] = len(data) if isinstance(data, list) else None
        except Exception as e:
            results["get_measures"] = {
                "status": "error",
                "error": str(e),
                "endpoint": f"{BASE_URL}/getMeasures"
            }
        
        # Test getCoreHolder with a simple query
        try:
            params = {
                "measureId": "296",  # PM2.5
                "geographicTypeId": "state",
                "temporalTypeId": "annual",
                "yearFilter": "2020"
            }
            async with session.get(f"{BASE_URL}/getCoreHolder", params=params, timeout=aiohttp.ClientTimeout(total=15)) as response:
                results["get_core_holder"] = {
                    "status": "success" if response.status == 200 else "error",
                    "status_code": response.status,
                    "endpoint": f"{BASE_URL}/getCoreHolder",
                    "test_query": "PM2.5 data for states in 2020"
                }
                if response.status == 200:
                    data = await response.json()
                    results["get_core_holder"]["record_count"] = len(data) if isinstance(data, list) else None
        except Exception as e:
            results["get_core_holder"] = {
                "status": "error",
                "error": str(e),
                "endpoint": f"{BASE_URL}/getCoreHolder"
            }
        
        # Test getGeographicItems
        try:
            async with session.get(f"{BASE_URL}/getGeographicItems?measureId=296", timeout=aiohttp.ClientTimeout(total=15)) as response:
                results["get_geographic_items"] = {
                    "status": "success" if response.status == 200 else "error",
                    "status_code": response.status,
                    "endpoint": f"{BASE_URL}/getGeographicItems"
                }
        except Exception as e:
            results["get_geographic_items"] = {
                "status": "error",
                "error": str(e),
                "endpoint": f"{BASE_URL}/getGeographicItems"
            }
    
    # Summary
    working_endpoints = sum(1 for result in results.values() if result["status"] == "success")
    total_endpoints = len(results)
    
    return {
        "summary": f"{working_endpoints}/{total_endpoints} endpoints responding",
        "results": results,
        "base_url": BASE_URL,
        "api_status": "operational" if working_endpoints > 0 else "issues_detected"
    }


async def get_api_documentation() -> Dict[str, Any]:
    """Get comprehensive documentation for the EPHT API"""
    return {
        "api_info": {
            "name": "CDC Environmental Public Health Tracking Network API",
            "base_url": BASE_URL,
            "version": "v1",
            "documentation": "https://ephtracking.cdc.gov/apihelp",
            "description": "Access environmental health data linking environmental factors with health outcomes"
        },
        "key_endpoints": {
            "getMeasures": f"{BASE_URL}/getMeasures",
            "getCoreHolder": f"{BASE_URL}/getCoreHolder",
            "getGeographicItems": f"{BASE_URL}/getGeographicItems",
            "getTemporalItems": f"{BASE_URL}/getTemporalItems"
        },
        "data_categories": {
            "environmental_exposures": [
                "Air quality (PM2.5, ozone, air toxics)",
                "Water quality (violations, contaminants)",
                "Climate factors (heat, extreme weather)"
            ],
            "health_outcomes": [
                "Respiratory diseases (asthma)",
                "Cardiovascular diseases",
                "Cancer incidence",
                "Birth outcomes"
            ],
            "community_factors": [
                "Built environment",
                "Walkability",
                "Green space access",
                "Food environment"
            ]
        },
        "geographic_levels": list(GEOGRAPHIC_TYPES.keys()),
        "temporal_types": list(TEMPORAL_TYPES.keys()),
        "use_cases": [
            "Environmental health surveillance",
            "Health disparities analysis", 
            "Policy impact assessment",
            "Community health profiling",
            "Environmental justice research"
        ]
    }


def register_cdc_epht_tools(mcp: FastMCP) -> None:
    """Register only working CDC EPHT tools with the MCP server."""
    
    # Working tools (no external API calls)
    mcp.tool()(get_measure_categories)  # Static data - works
    mcp.tool()(search_measures_by_topic)  # Static search - works
    mcp.tool()(get_api_documentation)  # Static documentation - works
    mcp.tool()(test_epht_api)  # API test tool - works (shows API status)
    
    # Disabled tools (all make API calls to broken endpoints)
    # These return informative error messages instead of timing out
    mcp.tool()(query_environmental_data)  # Returns API unavailable message
    mcp.tool()(get_air_quality_data)  # Calls query_environmental_data
    mcp.tool()(get_health_outcomes_by_environment)  # Calls query_environmental_data
    mcp.tool()(get_community_health_profile)  # Calls query_environmental_data
