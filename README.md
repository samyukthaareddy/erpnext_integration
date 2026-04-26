# Task 3: ERPNext CRM Integration

This repository contains the implementation of **Task 3** for the AI-Driven Sales & Marketing Automation System.

**Status:** ✅ Production Ready  
**Team:** Harshita & Samyukthaa  
**Test Coverage:** 91% (95 tests)  
**Last Updated:** 2026-04-25

---

## Overview

The ERPNext CRM Integration service receives structured lead data from upstream systems (WhatsApp, email, web forms) and orchestrates the complete lead-to-task workflow in ERPNext:

1. **Validate** incoming lead payload
2. **Create** Lead record in ERPNext
3. **Assign** lead to salesperson (round-robin, capacity, or expertise-based)
4. **Create** follow-up Task for assigned salesperson
5. **Return** ERPNext IDs (lead_id, task_id, assigned_to, status)

### Key Features

- ✅ RESTful API (`POST /api/crm/process-lead`)
- ✅ Input validation & sanitization (prevents SQL/XSS injection)
- ✅ 3 assignment strategies (round-robin, capacity, product expertise)
- ✅ Automatic follow-up task creation (24h due date)
- ✅ Comprehensive error handling with rollback logic
- ✅ Request size limiting (64 KB max)
- ✅ Detailed logging for debugging
- ✅ Docker support for easy deployment
- ✅ 91% code coverage with 95 tests
- ✅ Complete API documentation & Postman collection

---

## Quick Start

### Prerequisites

- Python 3.8+
- pip (Python package manager)
- Active ERPNext instance with API credentials
- Git

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/samyukthaareddy/erpnext_integration.git
   cd erpnext_integration
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

### Local Setup

1. **Create `.env` file from template:**
   ```bash
   cp .env.example .env
   ```

2. **Update `.env` with your credentials:**
   ```env
   # ERPNext Configuration
   ERPNEXT_BASE_URL=https://your-erpnext-instance.com
   ERPNEXT_API_KEY=your_api_key_here
   ERPNEXT_API_SECRET=your_api_secret_here
   
   # Flask Configuration
   FLASK_ENV=development
   FLASK_DEBUG=1
   
   # Logging
   LOG_LEVEL=INFO
   
   # Optional: Internal API Key (leave empty to disable)
   INTERNAL_API_KEY=
   ```

3. **Verify setup:**
   ```bash
   python -c "from app.main import create_app; app = create_app(); print('✓ Setup successful')"
   ```

### Running the Service

**Development mode:**
```bash
python -m flask run
```

Service available at: `http://localhost:5000`

**Using Makefile (recommended):**
```bash
make run
```

**Production mode (with Docker):**
```bash
docker-compose -f docker-compose.prod.yml up -d
```

### Testing

**Run all tests:**
```bash
pytest
```

**Run with coverage report:**
```bash
pytest --cov=app --cov=utils --cov-report=html
```

**Run specific test file:**
```bash
pytest tests/test_crm_routes.py -v
```

**Run tests matching pattern:**
```bash
pytest tests/ -k "validation" -v
```

### Making Requests

**Using cURL:**
```bash
curl -X POST http://localhost:5000/api/crm/process-lead \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "+1-800-555-0199",
    "company": "ACME Corp",
    "product_interest": "ERP Solutions",
    "message": "Interested in demo",
    "source": "website"
  }'
```

**Using Python:**
```python
import requests

payload = {
    "name": "Jane Smith",
    "email": "jane@example.com",
    "phone": "+1-555-123-4567",
    "company": "Tech Corp",
    "product_interest": "CRM System",
    "source": "email"
}

response = requests.post(
    'http://localhost:5000/api/crm/process-lead',
    json=payload
)

print(response.json())
```

---

## Project Structure

```
erpnext_integration/
├── app/                          # Main application code
│   ├── __init__.py
│   ├── main.py                   # Flask app initialization
│   ├── erpnext_client.py         # ERPNext API wrapper
│   ├── assignment_engine.py      # Lead assignment logic
│   ├── task_service.py           # Follow-up task creation
│   ├── exceptions.py             # Custom exceptions
│   ├── middleware.py             # Security & input sanitization
│   └── routes/
│       ├── __init__.py
│       └── crm.py                # Lead processing endpoint
├── config/                       # Configuration
│   ├── __init__.py
│   ├── settings.py               # Environment & config
│   ├── logging.py                # Logging setup
│   └── assignment_rules.json     # Assignment strategy config
├── tests/                        # Test suite (95 tests, 91% coverage)
│   ├── conftest.py
│   ├── test_validators.py
│   ├── test_erpnext_client.py
│   ├── test_crm_routes.py
│   ├── test_assignment_engine.py
│   ├── test_task_service.py
│   ├── test_middleware.py
│   ├── test_exceptions.py
│   └── fixtures/
├── utils/                        # Utility functions
│   ├── __init__.py
│   ├── schemas.py                # JSON validation schemas
│   └── validators.py             # Payload validation
├── docs/                         # Documentation
│   ├── API.md                    # Complete API reference
│   ├── TESTING.md                # Testing guide
│   └── postman_collection.json   # Postman collection
├── .env.example                  # Environment template
├── .gitignore
├── Dockerfile                    # Docker image
├── docker-compose.yml            # Local Docker setup
├── docker-compose.prod.yml       # Production Docker setup
├── Makefile                      # Common tasks
├── requirements.txt              # Python dependencies
├── setup.py                      # Package setup
└── README.md                     # This file
```

---

## Configuration

### Environment Variables

**Required:**
- `ERPNEXT_BASE_URL`: Your ERPNext instance URL
- `ERPNEXT_API_KEY`: ERPNext API key
- `ERPNEXT_API_SECRET`: ERPNext API secret

