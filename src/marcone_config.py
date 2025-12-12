"""
Marcone API Configuration
Centralized configuration management for Marcone API credentials
"""

from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class MarconeConfig(BaseSettings):
    """Marcone API configuration settings."""
    
    # Account 148083 - TEST Environment
    marcone_test_url: str
    marcone_test_username: str
    marcone_test_password: str
    
    # Account 148083 - PRODUCTION Environment
    marcone_prod_url: str
    marcone_prod_username: str
    marcone_prod_password: str
    
    # FTP Credentials (for file transfers)
    marcone_ftp_host: str
    marcone_ftp_username: str
    marcone_ftp_password: str
    
    # API Settings
    default_timeout: int = 30
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"


@lru_cache()
def get_marcone_config() -> MarconeConfig:
    """
    Get cached Marcone configuration instance.
    
    Returns:
        MarconeConfig: Configured Marcone settings
    """
    return MarconeConfig()


def get_credentials(environment: str = "prod") -> tuple[str, str, str]:
    """
    Get Marcone API credentials for specified environment.
    
    Args:
        environment: "prod" or "test"
    
    Returns:
        Tuple of (base_url, username, password)
    """
    config = get_marcone_config()
    
    if environment.lower() == "test":
        return (
            config.marcone_test_url,
            config.marcone_test_username,
            config.marcone_test_password
        )
    else:
        return (
            config.marcone_prod_url,
            config.marcone_prod_username,
            config.marcone_prod_password
        )


def get_ftp_credentials() -> tuple[str, str, str]:
    """
    Get Marcone FTP credentials.
    
    Returns:
        Tuple of (host, username, password)
    """
    config = get_marcone_config()
    return (
        config.marcone_ftp_host,
        config.marcone_ftp_username,
        config.marcone_ftp_password
    )


# Account Information
MARCONE_ACCOUNT = {
    "account_number": "148083",
    "account_name": "Mardeys",
    "environment": {
        "production": "https://api.marcone.com",
        "test": "https://testapi.marcone.com"
    }
}


if __name__ == "__main__":
    config = get_marcone_config()
    print("Marcone Configuration Loaded:")
    print(f"  Account: {MARCONE_ACCOUNT['account_number']}")
    print(f"  Test URL: {config.marcone_test_url}")
    print(f"  Prod URL: {config.marcone_prod_url}")
    print(f"  FTP Host: {config.marcone_ftp_host}")
