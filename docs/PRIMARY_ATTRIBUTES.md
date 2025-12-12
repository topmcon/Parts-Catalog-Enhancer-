# Primary Attributes - Universal Catalog Fields

## Overview

The Parts Catalog Enhancement System uses a **two-tier attribute structure**:

1. **PRIMARY ATTRIBUTES (34 fields)**: Universal fields required for ALL parts catalogs, populated first with highest priority
2. **ADDITIONAL ATTRIBUTES (50+ fields)**: Part-specific or extended fields populated based on availability

This document details the **34 PRIMARY attributes** that are considered standard across all catalog systems.

---

## Why PRIMARY Attributes?

**PRIMARY attributes are:**
- ✅ **Universal** - Apply to virtually all appliance parts
- ✅ **Essential** - Required for basic catalog functionality  
- ✅ **Salesforce-compatible** - Map directly to Salesforce catalog fields
- ✅ **SEO-critical** - Necessary for search visibility
- ✅ **Customer-facing** - Directly visible in product listings

**Processing Priority:**
1. AI validation focuses on PRIMARY attributes first
2. Confidence scoring weights PRIMARY attributes higher
3. Source selection prioritizes PRIMARY attribute accuracy
4. Cache keys based on PRIMARY attribute completeness

---

## The 34 PRIMARY Attributes

### 1. Primary Part Number (MPN)
**Field**: `mpn`  
**Type**: `string` (required)  
**Status Field**: `mpn_status`  
**Description**: Main manufacturer part number - the unique identifier  
**Example**: `"WR55X10025"`  
**Sources**: All 4 APIs (Encompass preferred for accuracy)

---

### 2. Alternative Model Number
**Field**: `alternative_model_numbers`  
**Type**: `List[string]`  
**Status Field**: `alternative_model_numbers_status`  
**Description**: Alternate part numbers or model variations  
**Example**: `["WR55X10025A", "WR55X10025B"]`  
**Sources**: Encompass, Marcone (common for OEM variations)

---

### 3. Manufacturer / Brand
**Field**: `manufacturer`  
**Type**: `string` (required)  
**Status Field**: `manufacturer_status`  
**Description**: Brand or manufacturer name  
**Example**: `"GE"`, `"Whirlpool"`, `"Samsung"`  
**Sources**: All 4 APIs

---

### 4. Part Type
**Field**: `part_type`  
**Type**: `PartType enum` (required)  
**Values**: `oem`, `generic`, `aftermarket`, `refurbished`, `universal`  
**Status Field**: `part_type_status`  
**Description**: Classification of part origin/quality  
**Example**: `"oem"`  
**Sources**: AI inference + Encompass data

---

### 5. Part Title
**Field**: `part_title`  
**Type**: `string` (required)  
**Status Field**: `part_title_status`  
**Description**: 1-3 sentence product title, AI-enhanced if inadequate  
**Example**: `"GE WR55X10025 Refrigerator Defrost Sensor - Genuine OEM Part"`  
**Sources**: All 4 APIs, AI-enhanced for SEO

---

### 6. Long Description
**Field**: `long_description`  
**Type**: `string` (required)  
**Status Field**: `long_description_status`  
**Description**: 200-1000 word detailed product description, AI-generated if missing  
**Example**: `"The GE WR55X10025 Defrost Sensor is a genuine OEM replacement part designed for..."`  
**Sources**: Encompass, AI-generated content

---

### 7. Primary Department
**Field**: `primary_department`  
**Type**: `string` (required)  
**Status Field**: `primary_department_status`  
**Description**: Main appliance department category  
**Example**: `"Refrigeration"`, `"Laundry"`, `"HVAC"`, `"Cooking"`  
**Sources**: Encompass categorization, AI classification

---

### 8. Primary Category
**Field**: `primary_category`  
**Type**: `string` (required)  
**Status Field**: `primary_category_status`  
**Description**: Specific functional category within department  
**Example**: `"Defrost System"`, `"Motor Assembly"`, `"Door Parts"`  
**Sources**: Encompass, Marcone taxonomies

---

### 9. All Sub-Categories / Tags
**Field**: `sub_categories`  
**Type**: `List[string]`  
**Status Field**: `sub_categories_status`  
**Description**: All applicable subcategories and searchable tags  
**Example**: `["Temperature Control", "Refrigerator Parts", "Defrost Components"]`  
**Sources**: All APIs + AI-generated tags

---

