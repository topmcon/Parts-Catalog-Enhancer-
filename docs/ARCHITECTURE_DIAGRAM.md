# System Architecture & Process Flow

## Complete End-to-End Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                  ENTRY POINTS                                       │
│                                                                                     │
│  ┌──────────────┐         ┌──────────────┐         ┌──────────────┐              │
│  │  Salesforce  │         │  Direct API  │         │ Web Interface│              │
│  │   Request    │         │    Client    │         │  (Optional)  │              │
│  └──────┬───────┘         └──────┬───────┘         └──────┬───────┘              │
│         │                        │                        │                        │
│         └────────────────────────┴────────────────────────┘                        │
│                                  │                                                  │
└──────────────────────────────────┼──────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                            API GATEWAY / LOAD BALANCER                              │
│                          (Authentication & Rate Limiting)                           │
└──────────────────────────────────┬──────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              LOOKUP ORCHESTRATOR                                    │
│  ┌─────────────────────────────────────────────────────────────────────────────┐  │
│  │ 1. Validate part number format                                              │  │
│  │ 2. Check cache (Redis) - If found, return immediately                       │  │
│  │ 3. Create lookup session record in database                                 │  │
│  │ 4. Dispatch parallel API calls to all suppliers                             │  │
│  └─────────────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────┬──────────────────────────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────────────────────────┐
│                        PARALLEL API CALLS (All at once)                              │
│                                                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  Encompass   │  │   Marcone    │  │  Reliable    │  │   Amazon     │          │
│  │     API      │  │     API      │  │  Parts API   │  │  Product API │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                 │                 │                 │                     │
│         │  Priority 1     │  Priority 2     │  Priority 3     │  Priority 4        │
│         │  (OEM Data)     │  (Supplier)     │  (Supplier)     │  (Retail)          │
│         │                 │                 │                 │                     │
│  ┌──────▼─────────────────▼─────────────────▼─────────────────▼───────┐           │
│  │         Response Handler (Timeout: 10 seconds each)                 │           │
│  │  • Store raw JSON responses in database                             │           │
│  │  • Handle errors/timeouts gracefully                                │           │
│  │  • Continue even if some APIs fail                                  │           │
│  └──────────────────────────────────────────┬───────────────────────────┘           │
└─────────────────────────────────────────────┼───────────────────────────────────────┘
                                              │
                                              ▼
┌──────────────────────────────────────────────────────────────────────────────────────┐
│                           DATA AGGREGATION ENGINE                                    │
│  ┌────────────────────────────────────────────────────────────────────────────┐     │
│  │ Step 1: Parse & Normalize                                                  │     │
│  │  • Convert all responses to common format                                  │     │
│  │  • Extract all available fields from each source                          │     │
│  │    (targeting 34 PRIMARY universal attributes + 50+ additional)           │     │
│  │  • Handle missing/null values                                              │     │
│  │  • Normalize units (inches, mm, etc.)                                      │     │
│  │                                                                             │     │
│  │ Step 2: Store Raw Data by Source (NO MERGING)                             │     │
│  │  • Keep each source's data SEPARATE                                        │     │
│  │  • Store in structured format:                                             │     │
│  │    - encompass_data: {field1: value1, field2: value2, ...}                │     │
│  │    - marcone_data: {field1: value1, field2: value2, ...}                  │     │
│  │    - reliable_data: {field1: value1, field2: value2, ...}                 │     │
│  │    - amazon_data: {field1: value1, field2: value2, ...}                   │     │
│  │  • Preserve original values without modification                           │     │
│  │  • Pass ALL raw source data to AI for intelligent analysis                │     │
│  └────────────────────────────────────────────────────────────────────────────┘     │
└──────────────────────────────────────────┬───────────────────────────────────────────┘
                                           │
                                           ▼
