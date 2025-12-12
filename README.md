# Parts Catalog Enhancer

AI-powered product attribute enhancement tool for appliance parts catalog.

## Overview

This tool receives appliance parts data from Salesforce via API, processes it through OpenAI and Grok AI platforms, and generates enhanced, customer-facing product attributes that are clean, clear, and educational.

## Features

- 🤖 **Dual AI Integration**: OpenAI (primary) with Grok (xAI) fallback
- 🔄 **Salesforce Integration**: Direct API connection for parts data
- ✨ **Attribute Enhancement**: Transform technical data into customer-friendly descriptions
- 🛡️ **Fallback System**: Automatic failover between AI providers
- 📊 **Data Processing**: Clean and structure product information

## Setup

### 1. Clone the repository
```bash
git clone https://github.com/topmcon/Parts-Catalog-Enhancer-.git
cd Parts-Catalog-Enhancer-
```

### 2. Create virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment variables
```bash
cp .env.example .env
```

Edit `.env` and add your API keys:
```env
OPENAI_API_KEY=your_openai_api_key_here
XAI_API_KEY=your_xai_api_key_here
ENCOMPASS_USERNAME=your_encompass_username
ENCOMPASS_PASSWORD=your_encompass_password
MARCONE_PROD_USERNAME=your_marcone_username
MARCONE_PROD_PASSWORD=your_marcone_password
RELIABLE_PARTS_USERNAME=your_reliable_parts_username
RELIABLE_PARTS_PASSWORD=your_reliable_parts_password
RELIABLE_PARTS_PART_SEARCH_API_KEY=your_api_key
AMAZON_API_KEY=your_amazon_api_key
```

**📖 Complete credential setup guide:** See [CREDENTIAL_SETUP_GUIDE.md](CREDENTIAL_SETUP_GUIDE.md) for detailed instructions.

## Project Structure

```
Parts-Catalog-Enhancer-/
├── src/
│   ├── __init__.py
│   ├── ai_config.py          # AI provider configuration
│   ├── enhancer.py            # Main enhancement logic (coming soon)
│   └── salesforce_client.py   # Salesforce API client (coming soon)
├── tests/
├── .env.example
├── .gitignore
├── requirements.txt
└── # Parts Catalog Enhancement System

## Overview

The Parts Catalog Enhancement System is an intelligent, AI-powered platform that aggregates appliance parts data from multiple suppliers (Encompass, Marcone, Reliable Parts, Amazon), validates and enriches it using dual AI validation (OpenAI + Grok), and provides a unified master catalog accessible via API to Salesforce and other systems.

## 🎯 Key Features

- **Multi-Source Data Aggregation**: Automatically queries 4 major parts suppliers in parallel
- **Dual AI Validation**: Uses both OpenAI GPT-4 and Grok to cross-validate data accuracy
- **Intelligent Consensus**: Resolves conflicts between sources using sophisticated algorithms
- **Master Catalog**: Creates comprehensive, unified product records with 80+ attributes
- **Complete Audit Trail**: Tracks all data sources, timestamps, and validation decisions
- **Salesforce Integration**: RESTful API optimized for Salesforce consumption
- **Data Quality Tracking**: Distinguishes "not applicable" vs "not found" for every field
- **SEO-Optimized Content**: AI-generated product titles and descriptions

## 📋 System Requirements

- Python 3.11+
- PostgreSQL 14+
- Redis 6+
- AWS Account (S3, RDS, EC2)
- API Access to:
  - Encompass API
  - Marcone API
  - Reliable Parts API
  - Amazon Product Advertising API
  - OpenAI API
  - Grok API

## 📚 Documentation

### Core Documents

1. **[Implementation Plan](IMPLEMENTATION_PLAN.md)** - Complete technical overview and project plan
2. **[Data Models](docs/DATA_MODELS.md)** - Detailed data structures and database schema
3. **[API Specification](docs/API_SPECIFICATION.md)** - API integration details and endpoints
4. **[Implementation Roadmap](docs/IMPLEMENTATION_ROADMAP.md)** - 18-week detailed execution plan
5. **[AI Validation Logic](docs/AI_VALIDATION_LOGIC.md)** - AI validation workflows and algorithms

### Quick Links

- [Architecture Overview](#architecture-overview)
- [Getting Started](#getting-started)
- [Configuration](#configuration)
- [Usage Examples](#usage-examples)
- [Development Guide](#development-guide)
- [Deployment](#deployment)
- [Monitoring](#monitoring)

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        API Gateway (FastAPI)                     │
│                    /lookup, /catalog, /validate                  │
└────────────────────────────────┬────────────────────────────────┘
                                 │
                ┌────────────────┴────────────────┐
                │                                  │
        ┌───────▼────────┐              ┌────────▼────────┐
        │ Lookup Service │              │  Catalog API    │
        │   Orchestrator │              │   (Salesforce)  │
        └───────┬────────┘              └─────────────────┘
                │
    ┌───────────┼───────────┬───────────┬───────────┐
    │           │           │           │           │
┌───▼───┐  ┌──▼───┐  ┌────▼────┐ ┌───▼────┐ ┌────▼─────┐
│Encomp.│  │Marco.│  │Reliable │ │ Amazon │ │Image     │
│  API  │  │ API  │  │   API   │ │  API   │ │Downloader│
└───┬───┘  └──┬───┘  └────┬────┘ └───┬────┘ └────┬─────┘
    │         │           │          │           │
    └─────────┴───────────┴──────────┴───────────┘
                         │
                ┌────────▼────────┐
                │ Data Aggregator │
                │  & Normalizer   │
                └────────┬────────┘
                         │
            ┌────────────┴────────────┐
            │                         │
    ┌───────▼────────┐       ┌───────▼────────┐
    │  OpenAI GPT-4  │       │   Grok API     │
    │   Validator    │       │   Validator    │
    └───────┬────────┘       └───────┬────────┘
            │                         │
            └────────────┬────────────┘
                         │
                ┌────────▼────────┐
                │ AI Consensus    │
                │    Engine       │
                └────────┬────────┘
                         │
                ┌────────▼────────┐
                │ Master Catalog  │
                │    Builder      │
                └────────┬────────┘
                         │
                ┌────────▼────────┐
                │   PostgreSQL    │
                │   + S3 Storage  │
                └─────────────────┘
```

