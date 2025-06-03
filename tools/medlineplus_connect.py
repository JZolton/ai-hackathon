import logging
import aiohttp
import json
from typing import Dict, List, Optional, Any, Union
from fastmcp import FastMCP
from pydantic import Field
from urllib.parse import urlencode, quote

logger = logging.getLogger(__name__)

# MedlinePlus Connect API base URL
BASE_URL = "https://connect.medlineplus.gov/service"

# Common health topic categories
HEALTH_TOPIC_CATEGORIES = {
    "diseases_conditions": "Diseases and Conditions",
    "drugs_supplements": "Drugs and Supplements", 
    "medical_tests": "Medical Tests and Procedures",
    "anatomy": "Body Systems and Anatomy",
    "wellness": "Health and Wellness",
    "prevention": "Prevention and Screening",
    "genetics": "Genetics and Heredity",
    "environmental_health": "Environmental Health",
    "mental_health": "Mental Health and Behavior",
    "women_health": "Women's Health",
    "men_health": "Men's Health",
    "children_health": "Children's Health",
    "seniors_health": "Seniors' Health"
}

# Language codes supported by MedlinePlus
SUPPORTED_LANGUAGES = {
    "en": "English",
    "es": "Spanish (Español)",
    "ar": "Arabic (العربية)",
    "zh": "Chinese (中文)",
    "fr": "French (Français)",
    "hi": "Hindi (हिन्दी)",
    "ja": "Japanese (日本語)",
    "ko": "Korean (한국어)",
    "pt": "Portuguese (Português)",
    "ru": "Russian (Русский)",
    "vi": "Vietnamese (Tiếng Việt)"
}

async def test_medlineplus_api() -> Dict[str, Any]:
    """Test connectivity to the MedlinePlus Connect API"""
    
    results = {}
    
    async with aiohttp.ClientSession() as session:
        # Test basic health topic search
        try:
            params = {
                "mainSearchCriteria.v.c": "diabetes",
                "knowledgeResponseType": "application/json"
            }
            async with session.get(f"{BASE_URL}", params=params, timeout=aiohttp.ClientTimeout(total=15)) as response:
                results["health_topic_search"] = {
                    "status": "success" if response.status == 200 else "error",
                    "status_code": response.status,
                    "endpoint": f"{BASE_URL}",
                    "test_query": "diabetes search"
                }
                if response.status == 200:
                    data = await response.json()
                    results["health_topic_search"]["response_type"] = type(data).__name__
        except Exception as e:
            results["health_topic_search"] = {
                "status": "error",
                "error": str(e),
                "endpoint": f"{BASE_URL}"
            }
        
        # Test ICD-10 code lookup
        try:
            params = {
                "mainSearchCriteria.v.cs": "2.16.840.1.113883.6.90",
                "mainSearchCriteria.v.c": "E11.9",
                "knowledgeResponseType": "application/json"
            }
            async with session.get(f"{BASE_URL}", params=params, timeout=aiohttp.ClientTimeout(total=15)) as response:
                results["icd10_lookup"] = {
                    "status": "success" if response.status == 200 else "error",
                    "status_code": response.status,
                    "endpoint": f"{BASE_URL}",
                    "test_query": "ICD-10 E11.9 (Type 2 diabetes)"
                }
        except Exception as e:
            results["icd10_lookup"] = {
                "status": "error",
                "error": str(e),
                "endpoint": f"{BASE_URL}"
            }
        
        # Test medication search
        try:
            params = {
                "mainSearchCriteria.v.c": "metformin",
                "mainSearchCriteria.v.cs": "2.16.840.1.113883.6.88",
                "knowledgeResponseType": "application/json"
            }
            async with session.get(f"{BASE_URL}", params=params, timeout=aiohttp.ClientTimeout(total=15)) as response:
                results["medication_search"] = {
                    "status": "success" if response.status == 200 else "error",
                    "status_code": response.status,
                    "endpoint": f"{BASE_URL}",
                    "test_query": "metformin medication search"
                }
        except Exception as e:
            results["medication_search"] = {
                "status": "error",
                "error": str(e),
                "endpoint": f"{BASE_URL}"
            }
    
    # Summary
    working_endpoints = sum(1 for result in results.values() if result["status"] == "success")
    total_endpoints = len(results)
    
    return {
        "summary": f"{working_endpoints}/{total_endpoints} endpoints responding",
        "results": results,
        "base_url": BASE_URL,
        "api_status": "operational" if working_endpoints > 0 else "issues_detected",
        "test_date": "2025-06-03"
    }

