"""
Amazon API Configuration
Configuration for Unwrangle Amazon API - Search, Detail, and Category APIs
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class AmazonConfig:
    """Amazon API configuration settings."""
    
    def __init__(self):
        self.base_url = "https://data.unwrangle.com/api/getter/"
        self.api_key = os.getenv("AMAZON_API_KEY")
        self.default_country = "us"
        self.timeout = 30
        
        # API platforms
        self.search_platform = "amazon_search"
        self.detail_platform = "amazon_detail"
        self.category_platform = "amazon_category"
        
        if not self.api_key:
            raise ValueError("AMAZON_API_KEY not found in environment variables")
    
    @property
    def is_configured(self) -> bool:
        """Check if API is properly configured."""
        return bool(self.api_key)


def get_amazon_config() -> AmazonConfig:
    """Get Amazon API configuration instance."""
    return AmazonConfig()