### 10. Primary Image URL
**Field**: `primary_image_url`  
**Type**: `string | null`  
**Status Field**: `primary_image_status`  
**Additional**: `primary_image_source` (which API provided it)  
**Description**: Main product image URL (may be S3 or external)  
**Example**: `"https://s3.amazonaws.com/parts-catalog/WR55X10025-main.jpg"`  
**Sources**: Encompass (best quality), Amazon (fallback)

---

### 11. Gallery Image URLs (array)
**Field**: `gallery_images`  
**Type**: `List[string]`  
**Status Field**: `gallery_images_status`  
**Description**: Additional product images for gallery view  
**Example**: `["url1.jpg", "url2.jpg", "url3.jpg"]`  
**Sources**: Encompass, Amazon

---

### 12. MSRP / Compare-at Price
**Field**: `msrp`  
**Type**: `float | null`  
**Status Field**: `msrp_status`  
**Description**: Manufacturer Suggested Retail Price  
**Example**: `49.99`  
**Sources**: Encompass (most reliable), Marcone

---

### 13. High Average Sale Price
**Field**: `high_avg_price`  
**Type**: `float | null`  
**Status Field**: `high_avg_price_status`  
**Description**: Highest typical selling price across retailers  
**Example**: `52.99`  
**Sources**: Amazon, AI aggregation

---

### 14. Low Average Sale Price
**Field**: `low_avg_price`  
**Type**: `float | null`  
**Status Field**: `low_avg_price_status`  
**Description**: Lowest typical selling price across retailers  
**Example**: `39.99`  
**Sources**: Reliable Parts, Amazon

---

### 15. Current Selling Price
**Field**: `current_selling_price`  
**Type**: `float | null`  
**Status Field**: `current_selling_price_status`  
**Description**: Current market/suggested selling price  
**Example**: `45.50`  
**Sources**: Marcone (wholesale), AI median calculation

---

### 16. Weight (shipping)
**Field**: `weight_lbs`  
**Type**: `float | null`  
**Status Field**: `weight_lbs_status`  
**Description**: Shipping weight in pounds  
**Example**: `0.5`  
**Sources**: All APIs (AI validates for consistency)

---

### 17. Product Manufacture Box Length (L×W×H)
**Field**: `box_length_in`  
**Type**: `float | null`  
**Status Field**: `box_length_in_status`  
**Description**: Manufacturer box length in inches  
**Example**: `6.0`  
**Sources**: Encompass, Amazon

---

### 18. Product Manufacture Box Width (L×W×H)
**Field**: `box_width_in`  
**Type**: `float | null`  
**Status Field**: `box_width_in_status`  
**Description**: Manufacturer box width in inches  
**Example**: `4.0`  
**Sources**: Encompass, Amazon

---

### 19. Product Manufacture Box Height (L×W×H)
**Field**: `box_height_in`  
**Type**: `float | null`  
**Status Field**: `box_height_in_status`  
**Description**: Manufacturer box height in inches  
**Example**: `2.0`  
**Sources**: Encompass, Amazon

---

### 20. Product Manufacture Length (Not In Box / Not Box)
**Field**: `product_length_in`  
**Type**: `float | null`  
**Status Field**: `product_length_in_status`  
**Description**: Actual product length unboxed in inches  
**Example**: `5.5`  
**Sources**: Encompass specifications

---

### 21. Product Manufacture Width (Not In Box / Not Box)
**Field**: `product_width_in`  
**Type**: `float | null`  
**Status Field**: `product_width_in_status`  
**Description**: Actual product width unboxed in inches  
**Example**: `3.0`  
**Sources**: Encompass specifications

---

### 22. Product Manufacture Height (Not In Box / Not Box)
**Field**: `product_height_in`  
**Type**: `float | null`  
**Status Field**: `product_height_in_status`  
**Description**: Actual product height unboxed in inches  
**Example**: `1.5`  
**Sources**: Encompass specifications

---

### 23. UPC / EAN / GTIN
**Field**: `upc_ean_gtin`  
**Type**: `string | null`  
**Status Field**: `upc_ean_gtin_status`  
**Description**: Universal Product Code / Global Trade Item Number  
**Example**: `"012345678905"`  
**Sources**: Amazon (most reliable), Encompass

---

### 24. Voltage
**Field**: `voltage`  
**Type**: `string | null`  
**Status Field**: `voltage_status` (often `NOT_APPLICABLE`)  
**Description**: Operating voltage (for electrical parts)  
**Example**: `"120V"`, `"240V"`, `"N/A"`  
**Sources**: Encompass, Marcone

