#!/usr/bin/env python3
"""
STAGE 1 ONLY - API Calls Test
Calls all 4 supplier APIs and shows raw results
"""

import json
import os
import requests
from dotenv import load_dotenv
from zeep import Client
from zeep.transports import Transport
from requests import Session
from requests.auth import HTTPBasicAuth

# Load environment
load_dotenv()

PART_NUMBER = "WR55X10025"

print("="*80)
print("STAGE 1: PARALLEL API CALLS")
print("="*80)
print(f"\nPart Number: {PART_NUMBER}\n")

results = {}

# ==============================================================================
# 1. ENCOMPASS API
# ==============================================================================
print("📞 1. Calling Encompass API...")
try:
    payload = {
        "settings": {
            "jsonUser": os.getenv("ENCOMPASS_USERNAME"),
            "jsonPassword": os.getenv("ENCOMPASS_PASSWORD"),
            "programName": "JSON.ITEM.INFORMATION"
        },
        "data": {
            "searchPartNumber": PART_NUMBER
        }
    }
    response = requests.post(
        f"{os.getenv('ENCOMPASS_BASE_URL')}/restfulservice/partsInformation",
        json=payload,
        timeout=30
    )
    if response.status_code == 200:
        data = response.json()
        if data.get('status', {}).get('errorCode') == '100':
            parts = data.get('data', {}).get('parts', [])
            
            # Filter for exact part number match only
            exact_matches = [
                part for part in parts 
                if part.get('partNumber', '').upper() == PART_NUMBER.upper()
            ]
            
            print(f"   Total parts from API: {len(parts)}, Exact matches: {len(exact_matches)}")
            
            results['encompass'] = {'success': True, 'count': len(exact_matches), 'data': exact_matches}
            print(f"   ✅ SUCCESS - Found {len(exact_matches)} exact match(es)")
        else:
            error_msg = data.get('status', {}).get('errorMessage', 'Unknown error')
            results['encompass'] = {'success': False, 'error': error_msg}
            print(f"   ❌ ERROR: {error_msg}")
    else:
        results['encompass'] = {'success': False, 'error': f"HTTP {response.status_code}"}
        print(f"   ❌ HTTP {response.status_code}")
except Exception as e:
    results['encompass'] = {'success': False, 'error': str(e)}
    print(f"   ❌ ERROR: {e}")

# ==============================================================================
# 2. MARCONE API
# ==============================================================================
print("\n📞 2. Calling Marcone API...")
try:
    session = Session()
    session.auth = HTTPBasicAuth(
        os.getenv("MARCONE_PROD_USERNAME"),
        os.getenv("MARCONE_PROD_PASSWORD")
    )
    transport = Transport(session=session)
    wsdl_url = f"{os.getenv('MARCONE_PROD_URL')}/b2b/parts_v2.asmx?WSDL"
    client = Client(wsdl_url, transport=transport)
    
    # Try exact lookup with GE make code
    response = client.service.ExactPartLookup(
        userName=os.getenv("MARCONE_PROD_USERNAME"),
        password=os.getenv("MARCONE_PROD_PASSWORD"),
        make="GEH",
        partNumber=PART_NUMBER
    )
    
    if response and hasattr(response, 'PartInformation_v2'):
        parts = response.PartInformation_v2
        if parts:
            results['marcone'] = {'success': True, 'count': len(parts), 'data': []}
            # Extract key fields
            for part in parts:
                part_info = {
                    'partNumber': getattr(part, 'PartNumber', None),
                    'description': getattr(part, 'PartDescription', None),
                    'manufacturer': getattr(part, 'Make', None),
                    'cost': getattr(part, 'Cost', None),
                    'price': getattr(part, 'CustomerPrice', None),
                }
                results['marcone']['data'].append(part_info)
            print(f"   ✅ SUCCESS - Found {len(parts)} parts")
        else:
            results['marcone'] = {'success': False, 'error': 'No parts found'}
            print(f"   ⚠️  Part not found")
    else:
        results['marcone'] = {'success': False, 'error': 'Invalid response structure'}
        print(f"   ⚠️  Part not found")
except Exception as e:
    results['marcone'] = {'success': False, 'error': str(e)}
    print(f"   ❌ ERROR: {e}")

# ==============================================================================
# 3. RELIABLE PARTS API
# ==============================================================================
print("\n📞 3. Calling Reliable Parts API...")
try:
    url = f"{os.getenv('RELIABLE_PARTS_BASE_URL')}/ws/rest/ReliablePartsBoomiAPI/partSearch/v2/query"
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-API-Key': os.getenv('RELIABLE_PARTS_PART_SEARCH_API_KEY')
    }
    auth = HTTPBasicAuth(
        os.getenv('RELIABLE_PARTS_USERNAME'),
        os.getenv('RELIABLE_PARTS_PASSWORD')
    )
    payload = {
        "searchCriteria": {
            "partNumber": PART_NUMBER
        }
    }
    response = requests.post(url, json=payload, headers=headers, auth=auth, timeout=30, verify=False)
    
    if response.status_code == 200:
        data = response.json()
        if data and isinstance(data, list) and len(data) > 0:
            results['reliable'] = {'success': True, 'count': len(data), 'data': data}
            print(f"   ✅ SUCCESS - Found {len(data)} parts")
        else:
            results['reliable'] = {'success': False, 'error': 'No parts found'}
            print(f"   ⚠️  No parts found")
    else:
        results['reliable'] = {'success': False, 'error': f"HTTP {response.status_code}: {response.text[:100]}"}
        print(f"   ❌ HTTP {response.status_code}")