## 🚀 Getting Started

### Prerequisites

```bash
# Clone the repository
git clone https://github.com/topmcon/Parts-Catalog-Enhancer-.git
cd Parts-Catalog-Enhancer-

# Install Python dependencies
pip install -r requirements.txt

# Install PostgreSQL (if not already installed)
# macOS: brew install postgresql
# Ubuntu: sudo apt-get install postgresql

# Install Redis
# macOS: brew install redis
# Ubuntu: sudo apt-get install redis-server
```

### Environment Setup

1. Copy the environment template:
```bash
cp .env.example .env
```

2. Configure your `.env` file with API keys and database credentials:
```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/parts_catalog
REDIS_URL=redis://localhost:6379/0

# API Keys
ENCOMPASS_API_KEY=your_key_here
MARCONE_CLIENT_ID=your_id_here
MARCONE_CLIENT_SECRET=your_secret_here
RELIABLE_API_KEY=your_key_here
RELIABLE_API_SECRET=your_secret_here
AMAZON_ACCESS_KEY=your_key_here
AMAZON_SECRET_KEY=your_secret_here
AMAZON_PARTNER_TAG=your_tag_here

# AI Services
OPENAI_API_KEY=your_key_here
GROK_API_KEY=your_key_here

# AWS
AWS_ACCESS_KEY_ID=your_key_here
AWS_SECRET_ACCESS_KEY=your_secret_here
S3_BUCKET=parts-catalog-images
S3_REGION=us-east-1

# Application
API_BASE_URL=http://localhost:8000
ENVIRONMENT=development
LOG_LEVEL=INFO
```

### Database Initialization

```bash
# Run database migrations
alembic upgrade head

# Verify database connection
python scripts/verify_db.py
```

### Start the Development Server

```bash
# Using uvicorn directly
uvicorn src.api:app --reload --port 8000

# Or using docker-compose
docker-compose up
```

The API will be available at `http://localhost:8000`

API documentation: `http://localhost:8000/docs`

## ⚙️ Configuration

### API Configuration

Configure each external API client in your `.env` file or through environment variables:

```python
# src/config.py
class Config:
    # Database
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 20
    
    # Redis
    REDIS_URL: str
    
    # External APIs
    ENCOMPASS_API_KEY: str
    ENCOMPASS_BASE_URL: str = "https://api.encompass.com/v1"
    ENCOMPASS_RATE_LIMIT: int = 100  # per minute
    
    # ... (see docs/API_SPECIFICATION.md for complete configuration)
```

### AI Configuration

```python
# AI Models
OPENAI_MODEL: str = "gpt-4-turbo"
OPENAI_MAX_TOKENS: int = 4000
OPENAI_TEMPERATURE: float = 0.2

GROK_MODEL: str = "grok-1"
GROK_MAX_TOKENS: int = 4000
GROK_TEMPERATURE: float = 0.2

# Cost Controls
MAX_AI_COST_PER_LOOKUP: float = 0.50
ENABLE_AI_CACHING: bool = True
USE_DUAL_AI_VALIDATION: bool = True  # Use both OpenAI and Grok
```

