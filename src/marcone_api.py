"""
Marcone API
Complete SOAP client for Marcone parts, orders, and returns
"""

from zeep import Client
from zeep.transports import Transport
from requests import Session
from requests.auth import HTTPBasicAuth
from zeep.helpers import serialize_object
import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MarconeSOAPClient:
    """Base class for Marcone SOAP API clients."""
    
    def __init__(self, wsdl_url: str, username: str, password: str):
        """Initialize SOAP client with authentication."""
        session = Session()
        session.auth = HTTPBasicAuth(username, password)
        transport = Transport(session=session)
        
        try:
            self.client = Client(wsdl_url, transport=transport)
            logger.info(f"✓ Connected to SOAP service: {wsdl_url}")
        except Exception as e:
            logger.error(f"✗ Failed to connect to SOAP service: {str(e)}")
            raise


class MarconePartService(MarconeSOAPClient):
    """Part Service v2 - Part lookups, pricing, inventory."""
    
    def __init__(self, base_url: str, username: str, password: str):
        wsdl_url = f"{base_url}/b2b/parts_v2.asmx?WSDL"
        super().__init__(wsdl_url, username, password)
        self.username = username
        self.password = password
    
    def exact_part_lookup(self, part_number: str, make: str):
        """
        Exact part lookup by make and part number.
        
        Args:
            part_number: Part number (e.g., "W10295370A")
            make: Manufacturer code (e.g., "WPL" for Whirlpool)
        
        Returns:
            List of PartInformation_v2 objects with full details
        """
        try:
            response = self.client.service.ExactPartLookup(
                userName=self.username,
                password=self.password,
                make=make,
                partNumber=part_number
            )
            
            if response and hasattr(response, 'PartInformation_v2'):
                parts = response.PartInformation_v2
                if parts:
                    logger.info(f"✓ Found part: {make} {part_number}")
                    return parts
            
            logger.warning(f"✗ Part not found: {make} {part_number}")
            return []
            
        except Exception as e:
            logger.error(f"✗ ExactPartLookup failed: {str(e)}")
            raise
    
    def part_lookup(self, part_number: str, make: str = ""):
        """
        Fuzzy part search (partial matching).
        
        Args:
            part_number: Full or partial part number
            make: Optional manufacturer code
        
        Returns:
            List of matching parts
        """
        try:
            response = self.client.service.PartLookup(
                userName=self.username,
                password=self.password,
                make=make,
                partnumber=part_number
            )
            
            if response and hasattr(response, 'PartInformation_v2'):
                return response.PartInformation_v2 or []
            return []
            
        except Exception as e:
            logger.error(f"✗ PartLookup failed: {str(e)}")
            raise
    
    def exact_part_lookup_by_customer(self, part_number: str, make: str, customer_number: int):
        """
        Exact part lookup with customer number (translates customer part numbers).
        
        Args:
            part_number: Customer's part number
            make: Manufacturer code
            customer_number: Your customer number
        
        Returns:
            List of matching parts with Marcone's internal part numbers
        """
        try:
            response = self.client.service.ExactPartLookupByCustomer(
                userName=self.username,
                password=self.password,
                make=make,
                partNumber=part_number,
                customerNumber=customer_number
            )
            
            if response and hasattr(response, 'PartInformation_v2'):
                parts = response.PartInformation_v2
                if parts:
                    logger.info(f"✓ Found part via customer lookup: {make} {part_number}")
                    return parts
            
            logger.warning(f"✗ Part not found via customer lookup: {make} {part_number}")
            return []
            
        except Exception as e:
            logger.error(f"✗ ExactPartLookupByCustomer failed: {str(e)}")
            raise
    
    def part_lookup_by_customer(self, part_number: str, customer_number: int, make: str = ""):
        """
        Fuzzy part search with customer number translation.
        
        Args:
            part_number: Customer's part number (full or partial)
            customer_number: Your customer number
            make: Optional manufacturer code
        
        Returns:
            List of matching parts
        """
        try:
            response = self.client.service.PartLookupByCustomer(
                username=self.username,
                password=self.password,
                make=make,
                partNumber=part_number,
                customerNumber=customer_number
            )
            
            if response and hasattr(response, 'PartInformation_v2'):
                return response.PartInformation_v2 or []
            return []
            
        except Exception as e:
            logger.error(f"✗ PartLookupByCustomer failed: {str(e)}")
            raise


