"""
Salesforce API Client
Handles connections and data retrieval from Salesforce
"""

import os
from typing import Dict, Any, List, Optional
from simple_salesforce import Salesforce
from dotenv import load_dotenv

load_dotenv()


class SalesforceClient:
    """Client for connecting to Salesforce and retrieving parts data"""
    
    def __init__(self):
        """Initialize Salesforce connection"""
        self.username = os.getenv("SALESFORCE_USERNAME")
        self.password = os.getenv("SALESFORCE_PASSWORD")
        self.security_token = os.getenv("SALESFORCE_SECURITY_TOKEN")
        self.instance_url = os.getenv("SALESFORCE_INSTANCE_URL")
        
        self.sf = None
        if all([self.username, self.password, self.security_token]):
            self._connect()
    
    def _connect(self):
        """Establish connection to Salesforce"""
        try:
            self.sf = Salesforce(
                username=self.username,
                password=self.password,
                security_token=self.security_token,
                instance_url=self.instance_url
            )
            print("✓ Connected to Salesforce")
        except Exception as e:
            print(f"✗ Failed to connect to Salesforce: {e}")
            raise
    
    def get_part_by_number(self, part_number: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a single part by part number
        
        Args:
            part_number: The part number to search for
            
        Returns:
            Part data dictionary or None if not found
        """
        if not self.sf:
            raise ConnectionError("Not connected to Salesforce")
        
        try:
            # Adjust the object name and field names to match your Salesforce schema
            query = f"""
                SELECT Id, Name, Part_Number__c, Description__c, 
                       Price__c, Model_Numbers__c, Category__c
                FROM Part__c
                WHERE Part_Number__c = '{part_number}'
                LIMIT 1
            """
            result = self.sf.query(query)
            
            if result['totalSize'] > 0:
                return self._format_part_data(result['records'][0])
            return None
        except Exception as e:
            print(f"Error retrieving part {part_number}: {e}")
            raise
    
    def get_parts_by_category(self, category: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Retrieve parts by category
        
        Args:
            category: Part category to filter by
            limit: Maximum number of results to return
            
        Returns:
            List of part data dictionaries
        """
        if not self.sf:
            raise ConnectionError("Not connected to Salesforce")
        
        try:
            query = f"""
                SELECT Id, Name, Part_Number__c, Description__c,
                       Price__c, Model_Numbers__c, Category__c
                FROM Part__c
                WHERE Category__c = '{category}'
                LIMIT {limit}
            """
            result = self.sf.query(query)
            
            return [self._format_part_data(record) for record in result['records']]
        except Exception as e:
            print(f"Error retrieving parts for category {category}: {e}")
            raise
    
    def _format_part_data(self, sf_record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format Salesforce record into standard part data structure
        
        Args:
            sf_record: Raw Salesforce record
            
        Returns:
            Formatted part data dictionary
        """
        return {
            "id": sf_record.get("Id"),
            "part_name": sf_record.get("Name"),
            "part_number": sf_record.get("Part_Number__c"),
            "description": sf_record.get("Description__c"),
            "price": sf_record.get("Price__c"),
            "model_numbers": sf_record.get("Model_Numbers__c"),
            "category": sf_record.get("Category__c")
        }
    
    def update_part_enhanced_data(self, part_id: str, enhanced_data: Dict[str, Any]) -> bool:
        """
        Update a part in Salesforce with enhanced data
        
        Args:
            part_id: Salesforce record ID
            enhanced_data: Dictionary containing enhanced attributes
            
        Returns:
            True if successful, False otherwise
        """
        if not self.sf:
            raise ConnectionError("Not connected to Salesforce")
        
        try:
            # Adjust field names to match your Salesforce schema
            update_data = {
                "Enhanced_Description__c": enhanced_data.get("enhanced_description"),
                "Key_Features__c": "\n".join(enhanced_data.get("key_features", [])),
                "Compatibility_Info__c": enhanced_data.get("compatibility_info")
            }
            
            self.sf.Part__c.update(part_id, update_data)
            print(f"✓ Updated part {part_id} with enhanced data")
            return True
        except Exception as e:
            print(f"✗ Failed to update part {part_id}: {e}")
            return False


# Example usage
if __name__ == "__main__":
    client = SalesforceClient()
    
    # Example: Get a part by part number
    # part = client.get_part_by_number("WPW10195677")
    # if part:
    #     print(f"Found part: {part['part_name']}")
