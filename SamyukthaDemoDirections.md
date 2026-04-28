# Demo Execution Guide

## 1. Current Delivery Status

### Phase 10: ERPNext Lead and Task Format Alignment

Completed scope:

- Lead payload mapping has been aligned with the shared ERPNext lead format sheet.
- Task payload mapping has been aligned with the shared ERPNext task format sheet.
- Canonical validation is applied before ERPNext payload construction.
- Legacy input compatibility is retained for existing callers.

Primary implementation files:

- app/routes/crm.py
- app/task_service.py
- utils/schemas.py

### Phase 11: Upstream Input Integration Foundation

Completed scope:

- Source adapter layer implemented for `legacy`, `whatsapp`, `email`, and `webform` inputs.
- Route pipeline is standardized as: normalize -> validate -> map -> create lead -> assign -> create task.

Primary implementation files:

- app/source_adapters.py
- app/routes/crm.py
- tests/test_source_adapters.py

### Validation status

- Test suites for validators, source adapters, CRM route flow, and task service are passing.

---

## 2. ERPNext Environment Preparation (Live Demo)

1. Open ERPNext web instance with an integration-capable user account.
2. Generate API credentials for the integration user:
- API Key
- API Secret
3. Capture ERPNext base URL.
4. Confirm user permissions for:
- Lead create/read/update
- ToDo or Task create/read

---

## 3. Local Configuration

Create or update `.env` with live ERPNext values:

```env
ERPNEXT_BASE_URL=https://your-erpnext-instance
ERPNEXT_API_KEY=your_real_api_key
ERPNEXT_API_SECRET=your_real_api_secret
FLASK_ENV=development
FLASK_DEBUG=1
LOG_LEVEL=INFO
```

Start the service:

```powershell
"d:/Git-REPOs/11. Intern/IdeaBytes/erpnext_integration/.venv/Scripts/python.exe" -m flask --app app.main run --debug --host 0.0.0.0 --port 5000
```

---

## 4. Demonstration Plan

Target duration: 6 to 9 minutes.

### Segment A: Brief project context

State:

- Phase 10 and Phase 11 were prioritized and completed.
- Lead and task mappings now follow official field formats.
- Upstream source adapters are implemented for multi-source intake.

### Segment B: Architecture walkthrough

Display and summarize:

- docs/API.md (API contract)
- app/source_adapters.py (normalization layer)
- app/routes/crm.py (processing pipeline)
- app/task_service.py (task field mapping and due date handling)

### Segment C: Live ERPNext flow

Execute request:

```powershell
curl -X POST http://127.0.0.1:5000/api/crm/process-lead -H "Content-Type: application/json" -d "{\"company\":\"Demo Corp\",\"first_name\":\"Riya\",\"last_name\":\"Shah\",\"email\":\"riya.demo+1@example.com\",\"phone\":\"+1-800-555-1111\",\"lead_source\":\"website\",\"message\":\"Please schedule a demo\"}"
```

Show API response keys:

- `lead_id`
- `task_id`
- `assigned_to`
- `status`

Then show ERPNext UI verification:

- CRM -> Leads: newly created lead
- ToDo/Tasks: linked follow-up task
- Assignment visibility on lead

### Segment D: Fallback demonstration (if live ERPNext is unavailable)

If external ERPNext connectivity is unavailable, run test proof path:

```powershell
"d:/Git-REPOs/11. Intern/IdeaBytes/erpnext_integration/.venv/Scripts/python.exe" -m pytest tests/test_validators.py tests/test_source_adapters.py tests/test_task_service.py tests/test_crm_routes.py -q
```

State:

- Phase-specific validation is passing.
- Field mapping is aligned to official formats.
- Only external connectivity boundary is mocked in fallback mode.

---

## 5. ERPNext Source Fork vs Web/API Integration

Recommended statement:

- Integration is implemented through ERPNext web instance and REST APIs.
- ERPNext source forking is required only for ERPNext internal customization (custom doctypes or server-side logic).
- Current project scope is correctly addressed by API-based integration.

---

## 6. Pre-Recording Checklist

- `.env` configured with valid live credentials
- Flask app starts without runtime errors
- ERPNext browser tabs prepared (Leads and ToDo/Tasks)
- Unique lead email prepared for live request
- Fallback test command ready

---

## 7. Push Commands

```powershell
git add app/source_adapters.py app/routes/crm.py app/task_service.py utils/schemas.py tests/test_source_adapters.py tests/test_crm_routes.py tests/test_task_service.py tests/test_validators.py docs/API.md README.md EXECUTION_STRUCTURE.md SamyukthaDemoDirections.md

git commit -m "docs: professional demo execution guide for live ERPNext and fallback flow"

git push
```

If branch tracking is required:

```powershell
git branch
git push -u origin <your-branch-name>
```
