# Local Testing Guide - Complete System Validation

## Overview

This guide walks you through testing the **entire Parts Catalog Enhancement System locally** before production deployment. You'll test:

1. ✅ Part number lookups across all 4 APIs
2. ✅ Data aggregation and storage
3. ✅ Dual AI validation (OpenAI + Grok)
4. ✅ Consensus engine decision-making
5. ✅ Master catalog building
6. ✅ Database operations
7. ✅ API endpoints
8. ✅ End-to-end workflow

**Goal**: Validate everything works correctly with real API calls and AI validation before spending money at scale.

---

## Phase 1: Local Environment Setup (30 minutes)

### Step 1.1: Install Dependencies

```bash
# Navigate to project
cd /workspaces/Parts-Catalog-Enhancer-

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install requirements
pip install -r requirements.txt
```

**Required packages** (add to `requirements.txt`):
```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
sqlalchemy==2.0.23
alembic==1.13.0
psycopg2-binary==2.9.9
redis==5.0.1
celery==5.3.4
httpx==0.25.2
openai==1.3.7
python-dotenv==1.0.0
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
```

---

### Step 1.2: Setup Local Database

```bash
# Start PostgreSQL using Docker
docker run --name parts-catalog-postgres \
  -e POSTGRES_DB=parts_catalog \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=yourpassword \
  -p 5432:5432 \
  -d postgres:14

# Start Redis
docker run --name parts-catalog-redis \
  -p 6379:6379 \
  -d redis:6

# Verify containers are running
docker ps
```

---

### Step 1.3: Configure Environment Variables

Create `.env` file in project root:

```bash
# Database
DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/parts_catalog
DATABASE_POOL_SIZE=5

# Redis
REDIS_URL=redis://localhost:6379/0

# API Keys (GET THESE FIRST!)
ENCOMPASS_API_KEY=your_encompass_key
ENCOMPASS_API_URL=https://api.encompassparts.com/v1

MARCONE_CLIENT_ID=your_marcone_client_id
MARCONE_CLIENT_SECRET=your_marcone_secret
MARCONE_API_URL=https://api.marcone.com/v2

RELIABLE_API_KEY=your_reliable_key
RELIABLE_API_SECRET=your_reliable_secret
RELIABLE_API_URL=https://api.reliableparts.com/v1

AMAZON_ACCESS_KEY=your_amazon_access_key
AMAZON_SECRET_KEY=your_amazon_secret_key
AMAZON_PARTNER_TAG=your_amazon_tag
AMAZON_REGION=us-east-1

# AI Services
OPENAI_API_KEY=sk-your-openai-key
OPENAI_MODEL=gpt-4-turbo-preview

GROK_API_KEY=your_grok_key
GROK_API_URL=https://api.x.ai/v1
GROK_MODEL=grok-beta

# Application
ENVIRONMENT=development
LOG_LEVEL=DEBUG
API_PORT=8000

# Testing flags
ENABLE_AI_CACHING=true
MOCK_APIS=false  # Set to true to use mock data
```

---

### Step 1.4: Initialize Database Schema

```bash
# Create database migration
alembic init alembic

# Generate initial migration
alembic revision --autogenerate -m "Initial schema"

# Apply migration
alembic upgrade head

# Verify tables created
psql -h localhost -U postgres -d parts_catalog -c "\dt"
```

Expected tables:
- `lookup_sessions`
- `raw_source_responses`
- `master_catalog`
- `ai_validations`
- `spec_table_entries`
- `images`
- `audit_log`
- `api_keys`

---

## Phase 2: Component Testing (2-3 hours)

### Test 2.1: API Client Connectivity

Create `tests/test_api_clients.py`:

