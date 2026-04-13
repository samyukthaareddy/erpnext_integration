# Task 3: ERPNext CRM Integration

This repository contains the work for **Task 3** of the AI-Driven Sales & Marketing Automation System.

Team members:
- Harshita
- Samyukthaa

## Purpose

Task 3 is the CRM backbone for the project. It receives structured lead data from the WhatsApp, email, or web-form workflows built by the other teams and pushes that lead into ERPNext.

The integration is responsible for:
- creating a Lead record in ERPNext
- assigning the lead to the right salesperson
- creating a follow-up Task for that salesperson
- returning the ERPNext IDs back to the caller

## Scope

The intended flow is:
1. Receive a lead payload through a REST endpoint.
2. Validate the payload.
3. Create a Lead in ERPNext through the Frappe REST API.
4. Assign the lead using configurable routing rules.
5. Create a follow-up Task linked to the Lead.
6. Return a response containing the Lead ID, Task ID, assignment, and status.

## Planned Stack

- Python 3.11+
- Flask for the API service
- requests for ERPNext REST calls
- python-dotenv for environment variables
- jsonschema for payload validation
- pytest for tests
- Postman for endpoint verification
- Redis as an optional persistence layer for assignment state

## Expected API Contract

The service is expected to expose a POST endpoint similar to:

```http
POST /api/crm/process-lead
Content-Type: application/json
```

Example payload:

```json
{
	"name": "Amit Sharma",
	"company": "Sharma Traders",
	"email": "amit@example.com",
	"phone": "+91-9876543210",
	"product_interest": "Industrial sensors",
	"message": "Need pricing for bulk order, urgent requirement this week",
	"source": "whatsapp"
}
```

Expected response shape:

```json
{
	"lead_id": "ERP-LEAD-0001",
	"task_id": "ERP-TASK-0009",
	"assigned_to": "Salesperson Name",
	"status": "success"
}
```

## Configuration

Runtime settings should be stored in a local `.env` file and must not be committed.

Common variables for this integration:
- ERPNext base URL
- ERPNext API key
- ERPNext API secret
- default assignment rules
- optional Redis connection details

## Development Notes

- Keep assignment logic isolated so it can be tested without ERPNext.
- Use a mock payload fixture while the upstream teams are still building their integrations.
- Log API failures and validation errors clearly so the integration is easy to debug.

## Repository Contents

At the moment this repository is documentation-first. As implementation starts, add the service code, tests, and supporting fixtures alongside this README.

## Deliverable Definition

Task 3 is complete when a single API call can:
- create a new ERPNext Lead
- assign it to the correct salesperson
- create a follow-up Task
- return the generated identifiers to the caller

