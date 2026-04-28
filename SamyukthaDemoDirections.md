# Samyuktha Demo Directions

## 1. What Has Been Completed (Phase 10 and Phase 11)

This section is the exact status you can present.

### Phase 10: ERPNext Lead/Task Format Alignment

Implemented now:

- Incoming payload now uses a canonical lead schema aligned to the provided format sheets.
- Lead mapping now supports spreadsheet-aligned fields across:
  - Company, First Name, Last Name, Job Title, Email, Phone, Fax, Mobile, Website, Industry
  - Lead Source, Lead Status, No. of Employees, Annual Revenue, Street, City, State, Zip Code, Country
  - Email Opt Out, Created By, Modified By, Last Activity Time, Description, Sales Person, Created Time, Lead Owner
- Task payload creation now supports spreadsheet-aligned fields across:
  - Task Owner, Company Name, Due Date, Contact Name, Related To, Status, Priority, Tag
  - Created By, Modified By, Reminder, Repeat, Closed Time, Description, Notes, Attachments
- Legacy payload support remains available for backward compatibility.
- ERPNext network dependencies are still mocked in tests, but lead/task field layout is no longer mock-only.

Code locations implemented:

- app/routes/crm.py
- app/task_service.py
- utils/schemas.py
- app/source_adapters.py

### Phase 11: Upstream Team Integration Foundation

Implemented now:

- Upstream adapter layer added to normalize different source payloads into one canonical schema before validation.
- Supported source adapters:
  - legacy
  - whatsapp
  - email
  - webform
- Route now runs adapter -> validation -> ERPNext mapping flow.

Code locations implemented:

- app/source_adapters.py
- app/routes/crm.py
- tests/test_source_adapters.py

### Test Status (for your confidence during demo)

Executed and passing:

- tests/test_validators.py
- tests/test_source_adapters.py
- tests/test_task_service.py
- tests/test_crm_routes.py

Result: 47 passed.

---

## 2. What You Need To Do Before Recording Demo

### Step A: Pull latest changes

```powershell
git pull
```

### Step B: Confirm app starts

```powershell
"d:/Git-REPOs/11. Intern/IdeaBytes/erpnext_integration/.venv/Scripts/python.exe" -m flask --app app.main run --debug --host 0.0.0.0 --port 5000
```

### Step C: Keep these files open while recording

- docs/API.md
- EXECUTION_STRUCTURE.md
- app/source_adapters.py
- app/routes/crm.py
- app/task_service.py
- tests/test_source_adapters.py

---

## 3. Exact Demo Video Flow (No Gaps)

Target length: 6 to 9 minutes.

### Part 1: Context (30 to 45 sec)

Say:

- We completed ERPNext integration architecture for lead to task flow.
- We finished Phase 10 and 11 priorities first.
- We replaced mock lead/task format assumptions with sheet-aligned mapping, while keeping non-ERPNext external dependencies mocked.

### Part 2: Show API Contract (60 to 90 sec)

Show docs/API.md and explain:

- POST /api/crm/process-lead
- Canonical required fields: company, first_name, last_name, email, phone
- Optional spreadsheet-driven lead/task fields
- source_type adapter support

### Part 3: Show Upstream Adapter Logic (90 sec)

Show app/source_adapters.py and explain quickly:

- legacy adapter for existing shape
- whatsapp adapter
- email adapter
- webform adapter
- all routes normalize to same schema before validation

### Part 4: Show Route + Mapping (90 sec)

Show app/routes/crm.py and explain flow:

- request parse
- normalize_incoming_lead
- validate_lead_payload
- build ERPNext lead payload
- assign salesperson
- create follow-up task
- response with lead_id, task_id, assigned_to, status

### Part 5: Show Task Mapping (60 sec)

Show app/task_service.py and explain:

- task description generation
- due date logic
- spreadsheet-aligned task keys
- create task call through ERPNext client

### Part 6: Prove It with Tests (60 to 90 sec)

Run:

```powershell
"d:/Git-REPOs/11. Intern/IdeaBytes/erpnext_integration/.venv/Scripts/python.exe" -m pytest tests/test_validators.py tests/test_source_adapters.py tests/test_task_service.py tests/test_crm_routes.py -q
```

Say:

- All updated phase-specific tests pass.
- Mocking is now only for external ERPNext call boundaries and not for lead/task field format assumptions.

### Part 7: Show API Example Run (60 sec)

Use one payload from docs/API.md and show response keys:

- lead_id
- task_id
- assigned_to
- status

### Part 8: Close with Remaining Scope (30 sec)

Say clearly:

- Next milestone is full live ERPNext verification plus final integration with other team systems in runtime environment.
- Current code already supports multi-source normalization and canonical validation.

---

## 4. What You Should Push

If you are pushing from your system after verification:

```powershell
git add app/source_adapters.py app/routes/crm.py app/task_service.py utils/schemas.py tests/test_source_adapters.py tests/test_crm_routes.py tests/test_task_service.py tests/test_validators.py docs/API.md README.md EXECUTION_STRUCTURE.md SamyukthaDemoDirections.md

git commit -m "feat: complete phase 10 and 11 with format-aligned mapping and source adapters"

git push
```

If push fails due branch mismatch:

```powershell
git branch

git push -u origin <your-branch-name>
```

---

## 5. Talking Track (Short)

You can use this exactly:

- We completed Phase 10 by aligning lead and task mapping with the mentor-shared format sheets.
- We completed Phase 11 by implementing upstream source adapters for legacy, WhatsApp, email, and webform payloads.
- The route now normalizes all inputs into a canonical schema, validates once, maps cleanly, and proceeds to assignment and task creation.
- Updated tests are passing, and we can demo the full flow from input to response with proof.
