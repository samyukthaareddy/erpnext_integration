# ERPNext CRM Integration API Documentation

**Version:** 1.0.0  
**Last Updated:** 2026-04-25  
**Status:** Production Ready

---

## Overview

The ERPNext CRM Integration API provides a unified endpoint for lead management with automated assignment and follow-up task creation. This service integrates with ERPNext to streamline the lead-to-task workflow.

## Base URL

```
http://localhost:5000/api/crm
```

## Authentication

### Internal API Key (Optional)
Set the `INTERNAL_API_KEY` environment variable to enable API key validation.

**Header:**
```
X-API-Key: <your-api-key>
```

When `INTERNAL_API_KEY` is empty or not set, key validation is disabled (development/test mode).

---

## Endpoints

### POST /process-lead

Process an incoming lead and automatically:
1. Validate the lead payload
2. Create a lead in ERPNext
3. Assign to a salesperson (using configured strategy)
4. Create a follow-up task

#### Request

**Method:** `POST`  
**Content-Type:** `application/json`  
**Max Payload Size:** 64 KB

##### Request Payload Schema

```json
{
  "name": "string (required)",
  "email": "string (required, valid email format)",
  "phone": "string (required, phone format: +1-XXX-XXX-XXXX or variations)",
  "company": "string (required)",
  "product_interest": "string (optional)",
  "message": "string (optional)",
  "source": "string (optional)"
}
```

##### Request Example

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

#### Response

##### Success Response (201 Created)

```json
{
  "lead_id": "LEAD-0001",
  "task_id": "TDO-000001",
  "assigned_to": "sales1@example.com",
  "status": "success"
}
```

**Response Fields:**
- `lead_id` (string): ERPNext Lead document ID
- `task_id` (string): ERPNext Task (ToDo) document ID
- `assigned_to` (string): Email/name of assigned salesperson
- `status` (string): Always "success" on 201

##### Error Response - Validation Failed (400 Bad Request)

```json
{
  "error": "Validation failed",
  "details": [
    "Email is not valid",
    "Phone is not valid"
  ]
}
```

##### Error Response - Missing Required Field (400 Bad Request)

```json
{
  "error": "Validation failed",
  "details": [
    "name is required",
    "email is required"
  ]
}
```

##### Error Response - Empty Payload (400 Bad Request)

```json
{
  "error": "No payload provided"
}
```

##### Error Response - Configuration Error (500 Internal Server Error)

```json
{
  "error": "Configuration error"
}
```

**Cause:** Missing ERPNext API credentials in environment variables.

##### Error Response - ERPNext API Error (500 Internal Server Error)

```json
{
  "error": "Lead creation failed: API Error message from ERPNext"
}
```

##### Error Response - Task Creation Failed (500 Internal Server Error)

```json
{
  "error": "Internal server error"
}
```

##### Error Response - Request Too Large (413 Payload Too Large)

```json
{
  "error": "Request too large"
}
```

**Cause:** Request payload exceeds 64 KB limit.

##### Error Response - Unauthorized (401 Unauthorized)

```json
{
  "error": "Unauthorized"
}
```

**Cause:** Invalid or missing `X-API-Key` header when `INTERNAL_API_KEY` is configured.

---

## Field Validation Rules

### Required Fields

| Field | Type | Rules | Example |
|-------|------|-------|---------|
| name | string | Non-empty, 1-500 chars | "John Doe" |
| email | string | Valid email format (RFC 5322) | "john@example.com" |
| phone | string | Phone format pattern | "+1-800-555-0199" |
| company | string | Non-empty, 1-500 chars | "ACME Corp" |

### Optional Fields

| Field | Type | Rules | Example |
|-------|------|-------|---------|
| product_interest | string | Max 500 chars | "ERP Solutions" |
| message | string | Max 1000 chars | "Need pricing info" |
| source | string | Max 100 chars | "website", "email", "phone" |

### Phone Format Examples

Valid phone formats (regex pattern):
```
+1-800-555-0199
+91-9999-999-999
+44-20-7946-0958
1-888-555-0000
```

---

## Assignment Strategies

The system supports three assignment strategies (configured in `config/assignment_rules.json`):

### 1. Round-Robin (Default)
Assigns leads sequentially to each salesperson in order. After the last salesperson, loops back to the first.

**Configuration:**
```json
{
  "strategy": "round_robin",
  "salespersons": [
    {"name": "sales1@example.com"},
    {"name": "sales2@example.com"}
  ]
}
```

### 2. By Capacity
Assigns leads to the salesperson with the most available capacity (highest capacity value).

**Configuration:**
```json
{
  "strategy": "by_capacity",
  "salespersons": [
    {"name": "sales1@example.com", "capacity": 10},
    {"name": "sales2@example.com", "capacity": 15}
  ]
}
```

