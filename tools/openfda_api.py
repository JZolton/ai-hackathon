import logging
import aiohttp
import json
from typing import Dict, List, Optional, Any, Union
from fastmcp import FastMCP
from pydantic import Field
from urllib.parse import urlencode, quote
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# OpenFDA API base URL
BASE_URL = "https://api.fda.gov"

# FDA API endpoints for different data types
ENDPOINTS = {
    "drug_adverse_events": f"{BASE_URL}/drug/event.json",
    "drug_labeling": f"{BASE_URL}/drug/label.json",
    "drug_enforcement": f"{BASE_URL}/drug/enforcement.json",
    "drug_ndc": f"{BASE_URL}/drug/ndc.json",
    "drug_drugsfda": f"{BASE_URL}/drug/drugsfda.json",
    "device_adverse_events": f"{BASE_URL}/device/event.json",
    "device_enforcement": f"{BASE_URL}/device/enforcement.json",
    "food_adverse_events": f"{BASE_URL}/food/event.json",
    "food_enforcement": f"{BASE_URL}/food/enforcement.json"
}

# Common adverse event outcome codes
ADVERSE_EVENT_OUTCOMES = {
    "1": "Recovered/Resolved",
    "2": "Recovering/Resolving", 
    "3": "Not Recovered/Not Resolved",
    "4": "Recovered/Resolved with Sequelae",
    "5": "Fatal",
    "6": "Unknown"
}

# Serious adverse event criteria
SERIOUS_CRITERIA = {
    "1": "Results in Death",
    "2": "Life-Threatening",
    "3": "Hospitalization - Initial or Prolonged",
    "4": "Disability",
    "5": "Congenital Anomaly",
    "6": "Required Intervention to Prevent Permanent Impairment/Damage",
    "7": "Other Serious (Important Medical Event)"
}

# Drug administration routes
DRUG_ROUTES = {
    "001": "Auricular (otic)",
    "002": "Buccal",
    "003": "Cutaneous",
    "004": "Dental",
    "005": "Endocervical",
    "006": "Endosinusial",
    "007": "Endotracheal",
    "008": "Epidural",
    "009": "Extra-amniotic",
    "010": "Hemodialysis",
    "011": "Intra corpus cavernosum",
    "012": "Intra-amniotic",
    "013": "Intra-arterial",
    "014": "Intra-articular",
    "015": "Intra-uterine",
    "016": "Intracardiac",
    "017": "Intracavernous",
    "018": "Intracerebral",
    "019": "Intracervical",
    "020": "Intracisternal",
    "021": "Intracorneal",
    "022": "Intracoronary",
    "023": "Intradermal",
    "024": "Intradiscal (intraspinal)",
    "025": "Intrahepatic",
    "026": "Intralesional",
    "027": "Intralymphatic",
    "028": "Intramedullar (bone marrow)",
    "029": "Intrameningeal",
    "030": "Intramuscular",
    "031": "Intraocular",
    "032": "Intrapericardial",
    "033": "Intraperitoneal",
    "034": "Intrapleural",
    "035": "Intrasynovial",
    "036": "Intrathecal",
    "037": "Intrathoracic",
    "038": "Intratracheal",
    "039": "Intravenous bolus",
    "040": "Intravenous drip",
    "041": "Intravenous (not otherwise specified)",
    "042": "Intravesical",
    "043": "Iontophoresis",
    "044": "Nasal",
    "045": "Occlusive dressing technique",
    "046": "Ophthalmic",
    "047": "Oral",
    "048": "Oropharyngeal",
    "049": "Other",
    "050": "Parenteral",
    "051": "Periarticular",
    "052": "Perineural",
    "053": "Rectal",
    "054": "Respiratory (inhalation)",
    "055": "Retrobulbar",
    "056": "Sunconjunctival",
    "057": "Subcutaneous",
    "058": "Subdermal",
    "059": "Sublingual",
    "060": "Topical",
    "061": "Transdermal",
    "062": "Transmammary",
    "063": "Transplacental",
    "064": "Unknown",
    "065": "Ureteral",
    "066": "Urethral",
    "067": "Vaginal"
}

