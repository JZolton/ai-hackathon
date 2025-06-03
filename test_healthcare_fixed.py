#!/usr/bin/env python3
"""
Fixed test script for Healthcare.gov API endpoints
"""

import asyncio
import aiohttp
import json
from datetime import datetime

# Data.Healthcare.gov API base URL
BASE_URL = "https://data.healthcare.gov/api/1"

async def test_basic_endpoints():
    """Test basic API endpoints to see what's working"""
    print("=" * 60)
    print("HEALTHCARE.GOV API BASIC TESTING")
    print("=" * 60)
    print(f"Test started at: {datetime.now()}")
    print()
    
    async with aiohttp.ClientSession() as session:
        # Test 1: Schemas endpoint
        print("1. Testing schemas endpoint...")
        try:
            async with session.get(f"{BASE_URL}/metastore/schemas", timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"   ✓ Success: Found {len(data)} schemas")
                    if data:
                        print("   Available schemas:")
                        for schema in data[:5]:
                            if isinstance(schema, str):
                                print(f"     - {schema}")
                            elif isinstance(schema, dict):
                                name = schema.get('name', schema.get('id', 'Unknown'))
                                print(f"     - {name}")
                else:
                    print(f"   ✗ Failed: HTTP {response.status}")
        except Exception as e:
            print(f"   ✗ Error: {e}")
        print()
        
        # Test 2: Dataset items
        print("2. Testing dataset items...")
        try:
            async with session.get(f"{BASE_URL}/metastore/schemas/dataset/items?limit=5", timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"   ✓ Success: Found {len(data)} datasets")
                    if data:
                        print("   Sample datasets:")
                        for item in data[:3]:
                            if isinstance(item, dict):
                                title = item.get('title', item.get('name', 'Untitled'))
                                identifier = item.get('identifier', 'No ID')
                                modified = item.get('modified', 'Unknown')
                                print(f"     - {title} (ID: {identifier})")
                                print(f"       Modified: {modified}")
                else:
                    print(f"   ✗ Failed: HTTP {response.status}")
        except Exception as e:
            print(f"   ✗ Error: {e}")
        print()
        
        # Test 3: Search endpoint
        print("3. Testing search endpoint...")
        try:
            async with session.get(f"{BASE_URL}/search?limit=5", timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"   ✓ Success: Search endpoint working")
                    if isinstance(data, dict):
                        total = data.get('total', 0)
                        results = data.get('results', {})
                        print(f"   Total available: {total}")
                        if isinstance(results, dict):
                            for key, value in results.items():
                                if isinstance(value, list):
                                    print(f"   {key}: {len(value)} items")
                else:
                    print(f"   ✗ Failed: HTTP {response.status}")
        except Exception as e:
            print(f"   ✗ Error: {e}")
        print()
        
        # Test 4: Search for specific terms
        print("4. Testing search for healthcare terms...")
        search_terms = ["marketplace", "insurance", "health", "plan"]
        for term in search_terms:
            try:
                async with session.get(f"{BASE_URL}/search?query={term}&limit=3", timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        data = await response.json()
                        if isinstance(data, dict):
                            results = data.get('results', {})
                            if isinstance(results, dict):
                                datasets = results.get('dataset', [])
                                print(f"   '{term}': {len(datasets)} datasets found")
                                for dataset in datasets[:1]:  # Show first result
                                    if isinstance(dataset, dict):
                                        title = dataset.get('title', 'Untitled')
                                        modified = dataset.get('modified', 'Unknown')
                                        print(f"     - {title} (Modified: {modified})")
                    else:
                        print(f"   '{term}': HTTP {response.status}")
            except Exception as e:
                print(f"   '{term}': Error - {e}")
        print()

async def test_recent_data_availability():
    """Test for recent data availability"""
    print("=" * 60)
    print("TESTING FOR RECENT DATA AVAILABILITY")
    print("=" * 60)
    
    async with aiohttp.ClientSession() as session:
        # Get all datasets and check modification dates
        print("Checking dataset modification dates...")
        try:
            async with session.get(f"{BASE_URL}/metastore/schemas/dataset/items?limit=50", timeout=aiohttp.ClientTimeout(total=15)) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"Analyzing {len(data)} datasets...")
                    
                    recent_datasets = []
                    date_counts = {}
                    
                    for item in data:
                        if isinstance(item, dict):
                            modified = item.get('modified', '')
                            title = item.get('title', 'Untitled')
                            
                            # Extract year from modified date
                            if modified:
                                try:
                                    year = modified[:4]
                                    if year.isdigit():
                                        date_counts[year] = date_counts.get(year, 0) + 1
                                        
                                        # Check for recent data (2024-2025)
                                        if year in ['2024', '2025']:
                                            recent_datasets.append({
                                                'title': title,
                                                'modified': modified,
                                                'identifier': item.get('identifier', 'No ID')
                                            })
                                except:
                                    pass
                    
                    print("\nDataset modification years:")
                    for year in sorted(date_counts.keys(), reverse=True):
                        print(f"   {year}: {date_counts[year]} datasets")
                    
                    if recent_datasets:
                        print(f"\nRecent datasets (2024-2025): {len(recent_datasets)}")
                        for dataset in recent_datasets[:5]:
                            print(f"   - {dataset['title']}")
                            print(f"     Modified: {dataset['modified']}")
                            print(f"     ID: {dataset['identifier']}")
                            print()
                    else:
                        print("\nNo datasets found with 2024-2025 modification dates")
                        
                else:
                    print(f"Failed to get datasets: HTTP {response.status}")
        except Exception as e:
            print(f"Error checking datasets: {e}")

async def test_datastore_access():
    """Test datastore access for actual data"""
    print("=" * 60)
    print("TESTING DATASTORE ACCESS")
    print("=" * 60)
    
    async with aiohttp.ClientSession() as session:
        # Try to access datastore with a simple query
        print("Testing basic datastore query...")
        try:
            async with session.get(f"{BASE_URL}/datastore/query?limit=1", timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"   ✓ Datastore accessible")
                    print(f"   Response type: {type(data)}")
                    if isinstance(data, list) and data:
                        print(f"   Sample record keys: {list(data[0].keys()) if isinstance(data[0], dict) else 'N/A'}")
                    elif isinstance(data, dict):
                        print(f"   Response keys: {list(data.keys())}")
                else:
                    print(f"   ✗ Failed: HTTP {response.status}")
                    error_text = await response.text()
                    print(f"   Error: {error_text[:200]}")
        except Exception as e:
            print(f"   ✗ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_basic_endpoints())
    asyncio.run(test_recent_data_availability())
    asyncio.run(test_datastore_access())
