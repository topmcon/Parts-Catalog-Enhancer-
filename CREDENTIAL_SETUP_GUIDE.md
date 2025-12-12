# Credential Setup Guide

**Last Verified:** December 12, 2025  
**Status:** ✅ ALL SYSTEMS CONFIGURED AND READY

---

## 📋 Overview

This guide documents how credentials are managed and loaded across the Parts Catalog Enhancer system.

### Credential Management Strategy

- **Storage:** All credentials stored in `.env` file (never committed to Git)
- **Template:** `.env.example` provides template for new developers
- **Loading:** `python-dotenv` automatically loads credentials at runtime
- **Security:** `.env` is in `.gitignore` to prevent accidental exposure

---

## ✅ Current Credential Status

### Required Services (All Configured ✅)

| Service | Status | Credentials Required |
|---------|--------|---------------------|
| **OpenAI API** | ✅ Ready | `OPENAI_API_KEY` |
| **Grok/xAI API** | ✅ Ready | `XAI_API_KEY` |
| **Encompass API** | ✅ Ready | `ENCOMPASS_BASE_URL`, `ENCOMPASS_USERNAME`, `ENCOMPASS_PASSWORD` |
| **Marcone API** | ✅ Ready | `MARCONE_PROD_URL`, `MARCONE_PROD_USERNAME`, `MARCONE_PROD_PASSWORD` |
| **Reliable Parts API** | ✅ Ready | `RELIABLE_PARTS_BASE_URL`, `RELIABLE_PARTS_USERNAME`, `RELIABLE_PARTS_PASSWORD`, `RELIABLE_PARTS_PART_SEARCH_API_KEY` |
| **Amazon API** | ✅ Ready | `AMAZON_API_KEY` |

### Optional Services

| Service | Status | Credentials Required |
|---------|--------|---------------------|
| **Salesforce** | ⚠️ Not Configured (Optional) | `SALESFORCE_INSTANCE_URL`, `SALESFORCE_USERNAME`, `SALESFORCE_PASSWORD`, `SALESFORCE_SECURITY_TOKEN` |

---

## 🔧 How It Works

### 1. Environment File (`.env`)

Located at project root, contains all API credentials:

```bash
/workspaces/Parts-Catalog-Enhancer-/.env
```

**Security:** 
- ✅ In `.gitignore` - never committed
- ✅ Read-only by application code
- ✅ Masked in logs and output

### 2. Configuration Files

Each API has a dedicated config file that loads from `.env`:

| API | Config File | Loads From .env |
|-----|-------------|-----------------|
| Amazon | `src/amazon_config.py` | ✅ Yes |
| Encompass | `src/encompass_config.py` | ✅ Yes |
| Marcone | `src/marcone_config.py` | ✅ Yes |
| Reliable Parts | `src/reliable_parts_config.py` | ✅ Yes |
| AI (OpenAI/Grok) | `src/openai_grok_code.py` | ✅ Yes |
| Salesforce | `src/salesforce_client.py` | ✅ Yes |

**Example from `amazon_config.py`:**
```python
from dotenv import load_dotenv
import os

load_dotenv()  # Loads .env automatically

class AmazonConfig:
    def __init__(self):
        self.api_key = os.getenv("AMAZON_API_KEY")  # Reads from .env
```

### 3. API Clients

API clients use config files to get credentials:

```python
# Amazon API
from src.amazon_api import AmazonAPIClient
client = AmazonAPIClient()  # Auto-loads credentials from .env

# Encompass API
from src.encompass_api import EncompassAPIClient
client = EncompassAPIClient()  # Auto-loads credentials from .env

# Marcone API
from src.marcone_config import get_credentials
url, user, pwd = get_credentials('prod')  # Auto-loads from .env
```

### 4. Test Scripts

Test scripts load `.env` at startup:

```python
# tests/run_part_test.py
from dotenv import load_dotenv
import os

load_dotenv()  # Load all credentials

openai_key = os.getenv("OPENAI_API_KEY")
xai_key = os.getenv("XAI_API_KEY")
# ... etc
```

---

## 📝 Complete Environment Variable Reference

### OpenAI API
```bash
OPENAI_API_KEY=sk-proj-xxxxx
```
**Used by:** `src/openai_grok_code.py`, `tests/run_part_test.py`

### Grok/xAI API
```bash
XAI_API_KEY=xai-xxxxx
```
**Used by:** `src/openai_grok_code.py`, `tests/run_part_test.py`

