"""
Reliable Parts API Client
Developer Portal: https://stgapi.reliableparts.net:9443
"""
import logging
import requests
from typing import Dict, Any, Optional, List
from requests.auth import HTTPBasicAuth
from .reliable_parts_config import config

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ReliablePartsAPIClient:
    """Client for interacting with Reliable Parts API"""
    
    def __init__(self, base_url: str = None, username: str = None, password: str = None):
        """
        Initialize Reliable Parts API client
        
        Args:
            base_url: Base URL for Reliable Parts API (default from config)
            username: API username (default from config)
            password: API password (default from config)
        """
        self.base_url = base_url or config.base_url
        self.username = username or config.username
        self.password = password or config.password
        self.timeout = config.timeout
        
        # Store API keys from config
        self.part_search_api_key = config.part_search_api_key
        self.model_search_api_key = config.model_search_api_key
        self.model_to_part_api_key = config.model_to_part_api_key
        
        # Create session with Basic Authentication
        self.session = requests.Session()
        self.session.auth = HTTPBasicAuth(self.username, self.password)
        
        # Set default headers (API Key will be added per-request)
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        
        # Disable SSL verification for test/dev environment
        self.session.verify = False
        
        # Suppress SSL warnings for test environment
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
    def _call_api(self, method: str, endpoint: str, api_key: str = None, **kwargs) -> Dict[str, Any]:
        """
        Make API call to Reliable Parts
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            api_key: API Key for this specific request
            **kwargs: Additional arguments for requests
            
        Returns:
            Response data as dictionary
        """
        url = f"{self.base_url}{endpoint}"
        
        # Add API key to headers for this request
        headers = kwargs.pop('headers', {})
        if api_key:
            headers['X-API-Key'] = api_key
        
        try:
            logger.info(f"Calling Reliable Parts API: {method} {url}")
            
            response = self.session.request(
                method=method,
                url=url,
                headers=headers,
                timeout=self.timeout,
                **kwargs
            )
            
            response.raise_for_status()
            
            logger.info(f"Response status: {response.status_code}")
            
            # Try to parse JSON response
            try:
                return response.json()
            except ValueError:
                return {"raw_response": response.text}
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API call failed: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response: {e.response.text}")
            raise
    
    def test_connection(self) -> bool:
        """
        Test the API connection
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            logger.info("Testing Reliable Parts API connection...")
            
            # Try to access the main portal/API endpoint
            response = self.session.get(
                self.base_url,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                logger.info("✓ Reliable Parts API is accessible!")
                logger.info(f"  Base URL: {self.base_url}")
                logger.info(f"  Username: {self.username}")
                logger.info(f"  Part Search API Key: {'Configured' if self.part_search_api_key else 'Missing'}")
                logger.info(f"  Model Search API Key: {'Configured' if self.model_search_api_key else 'Missing'}")
                logger.info(f"  Model To Part API Key: {'Configured' if self.model_to_part_api_key else 'Missing'}")
                return True
            else:
                logger.warning(f"⚠ Portal returned status: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"✗ Reliable Parts API connection failed: {str(e)}")
            return False
    
    def search_part(self, part_number: str, zip_code: str = None, quantity: str = None, warehouse: str = None) -> Dict[str, Any]:
        """
        Search for part using Part Search v2.0 API
        
        Args:
            part_number: Part number to search for
            zip_code: Optional ZIP code for geo-location based search
            quantity: Optional quantity
            warehouse: Optional warehouse ID
            
        Returns:
            Part information including availability, pricing, and thumbnail
        """
        # Part Search v2.0 endpoint - POST with JSON body
        endpoint = '/ws/rest/ReliablePartsBoomiAPI/partSearch/v2/query'
        
        # Build request body
        body = {
            'partNumber': part_number
        }
        
        if zip_code:
            body['postalCode'] = zip_code
        if quantity:
            body['quantity'] = str(quantity)
        if warehouse:
            body['warehouse'] = warehouse
        
        return self._call_api(
            'POST',
            endpoint,
            api_key=self.part_search_api_key,
            json=body
        )
    
    # Alias for backward compatibility
    def get_part_info(self, part_number: str, zip_code: str = None) -> Dict[str, Any]:
        """
        Get part information (alias for search_part)
        
        Args:
            part_number: Part number to search for
            zip_code: Optional ZIP code for geo-location based search
            
        Returns:
            Part information response
        """
        return self.search_part(part_number, zip_code)
    
    def search_model(self, model_number: str) -> Dict[str, Any]:
        """
        Search for a model using Model Search v1.0 API
        
        Args:
            model_number: Model number to search for
            
        Returns:
            Model information including part count
        """
        endpoint = '/ModelSearch/modelnumber'
        
        return self._call_api(
            'GET',
            endpoint,
            api_key=self.model_search_api_key,
            params={'modelNumber': model_number}
        )
    
    def get_model_parts(self, model_number: str) -> Dict[str, Any]:
        """
        Get exploded view of model parts using Model To Part v1.0 API
        
        Args:
            model_number: Model number to get parts for
            
        Returns:
            List of parts for the model
        """
        endpoint = '/ModelToPart/modelnumber'
        
        return self._call_api(
            'GET',
            endpoint,
            api_key=self.model_to_part_api_key,
            params={'modelNumber': model_number}
        )


def create_reliable_parts_client(base_url: str = None, username: str = None, password: str = None) -> ReliablePartsAPIClient:
    """
    Factory function to create a Reliable Parts API client
    
    Args:
        base_url: Base URL for Reliable Parts API (default from config)
        username: API username (default from config)
        password: API password (default from config)
        
    Returns:
        Configured ReliablePartsAPIClient instance
    """
    return ReliablePartsAPIClient(base_url, username, password)
