# AI PROMPT: Flask API Code Enhancements for Spring Boot Integration

**Codebase Analysis Completed**

Your existing Flask API has:
- ✅ Source adapters (legacy, whatsapp, email, webform)
- ✅ JSON schema validation
- ✅ ERPNext API client
- ✅ Assignment engine (3 strategies)
- ✅ Task service
- ✅ Error handling
- ✅ Logging

**What needs to be added for Spring Boot integration:**

---

## PART 1: CONTEXT FOR AI ASSISTANT

**When you invoke Claude with `/plan` or start coding, provide this context:**

```
PROJECT: AI-Driven Sales & Marketing Automation System
COMPONENT: Flask API Service (Task 3 - Enhancements)
CONTEXT: Spring Boot orchestrator will call this API for lead processing

CURRENT STRUCTURE:
- Entry point: app/main.py (Flask app)
- Routes: app/routes/crm.py (POST /api/crm/process-lead)
- Validation: utils/schemas.py, utils/validators.py
- ERPNext client: app/erpnext_client.py (REST API wrapper)
- Assignment: app/assignment_engine.py (3 strategies)
- Tasks: app/task_service.py (follow-up creation)
- Adapters: app/source_adapters.py (normalize 3 sources)
- Config: config/settings.py, config/logging.py

EXISTING ENDPOINTS:
1. POST /api/crm/process-lead
   - Input: {company, first_name, last_name, email, phone, ...}
   - Output: {lead_id, task_id, assigned_to, status}
   - Calls ERPNext: create lead, create task, assign

INTEGRATION POINT:
- Spring Boot will send normalized lead data
- Spring Boot expects specific response format
- Spring Boot needs to know if API is healthy
- Spring Boot may send bulk leads later

CONSTRAINTS:
- No changes to existing /process-lead endpoint (backward compatible)
- Keep source adapters (other teams may use)
- Keep assignment engine (reusable logic)
- Add new features without breaking existing tests
- Maintain 70%+ code coverage
```

---

## PART 2: DETAILED ENHANCEMENT PROMPT FOR AI

**Use this exact prompt when working with Claude:**