┌──────────────────────────────────────────────────────────────────────────────────────┐
│                        AI VALIDATION LAYER (Parallel)                                │
│                   Input: RAW DATA from ALL 4 sources separately                      │
│                                                                                      │
│  ┌─────────────────────────────────────┐    ┌─────────────────────────────────────┐│
│  │         OpenAI GPT-4                │    │           Grok AI                   ││
│  │                                     │    │                                     ││
│  │  Task 1: Review ALL Source Data    │    │  Task 1: Review ALL Source Data    ││
│  │  • Receive raw data from:           │    │  • Receive same raw data from:     ││
│  │    - Encompass (OEM authority)      │    │    - Encompass (OEM authority)     ││
│  │    - Marcone (supplier data)        │    │    - Marcone (supplier data)       ││
│  │    - Reliable Parts (supplier)      │    │    - Reliable Parts (supplier)     ││
│  │    - Amazon (retail/reviews)        │    │    - Amazon (retail/reviews)       ││
│  │  • Compare values across sources    │    │  • Independent comparison          ││
│  │                                     │    │                                     ││
│  │  Task 2: Determine Best Value      │    │  Task 2: Determine Best Value      ││
│  │  For EACH attribute (34 PRIMARY +  │    │  For EACH attribute (34 PRIMARY +  │
│  │  50+ additional = 84 total):       │    │  50+ additional = 84 total):       │
│  │  • Which source has most accurate?  │    │  • Which source is most reliable?  ││
│  │  • Resolve conflicts intelligently  │    │  • Provide second opinion          ││
│  │  • Assign confidence score (0-1)    │    │  • Assign confidence score (0-1)   ││
│  │  • Justify selection reasoning      │    │  • Cross-validate OpenAI choices   ││
│  │                                     │    │                                     ││
│  │  Task 3: Fill Missing Data         │    │  Task 3: Verify Completeness       ││
│  │  • Infer from available sources     │    │  • Check logical consistency       ││
│  │  • Calculate derived values         │    │  • Flag suspicious values          ││
│  │                                     │    │                                     ││
│  │  Task 4: Generate Content          │    │  Task 4: Validate Content          ││
│  │  • Create product description       │    │  • Verify description accuracy     ││
│  │  • Write SEO-friendly title         │    │  • Check for hallucinations        ││
│  │  • Generate marketing copy          │    │  • Ensure factual correctness      ││
│  │                                     │    │                                     ││
│  └─────────────────┬───────────────────┘    └─────────────────┬───────────────────┘│
│                    │                                           │                     │
│                    └───────────────────┬───────────────────────┘                     │
│                                        ▼                                             │
│                        ┌───────────────────────────────┐                            │
│                        │   Store AI Validation Records │                            │
│                        │    in ai_validations table    │                            │
│                        └───────────────┬───────────────┘                            │
└────────────────────────────────────────┼──────────────────────────────────────────────┘
                                         │
                                         ▼
┌──────────────────────────────────────────────────────────────────────────────────────┐
│                            CONSENSUS ENGINE                                          │
│  ┌────────────────────────────────────────────────────────────────────────────┐     │
│  │ Algorithm: Determine Final Values for Each Field                           │     │
│  │                                                                             │     │
│  │  IF OpenAI and Grok agree (within 10% tolerance):                          │     │
│  │    ✓ Use agreed value                                                      │     │
│  │    ✓ Mark confidence = HIGH                                                │     │
│  │                                                                             │     │
│  │  ELSE IF they disagree:                                                    │     │
│  │    → Apply source priority: Encompass > Marcone > Reliable > Amazon       │     │
│  │    → Use value from highest-priority source                                │     │
│  │    → Mark confidence = MEDIUM                                              │     │
│  │    → Flag for potential manual review                                      │     │
│  │                                                                             │     │
│  │  Calculate Overall Confidence Score:                                       │     │
│  │    • Field-level scores weighted by importance                             │     │
│  │    • Catalog-level score = average of all fields                           │     │
│  │    • Range: 0.0 (no confidence) to 1.0 (perfect)                           │     │
│  │                                                                             │     │
│  │  Determine Field Status:                                                   │     │
│  │    • FOUND = Data available and validated                                  │     │
│  │    • NOT_FOUND = Field applicable but no data                              │     │
│  │    • NOT_APPLICABLE = Field doesn't apply to this part type                │     │
│  └────────────────────────────────────────────────────────────────────────────┘     │
└──────────────────────────────────────────┬───────────────────────────────────────────┘
                                           │
                                           ▼
