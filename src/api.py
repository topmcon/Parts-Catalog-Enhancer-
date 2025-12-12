"""
API Server for Parts Catalog Enhancement
FastAPI application for receiving and processing part data
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
from src.enhancer import PartEnhancer
from src.salesforce_client import SalesforceClient

app = FastAPI(
    title="Parts Catalog Enhancer API",
    description="AI-powered enhancement of appliance parts data",
    version="0.1.0"
)

# Initialize services
enhancer = PartEnhancer()
sf_client = None

try:
    sf_client = SalesforceClient()
except Exception as e:
    print(f"Warning: Salesforce client not initialized: {e}")


class PartData(BaseModel):
    """Input model for part data"""
    part_number: str
    part_name: Optional[str] = None
    description: Optional[str] = None
    model_numbers: Optional[str] = None
    price: Optional[float] = None
    category: Optional[str] = None


class EnhancedPartResponse(BaseModel):
    """Response model for enhanced part data"""
    original_data: Dict[str, Any]
    enhanced_data: Dict[str, Any]
    ai_provider: Optional[str] = None


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "online",
        "service": "Parts Catalog Enhancer",
        "version": "0.1.0"
    }


@app.post("/enhance", response_model=EnhancedPartResponse)
async def enhance_part(part: PartData):
    """
    Enhance part attributes with AI
    
    Send part data to be enhanced with customer-friendly descriptions
    """
    try:
        part_dict = part.model_dump()
        enhanced = enhancer.enhance_part_attributes(part_dict)
        
        return {
            "original_data": part_dict,
            "enhanced_data": enhanced,
            "ai_provider": "openai/grok"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Enhancement failed: {str(e)}")


@app.get("/part/{part_number}")
async def get_and_enhance_part(part_number: str):
    """
    Retrieve part from Salesforce and enhance it
    
    Fetches part data from Salesforce and returns enhanced version
    """
    if not sf_client:
        raise HTTPException(
            status_code=503,
            detail="Salesforce client not configured. Please set SALESFORCE_* environment variables."
        )
    
    try:
        # Get part from Salesforce
        part_data = sf_client.get_part_by_number(part_number)
        
        if not part_data:
            raise HTTPException(status_code=404, detail=f"Part {part_number} not found")
        
        # Enhance the part data
        enhanced = enhancer.enhance_part_attributes(part_data)
        
        return {
            "original_data": part_data,
            "enhanced_data": enhanced,
            "ai_provider": "openai/grok"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing part: {str(e)}")


@app.post("/enhance-and-update/{part_number}")
async def enhance_and_update_part(part_number: str):
    """
    Retrieve, enhance, and update part in Salesforce
    
    Full workflow: fetch from Salesforce, enhance with AI, update Salesforce
    """
    if not sf_client:
        raise HTTPException(
            status_code=503,
            detail="Salesforce client not configured"
        )
    
    try:
        # Get part from Salesforce
        part_data = sf_client.get_part_by_number(part_number)
        
        if not part_data:
            raise HTTPException(status_code=404, detail=f"Part {part_number} not found")
        
        # Enhance the part data
        enhanced = enhancer.enhance_part_attributes(part_data)
        
        # Update back to Salesforce
        success = sf_client.update_part_enhanced_data(part_data["id"], enhanced)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update Salesforce")
        
        return {
            "status": "success",
            "part_number": part_number,
            "original_data": part_data,
            "enhanced_data": enhanced
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
