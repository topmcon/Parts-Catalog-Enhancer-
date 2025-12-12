# Quick Reference Guide

## 🔍 Find What You Need Fast

### "I need to understand the overall system"
→ Read: [IMPLEMENTATION_PLAN.md](../IMPLEMENTATION_PLAN.md) - Section 1 & 2

### "I need to know what to build first"
→ Read: [IMPLEMENTATION_ROADMAP.md](IMPLEMENTATION_ROADMAP.md) - Your current phase

### "I need to create database tables"
→ Read: [DATA_MODELS.md](DATA_MODELS.md) - Section 5 (SQL Schema)

### "I need to integrate an external API"
→ Read: [API_SPECIFICATION.md](API_SPECIFICATION.md) - Section 1

### "I need to implement AI validation"
→ Read: [AI_VALIDATION_LOGIC.md](AI_VALIDATION_LOGIC.md) - Sections 1-3

### "I need to create REST endpoints"
→ Read: [API_SPECIFICATION.md](API_SPECIFICATION.md) - Section 2

### "I need to set up the project locally"
→ Read: [README.md](../README.md) - Getting Started section

### "I need to deploy to production"
→ Read: [README.md](../README.md) - Deployment section

### "I need to know the data fields"
→ Read: [DATA_MODELS.md](DATA_MODELS.md) - Section 1.3 (MasterCatalogRecord)

### "I need to handle errors"
→ Read: [API_SPECIFICATION.md](API_SPECIFICATION.md) - Section 7

### "I need to optimize AI costs"
→ Read: [AI_VALIDATION_LOGIC.md](AI_VALIDATION_LOGIC.md) - Section 7

### "I need to resolve data conflicts"
→ Read: [AI_VALIDATION_LOGIC.md](AI_VALIDATION_LOGIC.md) - Section 5

### "I need the project timeline"
→ Read: [IMPLEMENTATION_ROADMAP.md](IMPLEMENTATION_ROADMAP.md)

### "I need success criteria"
→ Read: [IMPLEMENTATION_PLAN.md](../IMPLEMENTATION_PLAN.md) - Section 13

---

## 📋 Common Code Patterns

### Making an API Call
```python
from src.api_clients.encompass_client import EncompassAPIClient

client = EncompassAPIClient(api_key=config.ENCOMPASS_API_KEY)
result = await client.lookup_part("WR55X10025")
```

### Creating a Catalog Record
```python
from src.models.catalog import MasterCatalogRecord

catalog = MasterCatalogRecord(
    catalog_id=uuid4(),
    mpn="WR55X10025",
    manufacturer="GE",
    # ... other fields
)
await catalog_repository.save(catalog)
```

### AI Validation
```python
from src.ai.openai_validator import OpenAIValidator

validator = OpenAIValidator(api_key=config.OPENAI_API_KEY)
result = await validator.validate_part_data(part_number, source_data)
```

### Creating an Endpoint
```python
from fastapi import APIRouter, Depends

router = APIRouter()

@router.get("/catalog/{part_number}")
async def get_catalog(
    part_number: str,
    auth=Depends(verify_api_key)
):
    catalog = await catalog_repository.get_by_part_number(part_number)
    return catalog
```

---

## 🎯 Field Status Values

Every field in the master catalog has a status:

- **FOUND**: Data was located in at least one source
- **NOT_APPLICABLE**: Field doesn't apply to this part (e.g., voltage for non-electrical parts)
- **NOT_FOUND**: Field is applicable but no data available from any source

Use this to distinguish missing vs non-applicable data.

---

## 🔢 Confidence Score Ranges

- **0.9 - 1.0**: High confidence (both AIs agree, multiple sources confirm)
- **0.7 - 0.89**: Medium confidence (single AI or minor discrepancies)
- **0.5 - 0.69**: Low confidence (conflicts or limited data)
- **< 0.5**: Very low confidence (flagged for review)

---

## 🌊 Data Flow Quick Reference

```
User Request
    ↓
API Gateway
    ↓
Lookup Service → [Encompass, Marcone, Reliable, Amazon] (parallel)
    ↓
Data Aggregator
    ↓
[OpenAI, Grok] (parallel AI validation)
    ↓
Consensus Engine
    ↓
Catalog Builder
    ↓
Database (PostgreSQL)
    ↓
Response to User
```

---

## ⚙️ Environment Variables Checklist