┌──────────────────────────────────────────────────────────────────────────────────────┐
│                         MASTER CATALOG BUILDER                                       │
│  ┌────────────────────────────────────────────────────────────────────────────┐     │
│  │ Create Complete Catalog Record with 34 PRIMARY + 50+ ADDITIONAL Fields:    │     │
│  │                                                                             │     │
│  │ ===== PRIMARY ATTRIBUTES (34 fields - UNIVERSAL) =====                     │     │
│  │ These are populated FIRST with highest priority                            │     │
│  │                                                                             │     │
│  │  1. PRIMARY PART NUMBER (MPN)                                              │     │
│  │  ✓ manufacturer_part_number (mpn)                                          │     │
│  │                                                                             │     │
│  │  2-3. IDENTIFICATION                                                       │     │
│  │  ✓ alternative_model_numbers                                               │     │
│  │  ✓ manufacturer_name / brand                                               │     │
│  │                                                                             │     │
│  │  4-9. CORE DESCRIPTIONS & CATEGORIZATION                                   │     │
│  │  ✓ part_type (OEM, Generic, Aftermarket)                                   │     │
│  │  ✓ part_title (AI-enhanced if needed)                                      │     │
│  │  ✓ long_description (AI-enhanced, 200-1000 words)                          │     │
│  │  ✓ primary_department                                                      │     │
│  │  ✓ primary_category                                                        │     │
│  │  ✓ all_sub_categories / tags                                               │     │
│  │                                                                             │     │
│  │  10-11. IMAGES                                                             │     │
│  │  ✓ primary_image_url                                                       │     │
│  │  ✓ gallery_image_urls (array)                                              │     │
│  │                                                                             │     │
│  │  12-15. PRICING                                                            │     │
│  │  ✓ msrp / compare_at_price                                                 │     │
│  │  ✓ high_average_sale_price                                                 │     │
│  │  ✓ low_average_sale_price                                                  │     │
│  │  ✓ current_selling_price                                                   │     │
│  │                                                                             │     │
│  │  16-22. PHYSICAL DIMENSIONS                                                │     │
│  │  ✓ weight_lbs (shipping)                                                   │     │
│  │  ✓ box_length_in, box_width_in, box_height_in (L×W×H)                     │     │
│  │  ✓ product_length_in, product_width_in, product_height_in (unboxed)       │     │
│  │                                                                             │     │
│  │  23-25. IDENTIFIERS & ELECTRICAL                                           │     │
│  │  ✓ upc_ean_gtin                                                            │     │
│  │  ✓ voltage                                                                 │     │
│  │  ✓ terminal_type                                                           │     │
│  │                                                                             │     │
│  │  26-27. COMPATIBILITY                                                      │     │
│  │  ✓ top_10_compatible_models (list)                                         │     │
│  │  ✓ cross_reference_part_numbers                                            │     │
│  │                                                                             │     │
│  │  28-30. APPEARANCE                                                         │     │
│  │  ✓ color                                                                   │     │
│  │  ✓ material                                                                │     │
│  │  ✓ finish                                                                  │     │
│  │                                                                             │     │
│  │  31-34. SUPPORT & DOCUMENTATION                                            │     │
│  │  ✓ related_symptoms (what it fixes)                                        │     │
│  │  ✓ installation_suggestions                                                │     │
│  │  ✓ specification_table (key-value pairs)                                   │     │
│  │  ✓ manufacturer_product_page_url                                           │     │
│  │                                                                             │     │
│  │ ===== ADDITIONAL ATTRIBUTES (50+ fields) =====                             │     │
│  │ Part-specific or extended fields                                           │     │
│  │                                                                             │     │
│  │  ✓ Extended electrical (wattage, amperage, frequency, phase)              │     │
│  │  ✓ Temperature specs (operating range)                                     │     │
│  │  ✓ Pressure/flow ratings                                                   │     │
│  │  ✓ Certifications (UL, CSA, ETL)                                           │     │
│  │  ✓ Warranty information                                                    │     │
│  │  ✓ Availability & lead times                                               │     │
│  │  ✓ Country of origin                                                       │     │
│  │  ✓ Package quantity                                                        │     │
│  │  ✓ Replacement info (replaces/replaced by)                                 │     │
│  │  ✓ Additional documentation (manuals, videos, diagrams)                    │     │
│  │  ✓ SEO fields (keywords, meta descriptions)                                │     │
│  │  ... and more                                                              │     │
│  │                                                                             │     │
│  │ ===== SYSTEM METADATA =====                                                │     │
│  │  ✓ catalog_id, created_at, last_updated                                    │     │
│  │  ✓ data_confidence_score (0.0 - 1.0)                                       │     │
│  │  ✓ ai_validation_status                                                    │     │
│  │  ✓ source_attribution (which APIs provided data)                           │     │
│  │  ✓ ai_enhancement_applied                                                  │     │
│  └────────────────────────────────────────────────────────────────────────────┘     │
└──────────────────────────────────────────┬───────────────────────────────────────────┘
                                           │
                                           ▼
