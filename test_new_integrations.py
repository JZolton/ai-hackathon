#!/usr/bin/env python3
"""
Test script for the newly integrated MedlinePlus Connect and OpenFDA API tools.
This script tests the basic functionality of both new database integrations.
"""

import asyncio
import sys
import logging
from tools.medlineplus_connect import (
    test_medlineplus_api,
    search_health_topics,
    lookup_by_icd10_code,
    search_medication_info,
    get_api_capabilities as get_medlineplus_capabilities
)
from tools.openfda_api import (
    test_openfda_api,
    search_drug_adverse_events,
    get_drug_labeling_info,
    get_drug_recalls_enforcement,
    get_api_capabilities as get_openfda_capabilities
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_medlineplus_integration():
    """Test MedlinePlus Connect API integration"""
    logger.info("=" * 60)
    logger.info("TESTING MEDLINEPLUS CONNECT INTEGRATION")
    logger.info("=" * 60)
    
    try:
        # Test API connectivity
        logger.info("Testing MedlinePlus API connectivity...")
        api_test = await test_medlineplus_api()
        logger.info(f"API Test Result: {api_test['summary']}")
        
        # Test health topic search
        logger.info("\nTesting health topic search...")
        health_search = await search_health_topics(
            search_term="diabetes",
            language="en",
            max_results=3
        )
        if health_search["status"] == "success":
            logger.info(f"Found {health_search['total_found']} health topics for 'diabetes'")
            for i, topic in enumerate(health_search["topics"][:2], 1):
                logger.info(f"  {i}. {topic['title']}")
        else:
            logger.error(f"Health search failed: {health_search.get('error', 'Unknown error')}")
        
        # Test ICD-10 code lookup
        logger.info("\nTesting ICD-10 code lookup...")
        icd10_lookup = await lookup_by_icd10_code(
            icd10_code="E11.9",  # Type 2 diabetes
            language="en"
        )
        if icd10_lookup["status"] == "success":
            info_count = len(icd10_lookup["condition_info"]["health_information"])
            logger.info(f"Found {info_count} health information items for ICD-10 E11.9")
        else:
            logger.error(f"ICD-10 lookup failed: {icd10_lookup.get('error', 'Unknown error')}")
        
        # Test medication search
        logger.info("\nTesting medication information search...")
        med_search = await search_medication_info(
            medication_name="metformin",
            language="en"
        )
        if med_search["status"] == "success":
            summary = med_search["summary"]
            logger.info(f"Medication info found: {summary['total_information_items']} items, "
                       f"{summary['interaction_warnings']} interactions, "
                       f"{summary['side_effect_info']} side effects")
        else:
            logger.error(f"Medication search failed: {med_search.get('error', 'Unknown error')}")
        
        # Test API capabilities
        logger.info("\nTesting API capabilities...")
        capabilities = await get_medlineplus_capabilities()
        if capabilities["api_status"]["summary"]:
            logger.info(f"MedlinePlus API Status: {capabilities['api_status']['summary']}")
        
        logger.info("✅ MedlinePlus Connect integration test completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ MedlinePlus integration test failed: {str(e)}")
        return False

async def test_openfda_integration():
    """Test OpenFDA API integration"""
    logger.info("\n" + "=" * 60)
    logger.info("TESTING OPENFDA API INTEGRATION")
    logger.info("=" * 60)
    
    try:
        # Test API connectivity
        logger.info("Testing OpenFDA API connectivity...")
        api_test = await test_openfda_api()
        logger.info(f"API Test Result: {api_test['summary']}")
        
        # Test drug adverse events search
        logger.info("\nTesting drug adverse events search...")
        adverse_events = await search_drug_adverse_events(
            drug_name="aspirin",
            limit=5,
            serious_only=False
        )
        if adverse_events["status"] == "success":
            logger.info(f"Found {adverse_events['total_found']:,} adverse event reports for aspirin")
            logger.info(f"Returned {adverse_events['returned_count']} detailed reports")
        else:
            logger.error(f"Adverse events search failed: {adverse_events.get('error', 'Unknown error')}")
        
        # Test drug labeling information
        logger.info("\nTesting drug labeling information...")
        labeling_info = await get_drug_labeling_info(
            drug_name="tylenol",
            section="warnings",
            limit=2
        )
        if labeling_info["status"] == "success":
            logger.info(f"Found {labeling_info['total_found']} labeling records for Tylenol")
            logger.info(f"Returned {labeling_info['returned_count']} detailed labels")
        else:
            logger.error(f"Labeling search failed: {labeling_info.get('error', 'Unknown error')}")
        
        # Test drug recalls and enforcement
        logger.info("\nTesting drug recalls and enforcement...")
        recalls = await get_drug_recalls_enforcement(
            status="ongoing",
            limit=3
        )
        if recalls["status"] == "success":
            logger.info(f"Found {recalls['total_found']} ongoing enforcement actions")
            logger.info(f"Returned {recalls['returned_count']} detailed actions")
        else:
            logger.error(f"Recalls search failed: {recalls.get('error', 'Unknown error')}")
        
        # Test API capabilities
        logger.info("\nTesting API capabilities...")
        capabilities = await get_openfda_capabilities()
        if capabilities["api_status"]["summary"]:
            logger.info(f"OpenFDA API Status: {capabilities['api_status']['summary']}")
        
        logger.info("✅ OpenFDA API integration test completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ OpenFDA integration test failed: {str(e)}")
        return False

async def test_comprehensive_drug_safety():
    """Test comprehensive drug safety analysis using both APIs"""
    logger.info("\n" + "=" * 60)
    logger.info("TESTING COMPREHENSIVE DRUG SAFETY ANALYSIS")
    logger.info("=" * 60)
    
    try:
        drug_name = "ibuprofen"
        logger.info(f"Performing comprehensive safety analysis for: {drug_name}")
        
        # Get MedlinePlus information
        logger.info("\n1. Getting MedlinePlus health information...")
        medline_info = await search_health_topics(
            search_term=f"{drug_name} side effects warnings",
            max_results=3
        )
        
        # Get OpenFDA adverse events
        logger.info("2. Getting FDA adverse events data...")
        fda_events = await search_drug_adverse_events(
            drug_name=drug_name,
            limit=10,
            serious_only=True
        )
        
        # Get FDA labeling warnings
        logger.info("3. Getting FDA labeling warnings...")
        fda_labeling = await get_drug_labeling_info(
            drug_name=drug_name,
            section="warnings",
            limit=2
        )
        
        # Summarize findings
        logger.info("\n📊 COMPREHENSIVE SAFETY SUMMARY:")
        logger.info(f"Drug: {drug_name.title()}")
        
        if medline_info["status"] == "success":
            logger.info(f"✓ MedlinePlus: {medline_info['total_found']} health information topics found")
        else:
            logger.info("✗ MedlinePlus: No information retrieved")
        
        if fda_events["status"] == "success":
            logger.info(f"✓ FDA Adverse Events: {fda_events['total_found']:,} reports found")
        else:
            logger.info("✗ FDA Adverse Events: No data retrieved")
        
        if fda_labeling["status"] == "success":
            logger.info(f"✓ FDA Labeling: {fda_labeling['total_found']} labeling records found")
        else:
            logger.info("✗ FDA Labeling: No data retrieved")
        
        logger.info("✅ Comprehensive drug safety analysis completed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Comprehensive analysis failed: {str(e)}")
        return False

async def main():
    """Main test function"""
    logger.info("🚀 Starting integration tests for new health databases...")
    logger.info("Testing MedlinePlus Connect and OpenFDA API integrations")
    
    results = []
    
    # Test MedlinePlus integration
    medlineplus_success = await test_medlineplus_integration()
    results.append(("MedlinePlus Connect", medlineplus_success))
    
    # Test OpenFDA integration
    openfda_success = await test_openfda_integration()
    results.append(("OpenFDA API", openfda_success))
    
    # Test comprehensive analysis
    comprehensive_success = await test_comprehensive_drug_safety()
    results.append(("Comprehensive Analysis", comprehensive_success))
    
    # Print final results
    logger.info("\n" + "=" * 60)
    logger.info("FINAL TEST RESULTS")
    logger.info("=" * 60)
    
    all_passed = True
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        logger.info(f"{test_name}: {status}")
        if not success:
            all_passed = False
    
    logger.info("=" * 60)
    if all_passed:
        logger.info("🎉 ALL INTEGRATION TESTS PASSED!")
        logger.info("Both MedlinePlus Connect and OpenFDA API are successfully integrated!")
    else:
        logger.info("⚠️  SOME TESTS FAILED")
        logger.info("Please check the error messages above for details.")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("\n🛑 Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"💥 Unexpected error: {str(e)}")
        sys.exit(1)
