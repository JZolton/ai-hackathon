import logging
import aiohttp
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Any
from fastmcp import FastMCP
from pydantic import Field
import json

logger = logging.getLogger(__name__)

# CDC WONDER API base URL
BASE_URL = "https://wonder.cdc.gov/controller/datarequest"

# Common database IDs
DATABASES = {
    "mortality_detailed": "D76",  # Detailed Mortality 1999-2013
    "mortality_multiple_cause": "D77",  # Multiple Cause of Death 1999-2013
    "natality": "D66",  # Natality 2007-2019
    "infant_deaths": "D69",  # Linked Birth / Infant Death Records 2007-2018
    "aids": "D10",  # AIDS Public Use
    "tb": "D13",  # TB Case Reports
    "vaccine_adverse": "D8",  # VAERS Vaccine Adverse Event Reporting
}


def build_xml_request(
    database_id: str,
    group_by: List[str],
    measures: List[str],
    filters: Dict[str, Any],
    show_totals: bool = True,
    show_zeros: bool = False,
    show_suppressed: bool = False
) -> str:
    """Build XML request for CDC WONDER API"""
    
    # Build XML manually to match exact format
    xml_parts = ['<?xml version="1.0" encoding="utf-8"?>']
    xml_parts.append('<request-parameters>')
    
    # Add data use restrictions acceptance
    xml_parts.append('<parameter>')
    xml_parts.append('<name>accept_datause_restrictions</name>')
    xml_parts.append('<value>true</value>')
    xml_parts.append('</parameter>')
    
    # Add group by parameters (B_1, B_2, etc.)
    for i, group in enumerate(group_by, 1):
        xml_parts.append('<parameter>')
        xml_parts.append(f'<name>B_{i}</name>')
        xml_parts.append(f'<value>{group}</value>')
        xml_parts.append('</parameter>')
    
    # Add measures - they need to be M_1, M_2, etc. not the actual measure codes
    for i, measure in enumerate(measures, 1):
        xml_parts.append('<parameter>')
        xml_parts.append(f'<name>M_{i}</name>')
        xml_parts.append(f'<value>{measure}</value>')
        xml_parts.append('</parameter>')
    
    # Add filters (V_ parameters and O_ parameters)
    for key, values in filters.items():
        if isinstance(values, list):
            xml_parts.append('<parameter>')
            xml_parts.append(f'<name>{key}</name>')
            for value in values:
                xml_parts.append(f'<value>{str(value)}</value>')
            xml_parts.append('</parameter>')
        else:
            xml_parts.append('<parameter>')
            xml_parts.append(f'<name>{key}</name>')
            xml_parts.append(f'<value>{str(values)}</value>')
            xml_parts.append('</parameter>')
    
    # Add display options
    if show_totals:
        xml_parts.append('<parameter>')
        xml_parts.append('<name>O_show_totals</name>')
        xml_parts.append('<value>true</value>')
        xml_parts.append('</parameter>')
    
    if show_zeros:
        xml_parts.append('<parameter>')
        xml_parts.append('<name>O_show_zeros</name>')
        xml_parts.append('<value>true</value>')
        xml_parts.append('</parameter>')
    
    if show_suppressed:
        xml_parts.append('<parameter>')
        xml_parts.append('<name>O_show_suppressed</name>')
        xml_parts.append('<value>true</value>')
        xml_parts.append('</parameter>')
    
    xml_parts.append('</request-parameters>')
    
    return '\n'.join(xml_parts)


def parse_response(xml_response: str) -> Dict[str, Any]:
    """Parse XML response from CDC WONDER API"""
    try:
        root = ET.fromstring(xml_response)
        
        # Extract data table
        data_table = root.find('.//data-table')
        if data_table is None:
            return {"error": "No data table found in response"}
        
        rows = []
        for row in data_table.findall('.//r'):
            row_data = []
            for cell in row.findall('.//c'):
                cell_value = cell.text if cell.text else ""
                # Check for subordinate level values (like confidence intervals)
                sub_level = cell.get('l')
                if sub_level:
                    cell_value = f"{cell_value} (Level: {sub_level})"
                row_data.append(cell_value)
            rows.append(row_data)
        
        # Extract column headers
        headers = []
        header_section = root.find('.//response-header')
        if header_section:
            for label in header_section.findall('.//label'):
                headers.append(label.text)
        
        # Extract caveats and footnotes
        caveats = []
        caveat_section = root.find('.//caveats')
        if caveat_section:
            for caveat in caveat_section.findall('.//caveat'):
                caveats.append(caveat.text)
        
        return {
            "headers": headers,
            "data": rows,
            "caveats": caveats,
            "row_count": len(rows)
        }
    
    except ET.ParseError as e:
        return {"error": f"Failed to parse XML response: {str(e)}"}



