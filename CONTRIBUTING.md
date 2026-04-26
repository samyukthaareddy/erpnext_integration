# Contributing Guidelines

This document outlines how to contribute to the ERPNext CRM Integration project.

## Overview

This is a collaborative project with defined phases and clear ownership. We follow a structured workflow to maintain code quality and avoid conflicts.

---

## Workflow

### Phase-Based Development

The project is divided into 9 phases, each with specific deliverables:

**Phase 1-2:** Infrastructure & API Framework (Harshita → Samyukthaa)  
**Phase 3-4:** ERPNext Integration & Assignment (Harshita → Samyukthaa)  
**Phase 5-6:** Task Creation & Error Handling (Harshita → Samyukthaa)  
**Phase 7-8:** Testing, Docs & Deployment (Harshita → Samyukthaa)  
**Phase 9:** Final Integration & Cleanup (Harshita)

### Commit Structure

Each phase consists of 2 related commits, each representing a single logical feature/fix.

**Commit message format:**
```
<type>(<scope>): <subject>

<body>

Closes #<issue>
```

**Types:** feat, fix, docs, test, chore, refactor  
**Scopes:** crm, erpnext, assignment, task, middleware, etc.  
**Subject:** Imperative, lowercase, no period, max 50 chars

**Example:**
```
feat(crm): create follow-up task service with description generation

- Create app/task_service.py with task creation logic
- Implement generate_task_description() for task details
- Add comprehensive unit tests for task service
```

---

## Code Quality Standards

### Testing Requirements

- **Minimum coverage:** 80% (currently 91%)
- **All new features must include tests**
- **All tests must pass before commit**
- **Run: `pytest --cov`**

### Code Style

- Follow PEP 8 standards
- Use meaningful variable names
- Keep functions small (< 50 lines when possible)
- Add docstrings to all functions/classes
- Type hints preferred for new code

### Git Practices

- **One feature per branch**
- **Create PR from feature branch**
- **Rebase before merging** (not merge commits)
- **Never force push to main**
- **Delete branches after merge**

---

## Making Changes

### 1. Start New Feature

```bash
# Create feature branch from latest main
git checkout main
git pull
git checkout -b feature/<your-feature-name>
```

### 2. Develop & Test

```bash
# Make changes
vim app/routes/crm.py

# Run tests frequently
pytest tests/test_crm_routes.py -v

# Check coverage
pytest --cov=app --cov=utils
```

### 3. Commit Changes

```bash
# Stage changes
git add app/routes/crm.py tests/test_crm_routes.py

# Commit with descriptive message
git commit -m "feat(crm): add new endpoint functionality

- Description of what was added
- List key changes
- Reference any issues"
```

### 4. Push & Create PR

```bash
# Push to origin
git push -u origin feature/your-feature-name

# Create PR through GitHub
# - Write clear PR title and description
# - Link related issues
# - Request reviews
```

### 5. Code Review & Merge

- Address feedback and update PR
- Ensure CI/CD passes (tests, linting)
- Rebase on main if needed
- Squash commits if necessary
- Merge via "Squash and merge" (keeps history clean)

---

## Testing Checklist

Before committing, ensure:

- [ ] All new functions have docstrings
- [ ] All new features have tests
- [ ] All tests pass: `pytest`
- [ ] Coverage meets minimum: `pytest --cov` shows ≥ 80%
- [ ] No linting errors (if pre-commit configured)
- [ ] Code follows PEP 8 standards
- [ ] Error cases are tested
- [ ] Integration tests pass

---

## Collaboration Notes

### Communication

- Use GitHub issues for feature requests & bugs
- Reference issues in commits: `Closes #123`
- Keep commit messages clear for others
- Document non-obvious logic with comments

### Handling Conflicts

If two branches conflict:

1. Pull latest main: `git pull origin main`
2. Resolve conflicts in your editor
3. Run tests: `pytest`
4. Commit merge: `git add . && git commit -m "chore: resolve merge conflicts"`
5. Push: `git push`

**Never** commit without testing after conflict resolution.

### Phase Handoff

When passing work to next phase owner:

1. **Ensure all tests pass:** `pytest --cov`
2. **Push to main:** `git push`
3. **Create clear summary** of what's complete
4. **Document any TODOs** in comments or issues
5. **Send handoff message** with status update

---

## Common Tasks

### Running Tests

```bash
# All tests
pytest

# Specific file
pytest tests/test_crm_routes.py

# With coverage
pytest --cov=app --cov=utils --cov-report=html

# Verbose
pytest -v

# Stop on first failure
pytest -x

# Run pattern
pytest -k "assignment"
```

### Checking Code Quality

```bash
# View coverage report
pytest --cov=app --cov-report=term-missing

# Run linting (if configured)
flake8 app/
black --check app/
```

### Debugging

```bash
# Run with debug output
pytest -s -v

# Print debug info
pytest tests/test_crm_routes.py -v --tb=short

# Interactive debugger
pytest --pdb  # Drops to pdb on failure
```

### Local Development

```bash
# Activate virtual environment
source venv/bin/activate  # Or: venv\Scripts\activate on Windows

# Run development server
python -m flask run

# Access at http://localhost:5000
```

---

## Documentation Standards

### Docstrings

```python
def create_followup_task(lead_id: str, assigned_to: str) -> dict:
    """
    Create a follow-up task for a newly assigned lead.
    
    Args:
        lead_id (str): ERPNext Lead ID
        assigned_to (str): Assigned salesperson email
    
    Returns:
        dict: Created task with task_id and other fields
    
    Raises:
        ERPNextException: On API error during task creation
    """
```

### Comments

Use comments for **why**, not **what**:

```python
# Bad:
x = y + 1  # Add one to y

# Good:
# Account for zero-indexed vs one-indexed systems
lead_index = y + 1
```

### Commits

Each commit message should explain:
- **What** changed
- **Why** it changed
- **How** it was tested

---

## Troubleshooting

### Tests failing after code changes

1. Review error message carefully
2. Check related test file
3. Run single test: `pytest tests/test_file.py::test_name -v`
4. Add debug prints or use `pdb` debugger
5. Check git diff: `git diff`

### Git conflicts

1. View conflicts: `git status`
2. Resolve manually in editor
3. Test after resolving
4. Commit resolution

### Import errors

1. Verify virtual environment is activated
2. Install dependencies: `pip install -r requirements.txt`
3. Check Python version: `python --version` (should be 3.8+)

---

## Questions & Support

- Check project documentation in `docs/`
- Review existing tests for usage examples
- Check commit history for similar changes
- Open GitHub issue for questions
- Ask in team chat

---

## Code Review Checklist (For Reviewers)

- [ ] Commits are logical and well-described
- [ ] Code follows PEP 8 standards
- [ ] Tests are included and passing
- [ ] Coverage meets minimum (80%+)
- [ ] No hard-coded secrets or credentials
- [ ] Error handling is appropriate
- [ ] Docstrings are present
- [ ] Changes don't break existing functionality

---

**Thank you for contributing! Together we build better software.**
