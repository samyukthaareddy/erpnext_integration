# Manual Testing Guide

## Prerequisites

1. Service is running locally:
   ```bash
   make run
   # or
   docker-compose up
   ```
2. `.env` file is configured with valid ERPNext credentials
3. ERPNext instance is accessible at `ERPNEXT_BASE_URL`

---

## Postman Setup

1. Open Postman → Import → select `docs/postman_collection.json`
2. Set collection variable `base_url` to `http://localhost:5000`
3. If `INTERNAL_API_KEY` is set in `.env`, set the `api_key` variable and enable the `X-API-Key` header on each request

---

## Manual Testing Checklist

### ✅ Test 1: Happy Path

**Request:**
```bash
curl -X POST http://localhost:5000/api/crm/process-lead \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john.doe@example.com",
    "phone": "+1-800-555-0199",
    "company": "ACME Corp",
    "product_interest": "ERP Solutions",
    "message": "Interested in a demo",
    "source": "website"
  }'
```

**Expected Response (201):**
```json
{
  "lead_id": "LEAD-XXXX",
  "task_id": "TDO-XXXXXX",
  "assigned_to": "sales1@example.com",
  "status": "success"
}
```

**Verify in ERPNext:**
- [ ] Lead exists under CRM → Leads
- [ ] Lead is assigned to the correct salesperson
- [ ] Follow-up task exists under TODO with correct due date (24h from now)

---

### ✅ Test 2: Validation Error — Missing Fields

**Request:**
```bash
curl -X POST http://localhost:5000/api/crm/process-lead \
  -H "Content-Type: application/json" \
  -d '{"name": "Jane Smith", "company": "Tech Corp"}'
```

**Expected Response (400):**
```json
{
  "error": "Validation failed: [...]"
}
```

- [ ] Status code is 400
- [ ] Error message mentions missing fields
- [ ] No lead created in ERPNext

---

### ✅ Test 3: Validation Error — Invalid Email & Phone

**Request:**
```bash
curl -X POST http://localhost:5000/api/crm/process-lead \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Jane Smith",
    "email": "not-an-email",
    "phone": "abc",
    "company": "Tech Corp"
  }'
```

**Expected Response (400):**
```json
{
  "error": "Validation failed: [...]"
}
```

- [ ] Status code is 400
- [ ] No lead created in ERPNext

---

### ✅ Test 4: Assignment Verification

**Request:**
```bash
curl -X POST http://localhost:5000/api/crm/process-lead \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Alice Brown",
    "email": "alice@company.com",
    "phone": "+1-555-123-4567",
    "company": "Manufacturing Co",
    "product_interest": "Manufacturing",
    "source": "referral"
  }'
```

- [ ] `assigned_to` in response matches expected salesperson for "Manufacturing" expertise
- [ ] Lead in ERPNext shows correct assignment

---

### ✅ Test 5: Task Creation Verification

After a successful happy path request:

- [ ] `task_id` is present and non-null in response
- [ ] Task exists in ERPNext TODO list
- [ ] Task title is `Follow up: {lead_name}`
- [ ] Task due date is approximately 24 hours from creation time
- [ ] Task is linked to the correct Lead document

---

### ✅ Test 6: Empty Payload

**Request:**
```bash
curl -X POST http://localhost:5000/api/crm/process-lead \
  -H "Content-Type: application/json" \
  -d '{}'
```

- [ ] Status code is 400
- [ ] Error message is `"No payload provided"` or validation error

---

### ✅ Test 7: Request Too Large

```bash
# Generate a payload > 64KB and send it
python -c "import json, requests; requests.post('http://localhost:5000/api/crm/process-lead', json={'name': 'x' * 70000, 'email': 'a@b.com', 'phone': '1234567', 'company': 'x'})"
```

- [ ] Status code is 413
- [ ] Error message is `"Request too large"`

---

### ✅ Test 8: API Key Validation (if INTERNAL_API_KEY is set)

**Without key:**
```bash
curl -X POST http://localhost:5000/api/crm/process-lead \
  -H "Content-Type: application/json" \
  -d '{"name": "Test", "email": "t@t.com", "phone": "+1-800-555-0199", "company": "Test"}'
```
- [ ] Status code is 401

**With correct key:**
```bash
curl -X POST http://localhost:5000/api/crm/process-lead \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-key-here" \
  -d '{"name": "Test", "email": "t@t.com", "phone": "+1-800-555-0199", "company": "Test"}'
```
- [ ] Request proceeds normally

---

## Docker Testing

```bash
# Build and start
docker-compose up --build

# Run against containerized service
curl -X POST http://localhost:5000/api/crm/process-lead \
  -H "Content-Type: application/json" \
  -d @docs/sample_lead.json

# Stop
docker-compose down
```

- [ ] Container builds without errors
- [ ] Service starts and responds on port 5000
- [ ] All happy path tests pass against container

---

## Automated Tests

```bash
# Run full test suite
pytest --cov=app --cov=utils --cov-report=term-missing

# Expected: all tests pass, coverage >= 80%
```

- [ ] All tests pass
- [ ] Coverage report shows >= 80%