async def search_mortality_by_cause(
    cause_codes: List[str] = Field(description="ICD-10 codes for cause of death (e.g., ['C00-D48'] for cancer)"),
    years: List[int] = Field(description="Years to query (e.g., [2009, 2010, 2011])"),
    group_by: List[str] = Field(default=["year", "race"], description="Fields to group by: year, race, gender, age_group, state (note: state not available via API)"),
    include_rates: bool = Field(default=True, description="Include death rates in addition to counts")
) -> Dict[str, Any]:
    """Search CDC WONDER mortality database by cause of death"""
    
    database_id = DATABASES["mortality_detailed"]
    
    # Map group_by fields to CDC WONDER parameters
    group_mapping = {
        "year": "D76.V1-level1",
        "race": "D76.V8",
        "gender": "D76.V7",
        "age_group": "D76.V5"
    }
    
    group_params = [group_mapping.get(g, g) for g in group_by]
    
    # Default measures
    measures = ["D76.M1", "D76.M2", "D76.M3"]  # Deaths, Population, Crude Rate
    if include_rates:
        measures.extend(["D76.M4", "D76.M41", "D76.M42"])  # Age-adjusted rate, SE, CI
    
    # Build filters - simplified approach
    filters = {
        "O_ucd": "D76.V2",  # Use ICD-10 codes for underlying cause of death
        "F_D76.V2": cause_codes,  # ICD-10 codes
        "F_D76.V1": [str(year) for year in years],  # Years
        "I_D76.V1": "*All*",  # Currently selected indicator for years
        "I_D76.V2": "*All*",  # Currently selected indicator for ICD codes
        "O_V1_fmode": "freg",  # Regular mode for year selection
        "O_V2_fmode": "freg",  # Regular mode for cause selection
        "O_age": "D76.V5",  # Use ten-year age groups
        "O_precision": "0",  # Precision for rates
        "O_rate_per": "100000"  # Rate per 100,000
    }
    
    # Build XML request
    xml_request = build_xml_request(
        database_id=database_id,
        group_by=group_params,
        measures=measures,
        filters=filters,
        show_totals=True,
        show_zeros=False,
        show_suppressed=True
    )
    
    # Log the XML request for debugging
    logger.debug(f"Sending XML request to {BASE_URL}/{database_id}:")
    logger.debug(xml_request)
    
    # Send request
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                f"{BASE_URL}/{database_id}",
                data={"request_xml": xml_request},
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                response_text = await response.text()
                logger.debug(f"Response status: {response.status}")
                logger.debug(f"Response text: {response_text[:500]}...")  # First 500 chars
                
                if response.status == 200:
                    return parse_response(response_text)
                else:
                    # Try to parse error from response
                    error_msg = f"API request failed with status {response.status}"
                    try:
                        error_root = ET.fromstring(response_text)
                        error_detail = error_root.find('.//message')
                        if error_detail is not None and error_detail.text:
                            error_msg += f": {error_detail.text}"
                    except:
                        error_msg += f". Response: {response_text[:200]}"
                    return {"error": error_msg}
        except Exception as e:
            logger.error(f"Request failed: {str(e)}")
            return {"error": f"Request failed: {str(e)}"}


