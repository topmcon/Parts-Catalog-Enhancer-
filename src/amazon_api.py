"""
Amazon API Client
Client for Unwrangle Amazon APIs - Search, Product Detail, and Category Search
"""

import requests
import logging
from typing import Dict, Any, Optional, List
from urllib.parse import quote
from .amazon_config import AmazonConfig, get_amazon_config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AmazonAPIClient:
    """Client for Amazon Search, Detail, and Category APIs via Unwrangle."""
    
    # Supported countries
    SUPPORTED_COUNTRIES = [
        'us', 'uk', 'de', 'fr', 'es', 'it', 'ca', 'mx', 'br', 'jp', 'in', 'au'
    ]
    
    def __init__(self, config: Optional[AmazonConfig] = None):
        """
        Initialize Amazon API client.
        
        Args:
            config: Optional AmazonConfig instance. If not provided, will load from environment.
        """
        self.config = config or get_amazon_config()
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/json',
            'User-Agent': 'Parts-Catalog-Enhancer/1.0'
        })
    
    def _call_api(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make API call to Unwrangle Amazon API.
        
        Args:
            params: Query parameters for the API request
            
        Returns:
            API response as dictionary
        """
        try:
            logger.info(f"Calling Amazon API: {params.get('platform')} - {params.get('search', params.get('url', params.get('asin', 'N/A')))}")
            
            response = self.session.get(
                self.config.base_url,
                params=params,
                timeout=self.config.timeout
            )
            
            response.raise_for_status()
            
            logger.info(f"Response status: {response.status_code}")
            
            data = response.json()
            
            return {
                'success': True,
                'data': data,
                'message': 'Request successful'
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API call failed: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response: {e.response.text[:500]}")
            
            return {
                'success': False,
                'data': None,
                'message': str(e)
            }
    
    def search(self, 
               search_query: str, 
               page: int = 1, 
               country_code: Optional[str] = None) -> Dict[str, Any]:
        """
        Search for products on Amazon.
        
        Args:
            search_query: Search term (e.g., "toothpaste", "WR55X10025")
            page: Page number (default: 1)
            country_code: Country code (default: 'us'). Options: us, uk, de, fr, es, it, ca, mx, br, jp, in, au
            
        Returns:
            Search results with product listings
            
        Example:
            client.search("WR55X10025")
            client.search("refrigerator temperature sensor", page=2, country_code='us')
        """
        params = {
            'platform': self.config.search_platform,
            'search': search_query,
            'page': page,
            'api_key': self.config.api_key
        }
        
        # Add country code if specified
        if country_code:
            if country_code not in self.SUPPORTED_COUNTRIES:
                logger.warning(f"Country code '{country_code}' may not be supported. Supported: {', '.join(self.SUPPORTED_COUNTRIES)}")
            params['country_code'] = country_code
        else:
            params['country_code'] = self.config.default_country
        
        return self._call_api(params)
    
    def get_product_by_url(self, 
                           product_url: str, 
                           country_code: Optional[str] = None) -> Dict[str, Any]:
        """
        Get detailed product information by Amazon product URL.
        
        Args:
            product_url: Full Amazon product URL (will be URL encoded automatically)
            country_code: Country code (optional)
            
        Returns:
            Detailed product information including specs, pricing, reviews, etc.
            
        Example:
            client.get_product_by_url("https://www.amazon.com/Apple-iPhone-13-128GB-Blue/dp/B09LNX6KQS/")
        """
        params = {
            'platform': self.config.detail_platform,
            'url': quote(product_url, safe=''),
            'api_key': self.config.api_key
        }
        
        if country_code:
            params['country_code'] = country_code
        
        return self._call_api(params)
    
    def get_product_by_asin(self, 
                           asin: str, 
                           country_code: Optional[str] = None) -> Dict[str, Any]:
        """
        Get detailed product information by ASIN (Amazon Standard Identification Number).
        
        Args:
            asin: Product ASIN (e.g., "B09LNX6KQS")
            country_code: Country code (default: 'us')
            
        Returns:
            Detailed product information including specs, pricing, reviews, etc.
            
        Example:
            client.get_product_by_asin("B09LNX6KQS")
        """
        params = {
            'platform': self.config.detail_platform,
            'asin': asin,
            'country_code': country_code or self.config.default_country,
            'api_key': self.config.api_key
        }
        
        return self._call_api(params)
    
    def get_category_products(self, 
                             category_url: str, 
                             page: int = 1) -> Dict[str, Any]:
        """
        Scrape products from an Amazon category/department page.
        
        Args:
            category_url: Full Amazon category URL (will be URL encoded automatically)
                         Must be a page with product listings and pagination
            page: Page number (default: 1)
            
        Returns:
            List of products from the category page
            
        Example:
            url = "https://www.amazon.com/s?rh=n:565108&fs=true&ref=lp_565108_sar"
            client.get_category_products(url, page=1)
            
        Note:
            The URL must be from a page that has:
            1. A list of products
            2. Pagination at the bottom
            Any filters (price, brand, etc.) applied to the URL will be respected.
        """
        params = {
            'platform': self.config.category_platform,
            'url': quote(category_url, safe=''),
            'page': page,
            'api_key': self.config.api_key
        }
        
        return self._call_api(params)
    
    def search_part(self, part_number: str, **kwargs) -> Dict[str, Any]:
        """
        Search for a part by part number on Amazon.
        
        Args:
            part_number: Part number to search for
            **kwargs: Additional arguments to pass to search()
            
        Returns:
            Search results for the part with standardized format
            
        Example:
            client.search_part("WR55X10025")
        """
        result = self.search(part_number, **kwargs)
        
        # Standardize response format
        if result.get('success') and result.get('data'):
            data = result['data']
            
            # Extract and format products
            products = []
            for item in data.get('results', []):
                products.append(self._format_product(item))
            
            return {
                'success': True,
                'data': {
                    'products': products,
                    'total_results': data.get('result_count', len(products)),
                    'total_pages': data.get('no_of_pages', 1),
                    'current_page': data.get('page', 1),
                    'credits_used': data.get('credits_used', 0),
                    'remaining_credits': data.get('remaining_credits', 0)
                },
                'message': f"Found {len(products)} products"
            }
        
        return result
    
    def _format_product(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format product data with all available Amazon attributes.
        
        Args:
            item: Raw product data from Amazon API
            
        Returns:
            Formatted product dictionary with standardized fields
        """
        return {
            # Basic Info
            'name': item.get('name'),
            'brand': item.get('brand'),
            'asin': item.get('asin'),
            'url': item.get('url'),
            'listing_id': item.get('listing_id', item.get('asin')),
            
            # Pricing
            'price': item.get('price'),
            'price_reduced': item.get('price_reduced'),
            'price_per_unit': item.get('price_per_unit'),
            'currency': item.get('currency', 'USD'),
            'currency_symbol': item.get('currency_symbol', '$'),
            'typical_price': item.get('typical_price'),
            'deal_badge': item.get('deal_badge'),
            
            # Availability & Shipping
            'is_prime': item.get('is_prime', False),
            'shipping_info': item.get('shipping_info', []),
            'delivery_zipcode': item.get('delivery_zipcode'),
            'max_quantity': item.get('max_quantity'),
            
            # Ratings & Sales
            'rating': item.get('rating'),
            'total_ratings': item.get('total_ratings'),
            'past_month_sales': item.get('past_month_sales'),
            
            # Sellers
            'seller_name': item.get('seller_name'),
            'seller_url': item.get('seller_url'),
            'small_business': item.get('small_business', False),
            'buying_offers': item.get('buying_offers', []),
            'other_sellers': item.get('other_sellers'),
            
            # Product Details
            'features': item.get('features', []),
            'overview': item.get('overview', []),
            'details_table': item.get('details_table', []),
            'technical_details': item.get('technical_details', []),
            'specifications': item.get('specifications', {}),
            
            # Images & Media
            'main_image': item.get('main_image'),
            'thumbnail': item.get('thumbnail'),
            'images': item.get('images', []),
            'labelled_images': item.get('labelled_images', []),
            'product_videos': item.get('product_videos', []),
            
            # Categories & Rankings
            'categories': item.get('categories', []),
            'bestseller_ranks': item.get('bestseller_ranks', []),
            
            # Variants
            'variant': item.get('variant'),
            'variants': item.get('variants'),
            
            # Reviews
            'reviews_summary': item.get('reviews_summary'),
            'review_aspects': item.get('review_aspects', []),
            'top_reviews': item.get('top_reviews', []),
            
            # Additional Info
            'policy_badges': item.get('policy_badges', []),
            'product_guides': item.get('product_guides', []),
            'warranty_and_support': item.get('warranty_and_support'),
            'whats_in_box': item.get('whats_in_box', []),
            'from_the_manufacturer': item.get('from_the_manufacturer'),
            'addon_offers': item.get('addon_offers', []),
            'pay_later_offers': item.get('pay_later_offers', []),
            
            # Flags
            'is_sponsored': item.get('is_sponsored', False),
            'retailer_badge': item.get('retailer_badge')
        }
    
    def extract_part_attributes(self, asin: str, country_code: Optional[str] = None) -> Dict[str, Any]:
        """
        Get detailed part attributes suitable for catalog enhancement.
        
        Args:
            asin: Product ASIN
            country_code: Optional country code
            
        Returns:
            Structured part attributes optimized for enhancement
            
        Example:
            attrs = client.extract_part_attributes("B075M2Q4B2")
            print(attrs['specifications'])
            print(attrs['features'])
        """
        result = self.get_product_by_asin(asin, country_code)
        
        if not result.get('success'):
            return result
        
        product = self._format_product(result['data'])
        
        # Extract key attributes for part enhancement
        attributes = {
            'basic_info': {
                'name': product['name'],
                'brand': product['brand'],
                'asin': product['asin'],
                'part_number': self._extract_part_number(product),
            },
            'specifications': self._extract_specifications(product),
            'features': product['features'],
            'technical_details': product['technical_details'],
            'compatibility': self._extract_compatibility(product),
            'dimensions': self._extract_dimensions(product),
            'warranty': product.get('warranty_and_support', {}),
            'included_items': product['whats_in_box'],
            'images': {
                'main': product['main_image'],
                'all': product['images'],
                'labelled': product['labelled_images']
            },
            'pricing': {
                'current_price': product['price'],
                'list_price': product['price_reduced'],
                'currency': product['currency']
            },
            'reviews': {
                'rating': product['rating'],
                'total_ratings': product['total_ratings'],
                'summary': product['reviews_summary'],
                'key_aspects': product['review_aspects']
            }
        }
        
        return {
            'success': True,
            'data': attributes,
            'message': 'Part attributes extracted successfully'
        }
    
    def _extract_part_number(self, product: Dict[str, Any]) -> Optional[str]:
        """Extract part number from product data."""
        # Check name for part number patterns
        name = product.get('name') or ''
        
        if not name:
            return None
        
        # Common patterns: WR55X10025, B075M2Q4B2, etc.
        import re
        patterns = [
            r'\b([A-Z]{2}\d{2}[A-Z]\d{5})\b',  # WR55X10025 pattern
            r'\b([A-Z]\d{8})\b',                 # B075M2Q4B2 pattern
            r'\b(\d{3}-\d{4})\b'                 # 123-4567 pattern
        ]
        
        for pattern in patterns:
            match = re.search(pattern, name)
            if match:
                return match.group(1)
        
        return None
    
    def _extract_specifications(self, product: Dict[str, Any]) -> Dict[str, str]:
        """Extract specifications from various product fields."""
        specs = {}
        
        # From details_table
        for detail in product.get('details_table', []):
            if isinstance(detail, dict):
                name = detail.get('name', '')
                value = detail.get('value', '')
                if name and value:
                    specs[name] = value
        
        # From overview
        for overview in product.get('overview', []):
            if isinstance(overview, dict):
                name = overview.get('name', '')
                value = overview.get('value', '')
                if name and value:
                    specs[name] = value
        
        # From technical_details
        if isinstance(product.get('technical_details'), list):
            for detail in product['technical_details']:
                if isinstance(detail, dict):
                    name = detail.get('name', '')
                    value = detail.get('value', '')
                    if name and value:
                        specs[name] = value
        
        return specs
    
    def _extract_compatibility(self, product: Dict[str, Any]) -> List[str]:
        """Extract compatibility information from product data."""
        compatibility = []
        
        # Check features for "Compatible with" or "Fits" mentions
        for feature in product.get('features', []):
            if isinstance(feature, str):
                if any(keyword in feature.lower() for keyword in ['compatible', 'fits', 'replaces', 'works with']):
                    compatibility.append(feature)
        
        return compatibility
    
    def _extract_dimensions(self, product: Dict[str, Any]) -> Dict[str, str]:
        """Extract dimension information from specifications."""
        dimensions = {}
        specs = self._extract_specifications(product)
        
        dimension_keys = [
            'dimensions', 'product dimensions', 'item dimensions',
            'package dimensions', 'length', 'width', 'height', 'weight'
        ]
        
        for key, value in specs.items():
            if any(dim_key in key.lower() for dim_key in dimension_keys):
                dimensions[key] = value
        
        return dimensions
    
    def test_connection(self) -> Dict[str, str]:
        """
        Test the Amazon API connection with a simple search.
        
        Returns:
            Status message
        """
        logger.info("Testing Amazon API connection...")
        
        try:
            result = self.search("test", page=1)
            
            if result.get('success'):
                return {
                    'status': 'success',
                    'message': 'Amazon API connection successful',
                    'api_key': f"{self.config.api_key[:8]}...{self.config.api_key[-4:]}"
                }
            else:
                return {
                    'status': 'failed',
                    'message': f"API call failed: {result.get('message')}",
                    'api_key': f"{self.config.api_key[:8]}...{self.config.api_key[-4:]}"
                }
        except Exception as e:
            return {
                'status': 'error',
                'message': f"Connection test failed: {str(e)}",
                'api_key': 'configured' if self.config.api_key else 'not configured'
            }


def create_amazon_client(api_key: str = None) -> AmazonAPIClient:
    """
    Create Amazon API client instance.
    
    Args:
        api_key: Optional API key. If not provided, will load from environment.
        
    Returns:
        Configured AmazonAPIClient instance
        
    Example:
        client = create_amazon_client()
        results = client.search("WR55X10025")
    """
    if api_key:
        config = AmazonConfig()
        config.api_key = api_key
        return AmazonAPIClient(config)
    else:
        return AmazonAPIClient()