┌──────────────────────────────────────────────────────────────────────────────────────┐
│                      DATABASE STORAGE (PostgreSQL)                                   │
│                                                                                      │
│  ┌──────────────────────────────────────────────────────────────────────────────┐  │
│  │                        WRITE OPERATIONS                                      │  │
│  │                                                                               │  │
│  │  1. INSERT into master_catalog                                               │  │
│  │     • Store complete catalog record                                          │  │
│  │     • Generate UUID as primary key                                           │  │
│  │     • Set created_at timestamp                                               │  │
│  │                                                                               │  │
│  │  2. INSERT into spec_table_entries                                           │  │
│  │     • Store dynamic specifications                                           │  │
│  │     • Key-value pairs for custom fields                                      │  │
│  │                                                                               │  │
│  │  3. INSERT into images                                                       │  │
│  │     • Link to S3 URLs                                                        │  │
│  │     • Store image metadata                                                   │  │
│  │                                                                               │  │
│  │  4. UPDATE lookup_sessions                                                   │  │
│  │     • Mark as completed                                                      │  │
│  │     • Record processing time                                                 │  │
│  │                                                                               │  │
│  │  5. INSERT into audit_log                                                    │  │
│  │     • Track who created record                                               │  │
│  │     • Log all changes                                                        │  │
│  │                                                                               │  │
│  │  6. UPDATE cache (Redis)                                                     │  │
│  │     • Cache final result for 24 hours                                        │  │
│  │     • Key = part_number                                                      │  │
│  └──────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
│  ┌──────────────────────────────────────────────────────────────────────────────┐  │
│  │                            INDEXES                                           │  │
│  │  • idx_catalog_mpn (for fast part number lookup)                            │  │
│  │  • idx_catalog_manufacturer (filter by brand)                               │  │
│  │  • idx_catalog_search (full-text search)                                    │  │
│  │  • idx_sessions_timestamp (recent lookups)                                  │  │
│  └──────────────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────┬───────────────────────────────────────────┘
                                           │
                                           ▼
