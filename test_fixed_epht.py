import asyncio
import sys
import os

# Add the tools directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'tools'))

from cdc_epht import get_measure_categories, search_measures_by_topic, get_api_documentation, query_environmental_data

async def test_fixed_epht_tools():
    """Test the fixed EPHT tools to ensure they work without timeouts"""
    
    print("Testing Fixed CDC EPHT Tools")
    print("=" * 40)
    
    # Test 1: get_measure_categories (should work - static data)
    print("\n1. Testing get_measure_categories...")
    try:
        result = await get_measure_categories()
        print(f"   ✅ SUCCESS: Found {len(result['categories'])} categories")
        print(f"   Categories: {list(result['categories'].keys())}")
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
    
    # Test 2: search_measures_by_topic (should work - static search)
    print("\n2. Testing search_measures_by_topic...")
    try:
        result = await search_measures_by_topic("air")
        print(f"   ✅ SUCCESS: Found {result['total_matches']} matches for 'air'")
        if result['category_matches']:
            for category in result['category_matches']:
                print(f"   - {category}")
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
    
    # Test 3: get_api_documentation (should work - static data)
    print("\n3. Testing get_api_documentation...")
    try:
        result = await get_api_documentation()
        print(f"   ✅ SUCCESS: Got documentation for {result['api_info']['name']}")
        print(f"   Base URL: {result['api_info']['base_url']}")
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
    
    # Test 4: query_environmental_data (should return error message - API unavailable)
    print("\n4. Testing query_environmental_data...")
    try:
        result = await query_environmental_data("296", "state", "annual")
        if result['status'] == 'error':
            print(f"   ✅ SUCCESS: Correctly returns error - {result['error']}")
            print(f"   Alternative suggested: {result['alternative']}")
        else:
            print(f"   ❌ UNEXPECTED: Got success when expecting error")
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
    
    print("\n" + "=" * 40)
    print("Test completed!")

if __name__ == "__main__":
    asyncio.run(test_fixed_epht_tools())