async def search_mortality_simple(
    cause_code: str = Field(description="Single ICD-10 code for cause of death (e.g., 'C00-D48' for cancer, '*All*' for all causes)"),
    year: int = Field(description="Single year to query (e.g., 2013). Must be between 1999-2013."),
    group_by: str = Field(default="none", description="Optional grouping: 'none', 'gender', 'race', or 'age_group'. Note: grouping may cause API errors.")
) -> Dict[str, Any]:
    """Simplified CDC WONDER mortality search that avoids common API errors"""
    
    # Validate year
    if year < 1999 or year > 2013:
        return {"error": "Year must be between 1999 and 2013 for this database"}
    
    database_id = DATABASES["mortality_detailed"]
    
    # Build basic measures - just deaths and population
    measures = ["D76.M1", "D76.M2"]  # Deaths, Population
    
    # Build group by parameters
    group_params = []
    if group_by == "gender":
        group_params = ["D76.V7"]
    elif group_by == "race":
        group_params = ["D76.V8"]
    elif group_by == "age_group":
        group_params = ["D76.V5"]
    # Default: no grouping (national totals only)
    
    # Build filters with minimal required parameters
    filters = {
        "O_ucd": "D76.V2",  # Use ICD-10 codes
        "F_D76.V2": [cause_code],  # Single cause code
        "F_D76.V1": [str(year)],  # Single year
        "I_D76.V1": "*All*",  # Year indicator
        "I_D76.V2": "*All*",  # Cause indicator
        "O_V1_fmode": "freg",  # Regular mode
        "O_V2_fmode": "freg",  # Regular mode
        "O_precision": "0"  # No decimal places
    }
    
    # Only add age parameter if we're grouping by age
    if group_by == "age_group":
        filters["O_age"] = "D76.V5"  # Ten-year age groups
    
    try:
        # Build XML request
        xml_request = build_xml_request(
            database_id=database_id,
            group_by=group_params,
            measures=measures,
            filters=filters,
            show_totals=True,
            show_zeros=False,
            show_suppressed=False
        )
        
        # Send request
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{BASE_URL}/{database_id}",
                data={"request_xml": xml_request},
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                response_text = await response.text()
                
                if response.status == 200:
                    result = parse_response(response_text)
                    result["query_info"] = {
                        "cause_code": cause_code,
                        "year": year,
                        "group_by": group_by,
                        "database": "mortality_detailed"
                    }
                    return result
                else:
                    # Parse error details
                    error_details = []
                    try:
                        error_root = ET.fromstring(response_text)
                        for message in error_root.findall('.//message'):
                            if message.text and "{0}" not in message.text:
                                error_details.append(message.text)
                    except:
                        pass
                    
                    return {
                        "error": f"API request failed with status {response.status}",
                        "error_details": error_details,
                        "suggestion": "Try using group_by='none' or a different cause_code like '*All*'"
                    }
    
    except Exception as e:
        return {
            "error": f"Request failed: {str(e)}",
            "suggestion": "Try a simpler query with group_by='none'"
        }


async def search_injury_deaths(
    age_groups: List[int] = Field(description="Single year ages to include (e.g., [0, 1, 2, ..., 17] for under 18)"),
    years: Optional[List[int]] = Field(default=None, description="Years to query (defaults to all available)"),
    group_by_intent: bool = Field(default=True, description="Group results by injury intent"),
    group_by_mechanism: bool = Field(default=True, description="Group results by injury mechanism")
) -> Dict[str, Any]:
    """Search CDC WONDER for injury-related deaths"""
    
    database_id = DATABASES["mortality_detailed"]
    
    # Build group by parameters
    group_params = []
    if group_by_intent:
        group_params.append("D76.V22")  # Injury Intent
    if group_by_mechanism:
        group_params.append("D76.V23")  # Injury Mechanism
    
    # Default measures
    measures = ["D76.M1", "D76.M2", "D76.M3"]  # Deaths, Population, Crude Rate
    
    # Build filters
    filters = {
        "O_age": "D76.V52",  # Single-year age groups
        "V_D76.V52": [str(age) for age in age_groups],  # Specific ages
        "O_ucd": "D76.V22"  # Use injury intent for cause of death
    }
    
    if years:
        filters["V_D76.V1"] = [str(year) for year in years]
    
    # Build XML request
    xml_request = build_xml_request(
        database_id=database_id,
        group_by=group_params,
        measures=measures,
        filters=filters,
        show_totals=True
    )
    
    # Send request
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                f"{BASE_URL}/{database_id}",
                data={"request_xml": xml_request},
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    xml_response = await response.text()
                    return parse_response(xml_response)
                else:
                    return {"error": f"API request failed with status {response.status}"}
        except Exception as e:
            return {"error": f"Request failed: {str(e)}"}


