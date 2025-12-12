# Data Models Documentation

## Overview

This document defines all data structures used in the Parts Catalog Enhancement System.

---

## 1. Core Models

### 1.1 LookupSession

Tracks each part lookup request from initiation to completion.

```python
from datetime import datetime
from uuid import UUID
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field

class SessionStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"

class RequestSource(str, Enum):
    API = "api"
    UI = "ui"
    BATCH = "batch"
    SALESFORCE = "salesforce"
    SCHEDULED = "scheduled"

class LookupSession(BaseModel):
    """Main session tracking for each part lookup"""
    
    # Primary Identifiers
    session_id: UUID = Field(..., description="Unique session identifier")
    part_number: str = Field(..., description="Part number being looked up")
    
    # Timing
    request_timestamp: datetime = Field(..., description="When lookup was initiated")
    completion_timestamp: Optional[datetime] = Field(None, description="When lookup completed")
    processing_time_seconds: Optional[float] = Field(None, description="Total processing time")
    
    # Request Context
    request_source: RequestSource = Field(..., description="Source of the request")
    request_user_id: Optional[str] = Field(None, description="User who initiated request")
    request_metadata: Optional[dict] = Field(None, description="Additional request context")
    
    # Status
    status: SessionStatus = Field(default=SessionStatus.PENDING)
    status_message: Optional[str] = Field(None, description="Human-readable status")
    
    # Source Statistics
    total_sources_queried: int = Field(default=4)
    successful_sources: int = Field(default=0)
    failed_sources: List[str] = Field(default_factory=list)
    
    # Results
    catalog_record_id: Optional[UUID] = Field(None, description="Link to created catalog record")
    data_confidence_score: Optional[float] = Field(None, description="Overall confidence 0-1")
    
    # Error Tracking
    error_code: Optional[str] = Field(None)
    error_message: Optional[str] = Field(None)
    error_details: Optional[dict] = Field(None)
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "part_number": "WR55X10025",
                "request_timestamp": "2025-12-12T10:30:00Z",
                "request_source": "api",
                "status": "completed",
                "total_sources_queried": 4,
                "successful_sources": 3,
                "processing_time_seconds": 25.4
            }
        }
```

---

### 1.2 RawSourceResponse

Stores unmodified API responses from each supplier.

```python
class SourceName(str, Enum):
    ENCOMPASS = "encompass"
    MARCONE = "marcone"
    RELIABLE = "reliable"
    AMAZON = "amazon"

class RawSourceResponse(BaseModel):
    """Stores raw API response from each source"""
    
    # Identifiers
    response_id: UUID = Field(..., description="Unique response identifier")
    session_id: UUID = Field(..., description="Link to lookup session")
    source_name: SourceName = Field(..., description="Which API provider")
    
    # Request Details
    query_timestamp: datetime = Field(..., description="When API was called")
    query_part_number: str = Field(..., description="Part number sent to API")
    
    # Response Details
    response_timestamp: datetime = Field(..., description="When response received")
    response_status: int = Field(..., description="HTTP status code")
    response_time_ms: int = Field(..., description="Response time in milliseconds")
    
    # Raw Data (preserved exactly as received)
    raw_response: dict = Field(..., description="Complete API response")
    response_headers: Optional[dict] = Field(None)
    
    # Success/Error
    is_success: bool = Field(..., description="Whether request succeeded")
    error_message: Optional[str] = Field(None)
    error_code: Optional[str] = Field(None)
    
    # Data Quality Metrics
    data_completeness_score: Optional[float] = Field(None, description="0-1 score of data completeness")
    fields_found: Optional[List[str]] = Field(None)
    fields_missing: Optional[List[str]] = Field(None)
    
    # Media
    images_found: List[str] = Field(default_factory=list)
    documents_found: List[str] = Field(default_factory=list)
    videos_found: List[str] = Field(default_factory=list)
    
    class Config:
        json_schema_extra = {
            "example": {
                "response_id": "660e8400-e29b-41d4-a716-446655440000",
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "source_name": "encompass",
                "query_timestamp": "2025-12-12T10:30:05Z",
                "response_status": 200,
                "is_success": True,
                "data_completeness_score": 0.85,
                "images_found": ["https://example.com/img1.jpg"]
            }
        }
```

---

### 1.3 MasterCatalogRecord

The unified product record combining all source data.

