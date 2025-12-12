"""
Encompass API Client for Parts Information
Based on the Salesforce implementation
"""
import logging
import requests
from typing import Dict, Any, Optional, List
from .encompass_config import config

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EncompassAPIClient:
    """Client for interacting with Encompass REST API"""
    
    # Program names from Salesforce implementation
    PARTS_INFORMATION_PROGRAM = 'JSON.ITEM.INFORMATION'
    MODEL_PART_LIST_PROGRAM = 'JSON.MODEL.INFORMATION'
    
    # API endpoints
    PARTS_INFORMATION_PATH = '/restfulservice/partsInformation'
    MODEL_PART_LIST_PATH = '/restfulservice/modelPartList'
    MODEL_SEARCH_PATH = '/restfulservice/search'
    
    # Make code mappings from Salesforce
    MAKE_MAPPING = {
        'BSH': 'BCH',
        'SAM': 'SMG',
        'F-P': 'FAP',
        'WCI': 'FRI',
        'GEH': 'HOT',
        'L-G': 'ZEN',
        'SPE': 'SPQ',
        'WPL': 'WHI'
    }
    
    def __init__(self, base_url: str = None, username: str = None, password: str = None):
        """
        Initialize Encompass API client
        
        Args:
            base_url: Base URL for Encompass API (default from config)
            username: API username (default from config)
            password: API password (default from config)
        """
        self.base_url = base_url or config.base_url
        self.username = username or config.username
        self.password = password or config.password
        self.timeout = config.timeout
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        
    def _call_api(self, method: str, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make API call to Encompass
        
        Args:
            method: HTTP method (POST)
            path: API endpoint path
            payload: Request payload
            
        Returns:
            Response data as dictionary
        """
        url = f"{self.base_url}{path}"
        
        try:
            logger.info(f"Calling Encompass API: {method} {url}")
            logger.debug(f"Payload: {payload}")
            
            response = self.session.request(
                method=method,
                url=url,
                json=payload,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            
            logger.info(f"Response status: {response.status_code}")
            logger.debug(f"Response body: {response.text}")
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API call failed: {str(e)}")
            if hasattr(e.response, 'text'):
                logger.error(f"Response: {e.response.text}")
            raise
    
    def get_part_info(self, part_number: str, make: Optional[str] = None) -> Dict[str, Any]:
        """
        Get part information from Encompass
        
        Args:
            part_number: Part number to search for
            make: Optional make code (will be mapped if needed)
            
        Returns:
            Standardized response with success, data, and message fields
        """
        # Map make code if provided and mapping exists
        mfg_code = self.MAKE_MAPPING.get(make) if make else None
        
        payload = {
            "settings": {
                "jsonUser": self.username,
                "jsonPassword": self.password,
                "programName": self.PARTS_INFORMATION_PROGRAM
            },
            "data": {
                "searchPartNumber": part_number
            }
        }
        
        # Add manufacturer code if available
        if mfg_code:
            payload["data"]["searchMfgCode"] = mfg_code
        
        try:
            response = self._call_api('POST', self.PARTS_INFORMATION_PATH, payload)
            
            # Check if response has the expected structure
            if response.get('status', {}).get('errorCode') == '100':
                parts = response.get('data', {}).get('parts', [])
                
                # Filter for exact part number match only
                exact_matches = [
                    part for part in parts 
                    if part.get('partNumber', '').upper() == part_number.upper()
                ]
                
                logger.info(f"Total parts from API: {len(parts)}, Exact matches: {len(exact_matches)}")
                
                return {
                    'success': True,
                    'data': exact_matches,
                    'message': f'Found {len(exact_matches)} exact match(es)'
                }
            else:
                error_msg = response.get('status', {}).get('errorMessage', 'Unknown error')
                return {
                    'success': False,
                    'data': [],
                    'message': error_msg
                }
        except Exception as e:
            return {
                'success': False,
                'data': [],
                'message': str(e)
            }
    
    def search_model(self, model_number: str) -> Dict[str, Any]:
        """
        Search for a model to get its ID
        
        Args:
            model_number: Model number to search for
            
        Returns:
            Model search response with model ID
        """
        payload = {
            "settings": {
                "jsonUser": self.username,
                "jsonPassword": self.password
            },
            "data": {
                "searchTerm": model_number
            }
        }
        
        return self._call_api('POST', self.MODEL_SEARCH_PATH, payload)
    
    def get_model_part_list(self, model_id: str, make: Optional[str] = None) -> Dict[str, Any]:
        """
        Get list of parts for a specific model
        
        Args:
            model_id: Model ID from search_model
            make: Optional make code
            
        Returns:
            Model part list response
        """
        # Map make code if provided and mapping exists
        mfg_code = self.MAKE_MAPPING.get(make) if make else None
        
        payload = {
            "settings": {
                "jsonUser": self.username,
                "jsonPassword": self.password,
                "programName": self.MODEL_PART_LIST_PROGRAM
            },
            "data": {
                "modelID": model_id
            }
        }
        
        # Add manufacturer code if available
        if mfg_code:
            payload["data"]["searchMfgCode"] = mfg_code
        
        return self._call_api('POST', self.MODEL_PART_LIST_PATH, payload)
    
    def test_connection(self) -> bool:
        """
        Test the API connection with a simple part lookup
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            # Try a simple part search (use a common test part number)
            logger.info("Testing Encompass API connection...")
            response = self.get_part_info("WR55X10025", "GEH")
            
            # Check for success response - status.errorMessage should be "SUCCESS"
            status = response.get('status', {})
            if status.get('errorMessage') == 'SUCCESS':
                logger.info("✓ Encompass API connection successful!")
                
                # Show some data from the response
                parts = response.get('data', {}).get('parts', [])
                if parts:
                    logger.info(f"  Found {len(parts)} part(s) in test response")
                    logger.info(f"  Test part: {parts[0].get('partNumber')} - {parts[0].get('partDescription')}")
                
                return True
            else:
                logger.warning(f"⚠ Encompass API returned: {status.get('errorMessage')}")
                return False
                
        except Exception as e:
            logger.error(f"✗ Encompass API connection failed: {str(e)}")
            return False


def create_encompass_client(base_url: str = None, username: str = None, password: str = None) -> EncompassAPIClient:
    """
    Factory function to create an Encompass API client
    
    Args:
        base_url: Base URL for Encompass API (default from config)
        username: API username (default from config)
        password: API password (default from config)
        
    Returns:
        Configured EncompassAPIClient instance
    """
    return EncompassAPIClient(base_url, username, password)