### 3. By Product Expertise
Assigns leads based on matching product interest with salesperson expertise. Falls back to round-robin if no match.

**Configuration:**
```json
{
  "strategy": "by_product_expertise",
  "salespersons": [
    {
      "name": "sales1@example.com",
      "product_expertise": ["ERP", "CRM"]
    },
    {
      "name": "sales2@example.com",
      "product_expertise": ["Manufacturing", "Inventory"]
    }
  ]
}
```

---

## Follow-up Task Details

Automatically created tasks include:

- **Title:** "Follow up: {lead_name}"
- **Description:** Formatted with all lead details (email, phone, company, interests, message)
- **Due Date:** 24 hours from creation (configurable)
- **Assigned By:** The assigned salesperson
- **Reference:** Linked to the Lead document
- **Priority:** Medium

---

## Error Handling

### Validation Errors (400)
- Raised when lead payload fails schema validation
- Returns detailed list of validation failures
- No lead is created in ERPNext

### Configuration Errors (500)
- Raised when ERPNext credentials are missing
- Check `.env` file has `ERPNEXT_BASE_URL`, `ERPNEXT_API_KEY`, `ERPNEXT_API_SECRET`

### API Errors (500)
- Raised when ERPNext API calls fail
- Includes error message from ERPNext
- May result in partial state (lead created but not assigned, etc.)

### Request Size Errors (413)
- Raised when payload exceeds 64 KB
- Reduce payload size or split into multiple requests

### Security Errors (401)
- Raised when API key validation fails
- Verify `X-API-Key` header matches configured `INTERNAL_API_KEY`

---

## Rate Limiting

Currently no rate limiting is implemented. For production deployments, consider adding:
- Flask-Limiter for request rate limiting
- Database-backed session rate limiting per API key

---

## Example Integration Workflows

### Workflow 1: Website Lead Form → CRM

```javascript
fetch('http://localhost:5000/api/crm/process-lead', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    name: formData.name,
    email: formData.email,
    phone: formData.phone,
    company: formData.company,
    product_interest: formData.product,
    source: 'website_form'
  })
})
.then(response => response.json())
.then(data => {
  if (response.ok) {
    console.log('Lead created:', data.lead_id);
  } else {
    console.error('Error:', data.error);
  }
});
```

### Workflow 2: Email Integration

```python
import requests

payload = {
    "name": "Jane Smith",
    "email": "jane@company.com",
    "phone": "+1-555-123-4567",
    "company": "Tech Corp",
    "product_interest": "CRM System",
    "message": "Received inquiry from sales inquiry form",
    "source": "email"
}

response = requests.post(
    'http://localhost:5000/api/crm/process-lead',
    json=payload,
    headers={'X-API-Key': 'your-api-key'}
)

if response.status_code == 201:
    lead = response.json()
    print(f"Lead {lead['lead_id']} created and assigned to {lead['assigned_to']}")
else:
    print(f"Error: {response.json()['error']}")
```

---

## Environment Configuration

### Required Variables

```env
ERPNEXT_BASE_URL=https://your-erpnext-instance.com
ERPNEXT_API_KEY=your-api-key
ERPNEXT_API_SECRET=your-api-secret
```

### Optional Variables

```env
INTERNAL_API_KEY=your-internal-api-key      # Enables API key validation
FLASK_ENV=production                         # dev, test, or production
LOG_LEVEL=INFO                              # DEBUG, INFO, WARNING, ERROR
```

---

## Response Time & Performance

- **Typical Response Time:** 200-500ms (including ERPNext API calls)
- **Slow Query:** > 2s (indicates ERPNext performance issues)
- **Timeout:** No global timeout configured (set in production deployment)

---

## Status Codes Reference

| Code | Meaning | Action |
|------|---------|--------|
| 201 | Lead created successfully | Process complete, check response data |
| 400 | Bad request (validation/format) | Fix payload and retry |
| 401 | Unauthorized (invalid API key) | Check X-API-Key header |
| 413 | Payload too large | Reduce request size |
| 500 | Server error | Check logs, retry after fixing |

---

## Troubleshooting

### Lead created but not assigned
- Check `config/assignment_rules.json` has valid salesperson entries
- Verify assignment strategy is correctly configured

### Task not created but lead is assigned
- Check ERPNext Task/ToDo permissions for API user
- Verify task creation isn't failing silently (check logs)

### API key validation failing
- Ensure `X-API-Key` header exactly matches `INTERNAL_API_KEY` environment variable
- If key is empty, validation is disabled (development mode)

### ERPNext connection errors
- Verify `ERPNEXT_BASE_URL` is accessible
- Confirm `ERPNEXT_API_KEY` and `ERPNEXT_API_SECRET` are correct
- Check ERPNext user permissions for Lead and Task creation

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-04-25 | Initial release with lead creation, assignment, and task automation |
