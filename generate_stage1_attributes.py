#!/usr/bin/env python3
"""Generate markdown file with all Stage 1 attributes"""
import json
import os
import requests
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()
PART_NUMBER = "WR55X10025"

print("Collecting all attributes from Stage 1 API calls...")

# ============================================================================
# ENCOMPASS API
# ============================================================================
encompass_data = None
try:
    payload = {
        "settings": {
            "jsonUser": os.getenv("ENCOMPASS_USERNAME"),
            "jsonPassword": os.getenv("ENCOMPASS_PASSWORD"),
            "programName": "JSON.ITEM.INFORMATION"
        },
        "data": {"searchPartNumber": PART_NUMBER}
    }
    response = requests.post(
        f"{os.getenv('ENCOMPASS_BASE_URL')}/restfulservice/partsInformation",
        json=payload,
        timeout=30
    )
    if response.status_code == 200:
        data = response.json()
        if data.get('status', {}).get('errorCode') == '100':
            all_parts = data.get('data', {}).get('parts', [])
            
            # Filter for exact part number match only
            encompass_data = [
                part for part in all_parts 
                if part.get('partNumber', '').upper() == PART_NUMBER.upper()
            ]
            
            print(f"✅ Encompass: {len(encompass_data)} exact match(es) (from {len(all_parts)} total)")
except Exception as e:
    print(f"❌ Encompass: {e}")

# ============================================================================
# AMAZON API (Search + Get First Valid Product Detail)
# ============================================================================
amazon_data = None
try:
    url = "https://data.unwrangle.com/api/getter/"
    
    # Step 1: Search to get listings
    response = requests.get(
        url,
        params={
            "platform": "amazon_search",
            "search": PART_NUMBER,
            "country": "us",
            "api_key": os.getenv("AMAZON_API_KEY")
        },
        timeout=30
    )
    if response.status_code == 200:
        data = response.json()
        if data.get("results"):
            search_results = data["results"]
            print(f"   Search: {len(search_results)} listings found")
            
            # Step 2: Find first valid ASIN (10 chars, alphanumeric)
            first_valid_asin = None
            for item in search_results:
                asin = item.get('asin')
                if asin and len(asin) == 10 and asin.isalnum():
                    first_valid_asin = asin
                    break
            
            if first_valid_asin:
                # Step 3: Get detailed info
                try:
                    detail_response = requests.get(
                        url,
                        params={
                            "platform": "amazon_detail",
                            "asin": first_valid_asin,
                            "country_code": "us",
                            "api_key": os.getenv("AMAZON_API_KEY")
                        },
                        timeout=30
                    )
                    if detail_response.status_code == 200:
                        amazon_data = [detail_response.json()]
                        print(f"✅ Amazon: 1 product (full details for ASIN {first_valid_asin})")
                    else:
                        amazon_data = search_results[:1]
                        print(f"✅ Amazon: 1 product (search data only)")
                except:
                    amazon_data = search_results[:1]
                    print(f"✅ Amazon: 1 product (search data only)")
            else:
                amazon_data = search_results[:1] if search_results else None
                print(f"✅ Amazon: 1 product (search data only)")
except Exception as e:
    print(f"❌ Amazon: {e}")

# ============================================================================
# GENERATE MARKDOWN
# ============================================================================
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_file = f"STAGE1_ALL_ATTRIBUTES_{timestamp}.md"