```python
class PartType(str, Enum):
    OEM = "oem"
    GENERIC = "generic"
    AFTERMARKET = "aftermarket"
    REFURBISHED = "refurbished"
    UNIVERSAL = "universal"

class AIValidationStatus(str, Enum):
    VALIDATED = "validated"
    PARTIAL = "partial"
    UNVALIDATED = "unvalidated"
    VALIDATION_NEEDED = "validation_needed"

class DataStatus(str, Enum):
    FOUND = "found"
    NOT_APPLICABLE = "not_applicable"
    NOT_FOUND = "not_found"
    PENDING = "pending"

class MasterCatalogRecord(BaseModel):
    """Complete master catalog record with all attributes
    
    STRUCTURE:
    - Primary Attributes (33 fields): Universal fields required for ALL parts catalogs
    - System Metadata: Internal tracking fields
    - Additional Attributes: Part-specific or extended fields
    - AI Generated Content: Content created by AI validation
    - Specification Table: Dynamic key-value pairs for other attributes
    """
    
    # ========================================================================
    # PRIMARY ATTRIBUTES - UNIVERSAL FOR ALL PARTS CATALOGS (33 FIELDS)
    # These fields are considered standard across all catalog systems
    # and should be populated first with highest priority
    # ========================================================================
    
    # 1. Primary Part Number (MPN)
    mpn: str = Field(..., description="Primary Manufacturer Part Number")
    mpn_status: DataStatus = Field(default=DataStatus.FOUND)
    
    # 2. Alternative Model Number
    alternative_model_numbers: List[str] = Field(default_factory=list)
    alternative_model_numbers_status: DataStatus = Field(default=DataStatus.NOT_FOUND)
    
    # 3. Manufacturer / Brand
    manufacturer: str = Field(..., description="Brand/Manufacturer name")
    manufacturer_status: DataStatus = Field(default=DataStatus.FOUND)
    
    # 4. Part Type
    part_type: PartType = Field(..., description="OEM, Generic, Aftermarket, etc.")
    part_type_status: DataStatus = Field(default=DataStatus.FOUND)
    
    # 5. Part Title
    part_title: str = Field(..., description="1-3 sentence product title")
    part_title_status: DataStatus = Field(default=DataStatus.FOUND)
    
    # 6. Long Description
    long_description: str = Field(..., description="200-1000 word detailed description")
    long_description_status: DataStatus = Field(default=DataStatus.FOUND)
    
    # 7. Primary Department
    primary_department: str = Field(..., description="Main department: Refrigeration, Laundry, HVAC, etc.")
    primary_department_status: DataStatus = Field(default=DataStatus.FOUND)
    
    # 8. Primary Category
    primary_category: str = Field(..., description="Main category: Defrost System, Motor, Compressor, etc.")
    primary_category_status: DataStatus = Field(default=DataStatus.FOUND)
    
    # 9. All Sub-Categories / Tags
    sub_categories: List[str] = Field(default_factory=list, description="All applicable sub-categories and tags")
    sub_categories_status: DataStatus = Field(default=DataStatus.FOUND)
    
    # 10. Primary Image URL
    primary_image_url: Optional[str] = Field(None, description="Main product image URL")
    primary_image_status: DataStatus = Field(default=DataStatus.NOT_FOUND)
    primary_image_source: Optional[str] = Field(None, description="Source API that provided image")
    
    # 11. Gallery Image URLs (array)
    gallery_images: List[str] = Field(default_factory=list, description="Additional product images")
    gallery_images_status: DataStatus = Field(default=DataStatus.NOT_FOUND)
    
    # 12. MSRP / Compare-at Price
    msrp: Optional[float] = Field(None, description="Manufacturer Suggested Retail Price")
    msrp_status: DataStatus = Field(default=DataStatus.NOT_FOUND)
    
    # 13. High Average Sale Price
    high_avg_price: Optional[float] = Field(None, description="Highest typical selling price")
    high_avg_price_status: DataStatus = Field(default=DataStatus.NOT_FOUND)
    
    # 14. Low Average Sale Price
    low_avg_price: Optional[float] = Field(None, description="Lowest typical selling price")
    low_avg_price_status: DataStatus = Field(default=DataStatus.NOT_FOUND)
    
    # 15. Current Selling Price
    current_selling_price: Optional[float] = Field(None, description="Current market price")
    current_selling_price_status: DataStatus = Field(default=DataStatus.NOT_FOUND)
    
    # 16. Weight (shipping)
    weight_lbs: Optional[float] = Field(None, description="Shipping weight in pounds")
    weight_lbs_status: DataStatus = Field(default=DataStatus.NOT_FOUND)
    
    # 17. Product Manufacture Box length (L×W×H)
    box_length_in: Optional[float] = Field(None, description="Manufacturer box length in inches")
    box_length_in_status: DataStatus = Field(default=DataStatus.NOT_FOUND)
    
    # 18. Product Manufacture Box Width (L×W×H)
    box_width_in: Optional[float] = Field(None, description="Manufacturer box width in inches")
    box_width_in_status: DataStatus = Field(default=DataStatus.NOT_FOUND)
    
    # 19. Product Manufacture Box height (L×W×H)
    box_height_in: Optional[float] = Field(None, description="Manufacturer box height in inches")
    box_height_in_status: DataStatus = Field(default=DataStatus.NOT_FOUND)
    
    # 20. Product Manufacture Length (Not In Box / Not Box)
    product_length_in: Optional[float] = Field(None, description="Actual product length (unboxed) in inches")
    product_length_in_status: DataStatus = Field(default=DataStatus.NOT_FOUND)
    
    # 21. Product Manufacture Width (Not In Box / Not Box)
    product_width_in: Optional[float] = Field(None, description="Actual product width (unboxed) in inches")
    product_width_in_status: DataStatus = Field(default=DataStatus.NOT_FOUND)
    
    # 22. Product Manufacture Height (Not In Box / Not Box)
    product_height_in: Optional[float] = Field(None, description="Actual product height (unboxed) in inches")
    product_height_in_status: DataStatus = Field(default=DataStatus.NOT_FOUND)
    
    # 23. UPC / EAN / GTIN
    upc_ean_gtin: Optional[str] = Field(None, description="Universal Product Code / GTIN")
    upc_ean_gtin_status: DataStatus = Field(default=DataStatus.NOT_FOUND)
    
    # 24. Voltage
    voltage: Optional[str] = Field(None, description="Operating voltage: 120V, 240V, etc.")
    voltage_status: DataStatus = Field(default=DataStatus.NOT_APPLICABLE)
    
    # 25. Terminal Type
    terminal_type: Optional[str] = Field(None, description="Electrical terminal: Quick-connect, screw, blade, etc.")
    terminal_type_status: DataStatus = Field(default=DataStatus.NOT_APPLICABLE)
    
    # 26. Top 10 Compatible Models (list)
    compatible_models: List[str] = Field(default_factory=list, description="Top 10 compatible appliance models")
    compatible_models_status: DataStatus = Field(default=DataStatus.NOT_FOUND)
    
    # 27. Cross-Reference Part Numbers
    cross_reference_parts: List[str] = Field(default_factory=list, description="Interchangeable part numbers")
    cross_reference_parts_status: DataStatus = Field(default=DataStatus.NOT_FOUND)
    
    # 28. Color
    color: Optional[str] = Field(None, description="Product color")
    color_status: DataStatus = Field(default=DataStatus.NOT_APPLICABLE)
    
    # 29. Material
    material: Optional[str] = Field(None, description="Primary material: Plastic, Metal, Rubber, etc.")
    material_status: DataStatus = Field(default=DataStatus.NOT_APPLICABLE)
    
    # 30. Finish
    finish: Optional[str] = Field(None, description="Surface finish: Brushed, Polished, Matte, etc.")
    finish_status: DataStatus = Field(default=DataStatus.NOT_APPLICABLE)
    
    # 31. Related Symptoms
    related_symptoms: List[str] = Field(default_factory=list, description="Common appliance symptoms this part fixes")
    related_symptoms_status: DataStatus = Field(default=DataStatus.NOT_FOUND)
    
    # 32. Installation Suggestions
    installation_suggestions: Optional[str] = Field(None, description="Installation tips and guidance")
    installation_suggestions_status: DataStatus = Field(default=DataStatus.NOT_FOUND)
    
    # 33. Specification Table
    specification_table: dict = Field(default_factory=dict, description="Additional specifications as key-value pairs")
    specification_table_status: DataStatus = Field(default=DataStatus.NOT_FOUND)
    
    # 34. Manufacturer Product Page URL
    manufacturer_url: Optional[str] = Field(None, description="Official manufacturer product page")
    manufacturer_url_status: DataStatus = Field(default=DataStatus.NOT_FOUND)
    
    # ========================================================================
    # SYSTEM METADATA - Internal tracking fields
    # ========================================================================
    
    catalog_id: UUID = Field(..., description="Unique catalog record ID")
    created_at: datetime = Field(..., description="When record was created")
    last_updated: datetime = Field(..., description="Last modification timestamp")
    lookup_session_id: UUID = Field(..., description="Original lookup session")
    
    # Data Quality Metrics
    data_confidence_score: float = Field(..., ge=0, le=1, description="Overall confidence 0-1")
    ai_validation_status: AIValidationStatus = Field(...)
    field_completeness_percentage: float = Field(..., ge=0, le=100)
    
    # Source Attribution
    source_priority: List[str] = Field(..., description="Ordered list of sources used")
    encompass_source_id: Optional[UUID] = Field(None)
    marcone_source_id: Optional[UUID] = Field(None)
    reliable_source_id: Optional[UUID] = Field(None)
    amazon_source_id: Optional[UUID] = Field(None)
    
    # ========================================================================
    # ADDITIONAL ATTRIBUTES - Extended/part-specific fields (50+ fields)
    # ========================================================================
    
    # Additional identifiers
    sku: Optional[str] = Field(None, description="Seller SKU")
    sku_status: DataStatus = Field(default=DataStatus.NOT_FOUND)
    
    asin: Optional[str] = Field(None, description="Amazon ASIN")
    asin_status: DataStatus = Field(default=DataStatus.NOT_FOUND)
    
    # Extended physical specs
    diameter_in: Optional[float] = Field(None)
    diameter_in_status: DataStatus = Field(default=DataStatus.NOT_APPLICABLE)
    
    thickness_in: Optional[float] = Field(None)
    thickness_in_status: DataStatus = Field(default=DataStatus.NOT_APPLICABLE)
    
    capacity: Optional[str] = Field(None, description="e.g., '5 gallons', '20 lbs'")
    capacity_status: DataStatus = Field(default=DataStatus.NOT_APPLICABLE)
    
    # Extended electrical specs
    wattage: Optional[float] = Field(None)
    wattage_status: DataStatus = Field(default=DataStatus.NOT_APPLICABLE)
    
    amperage: Optional[float] = Field(None)
    amperage_status: DataStatus = Field(default=DataStatus.NOT_APPLICABLE)
    
    frequency_hz: Optional[int] = Field(None, description="50Hz or 60Hz")
    frequency_hz_status: DataStatus = Field(default=DataStatus.NOT_APPLICABLE)
    
    phase: Optional[str] = Field(None, description="Single-phase or Three-phase")
    phase_status: DataStatus = Field(default=DataStatus.NOT_APPLICABLE)
    
    # Temperature specs
    operating_temp_min_f: Optional[float] = Field(None)
    operating_temp_min_f_status: DataStatus = Field(default=DataStatus.NOT_APPLICABLE)
    
    operating_temp_max_f: Optional[float] = Field(None)
    operating_temp_max_f_status: DataStatus = Field(default=DataStatus.NOT_APPLICABLE)
    
    # Pressure specs
    pressure_rating_psi: Optional[float] = Field(None)
    pressure_rating_psi_status: DataStatus = Field(default=DataStatus.NOT_APPLICABLE)
    
    # Flow specs
    flow_rate: Optional[str] = Field(None, description="e.g., '2.5 GPM'")
    flow_rate_status: DataStatus = Field(default=DataStatus.NOT_APPLICABLE)
    
    # Certifications
    certifications: List[str] = Field(default_factory=list, description="UL, CSA, ETL, etc.")
    certifications_status: DataStatus = Field(default=DataStatus.NOT_FOUND)
    
    # Warranty
    warranty_period: Optional[str] = Field(None, description="e.g., '1 year', '90 days'")
    warranty_period_status: DataStatus = Field(default=DataStatus.NOT_FOUND)
    
    # Availability
    availability_status: Optional[str] = Field(None, description="In stock, Backordered, Discontinued")
    availability_status_flag: DataStatus = Field(default=DataStatus.NOT_FOUND)
    
    lead_time_days: Optional[int] = Field(None)
    lead_time_days_status: DataStatus = Field(default=DataStatus.NOT_FOUND)
    
    # Country of origin
    country_of_origin: Optional[str] = Field(None)
    country_of_origin_status: DataStatus = Field(default=DataStatus.NOT_FOUND)
    
    # Packaging
    package_quantity: Optional[int] = Field(None, description="Number of units per package")
    package_quantity_status: DataStatus = Field(default=DataStatus.NOT_FOUND)
    
    # Replacement info
    replaces_part_numbers: List[str] = Field(default_factory=list, description="Old part numbers this replaces")
    replaces_part_numbers_status: DataStatus = Field(default=DataStatus.NOT_FOUND)
    
    replaced_by_part_number: Optional[str] = Field(None, description="Newer part that replaces this")
    replaced_by_part_number_status: DataStatus = Field(default=DataStatus.NOT_FOUND)
    
    # Compatibility details
    compatible_brands: List[str] = Field(default_factory=list)
    compatible_brands_status: DataStatus = Field(default=DataStatus.NOT_FOUND)
    
    # Documentation
    manual_pdf_url: Optional[str] = Field(None)
    manual_pdf_url_status: DataStatus = Field(default=DataStatus.NOT_FOUND)
    
    installation_video_url: Optional[str] = Field(None)
    installation_video_url_status: DataStatus = Field(default=DataStatus.NOT_FOUND)
    
    diagram_url: Optional[str] = Field(None)
    diagram_url_status: DataStatus = Field(default=DataStatus.NOT_FOUND)
    
    # SEO fields
    seo_keywords: List[str] = Field(default_factory=list)
    seo_keywords_status: DataStatus = Field(default=DataStatus.NOT_FOUND)
    
    meta_description: Optional[str] = Field(None, description="SEO meta description")
    meta_description_status: DataStatus = Field(default=DataStatus.NOT_FOUND)
    
    
    # ========================================================================
    # AI GENERATED CONTENT - Content created during AI validation
    # ========================================================================
    
    ai_generated_title: Optional[str] = Field(None, description="AI-enhanced title if original inadequate")
    ai_generated_description: Optional[str] = Field(None, description="AI-generated marketing description")
    ai_title_source: Optional[str] = Field(None, description="OPENAI or GROK")
    ai_description_source: Optional[str] = Field(None, description="OPENAI or GROK")
    
    # ========================================================================
    # VERSION CONTROL
    # ========================================================================
    
    version: int = Field(default=1, description="Record version number")
    previous_version_id: Optional[UUID] = Field(None, description="Previous version if updated")
    
    class Config:
        json_schema_extra = {
            "example": {
                "catalog_id": "770e8400-e29b-41d4-a716-446655440000",
                "mpn": "WR55X10025",
                "manufacturer": "GE",
                "part_type": "oem",
                "part_title": "GE WR55X10025 Refrigerator Defrost Sensor",
                "long_description": "The GE WR55X10025 is a genuine OEM defrost sensor...",
                "primary_department": "Refrigeration",
                "primary_category": "Defrost System",
                "msrp": 49.99,
                "current_selling_price": 42.50,
                "weight_lbs": 0.2,
                "voltage": "N/A",
                "compatible_models": ["GFE28GMKES", "PFE28KSKSS", "GNE27JSMSS"],
                "data_confidence_score": 0.92,
                "ai_validation_status": "validated"
            }
        }
```