## 💻 Usage Examples

### Basic Part Lookup

```python
import requests

# Initiate a lookup
response = requests.post(
    "http://localhost:8000/v1/lookup",
    json={"part_number": "WR55X10025"},
    headers={"Authorization": "Bearer YOUR_API_KEY"}
)

session_data = response.json()
print(f"Session ID: {session_data['session_id']}")

# Check status
status_response = requests.get(
    f"http://localhost:8000/v1/lookup/{session_data['session_id']}",
    headers={"Authorization": "Bearer YOUR_API_KEY"}
)

print(status_response.json())
```

### Retrieve Catalog Record

```python
# Get catalog by part number
response = requests.get(
    "http://localhost:8000/v1/catalog/by-part/WR55X10025",
    headers={"Authorization": "Bearer YOUR_API_KEY"}
)

catalog = response.json()
print(f"Manufacturer: {catalog['manufacturer']}")
print(f"Title: {catalog['part_title']}")
print(f"Confidence Score: {catalog['data_confidence_score']}")
```

### Salesforce Integration

```python
# Salesforce-optimized endpoint
response = requests.get(
    "http://localhost:8000/sf/v1/catalog/lookup/WR55X10025",
    headers={"Authorization": "Bearer SALESFORCE_TOKEN"}
)

part_data = response.json()
# Use in Salesforce...
```

### Search Catalog

```python
# Search for parts
response = requests.get(
    "http://localhost:8000/v1/catalog/search",
    params={
        "q": "defrost sensor",
        "manufacturer": "GE",
        "limit": 20
    },
    headers={"Authorization": "Bearer YOUR_API_KEY"}
)

results = response.json()
for part in results['results']:
    print(f"{part['mpn']}: {part['part_title']}")
```

## 🛠️ Development Guide

### Project Structure

```
Parts-Catalog-Enhancer-/
├── src/
│   ├── __init__.py
│   ├── api.py                    # FastAPI application
│   ├── config.py                 # Configuration management
│   ├── api_clients/              # External API clients
│   │   ├── base_client.py
│   │   ├── encompass_client.py
│   │   ├── marcone_client.py
│   │   ├── reliable_client.py
│   │   └── amazon_client.py
│   ├── normalizers/              # Data normalization
│   │   ├── base_normalizer.py
│   │   └── ...
│   ├── services/                 # Business logic
│   │   ├── lookup_service.py
│   │   ├── catalog_builder.py
│   │   ├── data_aggregator.py
│   │   └── parallel_executor.py
│   ├── ai/                       # AI validation
│   │   ├── openai_client.py
│   │   ├── grok_client.py
│   │   ├── consensus_engine.py
│   │   └── prompts.py
│   ├── repositories/             # Database access
│   │   ├── session_repository.py
│   │   ├── catalog_repository.py
│   │   └── ...
│   ├── models/                   # Pydantic models
│   │   ├── catalog.py
│   │   ├── session.py
│   │   └── ...
│   └── utils/                    # Utilities
│       ├── logging.py
│       ├── rate_limiter.py
│       └── ...
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── docs/                         # Documentation
├── scripts/                      # Utility scripts
├── alembic/                      # Database migrations
├── requirements.txt
├── docker-compose.yml
├── .env.example
└── README.md
```

### Running Tests

```bash
# Run all tests
pytest

# Run unit tests only
pytest tests/unit/

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test
pytest tests/unit/test_consensus_engine.py -v
```

### Code Style

We use:
- **Black** for code formatting
- **Flake8** for linting
- **MyPy** for type checking

```bash
# Format code
black src/ tests/

# Lint
flake8 src/ tests/

# Type check
mypy src/
```

### Adding a New API Integration

1. Create client in `src/api_clients/`:
```python
class NewAPIClient(BaseAPIClient):
    async def lookup_part(self, part_number: str) -> Dict:
        # Implementation
        pass
```

2. Create normalizer in `src/normalizers/`:
```python
class NewAPINormalizer(BaseNormalizer):
    def normalize(self, raw_data: Dict) -> Dict:
        # Map to standard fields
        pass
```

3. Update lookup service to include new source

4. Write tests

5. Update documentation

## 🚢 Deployment

### Docker Deployment

```bash
# Build image
docker build -t parts-catalog-api .

# Run container
docker run -p 8000:8000 \
  --env-file .env \
  parts-catalog-api
```

### Production Deployment (AWS)

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for detailed instructions.

Quick overview:
1. Provision RDS PostgreSQL instance
2. Set up ElastiCache Redis
3. Deploy to ECS or EC2
4. Configure load balancer
5. Set up CloudWatch monitoring
6. Configure auto-scaling