┌──────────────────────────────────────────────────────────────────────────────────────┐
│                         RESPONSE FORMATTER                                           │
│  ┌────────────────────────────────────────────────────────────────────────────┐     │
│  │ Build API Response:                                                         │     │
│  │                                                                             │     │
│  │  {                                                                          │     │
│  │    "success": true,                                                         │     │
│  │    "lookup_session_id": "uuid",                                             │     │
│  │    "part_number": "WR55X10025",                                             │     │
│  │    "catalog": {                                                             │     │
│  │      "catalog_id": "uuid",                                                  │     │
│  │      "manufacturer": "GE",                                                  │     │
│  │      "title": "Refrigerator Water Filter",                                 │     │
│  │      "description": "...",                                                  │     │
│  │      "price": {"list": 49.99, "cost": 32.50},                              │     │
│  │      "specifications": {...},                                               │     │
│  │      "images": [...],                                                       │     │
│  │      "compatibility": {...},                                                │     │
│  │      "confidence_score": 0.94                                               │     │
│  │    },                                                                       │     │
│  │    "sources_consulted": ["Encompass", "Marcone", "Amazon"],                │     │
│  │    "processing_time_ms": 4500,                                              │     │
│  │    "cached": false                                                          │     │
│  │  }                                                                          │     │
│  └────────────────────────────────────────────────────────────────────────────┘     │
└──────────────────────────────────────────┬───────────────────────────────────────────┘
                                           │
                                           ▼
┌──────────────────────────────────────────────────────────────────────────────────────┐
│                           RETURN TO CLIENT                                           │
│                                                                                      │
│  ┌──────────────┐         ┌──────────────┐         ┌──────────────┐               │
│  │  Salesforce  │         │  Direct API  │         │ Web Interface│               │
│  │   ← Response │         │   ← Response │         │  ← Response  │               │
│  └──────────────┘         └──────────────┘         └──────────────┘               │
│                                                                                      │
│  • HTTP 200 OK with complete catalog data                                           │
│  • Typical response time: 3-6 seconds (first lookup)                                │
│  • Cached response time: <100ms (subsequent lookups)                                │
└──────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Detailed Process Flow by Stage

### Stage 1: Request Initiation (0-100ms)

```
User/System → API Gateway → Authentication → Rate Limit Check → Route to Service
```

**What Happens:**
1. Request arrives with part number (e.g., "WR55X10025")
2. API gateway validates authentication token
3. Check rate limits (max 100 requests/minute per client)
4. Route to appropriate backend service

---

### Stage 2: Cache Check (100-200ms)

```
┌─────────────┐
│Check Redis  │ ──Yes→ Return cached result (END)
│Cache        │
└──────┬──────┘
       │
       No (Cache miss)
       │
       ▼
  Continue to Stage 3
```

**Cache Keys:**
- `catalog:{part_number}`
- TTL: 24 hours
- Saves 3-5 seconds per lookup

---

### Stage 3: Parallel API Calls (200ms - 10 seconds)

```
Orchestrator dispatches 4 simultaneous API calls:

┌─────────────────┐
│  Encompass API  │ ─── Timeout: 10s ──┐
└─────────────────┘                     │
┌─────────────────┐                     │
│  Marcone API    │ ─── Timeout: 10s ──┤
└─────────────────┘                     ├──→ Wait for all (or timeout)
┌─────────────────┐                     │
│  Reliable API   │ ─── Timeout: 10s ──┤
└─────────────────┘                     │
┌─────────────────┐                     │
│  Amazon API     │ ─── Timeout: 10s ──┘
└─────────────────┘

Each API call:
1. Makes HTTP request
2. Parses response
3. Stores raw JSON in raw_source_responses table
4. Returns normalized data structure
```

**Timeout Strategy:**
- Don't wait for slow APIs
- Continue with available data
- Log failures for monitoring

---

### Stage 4: Data Aggregation (10-11 seconds)

