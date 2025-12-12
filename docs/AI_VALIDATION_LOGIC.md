# AI Validation Logic & Workflows

## Overview

This document details the AI validation system that uses OpenAI and Grok to validate, cross-check, and enhance part data from multiple supplier sources.

---

## Table of Contents

1. [Validation Workflow](#validation-workflow)
2. [AI Prompt Engineering](#ai-prompt-engineering)
3. [Consensus Algorithm](#consensus-algorithm)
4. [Confidence Scoring](#confidence-scoring)
5. [Conflict Resolution](#conflict-resolution)
6. [Content Generation](#content-generation)
7. [Cost Optimization](#cost-optimization)

---

## 1. Validation Workflow

### 1.1 High-Level Flow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Data Collection                                           │
│    ├─ Encompass Response                                     │
│    ├─ Marcone Response                                       │
│    ├─ Reliable Parts Response                                │
│    └─ Amazon Response                                        │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│ 2. Data Normalization                                        │
│    ├─ Convert to standard format                             │
│    ├─ Extract key fields                                     │
│    └─ Identify conflicts                                     │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
┌───────▼───────┐         ┌───────▼───────┐
│ 3a. OpenAI    │         │ 3b. Grok      │
│    Validation │         │    Validation │
│                │         │                │
│ • Verify data │         │ • Verify data │
│ • Check match │         │ • Check match │
│ • Confidence  │         │ • Confidence  │
│ • Conflicts   │         │ • Conflicts   │
└───────┬───────┘         └───────┬───────┘
        │                         │
        └────────────┬────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│ 4. AI Consensus Engine                                       │
│    ├─ Compare OpenAI vs Grok results                         │
│    ├─ Calculate agreement score                              │
│    ├─ Resolve conflicts                                      │
│    └─ Generate confidence scores                             │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│ 5. Content Generation                                        │
│    ├─ Select best title (OpenAI or Grok)                     │
│    ├─ Select best description (OpenAI or Grok)               │
│    └─ Generate final marketing content                       │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│ 6. Master Catalog Update                                     │
│    ├─ Populate validated fields                              │
│    ├─ Store confidence scores                                │
│    ├─ Mark data status (FOUND/NOT_FOUND/NOT_APPLICABLE)      │
│    └─ Store AI attribution                                   │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 Detailed Validation Steps

```python
async def validate_part_data(session_id: UUID, part_number: str) -> AIValidationRecord:
    """
    Complete AI validation workflow
    """
    
    # Step 1: Collect all source data
    raw_responses = await get_raw_responses(session_id)
    
    # Step 2: Normalize data
    normalized_data = {
        "encompass": normalize_encompass(raw_responses["encompass"]),
        "marcone": normalize_marcone(raw_responses["marcone"]),
        "reliable": normalize_reliable(raw_responses["reliable"]),
        "amazon": normalize_amazon(raw_responses["amazon"])
    }
    
    # Step 3: Prepare validation context
    validation_context = prepare_validation_context(part_number, normalized_data)
    
    # Step 4: Parallel AI validation
    openai_task = validate_with_openai(validation_context)
    grok_task = validate_with_grok(validation_context)
    
    openai_result, grok_result = await asyncio.gather(
        openai_task, 
        grok_task,
        return_exceptions=True
    )
    
    # Step 5: Handle AI failures
    if isinstance(openai_result, Exception):
        logger.error(f"OpenAI validation failed: {openai_result}")
        openai_result = None
    
    if isinstance(grok_result, Exception):
        logger.error(f"Grok validation failed: {grok_result}")
        grok_result = None
    
    # Step 6: Consensus
    consensus_result = build_consensus(
        openai_result, 
        grok_result, 
        normalized_data
    )
    
    # Step 7: Content generation (parallel)
    if openai_result and grok_result:
        openai_content = await generate_content_openai(consensus_result)
        grok_content = await generate_content_grok(consensus_result)
        
        # Select best content
        final_content = select_best_content(openai_content, grok_content)
    else:
        # Fallback to single AI or no AI-generated content
        final_content = generate_fallback_content(normalized_data)
    
    # Step 8: Store validation record
    validation_record = AIValidationRecord(
        validation_id=uuid4(),
        session_id=session_id,
        openai_result=openai_result,
        grok_result=grok_result,
        consensus=consensus_result,
        content=final_content,
        total_cost=calculate_total_cost(openai_result, grok_result)
    )
    
    await save_validation_record(validation_record)
    
    return validation_record
```

---

## 2. AI Prompt Engineering

### 2.1 Data Validation Prompt

**Objective**: Have AI verify data consistency and identify the most accurate values.

```python
VALIDATION_SYSTEM_PROMPT = """You are an expert appliance parts analyst with deep knowledge of OEM and aftermarket parts across all major brands (GE, Whirlpool, Samsung, LG, Maytag, etc.). 

Your task is to analyze parts data from multiple supplier sources and:
1. Verify that all sources are referring to the SAME physical part
2. Identify the most accurate value for each data field
3. Detect conflicts and inconsistencies
4. Assign confidence scores (0-1) to your assessments
5. Provide clear reasoning for your decisions

You must return responses in valid JSON format only."""

def build_validation_prompt(part_number: str, source_data: Dict) -> str:
    """Build the validation prompt"""
    
    prompt = f"""# Part Validation Task

## Part Number: {part_number}

## Data from Multiple Sources:

### Source 1: Encompass
```json
{json.dumps(source_data.get("encompass", {}), indent=2)}
```

### Source 2: Marcone
```json
{json.dumps(source_data.get("marcone", {}), indent=2)}
```

### Source 3: Reliable Parts
```json
{json.dumps(source_data.get("reliable", {}), indent=2)}
```

### Source 4: Amazon
```json
{json.dumps(source_data.get("amazon", {}), indent=2)}
```

---

## Your Tasks:

### 1. Part Identity Verification
Analyze all sources and determine if they all refer to the SAME physical part.
Consider:
- Part number matches and variations
- Manufacturer consistency
- Physical specifications (dimensions, weight)
- Application/usage descriptions
- Images (if available)

### 2. Field-by-Field Validation
For each field below, identify the most accurate value and explain why:

**Fields to validate:**
- Manufacturer/Brand
- Part Type (OEM/Generic/Aftermarket)
- Primary Description
- Category/Department
- Pricing (MSRP, current price)
- Dimensions (product and box)
- Weight
- Voltage (if applicable)
- Compatible Models
- Cross-Reference Part Numbers
- UPC/GTIN
- Color
- Material
- Specifications

### 3. Conflict Detection
Identify any significant conflicts between sources.
- What data points disagree?
- Which source is likely most accurate for that field?
- What is your confidence level?

---

## Required JSON Response Format:

```json
{{
  "part_match_confidence": 0.95,
  "part_match_reasoning": "All sources consistently identify this as a GE defrost sensor...",
  "same_part": true,
  
  "validated_fields": {{
    "manufacturer": {{
      "value": "GE",
      "confidence": 0.98,
      "source": "encompass",
      "reasoning": "Encompass is the official OEM source and all others agree"
    }},
    "part_type": {{
      "value": "oem",
      "confidence": 0.95,
      "source": "encompass",
      "reasoning": "Listed on official OEM site and confirmed by part number format"
    }},
    "msrp": {{
      "value": 48.99,
      "confidence": 0.85,
      "source": "encompass",
      "reasoning": "Encompass lists official MSRP, Amazon shows retail markup"
    }},
    // ... continue for all fields
  }},
  
  "conflicts": [
    {{
      "field": "weight",
      "values": {{
        "encompass": 0.38,
        "marcone": 0.35,
        "reliable": 0.40,
        "amazon": 0.38
      }},
      "resolution": {{
        "chosen_value": 0.38,
        "reasoning": "Encompass and Amazon agree, values are within shipping weight variance",
        "confidence": 0.80
      }}
    }}
  ],
  
  "missing_data": [
    "voltage",
    "terminal_type",
    "installation_video"
  ],
  
  "suspicious_data": [
    {{
      "field": "compatible_models",
      "source": "amazon",
      "issue": "Lists 500+ models which seems inflated",
      "recommendation": "Use OEM source (Encompass) instead"
    }}
  ],
  
  "overall_data_quality": {{
    "encompass": 0.92,
    "marcone": 0.85,
    "reliable": 0.78,
    "amazon": 0.70
  }}
}}
```

Think step-by-step and be thorough in your analysis."""
    
    return prompt
```

### 2.2 Content Generation Prompt

**Objective**: Generate SEO-optimized, marketing-friendly content.

```python
CONTENT_GENERATION_SYSTEM_PROMPT = """You are an expert appliance parts copywriter and SEO specialist. 

Your goal is to create compelling, accurate, and SEO-optimized product content that:
- Ranks well in search engines
- Converts browsers into buyers
- Provides all necessary technical information
- Builds trust and credibility

You must write in clear, professional language while incorporating relevant keywords naturally."""

def build_content_prompt(validated_data: Dict) -> str:
    """Build content generation prompt"""
    
    prompt = f"""# Content Generation Task

## Validated Part Data:
```json
{json.dumps(validated_data, indent=2)}
```

---

## Task 1: Generate SEO-Optimized Product Title

Requirements:
- 50-100 characters
- Include: Manufacturer, Part Number, Part Type, Key Feature
- Natural language (not keyword stuffing)
- Compelling and descriptive
- Include the full part number

Example:
"GE WR55X10025 Refrigerator Defrost Sensor - OEM Replacement Part"

## Task 2: Generate Comprehensive Product Description

Requirements:
- 200-1000 words
- Structure:
  1. **Opening paragraph** (2-3 sentences)
     - What is this part?
     - What does it do?
     - Why might someone need it?
  
  2. **Key Features & Benefits** (bullet list)
     - OEM vs aftermarket (if OEM, emphasize quality)
     - What problems it solves
     - Quality/reliability points
     - Compatibility highlights
  
  3. **Technical Specifications** (paragraph form)
     - Physical dimensions
     - Electrical specs (if applicable)
     - Material/construction
     - Installation requirements
  
  4. **Compatibility Information**
     - Which appliance models/brands
     - How to verify compatibility
  
  5. **Common Issues & Symptoms** (if applicable)
     - What symptoms indicate this part is needed?
     - Common error codes (if applicable)
  
  6. **Installation Notes**
     - Difficulty level
     - Required tools
     - Safety warnings
     - Professional vs DIY
  
  7. **SEO Keywords** (naturally integrated)
     - Part number variations
     - Cross-reference numbers
     - Common search terms
     - Brand names

- Tone: Professional, helpful, trustworthy
- Avoid: Hype, unsupported claims, keyword stuffing
- Include: Accurate technical data, practical advice

---

## Required JSON Response Format:

```json
{{
  "title": "GE WR55X10025 Refrigerator Defrost Sensor - OEM Replacement Part",
  "title_character_count": 67,
  "title_seo_score": 0.95,
  
  "description": "The GE WR55X10025 is a genuine OEM refrigerator defrost sensor...",
  "description_word_count": 487,
  "description_seo_score": 0.88,
  
  "primary_keywords": [
    "GE WR55X10025",
    "defrost sensor",
    "refrigerator sensor",
    "OEM replacement part"
  ],
  
  "secondary_keywords": [
    "AP3185409",
    "914093",
    "defrost thermistor",
    "GE refrigerator parts"
  ],
  
  "meta_description": "Genuine GE WR55X10025 refrigerator defrost sensor. OEM quality replacement for 500+ models. Fast shipping. Fix frost buildup and cooling issues."
}}
```

Be thorough, accurate, and persuasive."""
    
    return prompt
```

---

## 3. Consensus Algorithm

### 3.1 Agreement Scoring

```python
def calculate_agreement_score(openai_result: Dict, grok_result: Dict) -> float:
    """
    Calculate how much OpenAI and Grok agree on the validation
    
    Returns: 0.0 to 1.0 (1.0 = perfect agreement)
    """
    
    if not openai_result or not grok_result:
        return 0.0
    
    openai_fields = openai_result.get("validated_fields", {})
    grok_fields = grok_result.get("validated_fields", {})
    
    total_fields = set(openai_fields.keys()) | set(grok_fields.keys())
    
    if not total_fields:
        return 0.0
    
    agreements = 0
    total_comparisons = 0
    
    for field in total_fields:
        if field not in openai_fields or field not in grok_fields:
            # One AI didn't validate this field
            continue
        
        openai_value = openai_fields[field].get("value")
        grok_value = grok_fields[field].get("value")
        
        if openai_value == grok_value:
            agreements += 1
        elif are_values_similar(openai_value, grok_value, field):
            # Close enough (for numbers, strings with minor differences)
            agreements += 0.8
        
        total_comparisons += 1
    
    if total_comparisons == 0:
        return 0.0
    
    return agreements / total_comparisons


def are_values_similar(value1: Any, value2: Any, field_name: str) -> bool:
    """Determine if two values are similar enough to count as agreement"""
    
    # Numbers: within 5% tolerance
    if isinstance(value1, (int, float)) and isinstance(value2, (int, float)):
        if value1 == 0 and value2 == 0:
            return True
        avg = (abs(value1) + abs(value2)) / 2
        if avg == 0:
            return value1 == value2
        difference_pct = abs(value1 - value2) / avg
        return difference_pct < 0.05  # 5% tolerance
    
    # Strings: case-insensitive, whitespace-normalized comparison
    if isinstance(value1, str) and isinstance(value2, str):
        norm1 = value1.lower().strip()
        norm2 = value2.lower().strip()
        
        if norm1 == norm2:
            return True
        
        # Check for substring match (80%+ overlap)
        longer = max(norm1, norm2, key=len)
        shorter = min(norm1, norm2, key=len)
        
        if len(shorter) == 0:
            return False
        
        # Simple substring check
        if shorter in longer:
            return len(shorter) / len(longer) >= 0.8
        
        return False
    
    # Lists: check for significant overlap
    if isinstance(value1, list) and isinstance(value2, list):
        set1 = set(value1)
        set2 = set(value2)
        
        if not set1 or not set2:
            return set1 == set2
        
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        
        overlap = intersection / union if union > 0 else 0
        return overlap >= 0.7  # 70% overlap
    
    # Default: exact match required
    return value1 == value2
```

### 3.2 Conflict Resolution

```python
class ConsensusEngine:
    """Resolves conflicts between AI validators and source data"""
    
    def __init__(self, source_priority: List[str] = None):
        self.source_priority = source_priority or [
            "encompass", "marcone", "reliable", "amazon"
        ]
    
    def resolve_field(
        self, 
        field_name: str,
        openai_result: Optional[Dict],
        grok_result: Optional[Dict],
        source_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Resolve a single field using consensus logic
        
        Returns:
            {
                "value": final_value,
                "confidence": 0.0-1.0,
                "source": "openai|grok|encompass|...",
                "reasoning": "explanation"
            }
        """
        
        # Extract values from each AI
        openai_field = openai_result.get("validated_fields", {}).get(field_name) if openai_result else None
        grok_field = grok_result.get("validated_fields", {}).get(field_name) if grok_result else None
        
        # Case 1: Both AIs agree
        if openai_field and grok_field:
            openai_value = openai_field.get("value")
            grok_value = grok_field.get("value")
            
            if openai_value == grok_value or are_values_similar(openai_value, grok_value, field_name):
                return {
                    "value": openai_value,
                    "confidence": min(
                        openai_field.get("confidence", 0.8),
                        grok_field.get("confidence", 0.8)
                    ),
                    "source": "ai_consensus",
                    "reasoning": "Both OpenAI and Grok agree on this value"
                }
        
        # Case 2: Both AIs present but disagree
        if openai_field and grok_field:
            openai_conf = openai_field.get("confidence", 0.5)
            grok_conf = grok_field.get("confidence", 0.5)
            
            # Use the AI with higher confidence (if significantly higher)
            if openai_conf - grok_conf > 0.15:
                return {
                    "value": openai_field.get("value"),
                    "confidence": openai_conf * 0.9,  # Reduced due to disagreement
                    "source": "openai",
                    "reasoning": f"OpenAI has higher confidence ({openai_conf:.2f} vs {grok_conf:.2f})"
                }
            elif grok_conf - openai_conf > 0.15:
                return {
                    "value": grok_field.get("value"),
                    "confidence": grok_conf * 0.9,
                    "source": "grok",
                    "reasoning": f"Grok has higher confidence ({grok_conf:.2f} vs {openai_conf:.2f})"
                }
            
            # Similar confidence - check source data
            return self._resolve_from_sources(
                field_name,
                openai_field.get("value"),
                grok_field.get("value"),
                source_data
            )
        
        # Case 3: Only one AI available
        if openai_field:
            return {
                "value": openai_field.get("value"),
                "confidence": openai_field.get("confidence", 0.7) * 0.85,  # Reduced, no cross-validation
                "source": "openai",
                "reasoning": "Only OpenAI validation available"
            }
        
        if grok_field:
            return {
                "value": grok_field.get("value"),
                "confidence": grok_field.get("confidence", 0.7) * 0.85,
                "source": "grok",
                "reasoning": "Only Grok validation available"
            }
        
        # Case 4: No AI validation - fall back to source priority
        return self._resolve_from_sources(field_name, None, None, source_data)
    
    def _resolve_from_sources(
        self,
        field_name: str,
        ai_value1: Any,
        ai_value2: Any,
        source_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Resolve field using source data priority
        """
        
        # Apply field-specific rules
        if field_name in ["primary_image_url", "gallery_images"]:
            # For images, prefer Amazon (usually highest quality)
            priority = ["amazon", "encompass", "reliable", "marcone"]
        elif field_name in ["msrp", "pricing"]:
            # For pricing, prefer official OEM sources
            priority = ["encompass", "marcone", "reliable", "amazon"]
        elif field_name in ["compatible_models", "cross_references"]:
            # For compatibility, prefer OEM sources
            priority = ["encompass", "marcone", "reliable", "amazon"]
        else:
            # Default priority
            priority = self.source_priority
        
        # Try each source in priority order
        for source in priority:
            source_value = self._extract_field_from_source(
                source_data.get(source, {}),
                field_name
            )
            
            if source_value is not None:
                return {
                    "value": source_value,
                    "confidence": self._get_source_confidence(source, field_name),
                    "source": source,
                    "reasoning": f"No AI consensus; using {source} (highest priority source with data)"
                }
        
        # No data found anywhere
        return {
            "value": None,
            "confidence": 0.0,
            "source": "none",
            "reasoning": "No data available from any source"
        }
    
    def _extract_field_from_source(self, source_data: Dict, field_name: str) -> Any:
        """Extract a field value from normalized source data"""
        # This would map field names to source-specific field names
        # Implementation depends on your data structure
        return source_data.get(field_name)
    
    def _get_source_confidence(self, source: str, field_name: str) -> float:
        """Get confidence score for a source/field combination"""
        
        base_confidence = {
            "encompass": 0.90,
            "marcone": 0.85,
            "reliable": 0.80,
            "amazon": 0.75
        }
        
        # Adjust for specific fields
        if source == "amazon" and field_name in ["primary_image_url", "gallery_images"]:
            return 0.90  # Amazon has great images
        
        if source == "encompass" and field_name in ["compatible_models", "specifications"]:
            return 0.95  # Encompass is authoritative for OEM data
        
        return base_confidence.get(source, 0.70)
```

---

## 4. Confidence Scoring

### 4.1 Field-Level Confidence

```python
def calculate_field_confidence(
    field_name: str,
    consensus_result: Dict,
    ai_agreement: float,
    source_count: int
) -> float:
    """
    Calculate confidence score for a single field
    
    Factors:
    - AI agreement (0-1)
    - Number of sources with data (0-4)
    - Source quality
    - Field complexity
    """
    
    base_confidence = consensus_result.get("confidence", 0.5)
    
    # Boost for AI agreement
    ai_boost = ai_agreement * 0.2  # Up to +0.2
    
    # Boost for multiple sources
    source_boost = (source_count / 4) * 0.15  # Up to +0.15
    
    # Field-specific adjustments
    field_adjustment = get_field_difficulty_adjustment(field_name)
    
    final_confidence = min(1.0, base_confidence + ai_boost + source_boost + field_adjustment)
    
    return round(final_confidence, 3)


def get_field_difficulty_adjustment(field_name: str) -> float:
    """
    Adjust confidence based on field complexity
    
    Simple fields (part number, manufacturer) = +0.05
    Medium fields (price, dimensions) = 0.0
    Complex fields (compatible models, symptoms) = -0.05
    """
    
    simple_fields = [
        "manufacturer", "part_number", "upc", "color", "material"
    ]
    
    complex_fields = [
        "compatible_models", "cross_references", "related_symptoms",
        "installation_suggestions", "common_error_codes"
    ]
    
    if field_name in simple_fields:
        return 0.05
    elif field_name in complex_fields:
        return -0.05
    
    return 0.0
```

### 4.2 Overall Catalog Confidence

```python
def calculate_catalog_confidence(catalog_record: MasterCatalogRecord) -> float:
    """
    Calculate overall confidence for the entire catalog record
    
    Weighted average based on field importance
    """
    
    # Field weights (total = 1.0)
    field_weights = {
        # Critical fields (50%)
        "mpn": 0.10,
        "manufacturer": 0.10,
        "part_type": 0.08,
        "part_title": 0.08,
        "primary_category": 0.07,
        "primary_department": 0.07,
        
        # Important fields (30%)
        "long_description": 0.05,
        "primary_image_url": 0.05,
        "current_selling_price": 0.05,
        "compatible_models": 0.05,
        "weight_lbs": 0.03,
        "dimensions": 0.04,
        "upc": 0.03,
        
        # Nice-to-have fields (20%)
        "cross_references": 0.04,
        "related_symptoms": 0.04,
        "installation_suggestions": 0.03,
        "gallery_images": 0.03,
        "specifications": 0.06
    }
    
    total_weight = 0.0
    weighted_confidence = 0.0
    
    for field, weight in field_weights.items():
        field_confidence = get_field_confidence(catalog_record, field)
        
        if field_confidence > 0:
            weighted_confidence += field_confidence * weight
            total_weight += weight
    
    if total_weight == 0:
        return 0.0
    
    return round(weighted_confidence / total_weight, 3)
```

---

## 5. Conflict Resolution

### 5.1 Conflict Types

```python
class ConflictType(Enum):
    MINOR = "minor"          # < 10% difference, probably variance
    MODERATE = "moderate"    # 10-30% difference, needs review
    MAJOR = "major"          # > 30% difference, significant conflict
    INCOMPATIBLE = "incompatible"  # Completely different values

class Conflict:
    field: str
    values: Dict[str, Any]  # {source: value}
    conflict_type: ConflictType
    resolution: Dict[str, Any]
    confidence: float
```

### 5.2 Conflict Detection

```python
def detect_conflicts(normalized_data: Dict[str, Dict]) -> List[Conflict]:
    """
    Detect conflicts across all sources
    """
    
    conflicts = []
    
    # Get all fields across all sources
    all_fields = set()
    for source_data in normalized_data.values():
        all_fields.update(source_data.keys())
    
    for field in all_fields:
        # Collect values from all sources
        values = {}
        for source, data in normalized_data.items():
            if field in data and data[field] is not None:
                values[source] = data[field]
        
        if len(values) < 2:
            continue  # No conflict possible
        
        # Check for conflicts
        if has_conflict(values, field):
            conflict = analyze_conflict(field, values)
            conflicts.append(conflict)
    
    return conflicts


def has_conflict(values: Dict[str, Any], field: str) -> bool:
    """Determine if values represent a conflict"""
    
    unique_values = set()
    
    for value in values.values():
        # Normalize for comparison
        if isinstance(value, str):
            unique_values.add(value.lower().strip())
        elif isinstance(value, (int, float)):
            # Round to 2 decimal places for comparison
            unique_values.add(round(value, 2))
        elif isinstance(value, list):
            unique_values.add(tuple(sorted(value)))
        else:
            unique_values.add(value)
    
    return len(unique_values) > 1


def analyze_conflict(field: str, values: Dict[str, Any]) -> Conflict:
    """Analyze conflict severity and suggest resolution"""
    
    # Determine conflict type
    conflict_type = determine_conflict_type(field, values)
    
    # Propose resolution
    resolution = resolve_conflict_value(field, values, conflict_type)
    
    return Conflict(
        field=field,
        values=values,
        conflict_type=conflict_type,
        resolution=resolution,
        confidence=resolution["confidence"]
    )


def determine_conflict_type(field: str, values: Dict[str, Any]) -> ConflictType:
    """Determine severity of conflict"""
    
    # For numeric fields, calculate variance
    if all(isinstance(v, (int, float)) for v in values.values()):
        vals = list(values.values())
        avg = sum(vals) / len(vals)
        max_diff = max(abs(v - avg) for v in vals)
        
        if avg == 0:
            variance_pct = 0 if max_diff == 0 else 100
        else:
            variance_pct = (max_diff / avg) * 100
        
        if variance_pct < 10:
            return ConflictType.MINOR
        elif variance_pct < 30:
            return ConflictType.MODERATE
        else:
            return ConflictType.MAJOR
    
    # For text fields, check similarity
    if all(isinstance(v, str) for v in values.values()):
        # If any pair is very different, it's a major conflict
        vals = list(values.values())
        for i in range(len(vals)):
            for j in range(i + 1, len(vals)):
                similarity = calculate_string_similarity(vals[i], vals[j])
                if similarity < 0.5:
                    return ConflictType.MAJOR
                elif similarity < 0.8:
                    return ConflictType.MODERATE
        
        return ConflictType.MINOR
    
    # For lists, check overlap
    if all(isinstance(v, list) for v in values.values()):
        sets = [set(v) for v in values.values()]
        intersection = sets[0].intersection(*sets[1:])
        union = sets[0].union(*sets[1:])
        
        if len(union) == 0:
            return ConflictType.MINOR
        
        overlap = len(intersection) / len(union)
        
        if overlap > 0.7:
            return ConflictType.MINOR
        elif overlap > 0.4:
            return ConflictType.MODERATE
        else:
            return ConflictType.MAJOR
    
    # Different types = incompatible
    return ConflictType.INCOMPATIBLE


def calculate_string_similarity(s1: str, s2: str) -> float:
    """Calculate similarity between two strings (0-1)"""
    from difflib import SequenceMatcher
    return SequenceMatcher(None, s1.lower(), s2.lower()).ratio()
```

---

## 6. Content Generation

### 6.1 Title Selection

```python
def select_best_title(openai_title: str, grok_title: str, criteria: Dict) -> Dict:
    """
    Select the better title based on multiple criteria
    """
    
    openai_score = score_title(openai_title, criteria)
    grok_score = score_title(grok_title, criteria)
    
    if openai_score > grok_score:
        return {
            "title": openai_title,
            "source": "openai",
            "score": openai_score,
            "reasoning": f"OpenAI title scored {openai_score:.2f} vs Grok's {grok_score:.2f}"
        }
    else:
        return {
            "title": grok_title,
            "source": "grok",
            "score": grok_score,
            "reasoning": f"Grok title scored {grok_score:.2f} vs OpenAI's {openai_score:.2f}"
        }


def score_title(title: str, criteria: Dict) -> float:
    """
    Score a title based on SEO and marketing criteria
    
    Criteria:
    - Length (50-100 chars ideal)
    - Contains part number
    - Contains manufacturer
    - Contains part type
    - Natural language (not keyword stuffing)
    - Keyword placement
    """
    
    score = 0.0
    
    # Length score (0-0.20)
    length = len(title)
    if 50 <= length <= 100:
        score += 0.20
    elif 40 <= length < 50 or 100 < length <= 120:
        score += 0.15
    else:
        score += 0.10
    
    # Part number present (0-0.20)
    part_number = criteria.get("part_number", "")
    if part_number and part_number in title:
        score += 0.20
    
    # Manufacturer present (0-0.20)
    manufacturer = criteria.get("manufacturer", "")
    if manufacturer and manufacturer.lower() in title.lower():
        score += 0.20
    
    # Part type present (0-0.15)
    part_type = criteria.get("part_type", "")
    if part_type and part_type.lower() in title.lower():
        score += 0.15
    
    # Readability score (0-0.15)
    # Count words, check for natural language
    words = title.split()
    if 6 <= len(words) <= 15:
        score += 0.10
    
    # Not too many uppercase words (avoid keyword stuffing)
    uppercase_count = sum(1 for word in words if word.isupper())
    if uppercase_count <= 2:
        score += 0.05
    
    # Key term early (0-0.10)
    if part_number and title.lower().startswith(manufacturer.lower()):
        score += 0.10
    
    return min(1.0, score)
```

### 6.2 Description Selection

```python
def select_best_description(
    openai_desc: str,
    grok_desc: str,
    criteria: Dict
) -> Dict:
    """
    Select the better description based on completeness and quality
    """
    
    openai_score = score_description(openai_desc, criteria)
    grok_score = score_description(grok_desc, criteria)
    
    if openai_score > grok_score:
        return {
            "description": openai_desc,
            "source": "openai",
            "score": openai_score,
            "reasoning": f"OpenAI description scored {openai_score:.2f} vs Grok's {grok_score:.2f}"
        }
    else:
        return {
            "description": grok_desc,
            "source": "grok",
            "score": grok_score,
            "reasoning": f"Grok description scored {grok_score:.2f} vs OpenAI's {openai_score:.2f}"
        }


def score_description(description: str, criteria: Dict) -> float:
    """
    Score a description based on quality criteria
    """
    
    score = 0.0
    words = description.split()
    word_count = len(words)
    
    # Length score (0-0.20)
    if 200 <= word_count <= 1000:
        score += 0.20
    elif 150 <= word_count < 200 or 1000 < word_count <= 1200:
        score += 0.15
    else:
        score += 0.10
    
    # Structure score (0-0.20)
    # Check for sections: intro, features, specs, compatibility, etc.
    has_intro = True  # First paragraph
    has_features = "features" in description.lower() or "benefits" in description.lower()
    has_specs = "specifications" in description.lower() or "technical" in description.lower()
    has_compatibility = "compatible" in description.lower() or "models" in description.lower()
    has_installation = "installation" in description.lower() or "install" in description.lower()
    
    structure_score = sum([has_intro, has_features, has_specs, has_compatibility, has_installation]) / 5
    score += structure_score * 0.20
    
    # Technical accuracy (0-0.20)
    # Contains key technical terms from validated data
    tech_terms_present = 0
    tech_terms_expected = [
        criteria.get("part_number"),
        criteria.get("manufacturer"),
        criteria.get("part_type"),
        criteria.get("voltage"),
        criteria.get("category")
    ]
    
    for term in tech_terms_expected:
        if term and str(term).lower() in description.lower():
            tech_terms_present += 1
    
    score += (tech_terms_present / len([t for t in tech_terms_expected if t])) * 0.20
    
    # Readability (0-0.15)
    avg_sentence_length = word_count / description.count('.') if '.' in description else word_count
    if 15 <= avg_sentence_length <= 25:
        score += 0.15
    elif 10 <= avg_sentence_length < 15 or 25 < avg_sentence_length <= 30:
        score += 0.10
    
    # Keyword integration (0-0.15)
    # Check for natural keyword usage (not stuffing)
    part_number = criteria.get("part_number", "")
    part_number_count = description.count(part_number) if part_number else 0
    
    if 2 <= part_number_count <= 5:
        score += 0.10
    elif part_number_count == 1:
        score += 0.05
    
    # Check for varied vocabulary (not repetitive)
    unique_words = len(set(word.lower() for word in words))
    vocabulary_ratio = unique_words / word_count if word_count > 0 else 0
    
    if vocabulary_ratio > 0.5:
        score += 0.05
    
    # SEO elements (0-0.10)
    # Includes common search terms, questions, etc.
    seo_elements = [
        "how to", "what is", "why", "replacement", "fix", "repair",
        "compatible", "OEM", "genuine", "quality"
    ]
    
    seo_present = sum(1 for elem in seo_elements if elem.lower() in description.lower())
    score += min(0.10, seo_present * 0.02)
    
    return min(1.0, score)
```

---

## 7. Cost Optimization

### 7.1 Token Usage Tracking

```python
class AIUsageTracker:
    """Track AI usage and costs"""
    
    # Pricing (as of Dec 2025, adjust as needed)
    OPENAI_PRICING = {
        "gpt-4-turbo": {
            "input": 0.01 / 1000,   # $0.01 per 1K input tokens
            "output": 0.03 / 1000    # $0.03 per 1K output tokens
        }
    }
    
    GROK_PRICING = {
        "grok-1": {
            "input": 0.008 / 1000,
            "output": 0.024 / 1000
        }
    }
    
    def calculate_cost(self, provider: str, model: str, usage: Dict) -> float:
        """Calculate cost for an AI API call"""
        
        pricing = (
            self.OPENAI_PRICING if provider == "openai" else self.GROK_PRICING
        ).get(model, {"input": 0, "output": 0})
        
        input_cost = usage.get("prompt_tokens", 0) * pricing["input"]
        output_cost = usage.get("completion_tokens", 0) * pricing["output"]
        
        return round(input_cost + output_cost, 4)
    
    async def log_usage(
        self,
        session_id: UUID,
        provider: str,
        model: str,
        usage: Dict,
        cost: float
    ):
        """Log AI usage to database"""
        
        await db.ai_usage.insert_one({
            "session_id": session_id,
            "provider": provider,
            "model": model,
            "prompt_tokens": usage.get("prompt_tokens", 0),
            "completion_tokens": usage.get("completion_tokens", 0),
            "total_tokens": usage.get("total_tokens", 0),
            "cost": cost,
            "timestamp": datetime.now()
        })
```

### 7.2 Optimization Strategies

```python
class AIOptimizer:
    """Strategies to reduce AI costs"""
    
    def __init__(self):
        self.cache = {}  # Simple in-memory cache, use Redis in production
    
    async def validate_with_caching(
        self,
        part_number: str,
        source_data: Dict
    ) -> Dict:
        """
        Use caching to avoid redundant AI calls
        """
        
        # Create cache key from part data signature
        cache_key = self._generate_cache_key(part_number, source_data)
        
        # Check cache
        if cache_key in self.cache:
            logger.info(f"AI validation cache hit for {part_number}")
            return self.cache[cache_key]
        
        # No cache hit - call AI
        result = await self._call_ai_validation(part_number, source_data)
        
        # Store in cache (1 hour TTL)
        self.cache[cache_key] = result
        
        return result
    
    def _generate_cache_key(self, part_number: str, source_data: Dict) -> str:
        """Generate cache key from data signature"""
        import hashlib
        import json
        
        # Create deterministic string from data
        data_str = json.dumps(source_data, sort_keys=True)
        data_hash = hashlib.md5(data_str.encode()).hexdigest()
        
        return f"ai_validation:{part_number}:{data_hash}"
    
    def optimize_prompt(self, prompt: str) -> str:
        """
        Optimize prompt to reduce token usage
        
        Strategies:
        - Remove unnecessary whitespace
        - Abbreviate field names in examples
        - Use shorthand where possible
        """
        
        # Remove excessive whitespace
        optimized = " ".join(prompt.split())
        
        # Replace verbose phrases
        replacements = {
            "Please analyze the following": "Analyze:",
            "Based on the information provided": "Given:",
            "Return your response in the following format": "Format:",
        }
        
        for verbose, concise in replacements.items():
            optimized = optimized.replace(verbose, concise)
        
        return optimized
    
    async def should_use_dual_validation(
        self,
        data_quality: float,
        field_count: int
    ) -> bool:
        """
        Decide if we need both OpenAI and Grok, or just one
        
        Use both AIs when:
        - Data quality is low (< 0.7)
        - High-value parts
        - Many conflicts detected
        
        Use single AI when:
        - Data quality is high (> 0.9)
        - Simple parts with consistent data
        """
        
        # High quality data - use single AI
        if data_quality > 0.9:
            return False
        
        # Low quality or complex - use both
        if data_quality < 0.7 or field_count > 20:
            return True
        
        # Medium quality - default to single AI for cost savings
        return False
```

---

## 8. Error Handling & Fallbacks

```python
class AIValidationPipeline:
    """Robust AI validation with error handling"""
    
    async def validate_with_fallbacks(
        self,
        session_id: UUID,
        part_number: str,
        source_data: Dict
    ) -> AIValidationRecord:
        """
        Validate with comprehensive error handling
        """
        
        try:
            # Try primary validation (both AIs)
            return await self.dual_ai_validation(session_id, part_number, source_data)
        
        except OpenAIError as e:
            logger.error(f"OpenAI failed: {e}")
            
            try:
                # Fallback to Grok only
                return await self.grok_only_validation(session_id, part_number, source_data)
            
            except GrokError as e2:
                logger.error(f"Grok also failed: {e2}")
                
                # Fallback to rule-based validation (no AI)
                return await self.rule_based_validation(session_id, part_number, source_data)
        
        except GrokError as e:
            logger.error(f"Grok failed: {e}")
            
            try:
                # Fallback to OpenAI only
                return await self.openai_only_validation(session_id, part_number, source_data)
            
            except OpenAIError:
                # Fallback to rule-based
                return await self.rule_based_validation(session_id, part_number, source_data)
        
        except Exception as e:
            logger.error(f"Unexpected error in AI validation: {e}")
            
            # Last resort - rule-based
            return await self.rule_based_validation(session_id, part_number, source_data)
    
    async def rule_based_validation(
        self,
        session_id: UUID,
        part_number: str,
        source_data: Dict
    ) -> AIValidationRecord:
        """
        Validation without AI - use source priority rules only
        """
        
        logger.warning(f"Using rule-based validation (no AI) for {part_number}")
        
        consensus_engine = ConsensusEngine()
        
        # Resolve all fields using source priority only
        validated_fields = {}
        
        for field in get_all_catalog_fields():
            result = consensus_engine._resolve_from_sources(
                field_name=field,
                ai_value1=None,
                ai_value2=None,
                source_data=source_data
            )
            
            if result["value"] is not None:
                validated_fields[field] = result
        
        return AIValidationRecord(
            validation_id=uuid4(),
            session_id=session_id,
            ai_validation_status=AIValidationStatus.UNVALIDATED,
            openai_result=None,
            grok_result=None,
            consensus={"validated_fields": validated_fields},
            total_cost=0.0,
            processing_time_seconds=0.0
        )
```

---

## 9. Testing & Validation

### 9.1 AI Response Validation

```python
def validate_ai_response(response: Dict, expected_schema: Dict) -> bool:
    """
    Validate that AI response matches expected JSON schema
    """
    
    required_fields = [
        "part_match_confidence",
        "same_part",
        "validated_fields",
        "conflicts",
        "overall_data_quality"
    ]
    
    # Check all required fields present
    for field in required_fields:
        if field not in response:
            logger.error(f"AI response missing required field: {field}")
            return False
    
    # Validate confidence scores are 0-1
    if not (0 <= response["part_match_confidence"] <= 1):
        logger.error("Invalid part_match_confidence value")
        return False
    
    # Validate validated_fields structure
    for field_name, field_data in response.get("validated_fields", {}).items():
        if "value" not in field_data or "confidence" not in field_data:
            logger.error(f"Invalid structure for field {field_name}")
            return False
        
        if not (0 <= field_data["confidence"] <= 1):
            logger.error(f"Invalid confidence for field {field_name}")
            return False
    
    return True
```

---

**Document Version**: 1.0  
**Last Updated**: December 12, 2025  
**Status**: Ready for Implementation