async def test_cdc_wonder_api() -> Dict[str, Any]:
    """Test the CDC WONDER API with a simple request"""
    
    # Very basic test request - just get total deaths for 2013
    xml_request = '''<?xml version="1.0" encoding="utf-8"?>
<request-parameters>
<parameter>
<name>accept_datause_restrictions</name>
<value>true</value>
</parameter>
<parameter>
<name>M_1</name>
<value>D76.M1</value>
</parameter>
<parameter>
<name>O_ucd</name>
<value>D76.V2</value>
</parameter>
<parameter>
<name>F_D76.V2</name>
<value>*All*</value>
</parameter>
<parameter>
<name>F_D76.V1</name>
<value>2013</value>
</parameter>
<parameter>
<name>I_D76.V1</name>
<value>*All*</value>
</parameter>
<parameter>
<name>I_D76.V2</name>
<value>*All*</value>
</parameter>
<parameter>
<name>O_V1_fmode</name>
<value>freg</value>
</parameter>
<parameter>
<name>O_V2_fmode</name>
<value>freg</value>
</parameter>
</request-parameters>'''
    
    database_id = "D76"
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                f"{BASE_URL}/{database_id}",
                data={"request_xml": xml_request},
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                response_text = await response.text()
                
                if response.status == 200:
                    result = parse_response(response_text)
                    result["test_status"] = "SUCCESS"
                    result["xml_sent"] = xml_request
                    return result
                else:
                    # Parse error details
                    error_details = []
                    try:
                        error_root = ET.fromstring(response_text)
                        for message in error_root.findall('.//message'):
                            if message.text:
                                error_details.append(message.text)
                    except:
                        pass
                    
                    return {
                        "test_status": "FAILED",
                        "status_code": response.status,
                        "error_details": error_details,
                        "xml_sent": xml_request,
                        "raw_response": response_text[:1000]
                    }
        except Exception as e:
            return {
                "test_status": "ERROR",
                "error": str(e),
                "xml_sent": xml_request
            }


async def get_available_databases() -> Dict[str, Any]:
    """Get list of available CDC WONDER databases and their IDs"""
    return {
        "databases": [
            {
                "id": db_id,
                "name": name.replace("_", " ").title(),
                "description": get_database_description(name)
            }
            for name, db_id in DATABASES.items()
        ],
        "note": "Only national data is available via API for vital statistics databases"
    }


def get_database_description(db_name: str) -> str:
    """Get description for a database"""
    descriptions = {
        "mortality_detailed": "Detailed mortality statistics from death certificates (1999-2013)",
        "mortality_multiple_cause": "Multiple causes of death from death certificates (1999-2013)",
        "natality": "Birth statistics from birth certificates (2007-2019)",
        "infant_deaths": "Linked birth and infant death records (2007-2018)",
        "aids": "AIDS surveillance data",
        "tb": "Tuberculosis case reports",
        "vaccine_adverse": "Vaccine Adverse Event Reporting System (VAERS) data"
    }
    return descriptions.get(db_name, "CDC WONDER database")


async def search_cdc_wonder_custom(
    database: str = Field(description="Database name from get_available_databases (e.g., 'mortality_detailed')"),
    group_by_codes: List[str] = Field(description="Parameter codes to group by (e.g., ['D76.V1-level1', 'D76.V8'])"),
    measure_codes: List[str] = Field(description="Measure codes to include (e.g., ['D76.M1', 'D76.M2'])"),
    filters: Dict[str, Any] = Field(description="Filter parameters as key-value pairs"),
    show_totals: bool = Field(default=True, description="Show row totals"),
    show_zeros: bool = Field(default=False, description="Show zero-value rows")
) -> Dict[str, Any]:
    """Advanced custom query for CDC WONDER with full parameter control"""
    
    if database not in DATABASES:
        return {"error": f"Unknown database: {database}. Use get_available_databases to see options."}
    
    database_id = DATABASES[database]
    
    # Build XML request
    xml_request = build_xml_request(
        database_id=database_id,
        group_by=group_by_codes,
        measures=measure_codes,
        filters=filters,
        show_totals=show_totals,
        show_zeros=show_zeros,
        show_suppressed=True
    )
    
    # Send request
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                f"{BASE_URL}/{database_id}",
                data={"request_xml": xml_request},
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    xml_response = await response.text()
                    result = parse_response(xml_response)
                    result["query_info"] = {
                        "database": database,
                        "database_id": database_id,
                        "group_by": group_by_codes,
                        "measures": measure_codes,
                        "filters": filters
                    }
                    return result
                else:
                    return {"error": f"API request failed with status {response.status}"}
        except Exception as e:
            return {"error": f"Request failed: {str(e)}"}




def register_cdc_wonder_tools(mcp: FastMCP) -> None:
    """Register all CDC WONDER tools with the MCP server."""
    mcp.tool()(search_mortality_by_cause)
    mcp.tool()(search_mortality_simple)
    mcp.tool()(search_injury_deaths)
    mcp.tool()(test_cdc_wonder_api)
    mcp.tool()(get_available_databases)
    mcp.tool()(search_cdc_wonder_custom)
