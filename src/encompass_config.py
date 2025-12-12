"""
Encompass API Configuration
"""
import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Load environment variables
load_dotenv()

class EncompassConfig(BaseSettings):
    """Configuration for Encompass API"""
    base_url: str = os.getenv('ENCOMPASS_BASE_URL', 'https://encompass.com')
    username: str = os.getenv('ENCOMPASS_USERNAME', '')
    password: str = os.getenv('ENCOMPASS_PASSWORD', '')
    timeout: int = int(os.getenv('DEFAULT_TIMEOUT', '30'))
    
    class Config:
        env_file = '.env'
        extra = 'ignore'

# Create a global config instance
config = EncompassConfig()