class MarconeOrderService(MarconeSOAPClient):
    """Order Service v9 - Order placement and management."""
    
    def __init__(self, base_url: str, username: str, password: str):
        wsdl_url = f"{base_url}/b2b/orders_v9.asmx?WSDL"
        super().__init__(wsdl_url, username, password)
        self.username = username
        self.password = password
    
    def purchase_order(self, po_number: str, ship_to: dict, items: list, 
                      shipping_method_id: int = 15, bill_to: dict = None):
        """
        Place a purchase order.
        
        Args:
            po_number: Your PO number
            ship_to: Shipping address dict with Name, Address1, City, State, Zip
            items: List of item dicts with Make, PartNumber, Quantity
            shipping_method_id: Shipping method (15=UPS Ground, 2=Next Day, etc.)
            bill_to: Optional billing address (defaults to ship_to)
        
        Returns:
            Order response with OrderNumbers
        """
        try:
            # Create request object
            request = {
                'userName': self.username,
                'password': self.password,
                'PONumber': po_number,
                'ShipToAddress': ship_to,
                'BillToAddress': bill_to or ship_to,
                'ShippingMethodId': shipping_method_id,
                'Items': items
            }
            
            response = self.client.service.PurchaseOrder(**request)
            logger.info(f"✓ Order placed: {po_number}")
            return response
            
        except Exception as e:
            logger.error(f"✗ PurchaseOrder failed: {str(e)}")
            raise
    
    def get_order_by_po(self, po_number: str):
        """Get orders by PO number."""
        try:
            response = self.client.service.OSByPONumber(
                userName=self.username,
                password=self.password,
                PONumber=po_number
            )
            return response
        except Exception as e:
            logger.error(f"✗ Get order by PO failed: {str(e)}")
            raise
    
    def validate_address(self, address: dict):
        """
        Validate shipping address.
        
        Args:
            address: Dict with Address1, City, State, Zip
        
        Returns:
            Validated address or validation errors
        """
        try:
            request = {
                'userName': self.username,
                'password': self.password,
                'request': address
            }
            response = self.client.service.ValidateAddress(**request)
            return response
        except Exception as e:
            logger.error(f"✗ ValidateAddress failed: {str(e)}")
            raise


class MarconeREAService(MarconeSOAPClient):
    """REA Service - Returns authorization."""
    
    def __init__(self, base_url: str, username: str, password: str):
        wsdl_url = f"{base_url}/b2b/rea.asmx?WSDL"
        super().__init__(wsdl_url, username, password)
        self.username = username
        self.password = password
    
    def find_returnable_items(self, search_by: str, item_search: str):
        """
        Find items eligible for return.
        
        Args:
            search_by: Search type - "PO", "Part", or "InvoiceNumber"
            item_search: Search value (PO number, part number, or invoice)
        
        Returns:
            List of returnable items
        """
        try:
            request = {
                'userName': self.username,
                'password': self.password,
                'SearchBy': search_by,
                'ItemSearch': item_search
            }
            response = self.client.service.FindReturnableItems(**request)
            return response
        except Exception as e:
            logger.error(f"✗ FindReturnableItems failed: {str(e)}")
            raise


# ============================================================================
# FACTORY FUNCTIONS - Easy service creation
# ============================================================================

def create_part_service(environment: str = "prod") -> MarconePartService:
    """
    Create Part Service instance.
    
    Args:
        environment: "prod" or "test"
    
    Returns:
        MarconePartService instance
    """
    if environment == "test":
        base_url = os.getenv("MARCONE_TEST_URL")
        username = os.getenv("MARCONE_TEST_USERNAME")
        password = os.getenv("MARCONE_TEST_PASSWORD")
    else:
        base_url = os.getenv("MARCONE_PROD_URL")
        username = os.getenv("MARCONE_PROD_USERNAME")
        password = os.getenv("MARCONE_PROD_PASSWORD")
    
    return MarconePartService(base_url, username, password)


def create_order_service(environment: str = "prod") -> MarconeOrderService:
    """
    Create Order Service instance.
    
    Args:
        environment: "prod" or "test"
    
    Returns:
        MarconeOrderService instance
    """
    if environment == "test":
        base_url = os.getenv("MARCONE_TEST_URL")
        username = os.getenv("MARCONE_TEST_USERNAME")
        password = os.getenv("MARCONE_TEST_PASSWORD")
    else:
        base_url = os.getenv("MARCONE_PROD_URL")
        username = os.getenv("MARCONE_PROD_USERNAME")
        password = os.getenv("MARCONE_PROD_PASSWORD")
    
    return MarconeOrderService(base_url, username, password)


def create_rea_service(environment: str = "prod") -> MarconeREAService:
    """
    Create REA Service instance.
    
    Args:
        environment: "prod" or "test"
    
    Returns:
        MarconeREAService instance
    """
    if environment == "test":
        base_url = os.getenv("MARCONE_TEST_URL")
        username = os.getenv("MARCONE_TEST_USERNAME")
        password = os.getenv("MARCONE_TEST_PASSWORD")
    else:
        base_url = os.getenv("MARCONE_PROD_URL")
        username = os.getenv("MARCONE_PROD_USERNAME")
        password = os.getenv("MARCONE_PROD_PASSWORD")
    
    return MarconeREAService(base_url, username, password)


# ============================================================================
# COMMON MAKE CODES (for reference)
# ============================================================================

MAKE_CODES = {
    "WPL": "Whirlpool",
    "GE": "General Electric",
    "GEH": "General Electric (GE Hotpoint)",
    "MAY": "Maytag",
    "FRI": "Frigidaire",
    "KIT": "KitchenAid",
    "LG": "LG Electronics",
    "SAM": "Samsung",
    "BOC": "Bosch",
    "ELE": "Electrolux",
    "KEN": "Kenmore"
}


# ============================================================================
# SHIPPING METHOD IDs (for reference)
# ============================================================================

SHIPPING_METHODS = {
    2: "UPS Next Day Air",
    3: "UPS 2nd Day",
    15: "UPS Ground",
    20: "FedEx Ground"
}


if __name__ == "__main__":
    print("Marcone API module loaded successfully")
    print(f"Available make codes: {', '.join(MAKE_CODES.keys())}")
    print(f"Shipping methods: {list(SHIPPING_METHODS.keys())}")