```
Input: 4 API responses (some may be null if failed)

┌─────────────────────────────────────────┐
│  FOR each source:                       │
│                                         │
│  1. Parse raw JSON response             │
│  2. Extract all available fields        │
│     (34 PRIMARY + 50+ additional)       │
│  3. Normalize units to standard format  │
│  4. Store in structured object          │
│  5. Keep source data SEPARATE           │
│                                         │
│  NO MERGING - Preserve all raw data!    │
└─────────────────────────────────────────┘

Output: Structured data object with 4 separate source datasets

{
  "encompass_data": {weight: "2.5 lbs", ...},
  "marcone_data": {weight: "1.2 kg", ...},
  "reliable_data": {weight: null, ...},
  "amazon_data": {weight: "2.6 lbs", ...}
}
```

**Why No Merging?**
- AI needs to see ALL original data from each source
- AI determines which source is most accurate for EACH field
- Prevents information loss from premature merging
- Allows intelligent, context-aware decisions

---

### Stage 5: AI Validation (11-16 seconds)

```
Send ALL RAW SOURCE DATA to OpenAI and Grok in parallel:

Prompt Template:
"Given this part data from 4 sources, determine the BEST value for each attribute:

Part Number: WR55X10025
Manufacturer: GE

Source Data:
- Encompass (OEM, Priority 1): 
  {weight: '2.5 lbs', dimensions: '10x3x3', color: 'white', ...}
  
- Marcone (Supplier, Priority 2):
  {weight: '1.2 kg', dimensions: '254x76x76 mm', color: 'white', ...}
  
- Reliable Parts (Supplier, Priority 3):
  {weight: null, dimensions: null, color: 'white', ...}
  
- Amazon (Retail, Priority 4):
  {weight: '2.6 lbs', dimensions: '10.2x3.1x3', color: 'off-white', ...}

For EACH attribute, determine:
1. Which source has the most accurate value?
2. What is the best value to use?
3. Confidence score (0-1)
4. Reasoning for selection

Return validated catalog attributes."

┌──────────────────────────┐     ┌──────────────────────────┐
│ OpenAI Response          │     │  Grok Response           │
│                          │     │                          │
│ weight:                  │     │  weight:                 │
│   value: "2.5 lbs"       │     │    value: "2.5 lbs"      │
│   source: "Encompass"    │     │    source: "Encompass"   │
│   confidence: 0.92       │     │    confidence: 0.89      │
│   reason: "OEM data      │     │    reason: "Matches      │
│   most reliable"         │     │    converted value"      │
│                          │     │                          │
│ color:                   │     │  color:                  │
│   value: "white"         │     │    value: "white"        │
│   source: "Encompass"    │     │    source: "consensus"   │
│   confidence: 0.95       │     │    confidence: 0.93      │
└──────────────────────────┘     └──────────────────────────┘
         │                              │
         └──────────────┬───────────────┘
                        ▼
      Both selected same source/value → HIGH confidence
```

**AI Tasks:**
1. **Analyze** all raw data from every source
2. **Determine** which source is most accurate for EACH field
3. **Select** best value with justification
4. **Resolve** conflicts intelligently (not just by priority)
5. **Infer** missing data from context
6. **Generate** descriptions and marketing copy

---

### Stage 6: Consensus Engine (16-17 seconds)

