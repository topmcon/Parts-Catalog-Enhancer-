#!/usr/bin/env python3
"""
Complete Part Lookup Test - WR55X10025 (GE)
Standalone version - makes direct API calls without complex imports
"""

import json
import os
import requests
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI
from zeep import Client
from zeep.transports import Transport
from requests import Session
from requests.auth import HTTPBasicAuth

# Load environment
load_dotenv()

# Test configuration
PART_NUMBER = "WR55X10025"
BRAND = "GE"
TEST_TIMESTAMP = datetime.now().isoformat()

# Initialize AI clients
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
grok_client = OpenAI(
    api_key=os.getenv("XAI_API_KEY"),
    base_url="https://api.x.ai/v1"
)

class PartLookupTest:
    def __init__(self):
        self.part_number = PART_NUMBER
        self.brand = BRAND
        self.results = {
            "test_info": {
                "part_number": PART_NUMBER,
                "brand": BRAND,
                "timestamp": TEST_TIMESTAMP
            },
            "stage_1_api_calls": {},
            "stage_2_aggregation": {},
            "stage_3_openai_validation": {},
            "stage_4_grok_validation": {},
            "stage_5_consensus": {},
            "stage_6_final_catalog": {},
            "validation": {
                "both_ais_agree": None,
                "data_valid": None,
                "issues": []
            }
        }
    
    def stage_1_api_calls(self):
        """Stage 1: Call all APIs"""
        print("\n" + "="*80)
        print("STAGE 1: API CALLS")
        print("="*80)
        
        # Encompass API - CORRECTED payload structure
        print(f"\n📞 Encompass API for {self.part_number}...")
        try:
            payload = {
                "settings": {
                    "jsonUser": os.getenv("ENCOMPASS_USERNAME"),
                    "jsonPassword": os.getenv("ENCOMPASS_PASSWORD"),
                    "programName": "JSON.ITEM.INFORMATION"
                },
                "data": {
                    "searchPartNumber": self.part_number
                }
            }
            response = requests.post(
                f"{os.getenv('ENCOMPASS_BASE_URL')}/restfulservice/partsInformation",
                json=payload,
                timeout=30
            )
            if response.status_code == 200:
                data = response.json()
                # Check for success errorCode
                if data.get('status', {}).get('errorCode') == '100':
                    parts_data = data.get('data', {}).get('parts', [])
                    
                    # Filter for exact part number match only
                    exact_matches = [
                        part for part in parts_data 
                        if part.get('partNumber', '').upper() == self.part_number.upper()
                    ]
                    
                    print(f"   Total parts from API: {len(parts_data)}, Exact matches: {len(exact_matches)}")
                    
                    self.results["stage_1_api_calls"]["encompass"] = {"success": True, "data": exact_matches}
                    print(f"✅ Encompass: Success - found {len(exact_matches)} exact match(es)")
                else:
                    error_msg = data.get('status', {}).get('errorMessage', 'Unknown error')
                    self.results["stage_1_api_calls"]["encompass"] = {"success": False, "error": error_msg}
                    print(f"⚠️  Encompass: {error_msg}")
            else:
                self.results["stage_1_api_calls"]["encompass"] = {"success": False, "error": f"HTTP {response.status_code}"}
                print(f"⚠️  Encompass: HTTP {response.status_code}")
        except Exception as e:
            self.results["stage_1_api_calls"]["encompass"] = {"success": False, "error": str(e)}
            print(f"❌ Encompass: {e}")
        
        # Marcone API
        print(f"\n📞 Marcone API for {self.part_number}...")
        try:
            session = Session()
            session.auth = HTTPBasicAuth(os.getenv("MARCONE_TEST_USERNAME"), os.getenv("MARCONE_TEST_PASSWORD"))
            transport = Transport(session=session)
            
            wsdl_url = f"{os.getenv('MARCONE_TEST_URL')}/b2b/parts_v2.asmx?WSDL"
            client = Client(wsdl_url, transport=transport)
            
            # Try multiple GE make codes
            result = None
            for make in ["GEH", "GEN", "GE", "HOT"]:
                try:
                    response = client.service.ExactPartLookup(
                        userName=os.getenv("MARCONE_TEST_USERNAME"),
                        password=os.getenv("MARCONE_TEST_PASSWORD"),
                        make=make,
                        partNumber=self.part_number
                    )
                    if response and hasattr(response, 'PartInformation_v2'):
                        parts = response.PartInformation_v2
                        if parts:
                            from zeep.helpers import serialize_object
                            result = serialize_object(parts)
                            print(f"✅ Marcone: Found with make code '{make}'")
                            break
                except:
                    continue
            
            if result:
                self.results["stage_1_api_calls"]["marcone"] = {"success": True, "data": result}
            else:
                self.results["stage_1_api_calls"]["marcone"] = {"success": False, "error": "Part not found"}
                print(f"⚠️  Marcone: Part not found")
        except Exception as e:
            self.results["stage_1_api_calls"]["marcone"] = {"success": False, "error": str(e)}
            print(f"❌ Marcone: {e}")
        
        # Reliable Parts API
        print(f"\n📞 Reliable Parts API for {self.part_number}...")
        try:
            response = requests.get(
                f"{os.getenv('RELIABLE_PARTS_BASE_URL')}/part/search",
                params={"partNumber": self.part_number},
                headers={"X-API-Key": os.getenv("RELIABLE_PARTS_PART_SEARCH_API_KEY")},
                auth=HTTPBasicAuth(os.getenv("RELIABLE_PARTS_USERNAME"), os.getenv("RELIABLE_PARTS_PASSWORD")),
                timeout=30,
                verify=False
            )
            if response.status_code == 200:
                data = response.json()
                self.results["stage_1_api_calls"]["reliable"] = {"success": True, "data": data}
                print(f"✅ Reliable Parts: Success")
            else:
                self.results["stage_1_api_calls"]["reliable"] = {"success": False, "error": f"HTTP {response.status_code}"}
                print(f"⚠️  Reliable Parts: HTTP {response.status_code}")
        except Exception as e:
            self.results["stage_1_api_calls"]["reliable"] = {"success": False, "error": str(e)}
            print(f"❌ Reliable Parts: {e}")
        
        # Amazon API
        print(f"\n📞 Amazon API...")
        try:
            amazon_url = "https://data.unwrangle.com/api/getter/"
            amazon_params = {
                "platform": "amazon_search",
                "search": self.part_number,
                "country": "us",
                "api_key": os.getenv("AMAZON_API_KEY")
            }
            response = requests.get(amazon_url, params=amazon_params, timeout=30)
            if response.status_code == 200:
                data = response.json()
                # Check if we got results
                if data.get("results") and len(data["results"]) > 0:
                    self.results["stage_1_api_calls"]["amazon"] = {"success": True, "data": data}
                    print(f"✅ Amazon: Success - found {len(data['results'])} results")
                else:
                    self.results["stage_1_api_calls"]["amazon"] = {"success": False, "error": "No results found"}
                    print(f"⚠️  Amazon: No results found")
            else:
                self.results["stage_1_api_calls"]["amazon"] = {"success": False, "error": f"HTTP {response.status_code}"}
                print(f"⚠️  Amazon: HTTP {response.status_code}")
        except Exception as e:
            self.results["stage_1_api_calls"]["amazon"] = {"success": False, "error": str(e)}
            print(f"❌ Amazon: {e}")
        
        print("\n✅ Stage 1 Complete")
        for api, result in self.results["stage_1_api_calls"].items():
            status = "✅" if result.get("success") else "❌"
            print(f"  {status} {api.capitalize()}")
    
    def stage_2_aggregate(self):
        """Stage 2: Aggregate data (keep separate)"""
        print("\n" + "="*80)
        print("STAGE 2: DATA AGGREGATION (Kept Separate by Source)")
        print("="*80)
        
        aggregated = {}
        for source in ["encompass", "marcone", "reliable", "amazon"]:
            api_result = self.results["stage_1_api_calls"].get(source, {})
            if api_result.get("success"):
                aggregated[f"{source}_data"] = {"source": source, "raw_data": api_result["data"]}
                print(f"✅ {source.capitalize()}: Data stored separately")
            else:
                aggregated[f"{source}_data"] = None
                print(f"⚠️  {source.capitalize()}: No data")
        
        self.results["stage_2_aggregation"] = aggregated
        print("\n✅ Stage 2 Complete")
    
    def stage_3_openai(self):
        """Stage 3: OpenAI validation"""
        print("\n" + "="*80)
        print("STAGE 3: OpenAI VALIDATION")
        print("="*80)
        
        prompt = self.build_prompt()
        print(f"🤖 Calling OpenAI... (prompt: {len(prompt)} chars)")
        
        try:
            response = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert at analyzing appliance part data. Return ONLY valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            result = response.choices[0].message.content
            self.results["stage_3_openai_validation"] = {
                "success": True,
                "response": result,
                "model": "gpt-4o-mini",
                "tokens": response.usage.total_tokens
            }
            print(f"✅ OpenAI: Success ({response.usage.total_tokens} tokens)")
        except Exception as e:
            self.results["stage_3_openai_validation"] = {"success": False, "error": str(e)}
            print(f"❌ OpenAI: {e}")
    
    def stage_4_grok(self):
        """Stage 4: Grok validation"""
        print("\n" + "="*80)
        print("STAGE 4: GROK VALIDATION")
        print("="*80)
        
        prompt = self.build_prompt()
        print(f"🤖 Calling Grok... (prompt: {len(prompt)} chars)")
        
        try:
            response = grok_client.chat.completions.create(
                model="grok-3",
                messages=[
                    {"role": "system", "content": "You are an expert at analyzing appliance part data. Return ONLY valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            result = response.choices[0].message.content
            self.results["stage_4_grok_validation"] = {
                "success": True,
                "response": result,
                "model": "grok-beta"
            }
            print(f"✅ Grok: Success")
        except Exception as e:
            self.results["stage_4_grok_validation"] = {"success": False, "error": str(e)}
            print(f"❌ Grok: {e}")
    
    def build_prompt(self):
        """Build AI validation prompt"""
        aggregated = self.results["stage_2_aggregation"]
        
        prompt = f"""Analyze appliance part data from multiple sources.

Part: {self.part_number} ({self.brand})

SOURCE DATA:
"""
        for source in ["encompass", "marcone", "reliable", "amazon"]:
            data = aggregated.get(f"{source}_data")
            prompt += f"\n{'='*50}\n{source.upper()}:\n"
            if data:
                prompt += json.dumps(data.get("raw_data"), indent=2, default=str)[:2000]  # Limit size
            else:
                prompt += "No data"
            prompt += "\n"
        
        prompt += """

PRIMARY ATTRIBUTES (analyze these):
mpn, manufacturer, part_title, long_description, part_type, primary_department, 
primary_category, primary_image_url, msrp, current_selling_price, weight_lbs,
upc_ean_gtin, compatible_models, cross_reference_parts, related_symptoms

For EACH field, determine:
1. Best value (from which source?)
2. Confidence (0.0-1.0)
3. Brief reasoning

Return ONLY this JSON structure (no markdown):
{
  "field_analysis": {
    "mpn": {"selected_value": "...", "selected_source": "...", "confidence": 0.9, "reasoning": "..."},
    "manufacturer": {"selected_value": "...", "selected_source": "...", "confidence": 0.9, "reasoning": "..."},
    ... (for each field above)
  },
  "overall_confidence": 0.85
}
"""
        return prompt
    
    def stage_5_consensus(self):
        """Stage 5: Compare AI results - MUST AGREE"""
        print("\n" + "="*80)
        print("STAGE 5: CONSENSUS (Both AIs Must Agree)")
        print("="*80)
        
        openai_result = self.results.get("stage_3_openai_validation", {})
        grok_result = self.results.get("stage_4_grok_validation", {})
        
        if not openai_result.get("success") or not grok_result.get("success"):
            print("❌ Cannot proceed - AI validation failed")
            self.results["validation"]["data_valid"] = False
            self.results["validation"]["issues"].append("AI validation failed")
            return
        
        # Parse responses
        try:
            openai_text = openai_result["response"].strip()
            if "```" in openai_text:
                openai_text = openai_text.split("```")[1]
                if openai_text.startswith("json"):
                    openai_text = openai_text[4:]
            openai_data = json.loads(openai_text)
            
            grok_text = grok_result["response"].strip()
            if "```" in grok_text:
                grok_text = grok_text.split("```")[1]
                if grok_text.startswith("json"):
                    grok_text = grok_text[4:]
            grok_data = json.loads(grok_text)
        except Exception as e:
            print(f"❌ JSON parse error: {e}")
            self.results["validation"]["data_valid"] = False
            self.results["validation"]["issues"].append(f"JSON parse failed: {e}")
            return
        
        # Compare field by field
        openai_fields = openai_data.get("field_analysis", {})
        grok_fields = grok_data.get("field_analysis", {})
        
        agreements = []
        disagreements = []
        consensus_results = {}
        
        all_fields = set(list(openai_fields.keys()) + list(grok_fields.keys()))
        
        print("\n🔍 Field-by-Field Comparison:\n")
        for field in sorted(all_fields):
            openai_field = openai_fields.get(field, {})
            grok_field = grok_fields.get(field, {})
            
            openai_value = str(openai_field.get("selected_value", "")).lower()
            grok_value = str(grok_field.get("selected_value", "")).lower()
            openai_source = openai_field.get("selected_source")
            grok_source = grok_field.get("selected_source")
            
            if openai_value == grok_value and openai_source == grok_source:
                agreements.append(field)
                consensus_results[field] = {
                    "final_value": openai_field.get("selected_value"),
                    "source": openai_source,
                    "agreement": True
                }
                print(f"  ✅ {field}: AGREE - {openai_field.get('selected_value')} (from {openai_source})")
            else:
                disagreements.append(field)
                consensus_results[field] = {
                    "openai_value": openai_field.get("selected_value"),
                    "openai_source": openai_source,
                    "grok_value": grok_field.get("selected_value"),
                    "grok_source": grok_source,
                    "agreement": False
                }
                print(f"  ❌ {field}: DISAGREE")
                print(f"       OpenAI: {openai_field.get('selected_value')} (from {openai_source})")
                print(f"       Grok:   {grok_field.get('selected_value')} (from {grok_source})")
        
        total = len(all_fields)
        agreement_pct = (len(agreements) / total * 100) if total > 0 else 0
        
        print(f"\n📊 Agreement: {len(agreements)}/{total} ({agreement_pct:.1f}%)")
        
        both_agree = agreement_pct == 100.0
        self.results["validation"]["both_ais_agree"] = both_agree
        self.results["validation"]["data_valid"] = both_agree
        
        if both_agree:
            print("\n✅ VALIDATION PASSED: Both AIs agree on ALL fields")
        else:
            print("\n❌ VALIDATION FAILED: AIs disagree on some fields")
            self.results["validation"]["issues"].append(f"Disagree on: {', '.join(disagreements)}")
        
        self.results["stage_5_consensus"] = {
            "agreement_percentage": agreement_pct,
            "agreements": agreements,
            "disagreements": disagreements,
            "consensus_results": consensus_results
        }
    
    def stage_6_catalog(self):
        """Stage 6: Build final catalog"""
        print("\n" + "="*80)
        print("STAGE 6: BUILD FINAL CATALOG")
        print("="*80)
        
        if not self.results["validation"]["data_valid"]:
            print("❌ Cannot build catalog - validation failed")
            self.results["stage_6_final_catalog"] = {"success": False, "error": "Validation failed"}
            return
        
        print("✅ Building catalog...")
        consensus = self.results["stage_5_consensus"]["consensus_results"]
        
        catalog = {
            "catalog_id": f"catalog_{self.part_number}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "mpn": self.part_number,
            "created_at": TEST_TIMESTAMP,
            "validation_status": "VALID - Both AIs Agree",
            "primary_attributes": {},
            "metadata": {
                "openai_model": "gpt-4o-mini",
                "grok_model": "grok-beta",
                "validation_agreement": "100%"
            }
        }
        
        for field, data in consensus.items():
            if data.get("agreement") and data.get("final_value"):
                catalog["primary_attributes"][field] = {
                    "value": data["final_value"],
                    "source": data["source"],
                    "status": "FOUND"
                }
        
        self.results["stage_6_final_catalog"] = {"success": True, "catalog": catalog}
        print(f"✅ Catalog built: {len(catalog['primary_attributes'])} attributes")
    
    def generate_report(self):
        """Generate markdown report"""
        report = f"""# Part Lookup Test Results

**Part:** {self.part_number} ({self.brand})  
**Date:** {TEST_TIMESTAMP}

## Validation Status: {"✅ PASSED" if self.results["validation"]["data_valid"] else "❌ FAILED"}

**Requirement:** Both OpenAI and Grok must agree 100% for data to be valid.

"""
        if self.results["validation"]["data_valid"]:
            report += "✅ **Both AIs agreed on all fields. Data is VALID.**\n\n"
        else:
            report += "❌ **AIs disagreed. Data is INVALID.**\n\n"
            if self.results["validation"]["issues"]:
                report += "**Issues:**\n"
                for issue in self.results["validation"]["issues"]:
                    report += f"- {issue}\n"
                report += "\n"
        
        # Stage summaries
        report += "## Stage 1: API Calls\n\n"
        for api, result in self.results["stage_1_api_calls"].items():
            status = "✅ Success" if result.get("success") else "❌ Failed"
            report += f"- **{api.capitalize()}:** {status}\n"
            if not result.get("success"):
                report += f"  - Error: {result.get('error')}\n"
        
        report += "\n## Stage 2: Data Aggregation\n\n"
        report += "Data kept SEPARATE by source (no merging).\n\n"
        
        report += "## Stage 3: OpenAI Validation\n\n"
        openai = self.results.get("stage_3_openai_validation", {})
        if openai.get("success"):
            report += f"- ✅ Success\n- Model: {openai.get('model')}\n- Tokens: {openai.get('tokens')}\n\n"
        else:
            report += f"- ❌ Failed: {openai.get('error')}\n\n"
        
        report += "## Stage 4: Grok Validation\n\n"
        grok = self.results.get("stage_4_grok_validation", {})
        if grok.get("success"):
            report += f"- ✅ Success\n- Model: {grok.get('model')}\n\n"
        else:
            report += f"- ❌ Failed: {grok.get('error')}\n\n"
        
        report += "## Stage 5: Consensus\n\n"
        consensus = self.results.get("stage_5_consensus", {})
        if consensus:
            report += f"- Agreement: {consensus.get('agreement_percentage', 0):.1f}%\n"
            report += f"- Fields agree: {len(consensus.get('agreements', []))}\n"
            report += f"- Fields disagree: {len(consensus.get('disagreements', []))}\n\n"
            
            if consensus.get("disagreements"):
                report += "### Disagreements:\n\n"
                results = consensus.get("consensus_results", {})
                for field in consensus["disagreements"]:
                    data = results.get(field, {})
                    report += f"**{field}:**\n"
                    report += f"- OpenAI: {data.get('openai_value')} (from {data.get('openai_source')})\n"
                    report += f"- Grok: {data.get('grok_value')} (from {data.get('grok_source')})\n\n"
        
        report += "## Stage 6: Final Catalog\n\n"
        final = self.results.get("stage_6_final_catalog", {})
        if final.get("success"):
            catalog = final["catalog"]
            report += f"✅ Catalog built successfully\n\n"
            report += f"- Catalog ID: `{catalog['catalog_id']}`\n"
            report += f"- MPN: `{catalog['mpn']}`\n"
            report += f"- Attributes: {len(catalog['primary_attributes'])}\n\n"
            
            report += "### Sample Attributes:\n\n"
            for i, (field, data) in enumerate(catalog['primary_attributes'].items()):
                if i < 10:
                    report += f"- **{field}:** {data['value']} (from {data['source']})\n"
        else:
            report += f"❌ {final.get('error')}\n\n"
        
        report += "\n## Final Status\n\n"
        if self.results["validation"]["data_valid"]:
            report += "### ✅ VALIDATION PASSED\n\n"
            report += "Data is VALID and ready for:\n"
            report += "- Database storage\n"
            report += "- Production use\n"
            report += "- Salesforce integration\n\n"
        else:
            report += "### ❌ VALIDATION FAILED\n\n"
            report += "Data is INVALID:\n"
            report += "- Cannot use in production\n"
            report += "- Requires manual review\n"
            report += "- Do not store in database\n\n"
        
        report += f"\n---\n*Test completed: {datetime.now().isoformat()}*\n"
        return report
    
    def run(self):
        """Run complete test"""
        print("\n" + "="*80)
        print(f"🚀 COMPLETE PART LOOKUP TEST: {self.part_number} ({self.brand})")
        print("="*80)
        print("Following architecture:")
        print("  1. Parallel API Calls")
        print("  2. Data Aggregation (separate)")
        print("  3. OpenAI Validation")
        print("  4. Grok Validation")
        print("  5. Consensus (must agree 100%)")
        print("  6. Build Final Catalog")
        print("="*80)
        
        try:
            self.stage_1_api_calls()
            self.stage_2_aggregate()
            self.stage_3_openai()
            self.stage_4_grok()
            self.stage_5_consensus()
            self.stage_6_catalog()
            
            print("\n" + "="*80)
            print("📝 GENERATING REPORT")
            print("="*80)
            
            report = self.generate_report()
            filename = f"PART_LOOKUP_RESULTS_{self.part_number}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            with open(filename, 'w') as f:
                f.write(report)
            
            print(f"\n✅ Report saved: {filename}")
            
            print("\n" + "="*80)
            print("🏁 FINAL STATUS")
            print("="*80)
            if self.results["validation"]["data_valid"]:
                print("✅✅✅ VALIDATION PASSED - DATA IS VALID ✅✅✅")
            else:
                print("❌❌❌ VALIDATION FAILED - DATA IS INVALID ❌❌❌")
                for issue in self.results["validation"]["issues"]:
                    print(f"  • {issue}")
            print("="*80)
            
        except Exception as e:
            print(f"\n❌ Test failed: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    import urllib3
    urllib3.disable_warnings()
    test = PartLookupTest()
    test.run()
