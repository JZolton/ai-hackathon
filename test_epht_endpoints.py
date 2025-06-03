import asyncio
import aiohttp
import json

async def test_all_epht_endpoints():
    """Test all EPHT endpoints to identify working ones"""
    base_url = "https://ephtracking.cdc.gov/apigateway/api/v1"
    
    endpoints_to_test = [
        {
            "name": "getMeasures",
            "url": f"{base_url}/getMeasures",
            "method": "GET",
            "params": None
        },
        {
            "name": "getCoreHolder",
            "url": f"{base_url}/getCoreHolder",
            "method": "GET", 
            "params": {
                "measureId": "296",
                "geographicTypeId": "state",
                "temporalTypeId": "annual",
                "yearFilter": "2020"
            }
        },
        {
            "name": "getGeographicItems",
            "url": f"{base_url}/getGeographicItems",
            "method": "GET",
            "params": {"measureId": "296"}
        },
        {
            "name": "getTemporalItems", 
            "url": f"{base_url}/getTemporalItems",
            "method": "GET",
            "params": {"measureId": "296"}
        },
        {
            "name": "getContentAreas",
            "url": f"{base_url}/getContentAreas",
            "method": "GET",
            "params": None
        },
        {
            "name": "getIndicators",
            "url": f"{base_url}/getIndicators",
            "method": "GET", 
            "params": {"contentAreaId": "1"}
        }
    ]
    
    working_endpoints = []
    broken_endpoints = []
    
    async with aiohttp.ClientSession() as session:
        for endpoint in endpoints_to_test:
            try:
                print(f"\nTesting {endpoint['name']}...")
                
                if endpoint['method'] == 'GET':
                    async with session.get(
                        endpoint['url'], 
                        params=endpoint['params'], 
                        timeout=aiohttp.ClientTimeout(total=15)
                    ) as response:
                        print(f"  Status: {response.status}")
                        
                        if response.status == 200:
                            data = await response.json()
                            if isinstance(data, dict) and data.get('code') == 410:
                                print(f"  Result: DISABLED (410 Gone)")
                                broken_endpoints.append({
                                    "name": endpoint['name'],
                                    "status": "disabled",
                                    "reason": "410 Gone - Call is disabled"
                                })
                            elif isinstance(data, dict) and data.get('code') == 400:
                                print(f"  Result: BAD REQUEST (400)")
                                broken_endpoints.append({
                                    "name": endpoint['name'],
                                    "status": "bad_request", 
                                    "reason": "400 Bad Request - Invalid Call"
                                })
                            else:
                                print(f"  Result: WORKING - Got {len(data) if isinstance(data, list) else 'data'}")
                                working_endpoints.append({
                                    "name": endpoint['name'],
                                    "url": endpoint['url'],
                                    "params": endpoint['params'],
                                    "data_type": type(data).__name__,
                                    "record_count": len(data) if isinstance(data, list) else None
                                })
                        else:
                            print(f"  Result: HTTP ERROR {response.status}")
                            broken_endpoints.append({
                                "name": endpoint['name'],
                                "status": f"http_error_{response.status}",
                                "reason": f"HTTP {response.status}"
                            })
                            
            except Exception as e:
                print(f"  Result: EXCEPTION - {e}")
                broken_endpoints.append({
                    "name": endpoint['name'],
                    "status": "exception",
                    "reason": str(e)
                })
    
    print(f"\n{'='*50}")
    print("SUMMARY:")
    print(f"Working endpoints: {len(working_endpoints)}")
    print(f"Broken endpoints: {len(broken_endpoints)}")
    
    if working_endpoints:
        print(f"\n✅ WORKING ENDPOINTS:")
        for ep in working_endpoints:
            print(f"  - {ep['name']}: {ep['data_type']} with {ep['record_count']} records")
    
    if broken_endpoints:
        print(f"\n❌ BROKEN ENDPOINTS:")
        for ep in broken_endpoints:
            print(f"  - {ep['name']}: {ep['reason']}")
    
    return {
        "working": working_endpoints,
        "broken": broken_endpoints,
        "summary": {
            "total_tested": len(endpoints_to_test),
            "working_count": len(working_endpoints),
            "broken_count": len(broken_endpoints)
        }
    }

if __name__ == "__main__":
    asyncio.run(test_all_epht_endpoints())