---

### 1.4 AIValidationRecord

Stores results from OpenAI and Grok validation.

```python
class AIProvider(str, Enum):
    OPENAI = "openai"
    GROK = "grok"

class AIValidationRecord(BaseModel):
    """AI validation results for a catalog record"""
    
    # Identifiers
    validation_id: UUID = Field(...)
    session_id: UUID = Field(...)
    catalog_id: UUID = Field(...)
    
    # ===== OPENAI VALIDATION =====
    openai_request_timestamp: Optional[datetime] = Field(None)
    openai_response_timestamp: Optional[datetime] = Field(None)
    openai_model: Optional[str] = Field(None, description="e.g., gpt-4-turbo")
    openai_validation_result: Optional[dict] = Field(None)
    openai_confidence_scores: Optional[dict] = Field(None, description="Per-field confidence")
    openai_generated_title: Optional[str] = Field(None)
    openai_generated_description: Optional[str] = Field(None)
    openai_conflicts_found: List[str] = Field(default_factory=list)
    openai_tokens_used: Optional[int] = Field(None)
    openai_cost: Optional[float] = Field(None)
    
    # ===== GROK VALIDATION =====
    grok_request_timestamp: Optional[datetime] = Field(None)
    grok_response_timestamp: Optional[datetime] = Field(None)
    grok_model: Optional[str] = Field(None)
    grok_validation_result: Optional[dict] = Field(None)
    grok_confidence_scores: Optional[dict] = Field(None)
    grok_generated_title: Optional[str] = Field(None)
    grok_generated_description: Optional[str] = Field(None)
    grok_conflicts_found: List[str] = Field(default_factory=list)
    grok_tokens_used: Optional[int] = Field(None)
    grok_cost: Optional[float] = Field(None)
    
    # ===== CONSENSUS ANALYSIS =====
    ai_agreement_score: float = Field(..., ge=0, le=1, description="0-1 agreement between AIs")
    consensus_conflicts: List[dict] = Field(default_factory=list)
    final_title_source: Optional[AIProvider] = Field(None)
    final_description_source: Optional[AIProvider] = Field(None)
    resolution_logic: dict = Field(default_factory=dict)
    
    # ===== METRICS =====
    total_fields_validated: int = Field(default=0)
    fields_with_high_confidence: int = Field(default=0)
    fields_with_conflicts: int = Field(default=0)
    total_cost: float = Field(default=0.0)
    total_processing_time_seconds: float = Field(default=0.0)
    
    class Config:
        json_schema_extra = {
            "example": {
                "validation_id": "880e8400-e29b-41d4-a716-446655440000",
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "catalog_id": "770e8400-e29b-41d4-a716-446655440000",
                "ai_agreement_score": 0.89,
                "final_title_source": "openai",
                "total_cost": 0.12
            }
        }
```