```
Decision Tree:

┌───────────────────────────────────────────────────────┐
│ For each of 80+ fields:                               │
│                                                       │
│ ├─ Did OpenAI and Grok select SAME source & value?   │
│ │  └─ YES → Use value, HIGH confidence (0.9-1.0)     │
│ │                                                     │
│ └─ NO (Disagreement on source or value)?             │
│    ├─ Compare AI reasoning                            │
│    │                                                   │
│    ├─ If one AI has stronger justification:           │
│    │  └─ Use that AI's selection, MEDIUM confidence   │
│    │                                                   │
│    ├─ If equal justification:                         │
│    │  └─ Apply source priority as tiebreaker:         │
│    │     Encompass > Marcone > Reliable > Amazon     │
│    │  └─ Mark MEDIUM confidence (0.7-0.89)            │
│    │                                                   │
│    └─ Flag for manual review if:                      │
│       • Both AIs have low confidence (<0.7)           │
│       • Critical field (price, safety specs)          │
│       • Large discrepancy between sources             │
│                                                       │
│ Calculate overall catalog confidence score:           │
│ = Σ(field_confidence × field_importance_weight)       │
│   ─────────────────────────────────────────────       │
│   Σ(field_importance_weight)                          │
└───────────────────────────────────────────────────────┘

Final Output: 
- Catalog with values selected from best sources
- 34 PRIMARY attributes populated first (universal)
- 50+ additional attributes populated (part-specific)
- Each field tagged with source used
- Overall confidence: 0.94
- 78 fields FOUND (with source attribution)
- 4 fields NOT_FOUND (not in any source)
- 2 fields NOT_APPLICABLE (doesn't apply to part type)
```

---

### Stage 7: Catalog Building (17-18 seconds)

```
Construct final MasterCatalogRecord:

{
  catalog_id: UUID,
  mpn: "WR55X10025",
  manufacturer: "GE",
  
  // Core Info
  part_title: "GE WR55X10025 Refrigerator Water Filter...",
  short_description: "...",
  long_description: "...", (AI-generated, 500 words)
  
  // Pricing
  list_price: 49.99,
  cost_price: 32.50,
  
  // Physical
  weight: "2.5",
  weight_unit: "lbs",
  length: "10",
  width: "3",
  height: "3",
  dimensions_unit: "inches",
  
  // Compatibility
  compatible_models: ["GE Profile Series", ...],
  replaces: ["WR97X10006", "WR55X10023"],
  
  // Images
  images: [
    {url: "s3://bucket/images/WR55X10025-1.jpg", type: "primary"},
    {url: "s3://bucket/images/WR55X10025-2.jpg", type: "alternate"},
  ],
  
  // Metadata
  data_confidence_score: 0.94,
  sources_used: ["encompass", "marcone", "amazon"],
  ai_validated: true,
  last_validated_at: "2025-12-12T15:30:00Z"
}
```

---

### Stage 8: Database Storage (18-19 seconds)

```
Transaction begins:

┌────────────────────────────────────┐
│ 1. INSERT master_catalog           │
│    → Catalog ID: abc-123           │
│                                    │
│ 2. INSERT spec_table_entries       │
│    → 15 custom specifications      │
│                                    │
│ 3. INSERT images (3 rows)          │
│    → Link to catalog_id            │
│                                    │
│ 4. UPDATE lookup_sessions          │
│    → Status = "completed"          │
│    → Processing time = 18500ms     │
│                                    │
│ 5. INSERT audit_log                │
│    → Action = "catalog_created"    │
│    → User = "system"               │
│                                    │
│ 6. SET Redis cache                 │
│    → Key: catalog:WR55X10025       │
│    → TTL: 86400 seconds (24h)      │
└────────────────────────────────────┘

Transaction commits
```

**Database Tables Updated:**
- `master_catalog` (1 row)
- `spec_table_entries` (15 rows)
- `images` (3 rows)
- `lookup_sessions` (1 update)
- `audit_log` (1 row)

---

### Stage 9: Response Delivery (19-19.5 seconds)

```
Format and return JSON:

HTTP 200 OK
Content-Type: application/json

{
  "success": true,
  "lookup_session_id": "session-uuid",
  "processing_time_ms": 19200,
  "cached": false,
  
  "catalog": {
    ... (complete catalog data)
  },
  
  "metadata": {
    "sources_consulted": 3,
    "sources_successful": ["Encompass", "Marcone", "Amazon"],
    "sources_failed": ["Reliable"],
    "ai_validation_performed": true,
    "confidence_score": 0.94
  }
}
```

---

## Timing Summary