**Optional:**
- `FLASK_ENV`: `development`, `testing`, or `production` (default: `development`)
- `FLASK_DEBUG`: `1` to enable debug mode
- `LOG_LEVEL`: `DEBUG`, `INFO`, `WARNING`, `ERROR` (default: `INFO`)
- `INTERNAL_API_KEY`: Set to enable API key validation (leave empty to disable)

### Assignment Rules

Edit `config/assignment_rules.json` to configure lead assignment:

```json
{
  "strategy": "round_robin",
  "salespersons": [
    {"name": "sales1@example.com", "product_expertise": ["ERP"], "capacity": 10},
    {"name": "sales2@example.com", "product_expertise": ["CRM"], "capacity": 15}
  ]
}
```

**Strategies:**
- `round_robin`: Cycle through salespersons in order
- `by_capacity`: Assign to person with highest available capacity
- `by_product_expertise`: Match lead interest with person's expertise

---

## API Documentation

### Endpoint: POST /api/crm/process-lead

Full documentation available in `docs/API.md`

**Request:**
```json
{
  "name": "string (required)",
  "email": "string (required, valid email)",
  "phone": "string (required, phone format)",
  "company": "string (required)",
  "product_interest": "string (optional)",
  "message": "string (optional)",
  "source": "string (optional)"
}
```

**Success Response (201):**
```json
{
  "lead_id": "LEAD-0001",
  "task_id": "TDO-000001",
  "assigned_to": "sales1@example.com",
  "status": "success"
}
```

**Error Response (400/500):**
```json
{
  "error": "Validation failed",
  "details": ["email is not valid"]
}
```

---

## Troubleshooting

### Issue: "Missing ERPNext credentials"
**Solution:** Verify `.env` file has correct values:
```bash
cat .env | grep ERPNEXT
```

### Issue: "Invalid ERPNext credentials"
**Solution:** Test ERPNext connection:
```bash
python -c "from app.erpnext_client import ERPNextClient; c = ERPNextClient(); print('Connected!')"
```

### Issue: Leads created but not assigned
**Solution:** Check `config/assignment_rules.json` has valid salesperson entries:
```bash
cat config/assignment_rules.json
```

### Issue: Tests failing after environment changes
**Solution:** Clear cache and reinstall:
```bash
make clean
pip install -r requirements.txt
pytest
```

### Issue: Port 5000 already in use
**Solution:** Use different port:
```bash
FLASK_RUN_PORT=5001 python -m flask run
```

### Issue: ERPNext API returning 403 (Permission Denied)
**Solution:** Verify API user has permissions for:
- Lead (create, update, read)
- ToDo/Task (create, read)
- User (read)

### Issue: Request payload too large
**Solution:** Payload exceeded 64 KB limit. Split into multiple requests or optimize payload size.

---

## Testing

### Test Coverage

Current coverage: **91%** (295 statements)

```
app/__init__.py              100%
app/assignment_engine.py    100%
app/exceptions.py           100%
app/routes/crm.py           100%
app/task_service.py         100%
utils/                      100%
app/middleware.py            85%
app/main.py                  88%
app/erpnext_client.py        81%
```

### Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=app --cov=utils

# Specific test file
pytest tests/test_crm_routes.py

# Verbose output
pytest -v

# Stop on first failure
pytest -x

# Show print statements
pytest -s

# Run tests matching pattern
pytest -k "assignment"
```

### Test Files

- `test_validators.py` - Payload validation
- `test_erpnext_client.py` - ERPNext API client
- `test_crm_routes.py` - Lead processing endpoint (16 tests)
- `test_assignment_engine.py` - Lead assignment logic (9 tests)
- `test_task_service.py` - Task creation service (12 tests)
- `test_middleware.py` - Security & input sanitization (16 tests)
- `test_exceptions.py` - Error handling (18 tests)

---

## Development Workflow

### Making Changes

1. Create feature branch:
   ```bash
   git checkout -b feature/your-feature
   ```

2. Make changes and test:
   ```bash
   pytest --cov
   ```

3. Commit with descriptive message:
   ```bash
   git commit -m "feat(crm): add new feature"
   ```

4. Push and create PR:
   ```bash
   git push origin feature/your-feature
   ```

### Code Style

- Follow PEP 8
- Use type hints where possible
- Write docstrings for functions
- Keep functions small and focused
- Test-driven development preferred

---

## Docker Deployment

### Local Development (Docker)

```bash
docker-compose up -d
docker-compose logs -f
```

### Production Deployment

```bash
docker-compose -f docker-compose.prod.yml up -d
```

**Environment file:** Create `.env.prod` with production credentials

---

## Useful Commands

```bash
make install       # Install dependencies
make test          # Run tests with coverage
make run           # Run development server
make clean         # Clean up cache/build files
make lint          # Run code quality checks (if configured)
make docker-up     # Start Docker containers
make docker-down   # Stop Docker containers
```

---

## Documentation

- **[API Reference](docs/API.md)** - Complete endpoint documentation
- **[Testing Guide](docs/TESTING.md)** - Manual testing procedures
- **[Postman Collection](docs/postman_collection.json)** - Import into Postman for API testing

---

## Support & Issues

For issues, questions, or suggestions:

1. Check [Troubleshooting](#troubleshooting) section
2. Review [docs/API.md](docs/API.md) for API details
3. Check test files for usage examples
4. Open an issue on GitHub

---

## License

Internal project - Proprietary

---

## Contributors

- **Harshita** - Phases 1, 3, 5, 7, 9
- **Samyukthaa** - Phases 2, 4, 6, 8

---

**Ready for production deployment.** All 9 phases complete with 91% test coverage.