### Encompass API
```bash
ENCOMPASS_BASE_URL=https://encompass.com
ENCOMPASS_USERNAME=MARDEYS
ENCOMPASS_PASSWORD=xxxxx
```
**Used by:** `src/encompass_api.py`, `src/encompass_config.py`, `tests/run_part_test.py`

### Marcone API (Production)
```bash
MARCONE_PROD_URL=https://api.marcone.com
MARCONE_PROD_USERNAME=Api148083
MARCONE_PROD_PASSWORD=xxxxx
```
**Used by:** `src/marcone_api.py`, `src/marcone_config.py`, `tests/run_part_test.py`

### Marcone API (Test - Optional)
```bash
MARCONE_TEST_URL=https://testapi.marcone.com
MARCONE_TEST_USERNAME=Api148083
MARCONE_TEST_PASSWORD=xxxxx
```
**Used by:** `src/marcone_api.py`, `src/marcone_config.py`

### Marcone FTP (Optional)
```bash
MARCONE_FTP_HOST=ftp.marcone.com
MARCONE_FTP_USERNAME=148083Mardeys
MARCONE_FTP_PASSWORD=xxxxx
```
**Used by:** `src/marcone_api.py`, `src/marcone_config.py`

### Reliable Parts API
```bash
RELIABLE_PARTS_BASE_URL=https://stgapi.reliableparts.net:8077
RELIABLE_PARTS_PORTAL_URL=https://stgapi.reliableparts.net:9443
RELIABLE_PARTS_USERNAME=7109245
RELIABLE_PARTS_PASSWORD=xxxxx
RELIABLE_PARTS_PART_SEARCH_API_KEY=xxxxx
RELIABLE_PARTS_MODEL_SEARCH_API_KEY=xxxxx  # Optional
RELIABLE_PARTS_MODEL_TO_PART_API_KEY=xxxxx  # Optional
```
**Used by:** `src/reliable_parts_api.py`, `src/reliable_parts_config.py`, `tests/run_part_test.py`

### Amazon API
```bash
AMAZON_API_KEY=xxxxx
```
**Used by:** `src/amazon_api.py`, `src/amazon_config.py`, `tests/run_part_test.py`

### Salesforce (Optional)
```bash
SALESFORCE_INSTANCE_URL=https://your-instance.salesforce.com
SALESFORCE_USERNAME=your-username
SALESFORCE_PASSWORD=your-password
SALESFORCE_SECURITY_TOKEN=your-token
```
**Used by:** `src/salesforce_client.py`, `src/api.py`

### General Settings
```bash
DEFAULT_TIMEOUT=30
```
**Used by:** All API config files for request timeouts

---

## 🔍 Verification Commands

### Check All Credentials Loaded
```bash
python -c "
from dotenv import load_dotenv
import os

load_dotenv()

services = ['OPENAI_API_KEY', 'XAI_API_KEY', 'ENCOMPASS_USERNAME', 
            'MARCONE_PROD_USERNAME', 'RELIABLE_PARTS_USERNAME', 'AMAZON_API_KEY']

for var in services:
    value = os.getenv(var)
    status = '✅' if value else '❌'
    print(f'{status} {var}')
"
```

### Test API Client Initialization
```bash
python -c "
from src.amazon_api import AmazonAPIClient
from src.encompass_api import EncompassAPIClient
from src.marcone_config import get_credentials
from src.reliable_parts_api import ReliablePartsAPIClient

print('✅ Amazon:', bool(AmazonAPIClient().config.api_key))
print('✅ Encompass:', bool(EncompassAPIClient().username))
print('✅ Marcone:', bool(get_credentials('prod')[0]))
print('✅ Reliable Parts:', bool(ReliablePartsAPIClient().username))
"
```

### Run Complete Test
```bash
python tests/run_part_test.py
```
This will validate all credentials by attempting actual API calls.

---

## 🚀 Setup for New Developers

### 1. Clone Repository
```bash
git clone <repo-url>
cd Parts-Catalog-Enhancer-
```

### 2. Copy Environment Template
```bash
cp .env.example .env
```

### 3. Fill in Credentials
Edit `.env` with actual API keys and credentials:
```bash
nano .env  # or use your preferred editor
```

### 4. Verify Setup
```bash
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('✅ Loaded' if os.getenv('OPENAI_API_KEY') else '❌ Failed')"
```