```python
import pytest
import asyncio
from src.api_clients.encompass_client import EncompassAPIClient
from src.api_clients.marcone_client import MarconeAPIClient
from src.api_clients.reliable_client import ReliablePartsAPIClient
from src.api_clients.amazon_client import AmazonAPIClient

# Test part numbers (use real OEM parts)
TEST_PARTS = [
    "WR55X10025",  # GE Refrigerator sensor
    "W10813469",   # Whirlpool washer part
    "DA97-08406A"  # Samsung refrigerator part
]

@pytest.mark.asyncio
async def test_encompass_lookup():
    """Test Encompass API connectivity"""
    client = EncompassAPIClient()
    
    for part_number in TEST_PARTS:
        print(f"\n🔍 Testing Encompass lookup: {part_number}")
        result = await client.lookup_part(part_number)
        
        assert result is not None
        assert result.get("success") in [True, False]
        
        if result.get("success"):
            print(f"✅ Found: {result.get('manufacturer')} - {result.get('description')}")
            print(f"   Price: ${result.get('price')}")
            print(f"   Availability: {result.get('availability')}")
        else:
            print(f"❌ Not found or error: {result.get('error')}")

@pytest.mark.asyncio
async def test_marcone_lookup():
    """Test Marcone API connectivity"""
    client = MarconeAPIClient()
    
    # First authenticate
    await client.authenticate()
    
    for part_number in TEST_PARTS:
        print(f"\n🔍 Testing Marcone lookup: {part_number}")
        result = await client.lookup_part(part_number)
        
        if result.get("success"):
            print(f"✅ Found: {result.get('description')}")
            print(f"   Cost: ${result.get('cost')}")
        else:
            print(f"❌ Not found")

@pytest.mark.asyncio
async def test_reliable_lookup():
    """Test Reliable Parts API connectivity"""
    client = ReliablePartsAPIClient()
    
    for part_number in TEST_PARTS:
        print(f"\n🔍 Testing Reliable lookup: {part_number}")
        result = await client.lookup_part(part_number)
        
        if result.get("success"):
            print(f"✅ Found: {result.get('name')}")
        else:
            print(f"❌ Not found")

@pytest.mark.asyncio
async def test_amazon_lookup():
    """Test Amazon Product Advertising API connectivity"""
    client = AmazonAPIClient()
    
    for part_number in TEST_PARTS:
        print(f"\n🔍 Testing Amazon lookup: {part_number}")
        result = await client.search_by_keywords(part_number)
        
        if result.get("items"):
            print(f"✅ Found {len(result['items'])} results")
            for item in result['items'][:3]:
                print(f"   - {item.get('title')}: ${item.get('price')}")
        else:
            print(f"❌ No results")

@pytest.mark.asyncio
async def test_parallel_lookup():
    """Test all APIs in parallel"""
    part_number = "WR55X10025"
    
    print(f"\n🚀 Testing PARALLEL lookup for: {part_number}")
    
    tasks = [
        EncompassAPIClient().lookup_part(part_number),
        MarconeAPIClient().lookup_part(part_number),
        ReliablePartsAPIClient().lookup_part(part_number),
        AmazonAPIClient().search_by_keywords(part_number)
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    print("\n📊 Results:")
    api_names = ["Encompass", "Marcone", "Reliable", "Amazon"]
    for api, result in zip(api_names, results):
        if isinstance(result, Exception):
            print(f"❌ {api}: Error - {str(result)}")
        elif result.get("success") or result.get("items"):
            print(f"✅ {api}: Success")
        else:
            print(f"⚠️  {api}: No data")
```

**Run tests:**
```bash
pytest tests/test_api_clients.py -v -s
```

**Expected output:**
```
tests/test_api_clients.py::test_encompass_lookup 
🔍 Testing Encompass lookup: WR55X10025
✅ Found: GE - Refrigerator Defrost Sensor
   Price: $49.99
   Availability: In Stock
PASSED

tests/test_api_clients.py::test_parallel_lookup
🚀 Testing PARALLEL lookup for: WR55X10025
📊 Results:
✅ Encompass: Success
✅ Marcone: Success
⚠️  Reliable: No data
✅ Amazon: Success
PASSED
```

---

### Test 2.2: Data Aggregation Engine

Create `tests/test_aggregation.py`:

```python
import pytest
from src.aggregation.data_aggregator import DataAggregator
from src.models.catalog import MasterCatalogRecord

@pytest.mark.asyncio
async def test_data_aggregation():
    """Test aggregation of raw API responses"""
    
    # Simulate raw responses from 4 APIs
    raw_responses = {
        "encompass": {
            "part_number": "WR55X10025",
            "manufacturer": "GE",
            "description": "Defrost Sensor",
            "price": 49.99,
            "weight": "0.2 lbs",
            "dimensions": "5 x 3 x 1 inches",
            "voltage": "N/A",
            "compatible_models": ["GFE28GMKES", "PFE28KSKSS"]
        },
        "marcone": {
            "part_number": "WR55X10025",
            "brand": "GE Appliances",
            "title": "Sensor Defrost",
            "cost": 32.50,
            "weight_lbs": 0.2,
            "box_dimensions": "6x4x2"
        },
        "reliable": None,  # Not found
        "amazon": {
            "asin": "B07XKJB9C8",
            "title": "GE WR55X10025 Genuine OEM Defrost Sensor",
            "price": 45.50,
            "images": [
                "https://m.media-amazon.com/image1.jpg",
                "https://m.media-amazon.com/image2.jpg"
            ],
            "reviews_count": 124,
            "rating": 4.5
        }
    }
    
    aggregator = DataAggregator()
    
    # Aggregate (but DON'T merge - keep separate by source)
    aggregated = await aggregator.aggregate(raw_responses)
    
    print("\n📦 Aggregated Data Structure:")
    print(f"Encompass data: {aggregated['encompass_data']}")
    print(f"Marcone data: {aggregated['marcone_data']}")
    print(f"Reliable data: {aggregated['reliable_data']}")
    print(f"Amazon data: {aggregated['amazon_data']}")
    
    # Verify structure
    assert "encompass_data" in aggregated
    assert "marcone_data" in aggregated
    assert "reliable_data" in aggregated
    assert "amazon_data" in aggregated
    
    # Verify data stays separate (not merged)
    assert aggregated["encompass_data"]["price"] == 49.99
    assert aggregated["marcone_data"]["cost"] == 32.50
    assert aggregated["amazon_data"]["price"] == 45.50
    
    print("\n✅ Data aggregation successful - all sources kept separate")
```