---

### 25. Terminal Type
**Field**: `terminal_type`  
**Type**: `string | null`  
**Status Field**: `terminal_type_status` (often `NOT_APPLICABLE`)  
**Description**: Electrical connection type  
**Example**: `"Quick-connect"`, `"Screw terminal"`, `"Blade"`, `"N/A"`  
**Sources**: Encompass specifications

---

### 26. Top 10 Compatible Models (list)
**Field**: `compatible_models`  
**Type**: `List[string]`  
**Status Field**: `compatible_models_status`  
**Description**: Top 10 appliance models this part fits  
**Example**: `["GFE28GMKES", "PFE28KSKSS", "GNE27JSMSS", ...]`  
**Sources**: Encompass (authoritative), AI expansion

---

### 27. Cross-Reference Part Numbers
**Field**: `cross_reference_parts`  
**Type**: `List[string]`  
**Status Field**: `cross_reference_parts_status`  
**Description**: Interchangeable/equivalent part numbers  
**Example**: `["AP5806172", "PS9494422", "EAP9494422"]`  
**Sources**: Encompass, Marcone

---

### 28. Color
**Field**: `color`  
**Type**: `string | null`  
**Status Field**: `color_status` (may be `NOT_APPLICABLE`)  
**Description**: Product color/finish  
**Example**: `"White"`, `"Black"`, `"Stainless Steel"`, `"Clear"`  
**Sources**: Encompass, Amazon, AI image analysis

---

### 29. Material
**Field**: `material`  
**Type**: `string | null`  
**Status Field**: `material_status` (may be `NOT_APPLICABLE`)  
**Description**: Primary construction material  
**Example**: `"Plastic"`, `"Stainless Steel"`, `"Rubber"`, `"Aluminum"`  
**Sources**: Encompass specifications

---

### 30. Finish
**Field**: `finish`  
**Type**: `string | null`  
**Status Field**: `finish_status` (may be `NOT_APPLICABLE`)  
**Description**: Surface finish type  
**Example**: `"Brushed"`, `"Polished"`, `"Matte"`, `"Textured"`  
**Sources**: Encompass, Amazon

---

### 31. Related Symptoms
**Field**: `related_symptoms`  
**Type**: `List[string]`  
**Status Field**: `related_symptoms_status`  
**Description**: Common appliance symptoms this part fixes  
**Example**: `["Refrigerator not cooling", "Frost buildup", "Freezer too cold"]`  
**Sources**: Encompass repair guides, AI inference

---

### 32. Installation Suggestions
**Field**: `installation_suggestions`  
**Type**: `string | null`  
**Status Field**: `installation_suggestions_status`  
**Description**: Installation tips and guidance  
**Example**: `"Disconnect power before installation. Remove rear access panel..."`  
**Sources**: Encompass manuals, AI generation

---

### 33. Specification Table
**Field**: `specification_table`  
**Type**: `dict` (key-value pairs)  
**Status Field**: `specification_table_status`  
**Description**: Additional specifications as structured data  
**Example**: 
```json
{
  "Operating Temperature Range": "-20°F to 50°F",
  "Resistance": "10K ohms at 25°C",
  "Wire Length": "6 inches"
}
```
**Sources**: Encompass detailed specs

---

### 34. Manufacturer Product Page URL
**Field**: `manufacturer_url`  
**Type**: `string | null`  
**Status Field**: `manufacturer_url_status`  
**Description**: Official manufacturer product page  
**Example**: `"https://www.geapplianceparts.com/store/parts/spec/WR55X10025"`  
**Sources**: Encompass, direct lookup

---

## Field Status Values

Each PRIMARY attribute has an associated `_status` field with one of three values:

| Status | Meaning | Example Usage |
|--------|---------|---------------|
| **FOUND** | Data was located in at least one source and validated | `mpn_status = "FOUND"` |
| **NOT_APPLICABLE** | Field doesn't apply to this part type | `voltage_status = "NOT_APPLICABLE"` (for non-electrical parts) |
| **NOT_FOUND** | Field is applicable but no data available from any source | `warranty_period_status = "NOT_FOUND"` |

**Why This Matters:**
- Distinguishes "we don't have this data" from "this data doesn't apply"
- Enables accurate completeness scoring
- Helps identify data gaps for manual research
- Improves catalog quality metrics

---

## Confidence Scoring for PRIMARY Attributes