| Stage | Duration | Cumulative |
|-------|----------|------------|
| 1. Request Initiation | 100ms | 100ms |
| 2. Cache Check | 100ms | 200ms |
| 3. Parallel API Calls | 9,800ms | 10,000ms |
| 4. Data Aggregation | 1,000ms | 11,000ms |
| 5. AI Validation (parallel) | 5,000ms | 16,000ms |
| 6. Consensus Engine | 1,000ms | 17,000ms |
| 7. Catalog Building | 1,000ms | 18,000ms |
| 8. Database Storage | 1,000ms | 19,000ms |
| 9. Response Delivery | 500ms | 19,500ms |

**Total First Lookup: ~19.5 seconds**
**Total Cached Lookup: ~150ms**

---

## Error Handling Flow

```
┌─────────────────────────────────────────┐
│  Any stage can fail                     │
└─────────┬───────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────┐
│  Catch exception                        │
│  ├─ Log error with context              │
│  ├─ Attempt graceful degradation        │
│  │   (continue with partial data)       │
│  └─ Return error response if critical   │
└─────────────────────────────────────────┘

Example: If Marcone API fails
├─ Log: "Marcone API timeout"
├─ Continue with Encompass + Amazon data
└─ Return catalog with lower confidence
```

**Retry Logic:**
- Transient failures: Retry 3 times with exponential backoff
- Permanent failures: Log and continue
- Critical failures: Return 500 error with details

---

## Monitoring Points

```
┌──────────────────────────────────────────┐
│  CloudWatch Metrics at Each Stage:      │
├──────────────────────────────────────────┤
│  • Request rate                          │
│  • Cache hit/miss ratio                  │
│  • API response times (per source)       │
│  • API failure rates                     │
│  • AI validation duration                │
│  • AI cost per lookup                    │
│  • Consensus engine decisions            │
│  • Database write latency                │
│  • Overall end-to-end latency            │
│  • Confidence score distribution         │
└──────────────────────────────────────────┘
```

**Alerts Triggered:**
- Average response time > 25 seconds
- API failure rate > 10%
- Cache hit rate < 40%
- Database connection pool > 90% utilized
- AI cost > $0.50 per lookup

---

## Data Flow Size Estimates

| Stage | Data Size | Notes |
|-------|-----------|-------|
| API Responses | 50-200KB | Raw JSON per source |
| Aggregated Data | 100KB | Merged fields |
| AI Prompts | 10-20KB | Context + instructions |
| AI Responses | 5-10KB | Validation results |
| Final Catalog | 50KB | Compressed record |
| Database Storage | 150KB | With indexes |

---

## Scalability Considerations

```
Current Design Handles:

┌─────────────────────────────────────────┐
│  100 concurrent requests                │
│  ├─ 10 API worker threads each          │
│  ├─ 5 AI validation workers             │
│  └─ Database connection pool: 20        │
│                                         │
│  Daily capacity: ~50,000 lookups        │
│  Monthly: ~1.5 million lookups          │
└─────────────────────────────────────────┘

To scale to 1 million/day:
├─ Add horizontal scaling (5-10 servers)
├─ Increase database connection pools
├─ Add more Redis cache nodes
└─ Implement queue-based processing
```

---

## Key Decision Points in Flow

1. **Cache Hit?** → Return immediately (saves $0.15 + 19 seconds)
2. **API Timeout?** → Continue with available data
3. **AI Agreement?** → High confidence, no manual review
4. **Low Confidence?** → Flag for human review
5. **Missing Critical Field?** → Return with warning

---

This architecture ensures:
✅ **Reliability** - Multiple data sources with fallbacks
✅ **Accuracy** - Dual AI validation with consensus
✅ **Speed** - Parallel processing and caching
✅ **Completeness** - 34 PRIMARY + 50+ additional fields with status tracking
✅ **Auditability** - Full trail from source to final value
✅ **Scalability** - Horizontal scaling capability