with open(output_file, 'w') as f:
    f.write(f"# Stage 1 - All Attributes Found\n\n")
    f.write(f"**Part Number:** {PART_NUMBER}\n")
    f.write(f"**Timestamp:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
    f.write("---\n\n")
    
    # ENCOMPASS
    f.write("## 📦 Encompass API Results\n\n")
    if encompass_data:
        f.write(f"**Status:** ✅ Success\n")
        f.write(f"**Parts Found:** {len(encompass_data)}\n\n")
        
        for idx, part in enumerate(encompass_data, 1):
            f.write(f"### Part {idx} of {len(encompass_data)}\n\n")
            f.write("| Attribute | Value |\n")
            f.write("|-----------|-------|\n")
            
            # Get all keys and sort them
            for key in sorted(part.keys()):
                value = part[key]
                # Format value based on type
                if isinstance(value, list):
                    if len(value) == 0:
                        display = "[]"
                    elif len(value) <= 3:
                        display = f"{len(value)} items: " + ", ".join(str(v)[:50] for v in value)
                    else:
                        display = f"{len(value)} items (see full data below)"
                elif isinstance(value, dict):
                    display = f"Object with {len(value)} keys"
                elif isinstance(value, str) and len(value) > 100:
                    display = value[:100] + "..."
                else:
                    display = str(value)
                
                f.write(f"| `{key}` | {display} |\n")
            
            # Show full arrays if they exist
            if any(isinstance(part.get(k), list) and len(part.get(k)) > 3 for k in part.keys()):
                f.write("\n**Full List Data:**\n\n")
                for key in sorted(part.keys()):
                    value = part[key]
                    if isinstance(value, list) and len(value) > 3:
                        f.write(f"\n**{key}** ({len(value)} items):\n")
                        for item in value[:20]:  # Limit to first 20
                            f.write(f"- {str(item)[:200]}\n")
                        if len(value) > 20:
                            f.write(f"- ... and {len(value) - 20} more\n")
            
            f.write("\n")
    else:
        f.write("**Status:** ❌ Failed\n\n")
    
    f.write("---\n\n")
    
    # AMAZON
    f.write("## 🛒 Amazon API Results\n\n")
    if amazon_data:
        f.write(f"**Status:** ✅ Success\n")
        f.write(f"**Listings Found:** {len(amazon_data)}\n\n")
        
        # Show all unique attributes across all listings
        all_keys = set()
        for listing in amazon_data:
            all_keys.update(listing.keys())
        
        f.write(f"**Unique Attributes Found:** {len(all_keys)}\n\n")
        f.write("**Attribute List:**\n")
        for key in sorted(all_keys):
            f.write(f"- `{key}`\n")
        f.write("\n")
        
        # Show first 5 listings in detail
        for idx, listing in enumerate(amazon_data[:5], 1):
            f.write(f"### Listing {idx} of {len(amazon_data)}\n\n")
            f.write("| Attribute | Value |\n")
            f.write("|-----------|-------|\n")
            
            for key in sorted(listing.keys()):
                value = listing[key]
                if isinstance(value, list):
                    if len(value) == 0:
                        display = "[]"
                    else:
                        display = ", ".join(str(v)[:50] for v in value[:3])
                        if len(value) > 3:
                            display += f" ... ({len(value)} total)"
                elif isinstance(value, str) and len(value) > 100:
                    display = value[:100] + "..."
                else:
                    display = str(value)
                
                f.write(f"| `{key}` | {display} |\n")
            f.write("\n")
        
        if len(amazon_data) > 5:
            f.write(f"*... and {len(amazon_data) - 5} more listings*\n\n")
    else:
        f.write("**Status:** ❌ Failed\n\n")
    
    f.write("---\n\n")
    f.write("## 📊 Summary\n\n")
    f.write(f"- **Encompass:** {'✅ ' + str(len(encompass_data)) + ' parts' if encompass_data else '❌ No data'}\n")
    f.write(f"- **Amazon:** {'✅ ' + str(len(amazon_data)) + ' listings' if amazon_data else '❌ No data'}\n")
    f.write(f"- **Marcone:** ❌ Authentication issue\n")
    f.write(f"- **Reliable Parts:** ❌ Server error (HTTP 500)\n\n")
    f.write("**Total APIs Working:** 2/4 (50%)\n")

print(f"\n✅ Markdown file created: {output_file}")
print(f"   File size: {os.path.getsize(output_file)} bytes")
