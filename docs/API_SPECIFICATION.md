# API Specification Document

## Overview

This document defines all API endpoints, integration specifications, and protocols for the Parts Catalog Enhancement System.

---

## Table of Contents

1. [External API Integrations](#external-api-integrations)
2. [Internal API Endpoints](#internal-api-endpoints)
3. [Salesforce Integration API](#salesforce-integration-api)
4. [AI Service Integration](#ai-service-integration)
5. [Authentication & Authorization](#authentication--authorization)
6. [Rate Limiting](#rate-limiting)
7. [Error Handling](#error-handling)
8. [Webhooks](#webhooks)

---

## 1. External API Integrations

### 1.1 Encompass API

**Base URL**: `https://api.encompass.com/v1`  
**Authentication**: API Key (Header)  
**Rate Limit**: 100 requests/minute  

#### Endpoints

```python
# Part Lookup
GET /parts/{part_number}
Headers:
  Authorization: Bearer {API_KEY}
  Content-Type: application/json

Response 200:
{
  "partNumber": "WR55X10025",
  "manufacturer": "GE",
  "description": "Defrost Sensor Assembly",
  "price": {
    "msrp": 48.99,
    "current": 23.95
  },
  "specifications": {...},
  "images": [...],
  "compatibleModels": [...],
  "inStock": true
}

# Cross-Reference Search
GET /parts/cross-reference/{part_number}

# Compatible Models
GET /parts/{part_number}/models
```

#### Implementation

```python
class EncompassAPIClient:
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url
        self.session = aiohttp.ClientSession()
    
    async def lookup_part(self, part_number: str) -> Dict:
        """
        Lookup part by number
        
        Args:
            part_number: The part number to search
            
        Returns:
            Dict containing part information
            
        Raises:
            EncompassAPIError: If API call fails
            RateLimitError: If rate limit exceeded
        """
        url = f"{self.base_url}/parts/{part_number}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            async with self.session.get(url, headers=headers, timeout=30) as response:
                if response.status == 429:
                    raise RateLimitError("Encompass rate limit exceeded")
                if response.status == 404:
                    return {"found": False, "message": "Part not found"}
                response.raise_for_status()
                return await response.json()
        except asyncio.TimeoutError:
            raise EncompassAPIError("Request timeout")
        except Exception as e:
            raise EncompassAPIError(f"API call failed: {str(e)}")
    
    async def get_images(self, part_number: str) -> List[str]:
        """Get all images for a part"""
        data = await self.lookup_part(part_number)
        return data.get("images", [])
    
    async def get_compatible_models(self, part_number: str) -> List[str]:
        """Get compatible appliance models"""
        url = f"{self.base_url}/parts/{part_number}/models"
        # Implementation...
```

---

### 1.2 Marcone API

**Base URL**: `https://api.marcone.com/v2`  
**Authentication**: OAuth 2.0  
**Rate Limit**: 50 requests/minute  

#### Authentication Flow

```python
# OAuth 2.0 Token Request
POST /oauth/token
Content-Type: application/x-www-form-urlencoded

grant_type=client_credentials
&client_id={CLIENT_ID}
&client_secret={CLIENT_SECRET}

Response 200:
{
  "access_token": "eyJhbGc...",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

#### Endpoints

```python
# Part Search
GET /parts/search?q={part_number}
Headers:
  Authorization: Bearer {ACCESS_TOKEN}

Response 200:
{
  "results": [{
    "partNumber": "WR55X10025",
    "description": "Sensor, Defrost",
    "manufacturer": "GE",
    "pricing": {...},
    "availability": "In Stock",
    "specifications": {...}
  }],
  "total": 1
}

# Part Details
GET /parts/{part_id}

# Cross-References
GET /parts/{part_id}/cross-references
```

#### Implementation

```python
class MarconeAPIClient:
    def __init__(self, client_id: str, client_secret: str, base_url: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = base_url
        self.access_token = None
        self.token_expires_at = None
        self.session = aiohttp.ClientSession()
    
    async def authenticate(self):
        """Obtain OAuth 2.0 access token"""
        url = f"{self.base_url}/oauth/token"
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        
        async with self.session.post(url, data=data) as response:
            response.raise_for_status()
            token_data = await response.json()
            self.access_token = token_data["access_token"]
            self.token_expires_at = datetime.now() + timedelta(
                seconds=token_data["expires_in"] - 60  # Refresh 1 min early
            )
    
    async def ensure_authenticated(self):
        """Ensure we have a valid access token"""
        if not self.access_token or datetime.now() >= self.token_expires_at:
            await self.authenticate()
    
    async def lookup_part(self, part_number: str) -> Dict:
        """Search for part"""
        await self.ensure_authenticated()
        
        url = f"{self.base_url}/parts/search"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        params = {"q": part_number}
        
        async with self.session.get(url, headers=headers, params=params, timeout=30) as response:
            if response.status == 429:
                raise RateLimitError("Marcone rate limit exceeded")
            response.raise_for_status()
            data = await response.json()
            
            if data.get("total", 0) == 0:
                return {"found": False, "message": "Part not found"}
            
            return data["results"][0] if data.get("results") else {}
```

---

### 1.3 Reliable Parts API

**Base URL**: `https://api.reliableparts.com/v1`  
**Authentication**: API Key + Secret (HMAC)  
**Rate Limit**: 75 requests/minute  

#### Authentication

```python
# HMAC Signature
import hmac
import hashlib
import time

def generate_signature(api_secret: str, method: str, path: str, timestamp: str) -> str:
    """Generate HMAC signature for authentication"""
    message = f"{method}:{path}:{timestamp}"
    signature = hmac.new(
        api_secret.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()
    return signature

# Request Headers
Headers:
  X-API-Key: {API_KEY}
  X-Timestamp: {UNIX_TIMESTAMP}
  X-Signature: {HMAC_SIGNATURE}
```

#### Endpoints

```python
# Part Lookup
GET /parts/{part_number}

Response 200:
{
  "mpn": "WR55X10025",
  "brand": "GE",
  "title": "Refrigerator Defrost Sensor",
  "description": "...",
  "images": [...],
  "pricing": {...},
  "dimensions": {...},
  "weight": 0.38,
  "specifications": {...},
  "installationGuide": "https://..."
}

# Part Images
GET /parts/{part_number}/images

# Installation Guides
GET /parts/{part_number}/installation
```

#### Implementation

```python
class ReliablePartsAPIClient:
    def __init__(self, api_key: str, api_secret: str, base_url: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url
        self.session = aiohttp.ClientSession()
    
    def _generate_signature(self, method: str, path: str, timestamp: str) -> str:
        """Generate HMAC signature"""
        message = f"{method}:{path}:{timestamp}"
        signature = hmac.new(
            self.api_secret.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def _get_auth_headers(self, method: str, path: str) -> Dict[str, str]:
        """Generate authentication headers"""
        timestamp = str(int(time.time()))
        signature = self._generate_signature(method, path, timestamp)
        
        return {
            "X-API-Key": self.api_key,
            "X-Timestamp": timestamp,
            "X-Signature": signature,
            "Content-Type": "application/json"
        }
    
    async def lookup_part(self, part_number: str) -> Dict:
        """Lookup part by number"""
        path = f"/parts/{part_number}"
        url = f"{self.base_url}{path}"
        headers = self._get_auth_headers("GET", path)
        
        try:
            async with self.session.get(url, headers=headers, timeout=30) as response:
                if response.status == 429:
                    raise RateLimitError("Reliable Parts rate limit exceeded")
                if response.status == 404:
                    return {"found": False, "message": "Part not found"}
                response.raise_for_status()
                return await response.json()
        except Exception as e:
            raise ReliablePartsAPIError(f"API call failed: {str(e)}")
```

---

### 1.4 Amazon Product Advertising API

**Base URL**: `https://webservices.amazon.com/paapi5`  
**Authentication**: AWS Signature Version 4  
**Rate Limit**: 1 request/second (base tier)  

#### Authentication (AWS Signature V4)

```python
import hmac
import hashlib
from datetime import datetime
from urllib.parse import quote

class AWSSignatureV4:
    def __init__(self, access_key: str, secret_key: str, region: str):
        self.access_key = access_key
        self.secret_key = secret_key
        self.region = region
        self.service = "ProductAdvertisingAPI"
    
    def sign(self, method: str, url: str, headers: Dict, payload: str) -> Dict:
        """Generate AWS Signature V4"""
        # Implementation of AWS Signature V4 algorithm
        # (Full implementation omitted for brevity - use boto3 or aws-requests-auth)
        pass
```

#### Endpoints

```python
# Search Items
POST /paapi5/searchitems
Content-Type: application/json
X-Amz-Target: com.amazon.paapi5.v1.ProductAdvertisingAPIv1.SearchItems

{
  "PartnerTag": "{PARTNER_TAG}",
  "PartnerType": "Associates",
  "Keywords": "WR55X10025",
  "SearchIndex": "All",
  "Resources": [
    "Images.Primary.Large",
    "ItemInfo.Title",
    "ItemInfo.Features",
    "Offers.Listings.Price"
  ]
}

Response 200:
{
  "SearchResult": {
    "Items": [{
      "ASIN": "B00ABC123",
      "DetailPageURL": "https://amazon.com/...",
      "Images": {...},
      "ItemInfo": {...},
      "Offers": {...}
    }]
  }
}

# Get Items
POST /paapi5/getitems
```

#### Implementation

```python
from amazon_paapi import AmazonAPI

class AmazonAPIClient:
    def __init__(self, access_key: str, secret_key: str, partner_tag: str, region: str = "us-east-1"):
        self.api = AmazonAPI(
            access_key=access_key,
            secret_key=secret_key,
            partner_tag=partner_tag,
            country=region
        )
        self.rate_limiter = AsyncRateLimiter(1, 1)  # 1 request per second
    
    async def lookup_part(self, part_number: str) -> Dict:
        """Search for part on Amazon"""
        await self.rate_limiter.acquire()
        
        try:
            # Search by keyword
            result = self.api.search_items(
                keywords=part_number,
                search_index="All",
                resources=[
                    "Images.Primary.Large",
                    "Images.Variants.Large",
                    "ItemInfo.Title",
                    "ItemInfo.Features",
                    "ItemInfo.TechnicalInfo",
                    "Offers.Listings.Price",
                    "CustomerReviews.StarRating"
                ]
            )
            
            if not result or not result.items:
                return {"found": False, "message": "Part not found"}
            
            # Return first matching item
            item = result.items[0]
            return {
                "found": True,
                "asin": item.asin,
                "title": item.item_info.title.display_value,
                "url": item.detail_page_url,
                "images": self._extract_images(item),
                "price": self._extract_price(item),
                "rating": self._extract_rating(item),
                "features": self._extract_features(item)
            }
        except Exception as e:
            raise AmazonAPIError(f"Amazon API call failed: {str(e)}")
    
    def _extract_images(self, item) -> List[str]:
        """Extract image URLs"""
        images = []
        if item.images and item.images.primary:
            images.append(item.images.primary.large.url)
        if item.images and item.images.variants:
            images.extend([v.large.url for v in item.images.variants])
        return images
```

---

## 2. Internal API Endpoints

### 2.1 Lookup Service API

**Base URL**: `https://api.partscatalog.company.com/v1`  
**Authentication**: Bearer Token / API Key  

#### POST /lookup

Initiate a new part lookup.

```http
POST /v1/lookup
Authorization: Bearer {TOKEN}
Content-Type: application/json

{
  "part_number": "WR55X10025",
  "force_refresh": false,
  "priority": "normal",
  "source_filter": ["encompass", "marcone"],
  "callback_url": "https://callback.example.com/webhook"
}

Response 202 Accepted:
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "part_number": "WR55X10025",
  "status": "pending",
  "estimated_completion_seconds": 30,
  "status_url": "/v1/lookup/550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2025-12-12T10:30:00Z"
}

Response 400 Bad Request:
{
  "error": "invalid_part_number",
  "message": "Part number must be 1-100 characters",
  "field": "part_number"
}
```

#### GET /lookup/{session_id}

Get status of a lookup session.

```http
GET /v1/lookup/550e8400-e29b-41d4-a716-446655440000
Authorization: Bearer {TOKEN}

Response 200:
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "part_number": "WR55X10025",
  "status": "completed",
  "progress": {
    "encompass": "completed",
    "marcone": "completed",
    "reliable": "completed",
    "amazon": "completed"
  },
  "processing_time_seconds": 23.5,
  "catalog_record_id": "770e8400-e29b-41d4-a716-446655440000",
  "data_confidence_score": 0.91,
  "created_at": "2025-12-12T10:30:00Z",
  "completed_at": "2025-12-12T10:30:23Z"
}
```

#### GET /lookup/{session_id}/raw

Get raw API responses for a session.

```http
GET /v1/lookup/550e8400-e29b-41d4-a716-446655440000/raw
Authorization: Bearer {TOKEN}

Response 200:
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "sources": {
    "encompass": {
      "response_id": "660e8400-e29b-41d4-a716-446655440000",
      "status": "success",
      "response_time_ms": 1250,
      "data_completeness": 0.85,
      "raw_response": {...}
    },
    "marcone": {...},
    "reliable": {...},
    "amazon": {...}
  }
}
```

---

### 2.2 Catalog API

#### GET /catalog/{catalog_id}

Get a catalog record by ID.

```http
GET /v1/catalog/770e8400-e29b-41d4-a716-446655440000
Authorization: Bearer {TOKEN}

Response 200:
{
  "catalog_id": "770e8400-e29b-41d4-a716-446655440000",
  "mpn": "WR55X10025",
  "manufacturer": "GE",
  "part_type": "oem",
  "part_title": "GE WR55X10025 Refrigerator Defrost Sensor",
  "long_description": "...",
  "primary_department": "Refrigeration",
  "primary_category": "Defrost System",
  "images": {
    "primary": "https://cdn.example.com/images/...",
    "gallery": [...]
  },
  "pricing": {
    "msrp": 48.99,
    "high_avg": 45.00,
    "low_avg": 20.00,
    "current": 23.95
  },
  "specifications": {...},
  "compatible_models": [...],
  "data_confidence_score": 0.91,
  "last_updated": "2025-12-12T10:30:23Z"
}
```

#### GET /catalog/search

Search catalog.

```http
GET /v1/catalog/search?q=defrost+sensor&manufacturer=GE&limit=20&offset=0
Authorization: Bearer {TOKEN}

Response 200:
{
  "results": [{...}, {...}],
  "total": 42,
  "limit": 20,
  "offset": 0,
  "query": "defrost sensor"
}
```

#### GET /catalog/by-part/{part_number}

Lookup catalog by part number.

```http
GET /v1/catalog/by-part/WR55X10025
Authorization: Bearer {TOKEN}

Response 200:
{
  "catalog_id": "770e8400-e29b-41d4-a716-446655440000",
  "mpn": "WR55X10025",
  ...
}

Response 404:
{
  "error": "not_found",
  "message": "No catalog record found for part number WR55X10025",
  "suggestion": "Try using POST /v1/lookup to create a new record"
}
```

#### POST /catalog/{catalog_id}/refresh

Trigger refresh of catalog record.

```http
POST /v1/catalog/770e8400-e29b-41d4-a716-446655440000/refresh
Authorization: Bearer {TOKEN}

Response 202 Accepted:
{
  "catalog_id": "770e8400-e29b-41d4-a716-446655440000",
  "lookup_session_id": "880e8400-e29b-41d4-a716-446655440000",
  "status": "pending"
}
```

---

### 2.3 Validation API

#### GET /validation/{validation_id}

Get AI validation details.

```http
GET /v1/validation/880e8400-e29b-41d4-a716-446655440000
Authorization: Bearer {TOKEN}

Response 200:
{
  "validation_id": "880e8400-e29b-41d4-a716-446655440000",
  "catalog_id": "770e8400-e29b-41d4-a716-446655440000",
  "ai_agreement_score": 0.89,
  "openai": {
    "model": "gpt-4-turbo",
    "confidence_scores": {...},
    "conflicts_found": [...]
  },
  "grok": {
    "model": "grok-1",
    "confidence_scores": {...},
    "conflicts_found": [...]
  },
  "consensus": {
    "conflicts": [...],
    "resolutions": [...]
  },
  "total_cost": 0.12,
  "processing_time_seconds": 8.3
}
```

---

## 3. Salesforce Integration API

### 3.1 Authentication

**OAuth 2.0 Client Credentials Flow**

```http
POST /v1/auth/token
Content-Type: application/x-www-form-urlencoded

grant_type=client_credentials
&client_id={SALESFORCE_CLIENT_ID}
&client_secret={SALESFORCE_CLIENT_SECRET}
&scope=catalog:read catalog:write

Response 200:
{
  "access_token": "eyJhbGc...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "scope": "catalog:read catalog:write"
}
```

### 3.2 Catalog Endpoints for Salesforce

#### GET /sf/v1/catalog/lookup/{part_number}

Optimized endpoint for Salesforce part lookups.

```http
GET /sf/v1/catalog/lookup/WR55X10025
Authorization: Bearer {SALESFORCE_TOKEN}

Response 200:
{
  "part_number": "WR55X10025",
  "catalog_id": "770e8400-e29b-41d4-a716-446655440000",
  "manufacturer": "GE",
  "title": "GE WR55X10025 Refrigerator Defrost Sensor",
  "description": "...",
  "part_type": "oem",
  "department": "Refrigeration",
  "category": "Defrost System",
  "primary_image": "https://cdn.example.com/...",
  "gallery_images": [...],
  "pricing": {
    "msrp": 48.99,
    "current": 23.95
  },
  "weight_lbs": 0.38,
  "dimensions": {
    "box": {"length": 10, "width": 8, "height": 5},
    "product": {"length": 7, "width": 5, "height": 3}
  },
  "upc": "075835602345",
  "compatible_models": [...],
  "specifications": {...},
  "confidence_score": 0.91,
  "last_updated": "2025-12-12T10:30:23Z"
}
```

#### GET /sf/v1/catalog/batch

Batch lookup for multiple parts.

```http
GET /sf/v1/catalog/batch?part_numbers=WR55X10025,W10295370A,AP3185409
Authorization: Bearer {SALESFORCE_TOKEN}

Response 200:
{
  "results": [
    {
      "part_number": "WR55X10025",
      "status": "found",
      "data": {...}
    },
    {
      "part_number": "W10295370A",
      "status": "found",
      "data": {...}
    },
    {
      "part_number": "AP3185409",
      "status": "not_found",
      "message": "No catalog record exists"
    }
  ],
  "total_requested": 3,
  "total_found": 2
}
```

#### POST /sf/v1/catalog/request-lookup

Request new lookup (async).

```http
POST /sf/v1/catalog/request-lookup
Authorization: Bearer {SALESFORCE_TOKEN}
Content-Type: application/json

{
  "part_numbers": ["WR55X10025", "W10295370A"],
  "priority": "high",
  "callback_url": "https://salesforce.example.com/webhook"
}

Response 202 Accepted:
{
  "request_id": "990e8400-e29b-41d4-a716-446655440000",
  "part_numbers": ["WR55X10025", "W10295370A"],
  "status": "pending",
  "estimated_completion_seconds": 60
}
```

---

## 4. AI Service Integration

### 4.1 OpenAI Integration

```python
class OpenAIValidator:
    def __init__(self, api_key: str, model: str = "gpt-4-turbo"):
        self.client = OpenAI(api_key=api_key)
        self.model = model
    
    async def validate_part_data(
        self,
        part_number: str,
        source_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate part data from multiple sources
        
        Args:
            part_number: The part number
            source_data: Dict with keys: encompass, marcone, reliable, amazon
            
        Returns:
            Validation results with confidence scores
        """
        prompt = self._build_validation_prompt(part_number, source_data)
        
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a parts catalog expert..."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.2,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        
        return {
            "validation_result": result,
            "model": self.model,
            "tokens_used": response.usage.total_tokens,
            "cost": self._calculate_cost(response.usage)
        }
    
    async def generate_content(
        self,
        part_data: Dict[str, Any]
    ) -> Dict[str, str]:
        """Generate SEO-optimized title and description"""
        prompt = self._build_content_prompt(part_data)
        
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are an SEO and marketing expert..."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        
        return {
            "title": result["title"],
            "description": result["description"],
            "tokens_used": response.usage.total_tokens,
            "cost": self._calculate_cost(response.usage)
        }
```

### 4.2 Grok Integration

```python
class GrokValidator:
    def __init__(self, api_key: str, model: str = "grok-1"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.x.ai/v1"
    
    async def validate_part_data(
        self,
        part_number: str,
        source_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate part data using Grok
        """
        prompt = self._build_validation_prompt(part_number, source_data)
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a parts catalog expert..."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.2
                }
            ) as response:
                response.raise_for_status()
                data = await response.json()
                
                result = json.loads(data["choices"][0]["message"]["content"])
                
                return {
                    "validation_result": result,
                    "model": self.model,
                    "tokens_used": data["usage"]["total_tokens"],
                    "cost": self._calculate_cost(data["usage"])
                }
```

---

## 5. Authentication & Authorization

### 5.1 API Key Authentication

```python
from fastapi import Security, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def verify_api_key(credentials: HTTPAuthorizationCredentials = Security(security)):
    """Verify API key from Bearer token"""
    api_key = credentials.credentials
    
    # Hash the provided key
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    
    # Look up in database
    db_key = await db.api_keys.find_one({"key_hash": key_hash, "is_active": True})
    
    if not db_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    # Check expiration
    if db_key.get("expires_at") and datetime.now() > db_key["expires_at"]:
        raise HTTPException(status_code=401, detail="API key expired")
    
    # Update last used
    await db.api_keys.update_one(
        {"key_id": db_key["key_id"]},
        {
            "$set": {"last_used_at": datetime.now()},
            "$inc": {"total_requests": 1}
        }
    )
    
    return db_key

# Usage in endpoints
@app.get("/v1/catalog/{catalog_id}")
async def get_catalog(catalog_id: str, api_key=Depends(verify_api_key)):
    # Access granted
    pass
```

### 5.2 OAuth 2.0 for Salesforce

```python
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/v1/auth/token")

async def verify_oauth_token(token: str = Depends(oauth2_scheme)):
    """Verify OAuth 2.0 token"""
    try:
        # Decode JWT token
        payload = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=["HS256"]
        )
        
        client_id = payload.get("client_id")
        scopes = payload.get("scopes", [])
        expires_at = payload.get("exp")
        
        if datetime.fromtimestamp(expires_at) < datetime.now():
            raise HTTPException(status_code=401, detail="Token expired")
        
        return {
            "client_id": client_id,
            "scopes": scopes
        }
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Usage
@app.get("/sf/v1/catalog/lookup/{part_number}")
async def sf_catalog_lookup(part_number: str, auth=Depends(verify_oauth_token)):
    # Check scopes
    if "catalog:read" not in auth["scopes"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    pass
```

---

## 6. Rate Limiting

### 6.1 Implementation

```python
from fastapi import Request
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Per-endpoint rate limits
@app.get("/v1/catalog/search")
@limiter.limit("100/hour")
async def search_catalog(request: Request, q: str):
    pass

@app.post("/v1/lookup")
@limiter.limit("50/hour")
async def create_lookup(request: Request, data: LookupRequest):
    pass

# Salesforce endpoints (higher limits)
@app.get("/sf/v1/catalog/lookup/{part_number}")
@limiter.limit("1000/hour")
async def sf_lookup(request: Request, part_number: str):
    pass
```

### 6.2 Rate Limit Headers

```http
HTTP/1.1 200 OK
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 987
X-RateLimit-Reset: 1702388400
```

### 6.3 Rate Limit Exceeded Response

```http
HTTP/1.1 429 Too Many Requests
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1702388400
Retry-After: 3600

{
  "error": "rate_limit_exceeded",
  "message": "Rate limit of 1000 requests per hour exceeded",
  "retry_after_seconds": 3600,
  "reset_at": "2025-12-12T12:00:00Z"
}
```

---

## 7. Error Handling

### 7.1 Standard Error Response Format

```json
{
  "error": "error_code",
  "message": "Human-readable error message",
  "details": {
    "field": "part_number",
    "provided": "123",
    "expected": "Valid part number 1-100 characters"
  },
  "request_id": "req_abc123",
  "timestamp": "2025-12-12T10:30:00Z"
}
```

### 7.2 Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `invalid_request` | 400 | Malformed request |
| `invalid_part_number` | 400 | Part number format invalid |
| `unauthorized` | 401 | Missing/invalid authentication |
| `forbidden` | 403 | Insufficient permissions |
| `not_found` | 404 | Resource not found |
| `rate_limit_exceeded` | 429 | Too many requests |
| `internal_error` | 500 | Server error |
| `service_unavailable` | 503 | Service temporarily down |
| `api_error` | 502 | External API failure |

---

## 8. Webhooks

### 8.1 Webhook Registration

```http
POST /v1/webhooks
Authorization: Bearer {TOKEN}
Content-Type: application/json

{
  "url": "https://salesforce.example.com/webhook",
  "events": ["catalog.created", "catalog.updated", "lookup.completed"],
  "secret": "webhook_secret_key"
}

Response 201 Created:
{
  "webhook_id": "whk_abc123",
  "url": "https://salesforce.example.com/webhook",
  "events": ["catalog.created", "catalog.updated", "lookup.completed"],
  "is_active": true,
  "created_at": "2025-12-12T10:30:00Z"
}
```

### 8.2 Webhook Payload

```http
POST https://salesforce.example.com/webhook
Content-Type: application/json
X-Webhook-Signature: sha256=abc123...
X-Webhook-ID: whk_abc123
X-Event-Type: catalog.created

{
  "event": "catalog.created",
  "timestamp": "2025-12-12T10:30:23Z",
  "data": {
    "catalog_id": "770e8400-e29b-41d4-a716-446655440000",
    "part_number": "WR55X10025",
    "manufacturer": "GE",
    "confidence_score": 0.91
  }
}
```

### 8.3 Webhook Signature Verification

```python
import hmac
import hashlib

def verify_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
    """Verify webhook signature"""
    expected_signature = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(f"sha256={expected_signature}", signature)
```

---

**Document Version**: 1.0  
**Last Updated**: December 12, 2025  
**Status**: Ready for Implementation