```
# Flask API Enhancements: Spring Boot Integration

## Context
Your existing Flask API (app/routes/crm.py) currently has POST /api/crm/process-lead that:
- Receives: {company, first_name, last_name, email, phone, ...}
- Returns: {lead_id, task_id, assigned_to, status}
- Calls ERPNext to create lead → task → assign

Spring Boot (Java orchestrator) will now call this API. You need to add 3 new features.

## Current Code Reference
- API endpoint: /d/Git-REPOs/11. Intern/IdeaBytes/erpnext_integration/app/routes/crm.py
- Response format: Lines 116-120 (current success response)
- Error handling: Lines 123-129 (current error handling)
- Schemas: /d/Git-REPOs/11. Intern/IdeaBytes/erpnext_integration/utils/schemas.py
- ERPNext client: /d/Git-REPOs/11. Intern/IdeaBytes/erpnext_integration/app/erpnext_client.py (lines 1-100)

## Enhancement 1: Health Check Endpoint

### What it does:
- Returns API health status
- Checks ERPNext connectivity
- Used by Spring Boot liveness probe + Kubernetes

### Implementation:
File: app/routes/crm.py (add new endpoint)

```python
@bp.route("/health", methods=["GET"])
def health_check():
    """
    Health check endpoint for monitoring + Spring Boot liveness probe
    
    Returns: {status, erpnext_connected, timestamp, api_version}
    HTTP 200: Healthy
    HTTP 503: Unhealthy (ERPNext down)
    """
    try:
        client = ERPNextClient()
        # Verify ERPNext connectivity by attempting a simple API call
        # Example: Get a single lead to verify connection
        response = client.session.get(
            client._build_url("Lead?fields=[\"name\"]&limit_page_length=1"),
            timeout=5
        )
        erpnext_connected = response.status_code == 200
    except Exception as e:
        logger.warning(f"Health check: ERPNext unreachable - {e}")
        erpnext_connected = False
    
    status = "healthy" if erpnext_connected else "degraded"
    http_code = 200 if erpnext_connected else 503
    
    return jsonify({
        "status": status,
        "erpnext_connected": erpnext_connected,
        "api_version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }), http_code
```

### Tests needed:
- Test /health when ERPNext is up (should return 200 + healthy)
- Test /health when ERPNext is down (should return 503 + degraded)
- Test response format includes all required fields

---

## Enhancement 2: Bulk Lead Processing Endpoint

### What it does:
- Process multiple leads in one call (if Spring Boot gets batch)
- Return array of results with success/failure for each
- Atomic operations (each lead independent)

### Implementation:
File: app/routes/crm.py (add new endpoint)

```python
@bp.route("/process-leads", methods=["POST"])
def process_leads_batch():
    """
    Process multiple leads in batch
    
    Input: {leads: [{...lead1}, {...lead2}, {...lead3}]}
    Output: {
        success_count: 2,
        failed_count: 1,
        results: [
            {lead_id: "LEAD-0001", status: "success", ...},
            {lead_id: "LEAD-0002", status: "success", ...},
            {error: "Invalid email", status: "failed", index: 2}
        ]
    }
    
    Notes:
    - Each lead processed independently
    - Failures don't stop other leads
    - Return 207 Multi-Status (some success, some failure)
    """
    try:
        payload = request.get_json(silent=True)
        if not payload or not isinstance(payload.get("leads"), list):
            return jsonify({"error": "Expected {leads: [...]}"})(), 400
        
        leads = payload.get("leads", [])
        results = []
        success_count = 0
        failed_count = 0
        
        for index, lead_payload in enumerate(leads):
            try:
                # Normalize
                canonical = normalize_incoming_lead(lead_payload)
                
                # Validate
                errors = validate_lead_payload(canonical)
                if errors:
                    results.append({
                        "index": index,
                        "status": "failed",
                        "error": "Validation failed",
                        "details": errors
                    })
                    failed_count += 1
                    continue
                
                # Process (same as /process-lead)
                client = ERPNextClient()
                lead_data = {...}  # Same mapping as /process-lead
                lead = client.create_lead(lead_data)
                lead_id = lead.get("name")
                
                assigned_to = assign_to_salesperson(canonical)
                client.update_lead(lead_id, {"_assign": assigned_to})
                
                task = create_followup_task(lead_id, assigned_to, canonical, client)
                task_id = task.get("name")
                
                results.append({
                    "index": index,
                    "lead_id": lead_id,
                    "task_id": task_id,
                    "assigned_to": assigned_to,
                    "status": "success"
                })
                success_count += 1
                
            except Exception as e:
                logger.error(f"Batch processing failed at index {index}: {e}")
                results.append({
                    "index": index,
                    "status": "failed",
                    "error": str(e)
                })
                failed_count += 1
        
        http_code = 200 if failed_count == 0 else 207  # 207 = Multi-Status
        
        return jsonify({
            "success_count": success_count,
            "failed_count": failed_count,
            "results": results
        }), http_code
        
    except Exception as e:
        logger.error(f"Batch processing error: {e}")
        return jsonify({"error": "Batch processing failed", "message": str(e)}), 500
```

### Tests needed:
- Test batch of 3 leads, all valid (should return 200 + 3 successes)
- Test batch of 3 leads, 1 invalid (should return 207 + 2 success + 1 failed)
- Test empty batch (should return 400)
- Test concurrent batch calls (verify no race conditions)

---

## Enhancement 3: Enhanced Response with URLs + Metadata

### What it does:
- Current response only has {lead_id, task_id, assigned_to, status}
- Enhanced response includes: ERPNext URLs, timestamps, metadata for Spring Boot

### Implementation:
File: app/routes/crm.py (modify existing /process-lead endpoint)

**Find this section (lines 116-120):**
```python
return jsonify({
    "lead_id": lead_id,
    "task_id": task_id,
    "assigned_to": assigned_to,
    "status": "success"
}), 201
```

**Replace with:**
```python
# Construct ERPNext URLs for Spring Boot to verify
erpnext_base = ERPNextClient().base_url
lead_url = f"{erpnext_base}/app/lead/{lead_id}"
task_url = f"{erpnext_base}/app/todo/{task_id}"

response = {
    # Original fields (backward compatible)
    "lead_id": lead_id,
    "task_id": task_id,
    "assigned_to": assigned_to,
    "status": "success",
    
    # New fields for Spring Boot
    "lead_url": lead_url,        # For dashboard links
    "task_url": task_url,        # For dashboard links
    "created_at": datetime.utcnow().isoformat(),  # For audit
    "erpnext_name": lead_id,     # Confirm what was created
    "assignment_strategy": rules.get("strategy", "round_robin"),  # Which strategy was used
}

logger.info(f"Lead process success: {lead_id} → {assigned_to}")
return jsonify(response), 201
```

### Tests needed:
- Verify response contains all new fields
- Verify URLs are correct format
- Verify backward compatibility (old fields still present)

---

## Enhancement 4: Better Error Responses for Spring Boot

### Problem:
Current error responses don't tell Spring Boot whether to retry or fail permanently

### Implementation:
File: app/routes/crm.py (improve error handling)

**Find this section (lines 123-129):**
```python
except ERPNextException as e:
    logger.error(f"ERPNext error during lead creation: {e}")
    return jsonify({"error": f"Lead creation failed: {str(e)}"}), 500
```

**Replace with:**
```python
except ERPNextException as e:
    logger.error(f"ERPNext error: {e}")
    
    # Determine if retryable
    error_msg = str(e)
    retryable = any(keyword in error_msg.lower() for keyword in [
        "timeout", "connection", "temporarily", "unavailable"
    ])
    
    return jsonify({
        "status": "error",
        "error": str(e),
        "error_type": type(e).__name__,
        "retryable": retryable,  # Spring Boot knows if it should retry
        "timestamp": datetime.utcnow().isoformat()
    }), 503 if retryable else 400
```

### Tests needed:
- Test timeout error (should return retryable=true, 503)
- Test validation error (should return retryable=false, 400)
- Test auth error (should return retryable=false, 401)

---

## Implementation Checklist

```
### Code Changes
- [ ] Add /health endpoint (lines ~50 in crm.py)
- [ ] Add /process-leads endpoint (lines ~80 in crm.py)
- [ ] Enhance /process-lead response (lines 116-120)
- [ ] Improve error handling (lines 123-129)
- [ ] Import datetime if not already imported

### Configuration
- [ ] No new env vars needed
- [ ] No schema changes needed
- [ ] Backward compatible (old clients still work)

### Testing
- [ ] Add test_health_check() in tests/test_crm_routes.py
- [ ] Add test_process_leads_batch_all_valid()
- [ ] Add test_process_leads_batch_mixed()
- [ ] Add test_enhanced_response_fields()
- [ ] Add test_error_retryable_flag()
- [ ] Run full test suite: pytest --cov
- [ ] Verify coverage >= 70%

### Documentation
- [ ] Update docs/API.md with new endpoints
- [ ] Add request/response examples for /health
- [ ] Add request/response examples for /process-leads
- [ ] Add response fields documentation
- [ ] Update postman_collection.json

### Deployment
- [ ] Rebuild Docker image: docker build -t ideabytes-api:1.1 .
- [ ] Test locally: docker-compose up
- [ ] Verify endpoints: curl http://localhost:5000/api/crm/health
- [ ] Commit: git commit -m "feat: Spring Boot integration enhancements"
```

---

## Testing Commands (After Implementation)

```bash
# Health check
curl http://localhost:5000/api/crm/health

# Process single lead (existing)
curl -X POST http://localhost:5000/api/crm/process-lead \
  -H "Content-Type: application/json" \
  -d '{"company":"ABC","first_name":"John","last_name":"Doe","email":"john@abc.com","phone":"+1-555-1234"}'

# Process multiple leads (new)
curl -X POST http://localhost:5000/api/crm/process-leads \
  -H "Content-Type: application/json" \
  -d '{
    "leads": [
      {"company":"ABC","first_name":"John","last_name":"Doe","email":"john@abc.com","phone":"+1-555-1234"},
      {"company":"XYZ","first_name":"Jane","last_name":"Smith","email":"jane@xyz.com","phone":"+1-555-5678"}
    ]
  }'

# Run tests
pytest tests/test_crm_routes.py -v
pytest --cov=app --cov=utils --cov-report=html
```

---

## Files to Reference During Implementation

| File | Purpose | Lines |
|------|---------|-------|
| app/routes/crm.py | Current endpoint implementation | 15-130 |
| app/erpnext_client.py | ERPNext API client (understand methods) | 1-100 |
| utils/schemas.py | Validation schema | 1-57 |
| app/assignment_engine.py | Assignment logic | 48-80 |
| app/task_service.py | Task creation | - |
| config/settings.py | Configuration access | - |
| tests/test_crm_routes.py | Current tests (use as template) | - |

---

## Success Criteria

After implementation:
1. ✅ `/health` endpoint returns {status, erpnext_connected, timestamp}
2. ✅ `/process-leads` processes batch of leads with per-lead error handling
3. ✅ `/process-lead` response includes URLs, timestamps, strategy
4. ✅ Error responses include `retryable` flag for Spring Boot
5. ✅ All tests pass (70%+ coverage)
6. ✅ Backward compatible (no breaking changes)
7. ✅ Documentation updated
8. ✅ Docker image rebuilt and tested

---

**Use this prompt when invoking AI assistant for Flask API enhancements.**
```