except Exception as e:
    results['reliable'] = {'success': False, 'error': str(e)}
    print(f"   ❌ ERROR: {e}")

# ==============================================================================
# 4. AMAZON API (Search + Detail for ONE Match)
# ==============================================================================
print("\n📞 4. Calling Amazon API...")
print("   Step 1: Search for part...")
try:
    url = "https://data.unwrangle.com/api/getter/"
    
    # Step 1: Search to get listings
    params = {
        "platform": "amazon_search",
        "search": PART_NUMBER,
        "country": "us",
        "api_key": os.getenv("AMAZON_API_KEY")
    }
    response = requests.get(url, params=params, timeout=30)
    
    if response.status_code == 200:
        data = response.json()
        if data.get("results") and len(data["results"]) > 0:
            search_results = data["results"]
            print(f"   ✅ Found {len(search_results)} listings")
            
            # Step 2: Find first valid ASIN (10 chars, alphanumeric)
            print(f"   Step 2: Finding first valid product...")
            first_valid_asin = None
            
            for item in search_results:
                asin = item.get('asin')
                # Check if valid ASIN (10 characters, alphanumeric)
                if asin and len(asin) == 10 and asin.isalnum():
                    first_valid_asin = asin
                    print(f"   ✅ Found valid ASIN: {asin}")
                    break
            
            if first_valid_asin:
                # Step 3: Get detailed info for the product
                print(f"   Step 3: Fetching detailed product info...")
                try:
                    detail_params = {
                        "platform": "amazon_detail",
                        "asin": first_valid_asin,
                        "country_code": "us",
                        "api_key": os.getenv("AMAZON_API_KEY")
                    }
                    detail_response = requests.get(url, params=detail_params, timeout=30)
                    
                    if detail_response.status_code == 200:
                        detail_data = detail_response.json()
                        results['amazon'] = {'success': True, 'count': 1, 'data': [detail_data]}
                        print(f"   ✅ SUCCESS - Full product details retrieved")
                    else:
                        print(f"   ⚠️ Detail call failed (HTTP {detail_response.status_code}), using search data")
                        results['amazon'] = {'success': True, 'count': len(search_results), 'data': search_results}
                except Exception as e:
                    print(f"   ⚠️ Detail call error: {str(e)[:50]}")
                    results['amazon'] = {'success': True, 'count': len(search_results), 'data': search_results}
            else:
                # No valid ASIN found, use search results
                print(f"   ⚠️ No valid ASIN found, using search results")
                results['amazon'] = {'success': True, 'count': len(search_results), 'data': search_results}
        else:
            results['amazon'] = {'success': False, 'error': 'No results found'}
            print(f"   ⚠️  No results found")
    else:
        results['amazon'] = {'success': False, 'error': f"HTTP {response.status_code}"}
        print(f"   ❌ HTTP {response.status_code}")
except Exception as e:
    results['amazon'] = {'success': False, 'error': str(e)}
    print(f"   ❌ ERROR: {e}")

# ==============================================================================
# SUMMARY
# ==============================================================================
print("\n" + "="*80)
print("STAGE 1 COMPLETE - SUMMARY")
print("="*80)

successful_apis = sum(1 for r in results.values() if r.get('success'))
print(f"\n✅ Successful API calls: {successful_apis}/4\n")

for api_name, result in results.items():
    status = "✅" if result.get('success') else "❌"
    if result.get('success'):
        count = result.get('count', 0)
        print(f"{status} {api_name.upper()}: {count} items")
    else:
        error = result.get('error', 'Unknown error')
        print(f"{status} {api_name.upper()}: {error}")

# ==============================================================================
# DETAILED RESULTS
# ==============================================================================
print("\n" + "="*80)
print("DETAILED RESULTS BY API")
print("="*80)

for api_name, result in results.items():
    print(f"\n{'='*80}")
    print(f"📦 {api_name.upper()}")
    print('='*80)
    
    if result.get('success'):
        print(f"Status: ✅ SUCCESS")
        print(f"Items Found: {result.get('count', 0)}")
        print(f"\nSample Data (first item):")
        print(json.dumps(result['data'][0] if result['data'] else {}, indent=2, default=str)[:500] + "...")
    else:
        print(f"Status: ❌ FAILED")
        print(f"Error: {result.get('error')}")

print("\n" + "="*80)
print("🛑 STOPPING AT STAGE 1 - NO FURTHER PROCESSING")
print("="*80)
print("\nRaw data available in each result. Next stages would be:")
print("  Stage 2: Aggregate data (keep separate)")
print("  Stage 3: OpenAI validation")
print("  Stage 4: Grok validation")
print("  Stage 5: Consensus comparison")
print("  Stage 6: Build final catalog")