async def test_openfda_api() -> Dict[str, Any]:
    """Test connectivity to the OpenFDA API"""
    
    results = {}
    
    async with aiohttp.ClientSession() as session:
        # Test drug adverse events endpoint
        try:
            params = {
                "search": "patient.drug.medicinalproduct:aspirin",
                "limit": 1
            }
            async with session.get(ENDPOINTS["drug_adverse_events"], params=params, timeout=aiohttp.ClientTimeout(total=15)) as response:
                results["drug_adverse_events"] = {
                    "status": "success" if response.status == 200 else "error",
                    "status_code": response.status,
                    "endpoint": ENDPOINTS["drug_adverse_events"],
                    "test_query": "aspirin adverse events"
                }
                if response.status == 200:
                    data = await response.json()
                    results["drug_adverse_events"]["total_results"] = data.get("meta", {}).get("results", {}).get("total", 0)
        except Exception as e:
            results["drug_adverse_events"] = {
                "status": "error",
                "error": str(e),
                "endpoint": ENDPOINTS["drug_adverse_events"]
            }
        
        # Test drug labeling endpoint
        try:
            params = {
                "search": "openfda.brand_name:tylenol",
                "limit": 1
            }
            async with session.get(ENDPOINTS["drug_labeling"], params=params, timeout=aiohttp.ClientTimeout(total=15)) as response:
                results["drug_labeling"] = {
                    "status": "success" if response.status == 200 else "error",
                    "status_code": response.status,
                    "endpoint": ENDPOINTS["drug_labeling"],
                    "test_query": "tylenol labeling"
                }
        except Exception as e:
            results["drug_labeling"] = {
                "status": "error",
                "error": str(e),
                "endpoint": ENDPOINTS["drug_labeling"]
            }
        
        # Test drug enforcement endpoint
        try:
            params = {
                "search": "status:ongoing",
                "limit": 1
            }
            async with session.get(ENDPOINTS["drug_enforcement"], params=params, timeout=aiohttp.ClientTimeout(total=15)) as response:
                results["drug_enforcement"] = {
                    "status": "success" if response.status == 200 else "error",
                    "status_code": response.status,
                    "endpoint": ENDPOINTS["drug_enforcement"],
                    "test_query": "ongoing enforcement actions"
                }
        except Exception as e:
            results["drug_enforcement"] = {
                "status": "error",
                "error": str(e),
                "endpoint": ENDPOINTS["drug_enforcement"]
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

async def search_drug_adverse_events(
    drug_name: str,
    limit: int = 10,
    serious_only: bool = False,
    outcome_filter: Optional[str] = None,
    date_range_days: Optional[int] = None
) -> Dict[str, Any]:
    """Search for drug adverse events reported to FDA"""
    
    # Build search query
    search_terms = []
    
    # Drug name search (try both brand and generic names)
    drug_search = f"(patient.drug.medicinalproduct:\"{drug_name}\" OR patient.drug.openfda.brand_name:\"{drug_name}\" OR patient.drug.openfda.generic_name:\"{drug_name}\")"
    search_terms.append(drug_search)
    
    # Filter for serious events only
    if serious_only:
        search_terms.append("serious:1")
    
    # Filter by outcome
    if outcome_filter:
        outcome_mapping = {
            "fatal": "5",
            "life_threatening": "2", 
            "hospitalization": "3",
            "disability": "4",
            "other": "6"
        }
        if outcome_filter in outcome_mapping:
            search_terms.append(f"patient.patientdeath.patientdeathdate:*" if outcome_filter == "fatal" else f"seriousnessother:1")
    
    # Date range filter
    if date_range_days:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=date_range_days)
        date_filter = f"receivedate:[{start_date.strftime('%Y%m%d')}+TO+{end_date.strftime('%Y%m%d')}]"
        search_terms.append(date_filter)
    
    search_query = "+AND+".join(search_terms)
    
    params = {
        "search": search_query,
        "limit": min(limit, 1000)  # FDA API limit
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(ENDPOINTS["drug_adverse_events"], params=params, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Process adverse event results
                    adverse_events = []
                    results = data.get("results", [])
                    
                    for event in results:
                        if isinstance(event, dict):
                            # Extract patient information
                            patient = event.get("patient", {})
                            
                            # Extract drug information
                            drugs = patient.get("drug", [])
                            if not isinstance(drugs, list):
                                drugs = [drugs] if drugs else []
                            
                            # Extract reactions
                            reactions = patient.get("reaction", [])
                            if not isinstance(reactions, list):
                                reactions = [reactions] if reactions else []
                            
                            processed_event = {
                                "report_id": event.get("safetyreportid", "Unknown"),
                                "receive_date": event.get("receivedate", "Unknown"),
                                "serious": event.get("serious", "Unknown"),
                                "patient_info": {
                                    "age": patient.get("patientonsetage", "Unknown"),
                                    "age_unit": patient.get("patientonsetageunit", "Unknown"),
                                    "sex": patient.get("patientsex", "Unknown"),
                                    "weight": patient.get("patientweight", "Unknown")
                                },
                                "drugs": [],
                                "reactions": [],
                                "outcomes": []
                            }
                            
                            # Process drugs
                            for drug in drugs:
                                if isinstance(drug, dict):
                                    drug_info = {
                                        "name": drug.get("medicinalproduct", "Unknown"),
                                        "indication": drug.get("drugindication", "Unknown"),
                                        "dosage": drug.get("drugdosagetext", "Unknown"),
                                        "route": drug.get("drugadministrationroute", "Unknown"),
                                        "start_date": drug.get("drugstartdate", "Unknown"),
                                        "end_date": drug.get("drugenddate", "Unknown")
                                    }
                                    
                                    # Add OpenFDA information if available
                                    openfda = drug.get("openfda", {})
                                    if openfda:
                                        drug_info["brand_names"] = openfda.get("brand_name", [])
                                        drug_info["generic_names"] = openfda.get("generic_name", [])
                                        drug_info["manufacturer"] = openfda.get("manufacturer_name", [])
                                    
                                    processed_event["drugs"].append(drug_info)
                            
                            # Process reactions
                            for reaction in reactions:
                                if isinstance(reaction, dict):
                                    reaction_info = {
                                        "term": reaction.get("reactionmeddrapt", "Unknown"),
                                        "outcome": ADVERSE_EVENT_OUTCOMES.get(str(reaction.get("reactionoutcome", "")), "Unknown")
                                    }
                                    processed_event["reactions"].append(reaction_info)
                            
                            # Process serious criteria
                            serious_criteria = []
                            for i in range(1, 8):
                                if event.get(f"seriousness{['death', 'lifethreatening', 'hospitalization', 'disabling', 'congenitalanomali', 'other'][i-1] if i <= 6 else 'other'}", "") == "1":
                                    serious_criteria.append(SERIOUS_CRITERIA.get(str(i), f"Criteria {i}"))
                            
                            processed_event["serious_criteria"] = serious_criteria
                            adverse_events.append(processed_event)
                    
                    return {
                        "status": "success",
                        "drug_name": drug_name,
                        "search_parameters": {
                            "limit": limit,
                            "serious_only": serious_only,
                            "outcome_filter": outcome_filter,
                            "date_range_days": date_range_days
                        },
                        "adverse_events": adverse_events,
                        "total_found": data.get("meta", {}).get("results", {}).get("total", 0),
                        "returned_count": len(adverse_events),
                        "disclaimer": "This data is from FDA Adverse Event Reporting System (FAERS). Reports do not necessarily mean the drug caused the adverse event."
                    }
                else:
                    error_text = await response.text()
                    return {
                        "status": "error",
                        "error": f"API request failed with status {response.status}",
                        "details": error_text[:500],
                        "drug_name": drug_name
                    }
        except Exception as e:
            return {
                "status": "error",
                "error": f"Request failed: {str(e)}",
                "drug_name": drug_name
            }

async def get_drug_labeling_info(
    drug_name: str = Field(description="Drug name (brand or generic) to get labeling information"),
    section: Optional[str] = Field(default=None, description="Specific label section: warnings, indications, dosage, contraindications, adverse_reactions"),
    limit: int = Field(default=5, description="Maximum number of results to return")
) -> Dict[str, Any]:
    """Get FDA drug labeling information including warnings, indications, and dosage"""
    
    # Build search query
    search_query = f"(openfda.brand_name:\"{drug_name}\" OR openfda.generic_name:\"{drug_name}\" OR openfda.substance_name:\"{drug_name}\")"
    
    params = {
        "search": search_query,
        "limit": min(limit, 100)
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(ENDPOINTS["drug_labeling"], params=params, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Process labeling results
                    labeling_info = []
                    results = data.get("results", [])
                    
                    for label in results:
                        if isinstance(label, dict):
                            # Extract OpenFDA information
                            openfda = label.get("openfda", {})
                            
                            label_info = {
                                "brand_names": openfda.get("brand_name", []),
                                "generic_names": openfda.get("generic_name", []),
                                "manufacturer": openfda.get("manufacturer_name", []),
                                "product_type": openfda.get("product_type", []),
                                "route": openfda.get("route", []),
                                "substance_name": openfda.get("substance_name", [])
                            }
                            
                            # Extract specific sections based on request
                            sections = {}
                            
                            if not section or section == "warnings":
                                sections["warnings"] = label.get("warnings", ["No warnings section found"])
                                sections["boxed_warning"] = label.get("boxed_warning", ["No boxed warning"])
                                sections["warnings_and_cautions"] = label.get("warnings_and_cautions", ["No warnings and cautions section"])
                            
                            if not section or section == "indications":
                                sections["indications_and_usage"] = label.get("indications_and_usage", ["No indications section found"])
                            
                            if not section or section == "dosage":
                                sections["dosage_and_administration"] = label.get("dosage_and_administration", ["No dosage section found"])
                            
                            if not section or section == "contraindications":
                                sections["contraindications"] = label.get("contraindications", ["No contraindications section found"])
                            
                            if not section or section == "adverse_reactions":
                                sections["adverse_reactions"] = label.get("adverse_reactions", ["No adverse reactions section found"])
                            
                            # Additional important sections
                            if not section:
                                sections["drug_interactions"] = label.get("drug_interactions", ["No drug interactions section found"])
                                sections["pregnancy"] = label.get("pregnancy", ["No pregnancy section found"])
                                sections["pediatric_use"] = label.get("pediatric_use", ["No pediatric use section found"])
                                sections["geriatric_use"] = label.get("geriatric_use", ["No geriatric use section found"])
                            
                            label_info["sections"] = sections
                            labeling_info.append(label_info)
                    
                    return {
                        "status": "success",
                        "drug_name": drug_name,
                        "section_requested": section or "all",
                        "labeling_info": labeling_info,
                        "total_found": data.get("meta", {}).get("results", {}).get("total", 0),
                        "returned_count": len(labeling_info)
                    }
                else:
                    error_text = await response.text()
                    return {
                        "status": "error",
                        "error": f"API request failed with status {response.status}",
                        "details": error_text[:500],
                        "drug_name": drug_name
                    }
        except Exception as e:
            return {
                "status": "error",
                "error": f"Request failed: {str(e)}",
                "drug_name": drug_name
            }

async def get_drug_recalls_enforcement(
    drug_name: Optional[str] = None,
    status: str = "ongoing",
    classification: Optional[str] = None,
    limit: int = 10,
    date_range_days: Optional[int] = 365
) -> Dict[str, Any]:
    """Get FDA drug recalls and enforcement actions"""
    
    # Build search query
    search_terms = []
    
    # Drug name search if provided
    if drug_name:
        drug_search = f"(product_description:\"{drug_name}\" OR openfda.brand_name:\"{drug_name}\" OR openfda.generic_name:\"{drug_name}\")"
        search_terms.append(drug_search)
    
    # Status filter
    if status:
        search_terms.append(f"status:{status}")
    
    # Classification filter
    if classification:
        class_mapping = {
            "class_i": "Class I",
            "class_ii": "Class II", 
            "class_iii": "Class III"
        }
        if classification in class_mapping:
            search_terms.append(f"classification:\"{class_mapping[classification]}\"")
    
    # Date range filter
    if date_range_days:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=date_range_days)
        date_filter = f"report_date:[{start_date.strftime('%Y-%m-%d')}+TO+{end_date.strftime('%Y-%m-%d')}]"
        search_terms.append(date_filter)
    
    search_query = "+AND+".join(search_terms) if search_terms else "*"
    
    params = {
        "search": search_query,
        "limit": min(limit, 1000)
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(ENDPOINTS["drug_enforcement"], params=params, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Process enforcement results
                    enforcement_actions = []
                    results = data.get("results", [])
                    
                    for action in results:
                        if isinstance(action, dict):
                            # Extract OpenFDA information
                            openfda = action.get("openfda", {})
                            
                            action_info = {
                                "recall_number": action.get("recall_number", "Unknown"),
                                "status": action.get("status", "Unknown"),
                                "classification": action.get("classification", "Unknown"),
                                "product_description": action.get("product_description", "Unknown"),
                                "reason_for_recall": action.get("reason_for_recall", "Unknown"),
                                "report_date": action.get("report_date", "Unknown"),
                                "recall_initiation_date": action.get("recall_initiation_date", "Unknown"),
                                "termination_date": action.get("termination_date", "Not terminated"),
                                "recalling_firm": action.get("recalling_firm", "Unknown"),
                                "distribution_pattern": action.get("distribution_pattern", "Unknown"),
                                "product_quantity": action.get("product_quantity", "Unknown"),
                                "voluntary_mandated": action.get("voluntary_mandated", "Unknown")
                            }
                            
                            # Add OpenFDA information if available
                            if openfda:
                                action_info["fda_info"] = {
                                    "application_number": openfda.get("application_number", []),
                                    "brand_name": openfda.get("brand_name", []),
                                    "generic_name": openfda.get("generic_name", []),
                                    "manufacturer_name": openfda.get("manufacturer_name", []),
                                    "product_ndc": openfda.get("product_ndc", []),
                                    "product_type": openfda.get("product_type", []),
                                    "route": openfda.get("route", []),
                                    "substance_name": openfda.get("substance_name", [])
                                }
                            
                            enforcement_actions.append(action_info)
                    
                    return {
                        "status": "success",
                        "search_parameters": {
                            "drug_name": drug_name,
                            "status": status,
                            "classification": classification,
                            "date_range_days": date_range_days
                        },
                        "enforcement_actions": enforcement_actions,
                        "total_found": data.get("meta", {}).get("results", {}).get("total", 0),
                        "returned_count": len(enforcement_actions),
                        "classification_guide": {
                            "Class I": "Dangerous or defective products that predictably could cause serious health problems or death",
                            "Class II": "Products that might cause a temporary health problem, or pose only a slight threat of a serious nature",
                            "Class III": "Products that are unlikely to cause any adverse health reaction, but that violate FDA labeling or manufacturing laws"
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

async def analyze_drug_safety_profile(
    drug_name: str = Field(description="Drug name to analyze for comprehensive safety profile"),
    include_adverse_events: bool = Field(default=True, description="Include adverse event analysis"),
    include_labeling: bool = Field(default=True, description="Include labeling warnings and contraindications"),
    include_recalls: bool = Field(default=True, description="Include recall and enforcement history"),
    serious_events_only: bool = Field(default=False, description="Focus only on serious adverse events")
) -> Dict[str, Any]:
    """Comprehensive drug safety profile analysis combining adverse events, labeling, and recalls"""
    
    safety_profile = {
        "drug_name": drug_name,
        "analysis_date": datetime.now().strftime("%Y-%m-%d"),
        "adverse_events": {},
        "labeling_warnings": {},
        "recall_history": {},
        "safety_summary": {}
    }
    
    # Get adverse events data
    if include_adverse_events:
        try:
            ae_result = await search_drug_adverse_events(
                drug_name=drug_name,
                limit=50,
                serious_only=serious_events_only,
                date_range_days=365
            )
            
            if ae_result["status"] == "success":
                events = ae_result["adverse_events"]
                
                # Analyze adverse events
                reaction_counts = {}
                outcome_counts = {}
                serious_counts = {}
                
                for event in events:
                    # Count reactions
                    for reaction in event.get("reactions", []):
                        term = reaction.get("term", "Unknown")
                        reaction_counts[term] = reaction_counts.get(term, 0) + 1
                    
                    # Count outcomes
                    for reaction in event.get("reactions", []):
                        outcome = reaction.get("outcome", "Unknown")
                        outcome_counts[outcome] = outcome_counts.get(outcome, 0) + 1
                    
                    # Count serious criteria
                    for criteria in event.get("serious_criteria", []):
                        serious_counts[criteria] = serious_counts.get(criteria, 0) + 1
                
                safety_profile["adverse_events"] = {
                    "total_reports": ae_result["total_found"],
                    "analyzed_reports": len(events),
                    "most_common_reactions": dict(sorted(reaction_counts.items(), key=lambda x: x[1], reverse=True)[:10]),
                    "outcomes_distribution": outcome_counts,
                    "serious_criteria_distribution": serious_counts,
                    "data_source": "FDA Adverse Event Reporting System (FAERS)"
                }
            else:
                safety_profile["adverse_events"] = {"error": ae_result.get("error", "Unknown error")}
        except Exception as e:
            safety_profile["adverse_events"] = {"error": str(e)}
    
    # Get labeling warnings
    if include_labeling:
        try:
            labeling_result = await get_drug_labeling_info(
                drug_name=drug_name,
                limit=3
            )
            
            if labeling_result["status"] == "success":
                labeling_data = labeling_result["labeling_info"]
                
                # Extract key safety information
                all_warnings = []
                all_contraindications = []
                all_adverse_reactions = []
                boxed_warnings = []
                
                for label in labeling_data:
                    sections = label.get("sections", {})
                    
                    # Collect warnings
                    if "warnings" in sections:
                        all_warnings.extend(sections["warnings"])
                    if "warnings_and_cautions" in sections:
                        all_warnings.extend(sections["warnings_and_cautions"])
                    if "boxed_warning" in sections:
                        boxed_warnings.extend(sections["boxed_warning"])
                    
                    # Collect contraindications
                    if "contraindications" in sections:
                        all_contraindications.extend(sections["contraindications"])
                    
                    # Collect adverse reactions
                    if "adverse_reactions" in sections:
                        all_adverse_reactions.extend(sections["adverse_reactions"])
                
                safety_profile["labeling_warnings"] = {
                    "boxed_warnings": boxed_warnings,
                    "warnings": all_warnings,
                    "contraindications": all_contraindications,
                    "labeled_adverse_reactions": all_adverse_reactions,
                    "labels_analyzed": len(labeling_data)
                }
            else:
                safety_profile["labeling_warnings"] = {"error": labeling_result.get("error", "Unknown error")}
        except Exception as e:
            safety_profile["labeling_warnings"] = {"error": str(e)}
    
    # Get recall history
    if include_recalls:
        try:
            recall_result = await get_drug_recalls_enforcement(
                drug_name=drug_name,
                limit=20,
                date_range_days=1825  # 5 years
            )
            
            if recall_result["status"] == "success":
                recalls = recall_result["enforcement_actions"]
                
                # Analyze recalls
                status_counts = {}
                class_counts = {}
                reason_counts = {}
                
                for recall in recalls:
                    status = recall.get("status", "Unknown")
                    classification = recall.get("classification", "Unknown")
                    reason = recall.get("reason_for_recall", "Unknown")
                    
                    status_counts[status] = status_counts.get(status, 0) + 1
                    class_counts[classification] = class_counts.get(classification, 0) + 1
                    reason_counts[reason] = reason_counts.get(reason, 0) + 1
                
                safety_profile["recall_history"] = {
                    "total_recalls": len(recalls),
                    "status_distribution": status_counts,
                    "classification_distribution": class_counts,
                    "top_recall_reasons": dict(sorted(reason_counts.items(), key=lambda x: x[1], reverse=True)[:5]),
                    "recent_recalls": recalls[:5]  # Most recent 5 recalls
                }
            else:
                safety_profile["recall_history"] = {"error": recall_result.get("error", "Unknown error")}
        except Exception as e:
            safety_profile["recall_history"] = {"error": str(e)}
    
    # Generate safety summary
    try:
        summary = {
            "overall_risk_assessment": "Analysis completed",
            "key_findings": [],
            "recommendations": []
        }
        
        # Analyze adverse events findings
        if "error" not in safety_profile["adverse_events"]:
            ae_data = safety_profile["adverse_events"]
            total_reports = ae_data.get("total_reports", 0)
            
            if total_reports > 1000:
                summary["key_findings"].append(f"High volume of adverse event reports ({total_reports:,} total)")
            elif total_reports > 100:
                summary["key_findings"].append(f"Moderate volume of adverse event reports ({total_reports:,} total)")
            else:
                summary["key_findings"].append(f"Low volume of adverse event reports ({total_reports:,} total)")
            
            # Check for serious outcomes
            outcomes = ae_data.get("outcomes_distribution", {})
            if "Fatal" in outcomes and outcomes["Fatal"] > 0:
                summary["key_findings"].append(f"Fatal outcomes reported: {outcomes['Fatal']} cases")
                summary["recommendations"].append("Review fatal cases for potential safety signals")
        
        # Analyze labeling warnings
        if "error" not in safety_profile["labeling_warnings"]:
            labeling_data = safety_profile["labeling_warnings"]
            boxed_warnings = labeling_data.get("boxed_warnings", [])
            
            if any(warning for warning in boxed_warnings if warning != "No boxed warning"):
                summary["key_findings"].append("FDA-required boxed warning present")
                summary["recommendations"].append("Pay special attention to boxed warning requirements")
        
        # Analyze recall history
        if "error" not in safety_profile["recall_history"]:
            recall_data = safety_profile["recall_history"]
            total_recalls = recall_data.get("total_recalls", 0)
            
            if total_recalls > 0:
                summary["key_findings"].append(f"Recall history: {total_recalls} enforcement actions in past 5 years")
                
                class_dist = recall_data.get("classification_distribution", {})
                if "Class I" in class_dist and class_dist["Class I"] > 0:
                    summary["recommendations"].append("Review Class I recalls for serious safety concerns")
        
        safety_profile["safety_summary"] = summary
        
    except Exception as e:
        safety_profile["safety_summary"] = {"error": f"Summary generation failed: {str(e)}"}
    
    return {
        "status": "success",
        "safety_profile": safety_profile,
        "analysis_scope": {
            "adverse_events_included": include_adverse_events,
            "labeling_included": include_labeling,
            "recalls_included": include_recalls,
            "serious_events_only": serious_events_only
        },
        "disclaimer": "This analysis is based on publicly available FDA data. It should not replace professional medical or regulatory advice."
    }

async def get_drug_administration_routes() -> Dict[str, Any]:
    """Get list of drug administration routes with their codes"""
    return {
        "status": "success",
        "administration_routes": [
            {
                "code": code,
                "description": description
            }
            for code, description in DRUG_ROUTES.items()
        ],
        "total_routes": len(DRUG_ROUTES),
        "usage_note": "Use these codes when filtering adverse events by administration route"
    }

async def get_adverse_event_outcomes() -> Dict[str, Any]:
    """Get list of adverse event outcome codes and their meanings"""
    return {
        "status": "success",
        "outcome_codes": [
            {
                "code": code,
                "description": description
            }
            for code, description in ADVERSE_EVENT_OUTCOMES.items()
        ],
        "serious_criteria": [
            {
                "code": code,
                "description": description
            }
            for code, description in SERIOUS_CRITERIA.items()
        ],
        "usage_note": "Use these codes when interpreting adverse event outcomes and seriousness criteria"
    }

async def search_device_adverse_events(
    device_name: str = Field(description="Medical device name or type to search for adverse events"),
    limit: int = Field(default=10, description="Maximum number of results to return"),
    date_range_days: Optional[int] = Field(default=365, description="Number of days back to search")
) -> Dict[str, Any]:
    """Search for medical device adverse events reported to FDA"""
    
    # Build search query
    search_terms = []
    
    # Device name search
    device_search = f"(device.generic_name:\"{device_name}\" OR device.brand_name:\"{device_name}\" OR device.manufacturer_d_name:\"{device_name}\")"
    search_terms.append(device_search)
    
    # Date range filter
    if date_range_days:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=date_range_days)
        date_filter = f"date_received:[{start_date.strftime('%Y-%m-%d')}+TO+{end_date.strftime('%Y-%m-%d')}]"
        search_terms.append(date_filter)
    
    search_query = "+AND+".join(search_terms)
    
    params = {
        "search": search_query,
        "limit": min(limit, 1000)
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(ENDPOINTS["device_adverse_events"], params=params, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Process device adverse event results
                    device_events = []
                    results = data.get("results", [])
                    
                    for event in results:
                        if isinstance(event, dict):
                            # Extract device information
                            device_info = event.get("device", [])
                            if not isinstance(device_info, list):
                                device_info = [device_info] if device_info else []
                            
                            # Extract patient information
                            patient = event.get("patient", {})
                            
                            processed_event = {
                                "report_number": event.get("report_number", "Unknown"),
                                "date_received": event.get("date_received", "Unknown"),
                                "event_type": event.get("event_type", "Unknown"),
                                "report_source": event.get("report_source_code", "Unknown"),
                                "devices": [],
                                "patient_info": {
                                    "age": patient.get("patient_age", "Unknown"),
                                    "sex": patient.get("patient_sex", "Unknown"),
                                    "weight": patient.get("patient_weight", "Unknown")
                                },
                                "adverse_event_flag": event.get("adverse_event_flag", "Unknown"),
                                "product_problem_flag": event.get("product_problem_flag", "Unknown")
                            }
                            
                            # Process devices
                            for device in device_info:
                                if isinstance(device, dict):
                                    device_data = {
                                        "generic_name": device.get("generic_name", "Unknown"),
                                        "brand_name": device.get("brand_name", "Unknown"),
                                        "manufacturer": device.get("manufacturer_d_name", "Unknown"),
                                        "model_number": device.get("model_number", "Unknown"),
                                        "catalog_number": device.get("catalog_number", "Unknown"),
                                        "device_class": device.get("device_class", "Unknown"),
                                        "implant_flag": device.get("implant_flag", "Unknown"),
                                        "date_removed": device.get("date_removed_flag", "Unknown")
                                    }
                                    
                                    # Add OpenFDA information if available
                                    openfda = device.get("openfda", {})
                                    if openfda:
                                        device_data["fda_info"] = {
                                            "device_name": openfda.get("device_name", []),
                                            "medical_specialty": openfda.get("medical_specialty_description", []),
                                            "regulation_number": openfda.get("regulation_number", []),
                                            "device_class": openfda.get("device_class", [])
                                        }
                                    
                                    processed_event["devices"].append(device_data)
                            
                            device_events.append(processed_event)
                    
                    return {
                        "status": "success",
                        "device_name": device_name,
                        "device_events": device_events,
                        "total_found": data.get("meta", {}).get("results", {}).get("total", 0),
                        "returned_count": len(device_events),
                        "disclaimer": "This data is from FDA's MAUDE database. Reports do not necessarily mean the device caused the adverse event."
                    }
                else:
                    error_text = await response.text()
                    return {
                        "status": "error",
                        "error": f"API request failed with status {response.status}",
                        "details": error_text[:500],
                        "device_name": device_name
                    }
        except Exception as e:
            return {
                "status": "error",
                "error": f"Request failed: {str(e)}",
                "device_name": device_name
            }

async def get_api_capabilities() -> Dict[str, Any]:
    """Get comprehensive information about OpenFDA API capabilities"""
    
    # Test API connectivity
    api_test = await test_openfda_api()
    
    return {
        "api_info": {
            "name": "OpenFDA API",
            "base_url": BASE_URL,
            "description": "Provides access to FDA's public datasets including drug adverse events, labeling, recalls, and enforcement actions",
            "documentation": "https://open.fda.gov/apis/",
            "data_source": "U.S. Food and Drug Administration (FDA)"
        },
        "endpoints": ENDPOINTS,
        "capabilities": {
            "drug_adverse_events": "Search FDA Adverse Event Reporting System (FAERS) data",
            "drug_labeling": "Access FDA-approved drug labeling information",
            "drug_enforcement": "Search drug recalls and enforcement actions",
            "device_adverse_events": "Search medical device adverse events (MAUDE database)",
            "device_enforcement": "Search device recalls and enforcement actions",
            "food_adverse_events": "Search food adverse events",
            "food_enforcement": "Search food recalls and enforcement actions"
        },
        "data_types": {
            "adverse_events": "Reports of adverse reactions to drugs and devices",
            "labeling": "FDA-approved product labeling and package inserts",
            "enforcement": "Recalls, market withdrawals, and safety alerts",
            "ndc": "National Drug Code directory",
            "drugsfda": "FDA-approved drug products"
        },
        "search_features": {
            "field_search": "Search specific fields using field:value syntax",
            "date_ranges": "Filter by date ranges using [start+TO+end] syntax",
            "boolean_operators": "Use AND, OR, NOT for complex queries",
            "wildcards": "Use * for wildcard searches",
            "exact_phrases": "Use quotes for exact phrase matching"
        },
        "outcome_codes": ADVERSE_EVENT_OUTCOMES,
        "serious_criteria": SERIOUS_CRITERIA,
        "administration_routes": dict(list(DRUG_ROUTES.items())[:10]),  # Show first 10 routes
        "api_status": api_test,
        "use_cases": [
            "Drug safety surveillance and pharmacovigilance",
            "Adverse event analysis and signal detection",
            "Regulatory compliance and labeling review",
            "Recall monitoring and risk assessment",
            "Medical device safety analysis",
            "Post-market safety surveillance",
            "Clinical research and drug development support"
        ],
        "data_limitations": {
            "reporting_bias": "Adverse events are voluntarily reported and may be underreported",
            "causality": "Reports do not establish causal relationship between product and event",
            "completeness": "Not all adverse events are reported to FDA",
            "quality": "Report quality varies based on source and completeness"
        }
    }

def register_openfda_tools(mcp: FastMCP) -> None:
    """Register all OpenFDA API tools with the MCP server."""
    mcp.tool()(test_openfda_api)
    mcp.tool()(search_drug_adverse_events)
    mcp.tool()(get_drug_labeling_info)
    mcp.tool()(get_drug_recalls_enforcement)
    mcp.tool()(analyze_drug_safety_profile)
    mcp.tool()(get_drug_administration_routes)
    mcp.tool()(get_adverse_event_outcomes)
    mcp.tool()(search_device_adverse_events)
    mcp.tool()(get_api_capabilities)
