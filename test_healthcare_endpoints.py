#!/usr/bin/env python3
"""
Test script for Healthcare.gov API endpoints
"""

import asyncio
import aiohttp
import json
from datetime import datetime
from tools.healthcare_gov import (
    test_healthcare_api,
    get_all_schemas,
    get_schema_items,
    search_catalog,
    get_search_facets,
    query_datastore,
    get_healthcare_categories
)

async def test_all_endpoints():
    """Test all healthcare.gov API endpoints"""
    print("=" * 60)
    print("HEALTHCARE.GOV API ENDPOINT TESTING")
    print("=" * 60)
    print(f"Test started at: {datetime.now()}")
    print()
    
    # Test 1: Basic API connectivity
    print("1. Testing basic API connectivity...")
    try:
        result = await test_healthcare_api()
        print(f"   Status: {result.get('summary', 'Unknown')}")
        
        for endpoint, details in result.get('results', {}).items():
            status = details.get('status', 'unknown')
            status_code = details.get('status_code', 'N/A')
            print(f"   - {endpoint}: {status} (HTTP {status_code})")
        print()
    except Exception as e:
        print(f"   ERROR: {e}")
        print()
    
    # Test 2: Get all schemas
    print("2. Testing schemas endpoint...")
    try:
        result = await get_all_schemas()
        if result['status'] == 'success':
            schemas = result.get('schemas', [])
            print(f"   Found {len(schemas)} schemas")
            if schemas:
                print("   Available schemas:")
                for schema in schemas[:5]:  # Show first 5
                    if isinstance(schema, dict):
                        name = schema.get('name', schema.get('id', 'Unknown'))
                        print(f"     - {name}")
                    else:
                        print(f"     - {schema}")
        else:
            print(f"   ERROR: {result.get('error', 'Unknown error')}")
        print()
    except Exception as e:
        print(f"   ERROR: {e}")
        print()
    
    # Test 3: Get dataset schema items
    print("3. Testing dataset schema items...")
    try:
        result = await get_schema_items("dataset", limit=5)
        if result['status'] == 'success':
            items = result.get('items', [])
            print(f"   Found {len(items)} dataset items")
            if items:
                print("   Sample datasets:")
                for item in items[:3]:
                    if isinstance(item, dict):
                        title = item.get('title', item.get('name', 'Untitled'))
                        identifier = item.get('identifier', 'No ID')
                        print(f"     - {title} (ID: {identifier})")
        else:
            print(f"   ERROR: {result.get('error', 'Unknown error')}")
        print()
    except Exception as e:
        print(f"   ERROR: {e}")
        print()
    
    # Test 4: Search catalog
    print("4. Testing catalog search...")
    try:
        result = await search_catalog(query="insurance", limit=3)
        if result['status'] == 'success':
            results = result.get('results', {})
            if isinstance(results, dict):
                datasets = results.get('dataset', [])
                print(f"   Found {len(datasets)} datasets matching 'insurance'")
                for dataset in datasets[:2]:
                    if isinstance(dataset, dict):
                        title = dataset.get('title', 'Untitled')
                        print(f"     - {title}")
            else:
                print(f"   Search returned: {type(results)}")
        else:
            print(f"   ERROR: {result.get('error', 'Unknown error')}")
        print()
    except Exception as e:
        print(f"   ERROR: {e}")
        print()
    
    # Test 5: Get search facets
    print("5. Testing search facets...")
    try:
        result = await get_search_facets()
        if result['status'] == 'success':
            facets = result.get('facets', {})
            print(f"   Available facets: {list(facets.keys()) if isinstance(facets, dict) else 'None'}")
        else:
            print(f"   ERROR: {result.get('error', 'Unknown error')}")
        print()
    except Exception as e:
        print(f"   ERROR: {e}")
        print()
    
    # Test 6: Test datastore query (basic)
    print("6. Testing datastore query...")
    try:
        result = await query_datastore(limit=1)
        if result['status'] == 'success':
            data = result.get('data', {})
            print(f"   Datastore query successful, returned: {type(data)}")
            if isinstance(data, list) and data:
                print(f"   Sample record keys: {list(data[0].keys()) if isinstance(data[0], dict) else 'N/A'}")
        else:
            print(f"   ERROR: {result.get('error', 'Unknown error')}")
        print()
    except Exception as e:
        print(f"   ERROR: {e}")
        print()
    
    # Test 7: Healthcare categories
    print("7. Testing healthcare categories...")
    try:
        result = await get_healthcare_categories()
        if result['status'] == 'success':
            categories = result.get('categories', [])
            print(f"   Available categories: {len(categories)}")
            for cat in categories[:3]:
                print(f"     - {cat.get('name', 'Unknown')}: {cat.get('description', 'No description')}")
        else:
            print(f"   ERROR: {result.get('error', 'Unknown error')}")
        print()
    except Exception as e:
        print(f"   ERROR: {e}")
        print()
    
    print("=" * 60)
    print("TESTING COMPLETE")
    print("=" * 60)

async def test_recent_data():
    """Test for recent data availability (May 2025)"""
    print("\n" + "=" * 60)
    print("TESTING FOR RECENT DATA (MAY 2025)")
    print("=" * 60)
    
    # Search for recent datasets
    search_terms = ["2025", "2024", "recent", "current", "latest"]
    
    for term in search_terms:
        print(f"\nSearching for '{term}'...")
        try:
            result = await search_catalog(query=term, limit=5)
            if result['status'] == 'success':
                results = result.get('results', {})
                if isinstance(results, dict):
                    datasets = results.get('dataset', [])
                    print(f"   Found {len(datasets)} datasets")
                    
                    for dataset in datasets:
                        if isinstance(dataset, dict):
                            title = dataset.get('title', 'Untitled')
                            modified = dataset.get('modified', 'Unknown date')
                            issued = dataset.get('issued', 'Unknown date')
                            print(f"     - {title}")
                            print(f"       Modified: {modified}")
                            print(f"       Issued: {issued}")
                            print()
            else:
                print(f"   ERROR: {result.get('error', 'Unknown error')}")
        except Exception as e:
            print(f"   ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(test_all_endpoints())
    asyncio.run(test_recent_data())