---

### 1.5 SpecTableEntry

Dynamic specification table for attributes not in main fields.

```python
class SpecValueType(str, Enum):
    TEXT = "text"
    NUMBER = "number"
    BOOLEAN = "boolean"
    DATE = "date"
    URL = "url"
    LIST = "list"

class ConfidenceLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class SpecTableEntry(BaseModel):
    """Individual specification table entry"""
    
    spec_id: UUID = Field(...)
    catalog_id: UUID = Field(..., description="Link to master catalog")
    
    # Attribute Details
    attribute_name: str = Field(..., description="e.g., 'RPM', 'Voltage'")
    attribute_display_name: str = Field(..., description="Human-readable name")
    attribute_value: str = Field(..., description="The value")
    value_type: SpecValueType = Field(...)
    unit: Optional[str] = Field(None, description="e.g., 'lbs', 'V', 'Hz'")
    
    # Source & Quality
    data_source: str = Field(..., description="Which API or AI provided this")
    source_field_name: Optional[str] = Field(None)
    confidence_level: ConfidenceLevel = Field(...)
    status: DataStatus = Field(...)
    
    # Validation
    validated_by_ai: bool = Field(default=False)
    validation_notes: Optional[str] = Field(None)
    
    # Categorization
    category: Optional[str] = Field(None, description="Group specs by category")
    display_order: int = Field(default=0, description="Order in table")
    
    class Config:
        json_schema_extra = {
            "example": {
                "spec_id": "990e8400-e29b-41d4-a716-446655440000",
                "catalog_id": "770e8400-e29b-41d4-a716-446655440000",
                "attribute_name": "rpm",
                "attribute_display_name": "RPM",
                "attribute_value": "1075",
                "value_type": "number",
                "data_source": "encompass",
                "confidence_level": "high",
                "status": "found"
            }
        }
```