```bash
# Database
✓ DATABASE_URL
✓ REDIS_URL

# External APIs
✓ ENCOMPASS_API_KEY
✓ MARCONE_CLIENT_ID
✓ MARCONE_CLIENT_SECRET
✓ RELIABLE_API_KEY
✓ RELIABLE_API_SECRET
✓ AMAZON_ACCESS_KEY
✓ AMAZON_SECRET_KEY
✓ AMAZON_PARTNER_TAG

# AI
✓ OPENAI_API_KEY
✓ GROK_API_KEY

# AWS
✓ AWS_ACCESS_KEY_ID
✓ AWS_SECRET_ACCESS_KEY
✓ S3_BUCKET

# App
✓ ENVIRONMENT
✓ LOG_LEVEL
```

---

## 🧪 Testing Commands

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_consensus_engine.py

# Run with coverage
pytest --cov=src --cov-report=html

# Run integration tests only
pytest tests/integration/

# Run and show print statements
pytest -s

# Run specific test
pytest tests/unit/test_api.py::test_lookup_endpoint -v
```

---

## 🚀 Deployment Commands

```bash
# Run locally
uvicorn src.api:app --reload

# Run with docker-compose
docker-compose up

# Database migrations
alembic upgrade head

# Create new migration
alembic revision -m "description"

# Build docker image
docker build -t parts-catalog-api .

# Deploy to staging (example)
./scripts/deploy.sh staging

# Deploy to production (example)
./scripts/deploy.sh production
```

---

## 📊 Key Tables

### lookup_sessions
Tracks each part lookup request
- Primary key: `session_id`
- Links to: `raw_source_responses`, `master_catalog`

### raw_source_responses
Stores unmodified API responses
- Primary key: `response_id`
- Links to: `lookup_sessions`

### master_catalog
Main product records
- Primary key: `catalog_id`
- Unique: `mpn` (part number)

### ai_validations
AI analysis results
- Primary key: `validation_id`
- Links to: `lookup_sessions`, `master_catalog`

### spec_table_entries
Dynamic specifications
- Primary key: `spec_id`
- Links to: `master_catalog`

---

## 🔍 Useful SQL Queries

```sql
-- Find recent lookups
SELECT * FROM lookup_sessions 
ORDER BY request_timestamp DESC 
LIMIT 10;

-- Get catalog with high confidence
SELECT mpn, manufacturer, data_confidence_score 
FROM master_catalog 
WHERE data_confidence_score > 0.9
ORDER BY created_at DESC;

-- Find parts with conflicts
SELECT * FROM ai_validations 
WHERE ai_agreement_score < 0.7;

-- Check API success rates
SELECT source_name, 
       COUNT(*) as total,
       SUM(CASE WHEN is_success THEN 1 ELSE 0 END) as successes,
       AVG(response_time_ms) as avg_time
FROM raw_source_responses
GROUP BY source_name;
```

---

## 🐛 Debugging Tips

### API Not Responding
1. Check logs: `docker-compose logs api`
2. Verify environment variables
3. Check database connection: `curl http://localhost:8000/health/db`

### AI Validation Failing
1. Check API keys are valid
2. Review prompt in logs
3. Check token limits not exceeded
4. Verify response format

### Database Errors
1. Check connection string
2. Verify migrations: `alembic current`
3. Check database logs
4. Verify table exists

### Slow Lookups
1. Check which API is slow: Review response times in logs
2. Check database query performance
3. Verify caching is enabled
4. Check for rate limiting

---

## 📈 Monitoring Quick Links

### Local Development
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health
- Metrics: http://localhost:8000/metrics (if enabled)

### Production
- CloudWatch Dashboard: [AWS Console Link]
- API Gateway: https://api.partscatalog.company.com
- Admin Dashboard: https://api.partscatalog.company.com/admin

---

## 💡 Pro Tips

1. **Cache AI results** to save costs (set `ENABLE_AI_CACHING=True`)
2. **Use read replicas** for Salesforce queries to reduce load
3. **Batch similar requests** when possible
4. **Monitor AI costs daily** - they can add up quickly
5. **Test with mock data first** before using real API calls
6. **Always check data status** - distinguish NOT_FOUND vs NOT_APPLICABLE
7. **Use confidence scores** to prioritize manual review
8. **Log everything** - you'll need it for debugging

---

## 🆘 Getting Help

### Documentation
- Start with [EXECUTIVE_SUMMARY.md](EXECUTIVE_SUMMARY.md)
- Check relevant section above
- Search docs folder

### Code Issues
- Check existing GitHub issues
- Create new issue with template
- Include logs and steps to reproduce

### Questions
- Ask in team Slack channel
- Schedule office hours
- Check weekly demo/Q&A sessions

### Emergency
- Contact on-call engineer
- Check runbooks in `docs/RUNBOOKS.md`
- Review incident response procedures

---

**Last Updated**: December 12, 2025  
**Version**: 1.0
