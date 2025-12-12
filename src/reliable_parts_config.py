"""
Reliable Parts API Configuration
"""
import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Load environment variables
load_dotenv()

class ReliablePartsConfig(BaseSettings):
    """Configuration for Reliable Parts API (Test/Dev Environment)"""
    portal_url: str = os.getenv('RELIABLE_PARTS_PORTAL_URL', 'https://stgapi.reliableparts.net:9443')
    base_url: str = os.getenv('RELIABLE_PARTS_BASE_URL', 'https://stgapi.reliableparts.net:8077')
    username: str = os.getenv('RELIABLE_PARTS_USERNAME', '')
    password: str = os.getenv('RELIABLE_PARTS_PASSWORD', '')
    
    # API Keys per subscription
    part_search_api_key: str = os.getenv('RELIABLE_PARTS_PART_SEARCH_API_KEY', '')
    model_search_api_key: str = os.getenv('RELIABLE_PARTS_MODEL_SEARCH_API_KEY', '')
    model_to_part_api_key: str = os.getenv('RELIABLE_PARTS_MODEL_TO_PART_API_KEY', '')
    
    timeout: int = int(os.getenv('DEFAULT_TIMEOUT', '30'))
    
    class Config:
        env_file = '.env'
        extra = 'ignore'

# Create a global config instance
config = ReliablePartsConfig()
