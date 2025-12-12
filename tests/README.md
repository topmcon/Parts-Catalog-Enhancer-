# Tests

This directory contains test scripts for the Parts Catalog Enhancer.

## Available Tests

### `run_part_test.py`
Complete end-to-end test of the 6-stage architecture:
1. API Calls (Encompass, Marcone, Reliable Parts, Amazon)
2. Data Aggregation (keep sources separate)
3. OpenAI Validation
4. Grok Validation  
5. Consensus (requires 100% agreement)
6. Final Catalog Building

**Usage:**
```bash
python tests/run_part_test.py
```

**Output:**
- Console output showing each stage
- Markdown report: `PART_LOOKUP_RESULTS_<PART>_<TIMESTAMP>.md`

## Test Requirements

All tests use credentials from `.env` file in project root.

Required environment variables:
- `OPENAI_API_KEY`
- `XAI_API_KEY`
- `ENCOMPASS_USERNAME`, `ENCOMPASS_PASSWORD`, `ENCOMPASS_BASE_URL`
- `MARCONE_USERNAME_PROD`, `MARCONE_PASSWORD_PROD`, `MARCONE_API_URL_PROD`
- `RELIABLE_USERNAME`, `RELIABLE_PASSWORD`, `RELIABLE_API_KEY`, `RELIABLE_BASE_URL`
- `AMAZON_API_KEY`