---

## 2. Supporting Models

### 2.1 ImageMetadata

```python
class ImageMetadata(BaseModel):
    """Metadata for product images"""
    
    image_id: UUID = Field(...)
    catalog_id: UUID = Field(...)
    
    # Image Details
    original_url: str = Field(...)
    stored_url: Optional[str] = Field(None, description="S3 or CDN URL")
    thumbnail_url: Optional[str] = Field(None)
    
    # Source
    source_api: SourceName = Field(...)
    image_type: str = Field(..., description="primary, gallery, diagram, etc.")
    
    # Properties
    width: Optional[int] = Field(None)
    height: Optional[int] = Field(None)
    file_size_bytes: Optional[int] = Field(None)
    format: Optional[str] = Field(None, description="jpg, png, webp")
    
    # Status
    download_status: str = Field(default="pending")
    downloaded_at: Optional[datetime] = Field(None)
    
    # Order
    display_order: int = Field(default=0)
```

### 2.2 AuditLog

```python
class AuditAction(str, Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    VALIDATE = "validate"
    PUBLISH = "publish"

class AuditLog(BaseModel):
    """Audit trail for all system changes"""
    
    audit_id: UUID = Field(...)
    timestamp: datetime = Field(...)
    
    # Action Details
    action: AuditAction = Field(...)
    entity_type: str = Field(..., description="catalog, session, etc.")
    entity_id: UUID = Field(...)
    
    # User/System
    performed_by: str = Field(..., description="User ID or 'system'")
    source: str = Field(..., description="API, UI, scheduled_job, etc.")
    
    # Changes
    changes: Optional[dict] = Field(None, description="Before/after values")
    reason: Optional[str] = Field(None)
    
    # Context
    session_id: Optional[UUID] = Field(None)
    ip_address: Optional[str] = Field(None)
```