**Run:**
```bash
pytest tests/test_aggregation.py -v -s
```

---

### Test 2.3: AI Validation (CRITICAL TEST)

Create `tests/test_ai_validation.py`:

```python
import pytest
from src.ai.openai_validator import OpenAIValidator
from src.ai.grok_validator import GrokValidator
from src.ai.consensus_engine import ConsensusEngine

@pytest.mark.asyncio
async def test_openai_validation():
    """Test OpenAI validation of part data"""
    
    # Raw data from all sources (kept separate)
    source_data = {
        "encompass": {
            "mpn": "WR55X10025",
            "manufacturer": "GE",
            "weight": "0.2 lbs",
            "voltage": "N/A"
        },
        "marcone": {
            "mpn": "WR55X10025",
            "brand": "GE Appliances",
            "weight_lbs": 0.2
        },
        "reliable": None,
        "amazon": {
            "title": "GE WR55X10025",
            "weight": "3.2 ounces"
        }
    }
    
    validator = OpenAIValidator()
    
    print("\n🤖 Testing OpenAI Validation...")
    result = await validator.validate_part_data(
        part_number="WR55X10025",
        source_data=source_data
    )
    
    print(f"\n📊 OpenAI Validation Results:")
    print(f"Overall Confidence: {result['overall_confidence']}")
    print(f"\nField-by-Field Analysis:")
    for field, analysis in result['field_analysis'].items():
        print(f"  {field}:")
        print(f"    - Selected Value: {analysis['selected_value']}")
        print(f"    - Source: {analysis['selected_source']}")
        print(f"    - Confidence: {analysis['confidence']}")
        print(f"    - Reasoning: {analysis['reasoning']}")
    
    # Assertions
    assert result['overall_confidence'] > 0.5
    assert 'field_analysis' in result
    assert 'weight' in result['field_analysis']
    
    print("\n✅ OpenAI validation successful")

@pytest.mark.asyncio
async def test_grok_validation():
    """Test Grok validation (cross-check)"""
    
    source_data = {
        "encompass": {
            "mpn": "WR55X10025",
            "manufacturer": "GE",
            "weight": "0.2 lbs"
        },
        "marcone": {
            "mpn": "WR55X10025",
            "weight_lbs": 0.2
        },
        "amazon": {
            "weight": "3.2 ounces"
        }
    }
    
    validator = GrokValidator()
    
    print("\n🤖 Testing Grok Validation...")
    result = await validator.validate_part_data(
        part_number="WR55X10025",
        source_data=source_data
    )
    
    print(f"\n📊 Grok Validation Results:")
    print(f"Overall Confidence: {result['overall_confidence']}")
    
    assert result['overall_confidence'] > 0.5
    print("\n✅ Grok validation successful")

@pytest.mark.asyncio
async def test_consensus_engine():
    """Test consensus between OpenAI and Grok"""
    
    # Simulate AI validation results
    openai_result = {
        "field_analysis": {
            "weight": {
                "selected_value": 0.2,
                "selected_source": "encompass",
                "confidence": 0.92
            },
            "manufacturer": {
                "selected_value": "GE",
                "selected_source": "encompass",
                "confidence": 0.98
            }
        }
    }
    
    grok_result = {
        "field_analysis": {
            "weight": {
                "selected_value": 0.2,
                "selected_source": "encompass",
                "confidence": 0.89
            },
            "manufacturer": {
                "selected_value": "GE Appliances",
                "selected_source": "marcone",
                "confidence": 0.85
            }
        }
    }
    
    consensus = ConsensusEngine()
    final_values = consensus.resolve(openai_result, grok_result)
    
    print("\n⚖️  Consensus Results:")
    for field, decision in final_values.items():
        print(f"  {field}:")
        print(f"    - Final Value: {decision['final_value']}")
        print(f"    - Source: {decision['source']}")
        print(f"    - Confidence: {decision['confidence']}")
        print(f"    - Agreement: {'✅ Both AIs agree' if decision['agreement'] else '⚠️ AIs disagree'}")
    
    # Both AIs agreed on weight
    assert final_values['weight']['agreement'] == True
    assert final_values['weight']['confidence'] > 0.9
    
    # AIs disagreed on manufacturer (different values)
    assert final_values['manufacturer']['agreement'] == False
    assert final_values['manufacturer']['confidence'] < 0.9
    
    print("\n✅ Consensus engine working correctly")
```

**Run:**
```bash
pytest tests/test_ai_validation.py -v -s
```

**Expected Cost**: ~$0.10-0.20 per test run (3 tests with real AI calls)

---

### Test 2.4: Master Catalog Building

Create `tests/test_catalog_builder.py`:

```python
import pytest
from src.catalog.catalog_builder import CatalogBuilder
from src.models.catalog import MasterCatalogRecord, DataStatus

@pytest.mark.asyncio
async def test_catalog_building():
    """Test complete catalog record creation"""
    
    # Final consensus values (after AI validation)
    consensus_values = {
        "mpn": {
            "final_value": "WR55X10025",
            "source": "encompass",
            "confidence": 0.98
        },
        "manufacturer": {
            "final_value": "GE",
            "source": "encompass",
            "confidence": 0.95
        },
        "weight_lbs": {
            "final_value": 0.2,
            "source": "encompass",
            "confidence": 0.92
        },
        # ... other fields
    }
    
    builder = CatalogBuilder()
    catalog = await builder.build(consensus_values)
    
    print("\n📋 Master Catalog Record Built:")
    print(f"Catalog ID: {catalog.catalog_id}")
    print(f"MPN: {catalog.mpn} (status: {catalog.mpn_status})")
    print(f"Manufacturer: {catalog.manufacturer} (status: {catalog.manufacturer_status})")
    print(f"Weight: {catalog.weight_lbs} lbs (status: {catalog.weight_lbs_status})")
    print(f"Voltage: {catalog.voltage} (status: {catalog.voltage_status})")
    print(f"\nOverall Confidence: {catalog.data_confidence_score:.2f}")
    print(f"Field Completeness: {catalog.field_completeness_percentage:.1f}%")
    
    # Verify PRIMARY attributes populated
    assert catalog.mpn == "WR55X10025"
    assert catalog.mpn_status == DataStatus.FOUND
    assert catalog.manufacturer == "GE"
    assert catalog.data_confidence_score > 0.8
    
    # Check voltage is NOT_APPLICABLE (not an electrical part)
    assert catalog.voltage_status == DataStatus.NOT_APPLICABLE
    
    print("\n✅ Catalog building successful")
```

---

### Test 2.5: Database Operations

Create `tests/test_database.py`:

```python
import pytest
from src.repositories.catalog_repository import CatalogRepository
from src.models.catalog import MasterCatalogRecord, PartType, DataStatus
from uuid import uuid4

@pytest.mark.asyncio
async def test_database_crud():
    """Test Create, Read, Update, Delete operations"""
    
    repo = CatalogRepository()
    
    # CREATE
    catalog = MasterCatalogRecord(
        catalog_id=uuid4(),
        mpn="TEST123",
        manufacturer="TestBrand",
        part_type=PartType.OEM,
        part_title="Test Part",
        long_description="This is a test part",
        primary_department="Test",
        primary_category="Test Category",
        data_confidence_score=0.95,
        ai_validation_status="validated",
        field_completeness_percentage=85.0,
        source_priority=["encompass"],
        lookup_session_id=uuid4()
    )
    
    print("\n💾 Testing Database CREATE...")
    saved = await repo.save(catalog)
    assert saved.catalog_id == catalog.catalog_id
    print(f"✅ Created catalog record: {saved.catalog_id}")
    
    # READ
    print("\n📖 Testing Database READ...")
    found = await repo.get_by_mpn("TEST123")
    assert found is not None
    assert found.mpn == "TEST123"
    assert found.manufacturer == "TestBrand"
    print(f"✅ Read catalog record: {found.mpn}")
    
    # UPDATE
    print("\n✏️  Testing Database UPDATE...")
    found.manufacturer = "UpdatedBrand"
    updated = await repo.update(found)
    assert updated.manufacturer == "UpdatedBrand"
    print(f"✅ Updated manufacturer to: {updated.manufacturer}")
    
    # DELETE
    print("\n🗑️  Testing Database DELETE...")
    await repo.delete(catalog.catalog_id)
    deleted_check = await repo.get_by_id(catalog.catalog_id)
    assert deleted_check is None
    print(f"✅ Deleted catalog record")

@pytest.mark.asyncio
async def test_database_queries():
    """Test search and filter operations"""
    
    repo = CatalogRepository()
    
    # Search by manufacturer
    print("\n🔍 Testing SEARCH by manufacturer...")
    ge_parts = await repo.find_by_manufacturer("GE")
    print(f"Found {len(ge_parts)} GE parts")
    
    # Full-text search
    print("\n🔍 Testing FULL-TEXT search...")
    results = await repo.search("defrost sensor")
    print(f"Found {len(results)} results for 'defrost sensor'")
    
    # Filter by department
    print("\n🔍 Testing FILTER by department...")
    fridge_parts = await repo.filter_by_department("Refrigeration")
    print(f"Found {len(fridge_parts)} refrigeration parts")
    
    print("\n✅ All database queries successful")
```

**Run:**
```bash
pytest tests/test_database.py -v -s
```

---

## Phase 3: Integration Testing (1-2 hours)

### Test 3.1: End-to-End Workflow

Create `tests/test_end_to_end.py`:

```python
import pytest
from src.orchestrator.lookup_orchestrator import LookupOrchestrator

@pytest.mark.asyncio
async def test_complete_lookup_workflow():
    """
    Test ENTIRE workflow from part number input to final catalog
    
    Workflow:
    1. Lookup Orchestrator receives part number
    2. Check cache (miss)
    3. Parallel API calls (all 4 sources)
    4. Data aggregation (keep separate by source)
    5. Dual AI validation (OpenAI + Grok)
    6. Consensus engine
    7. Catalog building
    8. Database storage
    9. Cache update
    10. Return response
    """
    
    orchestrator = LookupOrchestrator()
    
    part_number = "WR55X10025"  # Real GE part
    
    print(f"\n🚀 Starting END-TO-END test for: {part_number}")
    print("=" * 60)
    
    # Execute complete workflow
    result = await orchestrator.lookup_part(part_number)
    
    # Validate result structure
    assert result["success"] == True
    assert result["part_number"] == part_number
    assert "lookup_session_id" in result
    assert "catalog" in result
    assert "processing_time_ms" in result
    
    catalog = result["catalog"]
    
    # Validate PRIMARY attributes
    print("\n📋 PRIMARY ATTRIBUTES:")
    print(f"  1. MPN: {catalog['mpn']} ({catalog['mpn_status']})")
    print(f"  3. Manufacturer: {catalog['manufacturer']} ({catalog['manufacturer_status']})")
    print(f"  5. Title: {catalog['part_title'][:50]}...")
    print(f"  6. Description: {catalog['long_description'][:100]}...")
    print(f" 12. MSRP: ${catalog.get('msrp', 'N/A')}")
    print(f" 16. Weight: {catalog.get('weight_lbs', 'N/A')} lbs")
    print(f" 26. Compatible Models: {len(catalog.get('compatible_models', []))} models")
    
    # Validate metadata
    print("\n📊 METADATA:")
    print(f"  Confidence Score: {catalog['data_confidence_score']:.2f}")
    print(f"  Field Completeness: {catalog['field_completeness_percentage']:.1f}%")
    print(f"  AI Validated: {catalog['ai_validation_status']}")
    print(f"  Sources Used: {', '.join(catalog['source_priority'])}")
    
    # Validate performance
    print("\n⚡ PERFORMANCE:")
    print(f"  Processing Time: {result['processing_time_ms']}ms")
    print(f"  Cached: {result['cached']}")
    print(f"  Sources Consulted: {result['metadata']['sources_consulted']}")
    print(f"  Sources Successful: {result['metadata']['sources_successful']}")
    
    # Assertions
    assert catalog['mpn'] == part_number
    assert catalog['data_confidence_score'] >= 0.7
    assert catalog['field_completeness_percentage'] >= 50.0
    assert len(catalog['source_priority']) > 0
    assert result['processing_time_ms'] < 30000  # Under 30 seconds
    
    print("\n" + "=" * 60)
    print("✅ END-TO-END TEST PASSED!")
    print("=" * 60)

@pytest.mark.asyncio
async def test_multiple_parts():
    """Test lookup of multiple different parts"""
    
    test_parts = [
        "WR55X10025",  # GE Refrigerator sensor
        "W10813469",   # Whirlpool washer part
        "DA97-08406A", # Samsung refrigerator part
        "2188664",     # Whirlpool ice maker
        "ADQ73613401"  # LG refrigerator filter
    ]
    
    orchestrator = LookupOrchestrator()
    
    results_summary = []
    
    for part_number in test_parts:
        print(f"\n{'='*60}")
        print(f"Testing: {part_number}")
        print('='*60)
        
        result = await orchestrator.lookup_part(part_number)
        
        summary = {
            "part_number": part_number,
            "success": result["success"],
            "manufacturer": result["catalog"].get("manufacturer") if result["success"] else None,
            "confidence": result["catalog"].get("data_confidence_score") if result["success"] else 0,
            "completeness": result["catalog"].get("field_completeness_percentage") if result["success"] else 0,
            "time_ms": result.get("processing_time_ms", 0)
        }
        
        results_summary.append(summary)
        
        print(f"  ✅ Success: {summary['success']}")
        print(f"  📊 Confidence: {summary['confidence']:.2f}")
        print(f"  📈 Completeness: {summary['completeness']:.1f}%")
        print(f"  ⚡ Time: {summary['time_ms']}ms")
    
    # Print summary table
    print("\n\n📊 SUMMARY TABLE:")
    print("=" * 80)
    print(f"{'Part Number':<15} {'Success':<10} {'Manufacturer':<15} {'Conf.':<8} {'Compl.':<8} {'Time':<8}")
    print("=" * 80)
    
    for s in results_summary:
        print(f"{s['part_number']:<15} "
              f"{'✅' if s['success'] else '❌':<10} "
              f"{(s['manufacturer'] or 'N/A'):<15} "
              f"{s['confidence']:.2f}{'':>6} "
              f"{s['completeness']:.1f}%{'':>4} "
              f"{s['time_ms']}ms")
    
    print("=" * 80)
    
    # Calculate averages
    successful = [s for s in results_summary if s['success']]
    if successful:
        avg_confidence = sum(s['confidence'] for s in successful) / len(successful)
        avg_completeness = sum(s['completeness'] for s in successful) / len(successful)
        avg_time = sum(s['time_ms'] for s in successful) / len(successful)
        
        print(f"\n📈 AVERAGES:")
        print(f"  Success Rate: {len(successful)}/{len(test_parts)} ({len(successful)/len(test_parts)*100:.1f}%)")
        print(f"  Avg Confidence: {avg_confidence:.2f}")
        print(f"  Avg Completeness: {avg_completeness:.1f}%")
        print(f"  Avg Processing Time: {avg_time:.0f}ms")
```