PRIMARY attributes receive **higher importance weights** in the overall confidence calculation:

```python
# Example importance weights
FIELD_IMPORTANCE = {
    "mpn": 1.0,  # Critical
    "manufacturer": 1.0,  # Critical
    "part_title": 0.9,  # Very important
    "long_description": 0.9,  # Very important
    "msrp": 0.8,  # Important
    "primary_image_url": 0.8,  # Important
    "compatible_models": 0.7,  # Important
    "weight_lbs": 0.6,  # Moderate
    "color": 0.4,  # Nice to have
    # ... etc
}

catalog_confidence = sum(field_confidence × importance) / sum(importance)
```

**Target Thresholds:**
- **HIGH confidence (0.9-1.0)**: All critical PRIMARY fields validated by both AIs
- **MEDIUM confidence (0.7-0.89)**: Most PRIMARY fields populated with single AI validation
- **LOW confidence (<0.7)**: Multiple PRIMARY fields missing or conflicting

---

## API Source Priority for PRIMARY Attributes

**Source Reliability by Field Type:**

| Field Category | Priority 1 | Priority 2 | Priority 3 | Priority 4 |
|----------------|-----------|-----------|-----------|-----------|
| **Part Numbers & IDs** | Encompass | Marcone | Reliable | Amazon |
| **Descriptions** | AI-Enhanced | Encompass | Marcone | Amazon |
| **Pricing** | Encompass | Marcone | Reliable | Amazon |
| **Images** | Encompass | Amazon | Marcone | - |
| **Dimensions/Weight** | Encompass | Amazon | Marcone | Reliable |
| **Compatibility** | Encompass | AI-Expanded | Marcone | - |
| **UPC Codes** | Amazon | Encompass | - | - |

---

## Salesforce Integration Mapping

PRIMARY attributes map directly to Salesforce Product2 and PricebookEntry objects:

| PRIMARY Attribute | Salesforce Field | Object |
|-------------------|------------------|---------|
| `mpn` | `ProductCode` | Product2 |
| `manufacturer` | `Family` | Product2 |
| `part_title` | `Name` | Product2 |
| `long_description` | `Description` | Product2 |
| `primary_image_url` | `DisplayUrl` | Product2 |
| `current_selling_price` | `UnitPrice` | PricebookEntry |
| `weight_lbs` | `Weight__c` | Product2 (custom) |
| `compatible_models` | `Compatible_Models__c` | Product2 (custom) |

See [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) Section 9 for complete Salesforce API specifications.

---

## Usage Examples

### Query by PRIMARY Attributes
```python
# Get parts by manufacturer (PRIMARY attribute)
parts = catalog_repository.find_by_manufacturer("GE")

# Search by title (PRIMARY attribute with full-text search)
results = catalog_repository.search_by_title("defrost sensor")

# Filter by department (PRIMARY attribute)
refrigeration_parts = catalog_repository.filter_by_department("Refrigeration")
```

### Validate PRIMARY Attribute Completeness
```python
def check_primary_completeness(catalog: MasterCatalogRecord) -> float:
    """Calculate percentage of PRIMARY attributes populated"""
    primary_fields = [
        "mpn", "manufacturer", "part_type", "part_title", 
        "long_description", "primary_department", "primary_category",
        # ... all 34 PRIMARY fields
    ]
    
    found_count = sum(
        1 for field in primary_fields 
        if getattr(catalog, f"{field}_status") == DataStatus.FOUND
    )
    
    return (found_count / len(primary_fields)) * 100

# Target: 90%+ completeness for PRIMARY attributes
```

### Prioritize AI Validation of PRIMARY Attributes
```python
# AI validation focuses on PRIMARY attributes first
primary_data = {
    field: getattr(catalog, field) 
    for field in PRIMARY_FIELDS
}

openai_validation = await openai_validator.validate(
    primary_data,
    priority="high"  # Allocate more tokens/focus
)
```

---

## Summary

✅ **34 PRIMARY attributes** are universal and essential for all parts catalogs  
✅ **Populated first** with highest priority during data aggregation  
✅ **Higher importance weights** in confidence scoring  
✅ **Direct Salesforce mapping** for seamless integration  
✅ **AI validation focused** on PRIMARY attribute accuracy  
✅ **Status tracking** for each field (FOUND/NOT_APPLICABLE/NOT_FOUND)  

**Result**: A complete, accurate, and standardized catalog that meets enterprise requirements while maintaining flexibility for part-specific attributes.