### 2.3 APIKey

```python
class APIKey(BaseModel):
    """API keys for Salesforce and other clients"""
    
    key_id: UUID = Field(...)
    key_hash: str = Field(..., description="Hashed API key")
    key_name: str = Field(..., description="Human-readable name")
    
    # Client Info
    client_id: str = Field(...)
    client_name: str = Field(..., description="e.g., 'Salesforce Production'")
    
    # Permissions
    scopes: List[str] = Field(..., description="Allowed operations")
    rate_limit_per_hour: int = Field(default=1000)
    
    # Status
    is_active: bool = Field(default=True)
    created_at: datetime = Field(...)
    expires_at: Optional[datetime] = Field(None)
    last_used_at: Optional[datetime] = Field(None)
    
    # Stats
    total_requests: int = Field(default=0)
    failed_requests: int = Field(default=0)
```

---

## 3. Request/Response Models

### 3.1 Lookup Request

```python
class LookupRequest(BaseModel):
    """API request to lookup a part"""
    
    part_number: str = Field(..., min_length=1, max_length=100)
    force_refresh: bool = Field(default=False, description="Force new lookup even if cached")
    source_filter: Optional[List[SourceName]] = Field(None, description="Only query specific sources")
    priority: str = Field(default="normal", description="normal, high, low")
    callback_url: Optional[str] = Field(None, description="Webhook for async results")
    
    # Metadata
    request_metadata: Optional[dict] = Field(None)
    
    class Config:
        json_schema_extra = {
            "example": {
                "part_number": "WR55X10025",
                "force_refresh": False,
                "priority": "normal"
            }
        }
```

### 3.2 Lookup Response

```python
class LookupResponse(BaseModel):
    """API response for part lookup"""
    
    session_id: UUID = Field(...)
    part_number: str = Field(...)
    status: SessionStatus = Field(...)
    
    # Results
    catalog_record: Optional[MasterCatalogRecord] = Field(None)
    
    # Metrics
    processing_time_seconds: float = Field(...)
    sources_queried: int = Field(...)
    sources_successful: int = Field(...)
    data_confidence_score: Optional[float] = Field(None)
    
    # Links
    catalog_url: Optional[str] = Field(None)
    session_url: Optional[str] = Field(None)
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "part_number": "WR55X10025",
                "status": "completed",
                "processing_time_seconds": 23.5,
                "sources_queried": 4,
                "sources_successful": 3,
                "data_confidence_score": 0.91
            }
        }
```

### 3.3 Catalog Query Response

```python
class CatalogQueryResponse(BaseModel):
    """Response for Salesforce catalog queries"""
    
    catalog_id: UUID = Field(...)
    mpn: str = Field(...)
    manufacturer: str = Field(...)
    
    # Core Info
    title: str = Field(...)
    description: str = Field(...)
    part_type: PartType = Field(...)
    
    # Pricing
    pricing: dict = Field(...)
    
    # Images
    images: List[str] = Field(...)
    primary_image: Optional[str] = Field(None)
    
    # Specs
    specifications: dict = Field(...)
    
    # Metadata
    data_confidence_score: float = Field(...)
    last_updated: datetime = Field(...)
    
    # Links
    detailed_url: str = Field(...)
```

---

## 4. Configuration Models

### 4.1 APIConfig

```python
class EncompassConfig(BaseModel):
    api_key: str
    base_url: str = "https://api.encompass.com/v1"
    timeout_seconds: int = 30
    rate_limit_per_minute: int = 100
    retry_attempts: int = 3

class MarconeConfig(BaseModel):
    client_id: str
    client_secret: str
    base_url: str = "https://api.marcone.com/v2"
    timeout_seconds: int = 30
    rate_limit_per_minute: int = 50
    retry_attempts: int = 3

class ReliableConfig(BaseModel):
    api_key: str
    api_secret: str
    base_url: str = "https://api.reliableparts.com/v1"
    timeout_seconds: int = 30
    rate_limit_per_minute: int = 75
    retry_attempts: int = 3

class AmazonConfig(BaseModel):
    access_key: str
    secret_key: str
    partner_tag: str
    region: str = "us-east-1"
    timeout_seconds: int = 30
    rate_limit_per_second: int = 1
    retry_attempts: int = 3
```

### 4.2 AIConfig

```python
class OpenAIConfig(BaseModel):
    api_key: str
    model: str = "gpt-4-turbo"
    max_tokens: int = 4000
    temperature: float = 0.2
    timeout_seconds: int = 60
    
class GrokConfig(BaseModel):
    api_key: str
    model: str = "grok-1"
    max_tokens: int = 4000
    temperature: float = 0.2
    timeout_seconds: int = 60
```

---

## 5. Database Schema (SQL)

