"""
OpenAI | Grok Code
OpenAI + Grok (xAI) API Configuration for Parts Catalog Enhancement
"""

import os
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ============================================================================
# INITIALIZE AI CLIENTS
# ============================================================================

# OpenAI Client (Primary)
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# xAI/Grok Client (Backup/Alternative)
xai_client = OpenAI(
    api_key=os.getenv("XAI_API_KEY"),
    base_url="https://api.x.ai/v1"
)

# ============================================================================
# PROVIDER CONFIGURATION
# ============================================================================

AI_PROVIDERS = {
    "openai": {
        "client": openai_client,
        "model": "gpt-4o-mini",  # or "gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"
        "name": "OpenAI GPT-4o-mini",
        "enabled": bool(os.getenv("OPENAI_API_KEY"))
    },
    "xai": {
        "client": xai_client,
        "model": "grok-2-latest",  # or "grok-beta"
        "name": "xAI Grok 2",
        "enabled": bool(os.getenv("XAI_API_KEY"))
    }
}

# ============================================================================
# USAGE FUNCTIONS
# ============================================================================

def call_openai(prompt: str, system_message: str = None, temperature: float = 0.7):
    """Call OpenAI API"""
    messages = []
    if system_message:
        messages.append({"role": "system", "content": system_message})
    messages.append({"role": "user", "content": prompt})
    
    response = openai_client.chat.completions.create(
        model=AI_PROVIDERS["openai"]["model"],
        messages=messages,
        temperature=temperature
    )
    return response.choices[0].message.content


def call_grok(prompt: str, system_message: str = None, temperature: float = 0.7):
    """Call Grok/xAI API (same interface as OpenAI)"""
    messages = []
    if system_message:
        messages.append({"role": "system", "content": system_message})
    messages.append({"role": "user", "content": prompt})
    
    response = xai_client.chat.completions.create(
        model=AI_PROVIDERS["xai"]["model"],
        messages=messages,
        temperature=temperature
    )
    return response.choices[0].message.content


def call_ai_with_fallback(prompt: str, system_message: str = None, temperature: float = 0.7):
    """Try OpenAI first, fallback to Grok if it fails"""
    try:
        # Try OpenAI first
        return call_openai(prompt, system_message, temperature), "openai"
    except Exception as e:
        print(f"OpenAI failed: {e}, trying Grok...")
        try:
            # Fallback to Grok
            return call_grok(prompt, system_message, temperature), "xai"
        except Exception as e2:
            print(f"Grok also failed: {e2}")
            raise Exception("Both AI providers failed")


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    # Example 1: Simple OpenAI call
    result = call_openai("What is the capital of France?")
    print("OpenAI:", result)
    
    # Example 2: Grok call with system message
    result = call_grok(
        "Explain quantum computing in simple terms",
        system_message="You are a helpful teacher explaining complex topics simply."
    )
    print("Grok:", result)
    
    # Example 3: With fallback
    result, provider = call_ai_with_fallback("Tell me a joke about programming")
    print(f"Response from {provider}:", result)