### Database Migrations

```bash
# Create a new migration
alembic revision -m "Description of change"

# Apply migrations
alembic upgrade head

# Rollback one version
alembic downgrade -1
```

## 📊 Monitoring

### Health Checks

```bash
# Check API health
curl http://localhost:8000/health

# Check database connection
curl http://localhost:8000/health/db

# Check external APIs
curl http://localhost:8000/health/apis
```

### Metrics

Key metrics to monitor:
- Lookup success rate
- Average processing time
- API response times (per source)
- AI validation success rate
- Database query performance
- Error rates
- Cost per lookup

### Dashboards

Access monitoring dashboards:
- Application: `http://localhost:8000/admin/dashboard`
- CloudWatch: AWS Console
- API Documentation: `http://localhost:8000/docs`

## 🔐 Security

- All API keys stored in environment variables or AWS Secrets Manager
- Database connections encrypted (SSL/TLS)
- API authentication via OAuth 2.0 or API keys
- Rate limiting on all endpoints
- Input validation and sanitization
- Regular security audits

## 📈 Performance

### Benchmarks (Target)

- Average lookup time: **< 30 seconds**
- API uptime: **99.5%+**
- Error rate: **< 2%**
- Database query time: **< 100ms (p95)**
- AI validation time: **< 15 seconds**

### Optimization Tips

1. **Enable caching**: Set `ENABLE_AI_CACHING=True`
2. **Use read replicas**: For high-traffic Salesforce queries
3. **Optimize images**: Compress before storing in S3
4. **Batch operations**: Use batch endpoints for multiple lookups
5. **Monitor costs**: Set up budget alerts for AI API usage

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

### Development Workflow

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`pytest`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## 📝 License

This project is proprietary and confidential.

## 👥 Team

- **Backend Lead**: [Name]
- **AI/ML Engineer**: [Name]
- **Database Engineer**: [Name]
- **DevOps Engineer**: [Name]
- **QA Engineer**: [Name]

## 📞 Support

- **Technical Issues**: Open a GitHub issue
- **Questions**: Contact the development team
- **Emergency**: [On-call rotation details]

## 🗺️ Roadmap

### Current Phase: Foundation (Weeks 1-3)
- ✅ Project setup complete
- ✅ Documentation complete
- ⏳ Encompass API integration
- ⏳ Database schema implementation

### Next Phases
- **Phase 2**: Multi-source integration (Weeks 4-6)
- **Phase 3**: AI validation (Weeks 7-10)
- **Phase 4**: Master catalog builder (Weeks 11-13)
- **Phase 5**: Salesforce integration (Weeks 14-16)
- **Phase 6**: Production readiness (Weeks 17-18)

See [docs/IMPLEMENTATION_ROADMAP.md](docs/IMPLEMENTATION_ROADMAP.md) for detailed timeline.

## 📚 Additional Resources

- [Implementation Plan](IMPLEMENTATION_PLAN.md) - Complete technical overview
- [Data Models](docs/DATA_MODELS.md) - Database schema and data structures
- [API Specification](docs/API_SPECIFICATION.md) - API documentation
- [AI Validation Logic](docs/AI_VALIDATION_LOGIC.md) - AI validation workflows
- [Troubleshooting Guide](docs/TROUBLESHOOTING.md) - Common issues and solutions

## 🎯 Success Metrics

### Phase 1 Success Criteria
- ✅ Can lookup parts from at least one source
- ✅ Data stored in database correctly
- ✅ API responds successfully

### Production Success Criteria
- 90%+ required fields populated
- 85%+ AI validation accuracy
- Cost per lookup < $0.50
- 99.5%+ uptime
- < 30 second average lookup time

---

**Version**: 1.0  
**Last Updated**: December 12, 2025  
**Status**: In Development

For questions or support, please contact the development team.
```

## Usage

### Testing AI Configuration

```python
from src.ai_config import call_openai, call_grok, call_ai_with_fallback

# Using OpenAI
result = call_openai("Describe a washing machine water inlet valve")

# Using Grok
result = call_grok("Describe a washing machine water inlet valve")

# With automatic fallback
result, provider = call_ai_with_fallback("Describe a washing machine water inlet valve")
print(f"Response from {provider}: {result}")
```

## API Keys

You'll need API keys from:
- **OpenAI**: https://platform.openai.com/api-keys
- **xAI (Grok)**: https://x.ai/api

## Next Steps

- [ ] Implement Salesforce API integration
- [ ] Create part enhancement service
- [ ] Build API endpoints for data input/output
- [ ] Add data validation and cleaning
- [ ] Implement batch processing
- [ ] Add logging and monitoring

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]