```sql
-- Main Tables

CREATE TABLE lookup_sessions (
    session_id UUID PRIMARY KEY,
    part_number VARCHAR(100) NOT NULL,
    request_timestamp TIMESTAMP NOT NULL,
    completion_timestamp TIMESTAMP,
    request_source VARCHAR(50) NOT NULL,
    request_user_id VARCHAR(100),
    status VARCHAR(20) NOT NULL,
    status_message TEXT,
    total_sources_queried INT DEFAULT 4,
    successful_sources INT DEFAULT 0,
    failed_sources JSONB,
    catalog_record_id UUID,
    data_confidence_score FLOAT,
    processing_time_seconds FLOAT,
    error_code VARCHAR(50),
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE raw_source_responses (
    response_id UUID PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES lookup_sessions(session_id),
    source_name VARCHAR(50) NOT NULL,
    query_timestamp TIMESTAMP NOT NULL,
    query_part_number VARCHAR(100) NOT NULL,
    response_timestamp TIMESTAMP NOT NULL,
    response_status INT NOT NULL,
    response_time_ms INT NOT NULL,
    raw_response JSONB NOT NULL,
    response_headers JSONB,
    is_success BOOLEAN NOT NULL,
    error_message TEXT,
    error_code VARCHAR(50),
    data_completeness_score FLOAT,
    fields_found JSONB,
    fields_missing JSONB,
    images_found JSONB,
    documents_found JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE master_catalog (
    catalog_id UUID PRIMARY KEY,
    mpn VARCHAR(100) NOT NULL,
    alternative_model_numbers JSONB,
    
    -- Metadata
    created_at TIMESTAMP NOT NULL,
    last_updated TIMESTAMP NOT NULL,
    lookup_session_id UUID REFERENCES lookup_sessions(session_id),
    data_confidence_score FLOAT,
    ai_validation_status VARCHAR(50),
    field_completeness_percentage FLOAT,
    
    -- Source attribution
    source_priority JSONB,
    encompass_source_id UUID,
    marcone_source_id UUID,
    reliable_source_id UUID,
    amazon_source_id UUID,
    
    -- Required fields
    manufacturer VARCHAR(200),
    manufacturer_status VARCHAR(20),
    part_type VARCHAR(50),
    part_type_status VARCHAR(20),
    part_title TEXT,
    part_title_status VARCHAR(20),
    long_description TEXT,
    long_description_status VARCHAR(20),
    
    primary_department VARCHAR(100),
    primary_department_status VARCHAR(20),
    primary_category VARCHAR(100),
    primary_category_status VARCHAR(20),
    sub_categories JSONB,
    sub_categories_status VARCHAR(20),
    
    -- Images
    primary_image_url TEXT,
    primary_image_status VARCHAR(20),
    gallery_images JSONB,
    gallery_images_status VARCHAR(20),
    
    -- Pricing
    msrp DECIMAL(10,2),
    msrp_status VARCHAR(20),
    high_avg_price DECIMAL(10,2),
    high_avg_price_status VARCHAR(20),
    low_avg_price DECIMAL(10,2),
    low_avg_price_status VARCHAR(20),
    current_selling_price DECIMAL(10,2),
    current_selling_price_status VARCHAR(20),
    
    -- Physical specs
    weight_lbs FLOAT,
    weight_lbs_status VARCHAR(20),
    box_length_in FLOAT,
    box_width_in FLOAT,
    box_height_in FLOAT,
    product_length_in FLOAT,
    product_width_in FLOAT,
    product_height_in FLOAT,
    
    -- Identifiers
    upc_ean_gtin VARCHAR(50),
    upc_ean_gtin_status VARCHAR(20),
    
    -- Electrical
    voltage VARCHAR(50),
    voltage_status VARCHAR(20),
    terminal_type VARCHAR(100),
    terminal_type_status VARCHAR(20),
    
    -- Compatibility
    compatible_models JSONB,
    compatible_models_status VARCHAR(20),
    cross_reference_parts JSONB,
    cross_reference_parts_status VARCHAR(20),
    
    -- Details
    color VARCHAR(50),
    color_status VARCHAR(20),
    material VARCHAR(100),
    material_status VARCHAR(20),
    finish VARCHAR(50),
    finish_status VARCHAR(20),
    
    -- Support
    related_symptoms JSONB,
    related_symptoms_status VARCHAR(20),
    installation_suggestions TEXT,
    installation_suggestions_status VARCHAR(20),
    manufacturer_url TEXT,
    manufacturer_url_status VARCHAR(20),
    
    -- AI content
    ai_generated_title TEXT,
    ai_generated_description TEXT,
    ai_title_source VARCHAR(20),
    ai_description_source VARCHAR(20),
    
    -- Spec table
    spec_table JSONB,
    
    -- Versioning
    version INT DEFAULT 1,
    previous_version_id UUID,
    
    CONSTRAINT unique_mpn UNIQUE(mpn)
);

CREATE TABLE ai_validations (
    validation_id UUID PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES lookup_sessions(session_id),
    catalog_id UUID NOT NULL REFERENCES master_catalog(catalog_id),
    
    -- OpenAI
    openai_request_timestamp TIMESTAMP,
    openai_response_timestamp TIMESTAMP,
    openai_model VARCHAR(50),
    openai_validation_result JSONB,
    openai_confidence_scores JSONB,
    openai_generated_title TEXT,
    openai_generated_description TEXT,
    openai_conflicts_found JSONB,
    openai_tokens_used INT,
    openai_cost DECIMAL(10,4),
    
    -- Grok
    grok_request_timestamp TIMESTAMP,
    grok_response_timestamp TIMESTAMP,
    grok_model VARCHAR(50),
    grok_validation_result JSONB,
    grok_confidence_scores JSONB,
    grok_generated_title TEXT,
    grok_generated_description TEXT,
    grok_conflicts_found JSONB,
    grok_tokens_used INT,
    grok_cost DECIMAL(10,4),
    
    -- Consensus
    ai_agreement_score FLOAT,
    consensus_conflicts JSONB,
    final_title_source VARCHAR(20),
    final_description_source VARCHAR(20),
    resolution_logic JSONB,
    
    -- Metrics
    total_fields_validated INT DEFAULT 0,
    fields_with_high_confidence INT DEFAULT 0,
    fields_with_conflicts INT DEFAULT 0,
    total_cost DECIMAL(10,4),
    total_processing_time_seconds FLOAT,
    
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE spec_table_entries (
    spec_id UUID PRIMARY KEY,
    catalog_id UUID NOT NULL REFERENCES master_catalog(catalog_id),
    
    attribute_name VARCHAR(100) NOT NULL,
    attribute_display_name VARCHAR(200) NOT NULL,
    attribute_value TEXT NOT NULL,
    value_type VARCHAR(20) NOT NULL,
    unit VARCHAR(20),
    
    data_source VARCHAR(50) NOT NULL,
    source_field_name VARCHAR(100),
    confidence_level VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL,
    
    validated_by_ai BOOLEAN DEFAULT FALSE,
    validation_notes TEXT,
    
    category VARCHAR(100),
    display_order INT DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT NOW(),
    
    CONSTRAINT unique_catalog_attribute UNIQUE(catalog_id, attribute_name)
);

CREATE TABLE images (
    image_id UUID PRIMARY KEY,
    catalog_id UUID NOT NULL REFERENCES master_catalog(catalog_id),
    
    original_url TEXT NOT NULL,
    stored_url TEXT,
    thumbnail_url TEXT,
    
    source_api VARCHAR(50) NOT NULL,
    image_type VARCHAR(50) NOT NULL,
    
    width INT,
    height INT,
    file_size_bytes INT,
    format VARCHAR(20),
    
    download_status VARCHAR(20) DEFAULT 'pending',
    downloaded_at TIMESTAMP,
    
    display_order INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE audit_logs (
    audit_id UUID PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    
    action VARCHAR(50) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id UUID NOT NULL,
    
    performed_by VARCHAR(100) NOT NULL,
    source VARCHAR(50) NOT NULL,
    
    changes JSONB,
    reason TEXT,
    
    session_id UUID,
    ip_address VARCHAR(50),
    
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE api_keys (
    key_id UUID PRIMARY KEY,
    key_hash VARCHAR(255) NOT NULL UNIQUE,
    key_name VARCHAR(200) NOT NULL,
    
    client_id VARCHAR(100) NOT NULL,
    client_name VARCHAR(200) NOT NULL,
    
    scopes JSONB NOT NULL,
    rate_limit_per_hour INT DEFAULT 1000,
    
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL,
    expires_at TIMESTAMP,
    last_used_at TIMESTAMP,
    
    total_requests BIGINT DEFAULT 0,
    failed_requests BIGINT DEFAULT 0
);

-- Indexes
CREATE INDEX idx_sessions_part_number ON lookup_sessions(part_number);
CREATE INDEX idx_sessions_timestamp ON lookup_sessions(request_timestamp);
CREATE INDEX idx_sessions_status ON lookup_sessions(status);
CREATE INDEX idx_sessions_catalog ON lookup_sessions(catalog_record_id);

CREATE INDEX idx_responses_session ON raw_source_responses(session_id);
CREATE INDEX idx_responses_source ON raw_source_responses(source_name);
CREATE INDEX idx_responses_timestamp ON raw_source_responses(query_timestamp);

CREATE INDEX idx_catalog_mpn ON master_catalog(mpn);
CREATE INDEX idx_catalog_manufacturer ON master_catalog(manufacturer);
CREATE INDEX idx_catalog_updated ON master_catalog(last_updated);
CREATE INDEX idx_catalog_validation_status ON master_catalog(ai_validation_status);

CREATE INDEX idx_validations_session ON ai_validations(session_id);
CREATE INDEX idx_validations_catalog ON ai_validations(catalog_id);

CREATE INDEX idx_specs_catalog ON spec_table_entries(catalog_id);
CREATE INDEX idx_specs_category ON spec_table_entries(category);

CREATE INDEX idx_images_catalog ON images(catalog_id);
CREATE INDEX idx_images_type ON images(image_type);

CREATE INDEX idx_audit_timestamp ON audit_logs(timestamp);
CREATE INDEX idx_audit_entity ON audit_logs(entity_type, entity_id);

-- Full-text search
CREATE INDEX idx_catalog_search ON master_catalog 
USING GIN(to_tsvector('english', part_title || ' ' || COALESCE(long_description, '')));
```

---

**Document Version**: 1.0  
**Last Updated**: December 12, 2025  
**Status**: Ready for Implementation