**Run:**
```bash
# Single part test (detailed)
pytest tests/test_end_to_end.py::test_complete_lookup_workflow -v -s

# Multiple parts test
pytest tests/test_end_to_end.py::test_multiple_parts -v -s
```

---

### Test 3.2: API Endpoint Testing

Create `tests/test_api_endpoints.py`:

```python
import pytest
from fastapi.testclient import TestClient
from src.api import app

client = TestClient(app)

def test_health_endpoint():
    """Test health check"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_lookup_endpoint():
    """Test part lookup via API"""
    response = client.get("/api/v1/catalog/lookup/WR55X10025")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] == True
    assert data["part_number"] == "WR55X10025"
    assert "catalog" in data
    
    print(f"\n✅ API Response:")
    print(f"  Status: {response.status_code}")
    print(f"  Confidence: {data['catalog']['data_confidence_score']}")

def test_search_endpoint():
    """Test catalog search"""
    response = client.get("/api/v1/catalog/search?q=defrost+sensor&manufacturer=GE")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "results" in data
    assert len(data["results"]) > 0
    
    print(f"\n✅ Search Results: {len(data['results'])} found")

def test_authentication():
    """Test API key authentication"""
    # Without API key
    response = client.get("/api/v1/catalog/lookup/WR55X10025")
    assert response.status_code == 401
    
    # With valid API key
    headers = {"X-API-Key": "test-api-key"}
    response = client.get("/api/v1/catalog/lookup/WR55X10025", headers=headers)
    assert response.status_code == 200
```

**Run:**
```bash
# Start API server
uvicorn src.api:app --reload --port 8000

# In another terminal, run tests
pytest tests/test_api_endpoints.py -v
```

---

## Phase 4: Performance & Cost Testing (30 minutes)

### Test 4.1: Timing Analysis

Create `tests/test_performance.py`:

```python
import pytest
import time
import asyncio

@pytest.mark.asyncio
async def test_lookup_performance():
    """Measure timing at each stage"""
    
    from src.orchestrator.lookup_orchestrator import LookupOrchestrator
    
    orchestrator = LookupOrchestrator()
    part_number = "WR55X10025"
    
    timings = {}
    
    # Total time
    start_total = time.time()
    
    # Stage 1: Cache check
    start = time.time()
    # ... cache check code
    timings['cache_check'] = (time.time() - start) * 1000
    
    # Stage 2: Parallel API calls
    start = time.time()
    # ... API calls
    timings['api_calls'] = (time.time() - start) * 1000
    
    # Stage 3: AI Validation
    start = time.time()
    # ... AI validation
    timings['ai_validation'] = (time.time() - start) * 1000
    
    # Stage 4: Catalog building
    start = time.time()
    # ... catalog building
    timings['catalog_building'] = (time.time() - start) * 1000
    
    # Stage 5: Database storage
    start = time.time()
    # ... database save
    timings['database_save'] = (time.time() - start) * 1000
    
    timings['total'] = (time.time() - start_total) * 1000
    
    print("\n⏱️  TIMING BREAKDOWN:")
    print(f"  1. Cache Check:      {timings['cache_check']:>8.0f}ms")
    print(f"  2. API Calls:        {timings['api_calls']:>8.0f}ms")
    print(f"  3. AI Validation:    {timings['ai_validation']:>8.0f}ms")
    print(f"  4. Catalog Building: {timings['catalog_building']:>8.0f}ms")
    print(f"  5. Database Save:    {timings['database_save']:>8.0f}ms")
    print(f"  " + "-" * 30)
    print(f"  TOTAL:               {timings['total']:>8.0f}ms")
    
    # Assert performance targets
    assert timings['cache_check'] < 200  # Under 200ms
    assert timings['api_calls'] < 15000  # Under 15s
    assert timings['ai_validation'] < 10000  # Under 10s
    assert timings['total'] < 30000  # Under 30s
    
    print("\n✅ Performance targets met!")
```

---

### Test 4.2: Cost Tracking

Create `tests/test_cost_tracking.py`:

```python
import pytest

@pytest.mark.asyncio
async def test_ai_cost_tracking():
    """Track AI API costs"""
    
    from src.orchestrator.lookup_orchestrator import LookupOrchestrator
    
    orchestrator = LookupOrchestrator()
    
    costs = {
        "openai": 0.0,
        "grok": 0.0,
        "total": 0.0
    }
    
    # Perform lookup
    result = await orchestrator.lookup_part("WR55X10025")
    
    # Get cost from AI validation records
    ai_validation = result.get("ai_validation")
    if ai_validation:
        costs["openai"] = ai_validation.get("openai_cost", 0.0)
        costs["grok"] = ai_validation.get("grok_cost", 0.0)
        costs["total"] = costs["openai"] + costs["grok"]
    
    print("\n💰 AI COST BREAKDOWN:")
    print(f"  OpenAI (GPT-4):  ${costs['openai']:.4f}")
    print(f"  Grok:            ${costs['grok']:.4f}")
    print(f"  TOTAL:           ${costs['total']:.4f}")
    
    # Cost targets (per lookup)
    assert costs["total"] < 0.30  # Under $0.30 per lookup
    
    # Estimate daily/monthly costs
    lookups_per_day = 1000
    daily_cost = costs["total"] * lookups_per_day
    monthly_cost = daily_cost * 30
    
    print(f"\n📊 COST PROJECTIONS:")
    print(f"  Cost per lookup: ${costs['total']:.4f}")
    print(f"  Daily (1,000 lookups): ${daily_cost:.2f}")
    print(f"  Monthly (30,000 lookups): ${monthly_cost:.2f}")
    
    print("\n✅ Cost tracking complete")
```

---

## Phase 5: Test Results & Validation Checklist

### 5.1: Run Complete Test Suite

```bash
# Run ALL tests
pytest tests/ -v -s --cov=src --cov-report=html

# View coverage report
open htmlcov/index.html
```

### 5.2: Validation Checklist

Use this checklist before production deployment:

```markdown
## ✅ Pre-Production Validation Checklist

### API Connectivity
- [ ] Encompass API connects successfully
- [ ] Marcone API connects and authenticates
- [ ] Reliable Parts API connects
- [ ] Amazon Product API connects
- [ ] All 4 APIs return data for test parts
- [ ] Parallel API execution works correctly

### Data Processing
- [ ] Raw data aggregation keeps sources separate
- [ ] PRIMARY attributes identified correctly
- [ ] Field status tracking works (FOUND/NOT_APPLICABLE/NOT_FOUND)
- [ ] Unit normalization handles different formats

### AI Validation
- [ ] OpenAI validation returns field-level confidence
- [ ] Grok validation provides cross-verification
- [ ] Both AIs receive ALL raw source data
- [ ] AIs select best source per field intelligently
- [ ] Consensus engine resolves disagreements
- [ ] Source priority fallback works correctly

### Catalog Building
- [ ] 34 PRIMARY attributes populated first
- [ ] Additional attributes populated based on availability
- [ ] Confidence scoring calculated correctly
- [ ] Field completeness percentage accurate
- [ ] Source attribution tracked per field

### Database Operations
- [ ] CREATE: Records save successfully
- [ ] READ: Queries by MPN work
- [ ] UPDATE: Records update correctly
- [ ] DELETE: Cleanup works
- [ ] Full-text search functional
- [ ] Indexes improve query performance

### API Endpoints
- [ ] Health check responds
- [ ] Lookup endpoint returns complete catalog
- [ ] Search endpoint filters correctly
- [ ] Authentication validates API keys
- [ ] Rate limiting works
- [ ] Error responses formatted correctly

### Performance
- [ ] Cache hit returns < 200ms
- [ ] First lookup completes < 30 seconds
- [ ] API calls timeout handled gracefully
- [ ] Parallel processing reduces total time
- [ ] Database queries optimized

### Cost Management
- [ ] AI cost per lookup < $0.30
- [ ] Caching reduces repeat lookup costs
- [ ] Token usage tracked accurately
- [ ] Cost projections calculated

### Error Handling
- [ ] API failures handled gracefully
- [ ] Partial data scenarios work
- [ ] AI timeout doesn't crash system
- [ ] Database connection errors caught
- [ ] User receives meaningful error messages

### Data Quality
- [ ] Confidence scores realistic (0.7-1.0 range)
- [ ] HIGH confidence when both AIs agree
- [ ] MEDIUM confidence for single source
- [ ] LOW confidence triggers manual review flag
- [ ] NOT_APPLICABLE correctly identified
```

---

## Phase 6: Test with Real Parts (Production-like)

### Step 6.1: Create Test Part List

Create `test_parts.csv`:
```csv
part_number,expected_manufacturer,expected_category
WR55X10025,GE,Refrigerator
W10813469,Whirlpool,Washer
DA97-08406A,Samsung,Refrigerator
2188664,Whirlpool,Ice Maker
ADQ73613401,LG,Water Filter
WR60X10168,GE,Ice Maker
W11130558,Whirlpool,Dishwasher
5304506469,Frigidaire,Oven
DWD-HFE,GE,Dryer
DC97-16742A,Samsung,Dryer
```

### Step 6.2: Batch Test Script

Create `scripts/batch_test.py`:

```python
import asyncio
import csv
from src.orchestrator.lookup_orchestrator import LookupOrchestrator

async def batch_test():
    orchestrator = LookupOrchestrator()
    
    with open('test_parts.csv', 'r') as f:
        reader = csv.DictReader(f)
        test_parts = list(reader)
    
    results = []
    
    for i, part in enumerate(test_parts, 1):
        print(f"\n[{i}/{len(test_parts)}] Testing {part['part_number']}...")
        
        try:
            result = await orchestrator.lookup_part(part['part_number'])
            
            success = result['success']
            catalog = result.get('catalog', {})
            
            results.append({
                'part_number': part['part_number'],
                'expected_manufacturer': part['expected_manufacturer'],
                'actual_manufacturer': catalog.get('manufacturer'),
                'match': catalog.get('manufacturer') == part['expected_manufacturer'],
                'confidence': catalog.get('data_confidence_score', 0),
                'completeness': catalog.get('field_completeness_percentage', 0),
                'time_ms': result.get('processing_time_ms', 0),
                'success': success
            })
            
            print(f"  ✅ Success: {success}")
            print(f"  Manufacturer: {catalog.get('manufacturer')}")
            print(f"  Confidence: {catalog.get('data_confidence_score', 0):.2f}")
            
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
            results.append({
                'part_number': part['part_number'],
                'success': False,
                'error': str(e)
            })
    
    # Generate report
    print("\n\n" + "="*80)
    print("BATCH TEST REPORT")
    print("="*80)
    
    successful = [r for r in results if r.get('success')]
    matched = [r for r in successful if r.get('match')]
    
    print(f"\nSuccess Rate: {len(successful)}/{len(results)} ({len(successful)/len(results)*100:.1f}%)")
    print(f"Manufacturer Match Rate: {len(matched)}/{len(successful)} ({len(matched)/len(successful)*100:.1f}%)")
    
    if successful:
        avg_conf = sum(r['confidence'] for r in successful) / len(successful)
        avg_comp = sum(r['completeness'] for r in successful) / len(successful)
        avg_time = sum(r['time_ms'] for r in successful) / len(successful)
        
        print(f"\nAverages (successful lookups):")
        print(f"  Confidence: {avg_conf:.2f}")
        print(f"  Completeness: {avg_comp:.1f}%")
        print(f"  Processing Time: {avg_time:.0f}ms")
    
    # Save detailed results
    with open('test_results.csv', 'w', newline='') as f:
        if results:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)
    
    print(f"\nDetailed results saved to: test_results.csv")

if __name__ == "__main__":
    asyncio.run(batch_test())
```

**Run:**
```bash
python scripts/batch_test.py
```

---

## Estimated Testing Costs

| Phase | Duration | AI Calls | Estimated Cost |
|-------|----------|----------|----------------|
| Phase 2.3 - AI Validation | 15 min | 6 calls | $0.60 |
| Phase 3.1 - End-to-End | 30 min | 20 calls | $2.00 |
| Phase 3.2 - API Tests | 15 min | 10 calls | $1.00 |
| Phase 6 - Batch Test (10 parts) | 1 hour | 40 calls | $4.00 |
| **TOTAL** | **~3 hours** | **76 calls** | **~$7.60** |

**This is CHEAP for validating a $250K+ system!**

---

## Success Criteria

Before moving to production, ensure:

✅ **API Success Rate**: ≥90% of test parts found in at least one source  
✅ **Confidence Score**: Average ≥0.85 for successful lookups  
✅ **Completeness**: Average ≥80% PRIMARY attributes populated  
✅ **Performance**: Average lookup time <25 seconds  
✅ **Cost**: Per-lookup cost <$0.25  
✅ **Accuracy**: Manufacturer matching ≥95% when found  
✅ **AI Agreement**: OpenAI & Grok agree on ≥70% of fields  

---

## Next Steps After Local Testing

Once all tests pass:

1. **Stage 1**: Deploy to AWS staging environment
2. **Stage 2**: Run same test suite in staging (cloud database)
3. **Stage 3**: Load testing with 100+ concurrent requests
4. **Stage 4**: Cost validation over 1000 lookups
5. **Stage 5**: Salesforce integration testing
6. **Stage 6**: Production deployment with monitoring

---

## Troubleshooting Common Issues

### Issue: API Timeouts
```python
# Increase timeout in API clients
httpx.AsyncClient(timeout=30.0)  # 30 second timeout
```

### Issue: AI Costs Too High
```python
# Enable aggressive caching
ENABLE_AI_CACHING=true

# Use cheaper model for validation
OPENAI_MODEL=gpt-3.5-turbo  # Instead of gpt-4
```

### Issue: Low Confidence Scores
- Check if all 4 APIs are returning data
- Verify source priority is correct
- Review AI prompts for clarity

### Issue: Database Connection Errors
```bash
# Check PostgreSQL is running
docker ps | grep postgres

# Test connection
psql -h localhost -U postgres -d parts_catalog -c "SELECT 1"
```

---

## Monitoring During Tests

Use this script to monitor test execution:

```bash
# Terminal 1: Watch logs
tail -f logs/app.log

# Terminal 2: Monitor database
watch -n 1 'psql -h localhost -U postgres -d parts_catalog -c "SELECT COUNT(*) FROM master_catalog"'

# Terminal 3: Monitor Redis cache
watch -n 1 'redis-cli INFO stats | grep keyspace_hits'
```

---

**You're now ready to test the entire system locally before any production deployment!** 🚀
