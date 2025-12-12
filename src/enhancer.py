"""
Part Enhancement Service
Enhances appliance parts data using AI
"""

from typing import Dict, Any, Optional
from src.openai_grok_code import call_ai_with_fallback


class PartEnhancer:
    """Enhances appliance parts data with AI-generated descriptions"""
    
    def __init__(self):
        self.system_message = """You are an expert in appliance parts and customer education. 
Your job is to take technical parts data and create clear, customer-friendly descriptions 
that are educational and easy to understand. Focus on:
- What the part does
- Why it's important
- Common issues it solves
- Compatibility information
Keep language simple and avoid excessive technical jargon."""
    
    def enhance_part_attributes(self, part_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhance part attributes with AI-generated content
        
        Args:
            part_data: Dictionary containing part information from Salesforce
            
        Returns:
            Enhanced part data with customer-friendly attributes
        """
        enhanced_data = part_data.copy()
        
        # Generate enhanced description
        if "description" in part_data or "part_name" in part_data:
            enhanced_data["enhanced_description"] = self._generate_description(part_data)
        
        # Generate features list
        enhanced_data["key_features"] = self._generate_features(part_data)
        
        # Generate compatibility information
        if "model_numbers" in part_data or "part_number" in part_data:
            enhanced_data["compatibility_info"] = self._generate_compatibility(part_data)
        
        return enhanced_data
    
    def _generate_description(self, part_data: Dict[str, Any]) -> str:
        """Generate customer-friendly description"""
        part_name = part_data.get("part_name", "Unknown Part")
        technical_desc = part_data.get("description", "")
        part_number = part_data.get("part_number", "")
        
        prompt = f"""Create a customer-friendly description for this appliance part:

Part Name: {part_name}
Part Number: {part_number}
Technical Description: {technical_desc}

Write a 2-3 sentence description that explains what this part does and why a customer 
might need it. Make it clear and educational."""
        
        result, provider = call_ai_with_fallback(prompt, self.system_message, temperature=0.7)
        return result
    
    def _generate_features(self, part_data: Dict[str, Any]) -> list:
        """Generate key features list"""
        part_name = part_data.get("part_name", "Unknown Part")
        description = part_data.get("description", "")
        
        prompt = f"""List 3-5 key features or benefits of this appliance part:

Part Name: {part_name}
Description: {description}

Return ONLY a bullet-point list, one feature per line."""
        
        result, provider = call_ai_with_fallback(prompt, self.system_message, temperature=0.7)
        
        # Parse bullet points into list
        features = [line.strip("- •*").strip() for line in result.split("\n") if line.strip()]
        return features[:5]  # Limit to 5 features
    
    def _generate_compatibility(self, part_data: Dict[str, Any]) -> str:
        """Generate compatibility information"""
        part_number = part_data.get("part_number", "")
        model_numbers = part_data.get("model_numbers", "")
        
        prompt = f"""Create a brief compatibility statement for this part:

Part Number: {part_number}
Compatible Models: {model_numbers}

Write 1-2 sentences explaining compatibility in customer-friendly language."""
        
        result, provider = call_ai_with_fallback(prompt, self.system_message, temperature=0.7)
        return result


# Example usage
if __name__ == "__main__":
    # Sample part data from Salesforce
    sample_part = {
        "part_number": "WPW10195677",
        "part_name": "Water Inlet Valve",
        "description": "Washing machine water inlet valve assembly",
        "model_numbers": "WTW5000DW, WTW5500XW, WTW8500DC",
        "price": 45.99
    }
    
    enhancer = PartEnhancer()
    enhanced = enhancer.enhance_part_attributes(sample_part)
    
    print("Enhanced Part Data:")
    print(f"\nOriginal: {sample_part['part_name']}")
    print(f"\nEnhanced Description:\n{enhanced['enhanced_description']}")
    print(f"\nKey Features:")
    for feature in enhanced['key_features']:
        print(f"  • {feature}")
    print(f"\nCompatibility:\n{enhanced['compatibility_info']}")