### 5. Run Test
```bash
python tests/run_part_test.py
```

---

## 🔒 Security Best Practices

### ✅ Currently Implemented

1. **Environment File Not Committed**
   - `.env` in `.gitignore`
   - Only `.env.example` (template) is committed

2. **Credential Masking in Logs**
   - API keys displayed as `xxxxx...` in output
   - Passwords never printed in full

3. **No Hardcoded Credentials**
   - All credentials loaded from environment
   - No credentials in source code

4. **Separate Test/Production Environments**
   - Marcone has separate test and production credentials
   - Reliable Parts has staging environment credentials

### 🔐 Additional Recommendations

1. **Rotate Credentials Regularly**
   - Change API keys every 90 days
   - Update `.env` and notify team

2. **Use Different Credentials per Environment**
   - Development: Test credentials
   - Production: Production credentials
   - Never mix environments

3. **Restrict Access**
   - Only authorized personnel should have access to `.env`
   - Use proper file permissions: `chmod 600 .env`

4. **Monitor Usage**
   - Track API key usage in provider dashboards
   - Alert on unusual activity

---

## 🐛 Troubleshooting

### Problem: "API Key not found in environment"

**Solution:**
```bash
# Verify .env file exists
ls -la .env

# Check if load_dotenv() is called
grep "load_dotenv" src/*.py

# Manually test loading
python -c "from dotenv import load_dotenv; load_dotenv(); import os; print(os.getenv('OPENAI_API_KEY'))"
```

### Problem: "Module 'dotenv' not found"

**Solution:**
```bash
pip install python-dotenv
```

### Problem: "Credentials loaded but API calls fail"

**Solution:**
1. Verify credentials are correct (check with provider)
2. Check if credentials have expired
3. Verify API endpoints are correct
4. Check network connectivity
5. Review API provider status page

### Problem: "Some credentials missing"

**Solution:**
```bash
# Compare .env with .env.example
diff .env .env.example

# Copy missing variables from .env.example to .env
# Then fill in actual values
```

---

## 📊 Credential Load Flow

```
1. Application starts
   ↓
2. load_dotenv() called in config files
   ↓
3. Reads /workspaces/Parts-Catalog-Enhancer-/.env
   ↓
4. Loads all KEY=VALUE pairs into os.environ
   ↓
5. Config classes use os.getenv("KEY")
   ↓
6. API clients instantiate with config values
   ↓
7. Ready to make API calls ✅
```

---

## 📈 Testing Credential Setup

Run this comprehensive test to verify everything:

```bash
cd /workspaces/Parts-Catalog-Enhancer-
python -c "
from dotenv import load_dotenv
import os

load_dotenv()

required = {
    'OpenAI': 'OPENAI_API_KEY',
    'Grok': 'XAI_API_KEY',
    'Encompass': 'ENCOMPASS_USERNAME',
    'Marcone': 'MARCONE_PROD_USERNAME',
    'Reliable': 'RELIABLE_PARTS_USERNAME',
    'Amazon': 'AMAZON_API_KEY'
}

print('Credential Status:')
all_ok = True
for service, var in required.items():
    value = os.getenv(var)
    if value:
        print(f'✅ {service}: Configured')
    else:
        print(f'❌ {service}: Missing {var}')
        all_ok = False

if all_ok:
    print('\n✅ ALL CREDENTIALS CONFIGURED - READY TO RUN')
else:
    print('\n⚠️  SOME CREDENTIALS MISSING - CHECK .env FILE')
"
```

Expected output:
```
Credential Status:
✅ OpenAI: Configured
✅ Grok: Configured
✅ Encompass: Configured
✅ Marcone: Configured
✅ Reliable: Configured
✅ Amazon: Configured

✅ ALL CREDENTIALS CONFIGURED - READY TO RUN
```

---

## ✅ Summary

**Current Status:** ✅ **FULLY CONFIGURED AND OPERATIONAL**

- ✅ All 6 required APIs have credentials loaded
- ✅ All config files properly reading from `.env`
- ✅ All API clients initializing correctly
- ✅ Test script validated with actual API calls
- ✅ Security best practices implemented
- ✅ Documentation complete

**Ready for:** Production deployment, development, and testing

**Last Validated:** December 12, 2025

---

*For questions or issues with credential setup, contact the development team or refer to individual API documentation in `docs/` directory.*