async def search_health_topics(
    search_term: str = Field(description="Health topic, condition, or symptom to search for"),
    language: str = Field(default="en", description="Language code (en, es, ar, zh, fr, hi, ja, ko, pt, ru, vi)"),
    max_results: int = Field(default=10, description="Maximum number of results to return")
) -> Dict[str, Any]:
    """Search for health topics and information using MedlinePlus Connect"""
    
    if language not in SUPPORTED_LANGUAGES:
        return {
            "status": "error",
            "error": f"Unsupported language: {language}",
            "supported_languages": SUPPORTED_LANGUAGES
        }
    
    params = {
        "mainSearchCriteria.v.c": search_term,
        "knowledgeResponseType": "application/json",
        "informationRecipient.languageCode.c": language
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{BASE_URL}", params=params, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Process the response to extract relevant health information
                    health_topics = []
                    if isinstance(data, dict) and "feed" in data:
                        entries = data.get("feed", {}).get("entry", [])
                        if not isinstance(entries, list):
                            entries = [entries] if entries else []
                        
                        for entry in entries[:max_results]:
                            if isinstance(entry, dict):
                                topic = {
                                    "title": entry.get("title", {}).get("_value", "No title"),
                                    "summary": entry.get("summary", {}).get("_value", "No summary"),
                                    "id": entry.get("id", "No ID"),
                                    "updated": entry.get("updated", "No date"),
                                    "language": language
                                }
                                
                                # Extract links if available
                                links = entry.get("link", [])
                                if not isinstance(links, list):
                                    links = [links] if links else []
                                
                                topic["links"] = []
                                for link in links:
                                    if isinstance(link, dict):
                                        topic["links"].append({
                                            "href": link.get("href", ""),
                                            "title": link.get("title", ""),
                                            "type": link.get("type", "")
                                        })
                                
                                health_topics.append(topic)
                    
                    return {
                        "status": "success",
                        "search_term": search_term,
                        "language": language,
                        "topics": health_topics,
                        "total_found": len(health_topics),
                        "raw_response_keys": list(data.keys()) if isinstance(data, dict) else []
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

async def lookup_by_icd10_code(
    icd10_code: str = Field(description="ICD-10 diagnosis code (e.g., 'E11.9' for Type 2 diabetes)"),
    language: str = Field(default="en", description="Language code for results")
) -> Dict[str, Any]:
    """Look up health information using ICD-10 diagnosis codes"""
    
    if language not in SUPPORTED_LANGUAGES:
        return {
            "status": "error",
            "error": f"Unsupported language: {language}",
            "supported_languages": SUPPORTED_LANGUAGES
        }
    
    params = {
        "mainSearchCriteria.v.cs": "2.16.840.1.113883.6.90",  # ICD-10-CM code system
        "mainSearchCriteria.v.c": icd10_code.upper(),
        "knowledgeResponseType": "application/json",
        "informationRecipient.languageCode.c": language
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{BASE_URL}", params=params, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Process ICD-10 lookup response
                    condition_info = {
                        "icd10_code": icd10_code.upper(),
                        "language": language,
                        "health_information": []
                    }
                    
                    if isinstance(data, dict) and "feed" in data:
                        entries = data.get("feed", {}).get("entry", [])
                        if not isinstance(entries, list):
                            entries = [entries] if entries else []
                        
                        for entry in entries:
                            if isinstance(entry, dict):
                                info = {
                                    "title": entry.get("title", {}).get("_value", "No title"),
                                    "summary": entry.get("summary", {}).get("_value", "No summary"),
                                    "category": entry.get("category", {}).get("term", "General"),
                                    "updated": entry.get("updated", "No date")
                                }
                                
                                # Extract content links
                                links = entry.get("link", [])
                                if not isinstance(links, list):
                                    links = [links] if links else []
                                
                                info["resources"] = []
                                for link in links:
                                    if isinstance(link, dict):
                                        info["resources"].append({
                                            "url": link.get("href", ""),
                                            "title": link.get("title", ""),
                                            "type": link.get("type", "")
                                        })
                                
                                condition_info["health_information"].append(info)
                    
                    return {
                        "status": "success",
                        "condition_info": condition_info,
                        "total_resources": len(condition_info["health_information"])
                    }
                else:
                    error_text = await response.text()
                    return {
                        "status": "error",
                        "error": f"API request failed with status {response.status}",
                        "details": error_text[:500],
                        "icd10_code": icd10_code
                    }
        except Exception as e:
            return {
                "status": "error",
                "error": f"Request failed: {str(e)}",
                "icd10_code": icd10_code
            }

async def search_medication_info(
    medication_name: str = Field(description="Medication name or RxNorm code"),
    language: str = Field(default="en", description="Language code for results"),
    include_interactions: bool = Field(default=True, description="Include drug interaction information")
) -> Dict[str, Any]:
    """Search for medication information and drug interactions"""
    
    if language not in SUPPORTED_LANGUAGES:
        return {
            "status": "error",
            "error": f"Unsupported language: {language}",
            "supported_languages": SUPPORTED_LANGUAGES
        }
    
    params = {
        "mainSearchCriteria.v.c": medication_name,
        "mainSearchCriteria.v.cs": "2.16.840.1.113883.6.88",  # RxNorm code system
        "knowledgeResponseType": "application/json",
        "informationRecipient.languageCode.c": language
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{BASE_URL}", params=params, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    medication_info = {
                        "medication_name": medication_name,
                        "language": language,
                        "drug_information": [],
                        "interactions": [],
                        "side_effects": [],
                        "usage_instructions": []
                    }
                    
                    if isinstance(data, dict) and "feed" in data:
                        entries = data.get("feed", {}).get("entry", [])
                        if not isinstance(entries, list):
                            entries = [entries] if entries else []
                        
                        for entry in entries:
                            if isinstance(entry, dict):
                                title = entry.get("title", {}).get("_value", "").lower()
                                summary = entry.get("summary", {}).get("_value", "")
                                
                                info_item = {
                                    "title": entry.get("title", {}).get("_value", "No title"),
                                    "content": summary,
                                    "category": entry.get("category", {}).get("term", "General"),
                                    "updated": entry.get("updated", "No date")
                                }
                                
                                # Categorize information based on title/content
                                if any(keyword in title for keyword in ["interaction", "drug interaction"]):
                                    medication_info["interactions"].append(info_item)
                                elif any(keyword in title for keyword in ["side effect", "adverse", "reaction"]):
                                    medication_info["side_effects"].append(info_item)
                                elif any(keyword in title for keyword in ["dosage", "how to", "usage", "administration"]):
                                    medication_info["usage_instructions"].append(info_item)
                                else:
                                    medication_info["drug_information"].append(info_item)
                    
                    return {
                        "status": "success",
                        "medication_info": medication_info,
                        "summary": {
                            "total_information_items": len(medication_info["drug_information"]),
                            "interaction_warnings": len(medication_info["interactions"]),
                            "side_effect_info": len(medication_info["side_effects"]),
                            "usage_instructions": len(medication_info["usage_instructions"])
                        }
                    }
                else:
                    error_text = await response.text()
                    return {
                        "status": "error",
                        "error": f"API request failed with status {response.status}",
                        "details": error_text[:500],
                        "medication_name": medication_name
                    }
        except Exception as e:
            return {
                "status": "error",
                "error": f"Request failed: {str(e)}",
                "medication_name": medication_name
            }

async def get_health_topic_categories() -> Dict[str, Any]:
    """Get list of common health topic categories available in MedlinePlus"""
    return {
        "status": "success",
        "categories": [
            {
                "category_id": category_id,
                "category_name": category_name,
                "description": f"Health information related to {category_name.lower()}"
            }
            for category_id, category_name in HEALTH_TOPIC_CATEGORIES.items()
        ],
        "supported_languages": SUPPORTED_LANGUAGES,
        "total_categories": len(HEALTH_TOPIC_CATEGORIES),
        "usage_note": "Use category names as search terms with search_health_topics"
    }

async def search_by_symptom(
    symptom: str = Field(description="Symptom or group of symptoms to search for"),
    language: str = Field(default="en", description="Language code for results"),
    include_related: bool = Field(default=True, description="Include related conditions and causes")
) -> Dict[str, Any]:
    """Search for health information based on symptoms"""
    
    # Enhance symptom search with medical terminology
    symptom_enhanced = f"{symptom} symptoms causes treatment"
    
    # Use the general health topic search but focus on symptom-related results
    search_result = await search_health_topics(
        search_term=symptom_enhanced,
        language=language,
        max_results=15
    )
    
    if search_result["status"] == "success":
        # Filter and categorize results for symptom-specific information
        symptom_info = {
            "symptom": symptom,
            "language": language,
            "possible_conditions": [],
            "treatment_options": [],
            "when_to_see_doctor": [],
            "general_information": []
        }
        
        for topic in search_result.get("topics", []):
            title_lower = topic.get("title", "").lower()
            summary_lower = topic.get("summary", "").lower()
            
            # Categorize based on content
            if any(keyword in title_lower or keyword in summary_lower 
                   for keyword in ["condition", "disease", "disorder", "syndrome"]):
                symptom_info["possible_conditions"].append(topic)
            elif any(keyword in title_lower or keyword in summary_lower 
                     for keyword in ["treatment", "therapy", "medication", "cure"]):
                symptom_info["treatment_options"].append(topic)
            elif any(keyword in title_lower or keyword in summary_lower 
                     for keyword in ["emergency", "urgent", "doctor", "medical attention"]):
                symptom_info["when_to_see_doctor"].append(topic)
            else:
                symptom_info["general_information"].append(topic)
        
        return {
            "status": "success",
            "symptom_analysis": symptom_info,
            "summary": {
                "possible_conditions_found": len(symptom_info["possible_conditions"]),
                "treatment_options_found": len(symptom_info["treatment_options"]),
                "urgent_care_info": len(symptom_info["when_to_see_doctor"]),
                "general_info_items": len(symptom_info["general_information"])
            },
            "disclaimer": "This information is for educational purposes only. Always consult healthcare professionals for medical advice."
        }
    else:
        return search_result

async def get_multilingual_health_info(
    health_topic: str = Field(description="Health topic to search for"),
    languages: List[str] = Field(default=["en", "es"], description="List of language codes to retrieve information in")
) -> Dict[str, Any]:
    """Get health information in multiple languages for the same topic"""
    
    # Validate languages
    invalid_languages = [lang for lang in languages if lang not in SUPPORTED_LANGUAGES]
    if invalid_languages:
        return {
            "status": "error",
            "error": f"Unsupported languages: {invalid_languages}",
            "supported_languages": SUPPORTED_LANGUAGES
        }
    
    multilingual_info = {
        "health_topic": health_topic,
        "languages_requested": languages,
        "information_by_language": {}
    }
    
    # Search in each requested language
    for language in languages:
        try:
            result = await search_health_topics(
                search_term=health_topic,
                language=language,
                max_results=5
            )
            
            if result["status"] == "success":
                multilingual_info["information_by_language"][language] = {
                    "language_name": SUPPORTED_LANGUAGES[language],
                    "topics": result["topics"],
                    "total_found": result["total_found"]
                }
            else:
                multilingual_info["information_by_language"][language] = {
                    "language_name": SUPPORTED_LANGUAGES[language],
                    "error": result.get("error", "Unknown error"),
                    "topics": []
                }
        except Exception as e:
            multilingual_info["information_by_language"][language] = {
                "language_name": SUPPORTED_LANGUAGES[language],
                "error": str(e),
                "topics": []
            }
    
    # Summary statistics
    successful_languages = [lang for lang, info in multilingual_info["information_by_language"].items() 
                           if "error" not in info]
    total_topics = sum(len(info.get("topics", [])) 
                      for info in multilingual_info["information_by_language"].values())
    
    return {
        "status": "success",
        "multilingual_info": multilingual_info,
        "summary": {
            "successful_languages": len(successful_languages),
            "failed_languages": len(languages) - len(successful_languages),
            "total_topics_found": total_topics,
            "languages_with_content": successful_languages
        }
    }

async def get_api_capabilities() -> Dict[str, Any]:
    """Get comprehensive information about MedlinePlus Connect API capabilities"""
    
    # Test API connectivity
    api_test = await test_medlineplus_api()
    
    return {
        "api_info": {
            "name": "MedlinePlus Connect API",
            "base_url": BASE_URL,
            "description": "Provides access to reliable health information from the National Library of Medicine",
            "documentation": "https://medlineplus.gov/connect/overview.html",
            "data_source": "National Library of Medicine (NLM)"
        },
        "capabilities": {
            "health_topic_search": "Search for health topics, conditions, and symptoms",
            "icd10_code_lookup": "Look up health information using ICD-10 diagnosis codes",
            "medication_information": "Search for drug information, interactions, and side effects",
            "symptom_analysis": "Analyze symptoms and find related conditions",
            "multilingual_support": "Access health information in 11 languages",
            "code_system_support": ["ICD-10-CM", "RxNorm", "SNOMED CT"]
        },
        "supported_languages": SUPPORTED_LANGUAGES,
        "health_categories": list(HEALTH_TOPIC_CATEGORIES.values()),
        "api_status": api_test,
        "use_cases": [
            "Patient education and health literacy",
            "Clinical decision support",
            "Health information lookup by medical codes",
            "Multilingual health communication",
            "Symptom checker and triage support",
            "Drug information and interaction checking"
        ],
        "data_quality": {
            "source": "Peer-reviewed medical literature and government health agencies",
            "review_process": "Reviewed by medical librarians and health professionals",
            "update_frequency": "Regular updates from authoritative sources",
            "languages_quality": "Professional medical translations available"
        }
    }

def register_medlineplus_tools(mcp: FastMCP) -> None:
    """Register all MedlinePlus Connect tools with the MCP server."""
    mcp.tool()(test_medlineplus_api)
    mcp.tool()(search_health_topics)
    mcp.tool()(lookup_by_icd10_code)
    mcp.tool()(search_medication_info)
    mcp.tool()(get_health_topic_categories)
    mcp.tool()(search_by_symptom)
    mcp.tool()(get_multilingual_health_info)
    mcp.tool()(get_api_capabilities)
