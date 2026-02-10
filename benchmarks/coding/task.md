# Coding/Engineering Benchmark Tasks

## Overview

This benchmark evaluates agent capabilities in software engineering tasks including refactoring, testing, debugging, and code migration.

---

## Task 1: Python Module Refactoring

### Description
Refactor the legacy `data_processor.py` module to follow modern Python best practices.

### Input
- `data/data_processor.py` - Legacy Python module with procedural code

### Requirements
1. Convert procedural functions to a class-based design
2. Add type hints to all functions/methods
3. Replace string formatting with f-strings
4. Extract configuration to a separate config object
5. Maintain backward compatibility with existing function signatures

### Success Criteria
- All existing tests pass
- Code passes `mypy --strict`
- Pylint score >= 9.0
- No breaking changes to public API

---

## Task 2: Add Unit Tests

### Description
Add comprehensive unit tests to an existing codebase with no test coverage.

### Input
- `data/user_service.py` - User management service module
- `data/database.py` - Database abstraction layer

### Requirements
1. Achieve minimum 80% code coverage
2. Test all public methods
3. Include edge cases and error conditions
4. Mock external dependencies (database, API calls)
5. Use pytest with fixtures

### Success Criteria
- Coverage >= 80%
- All tests pass
- Tests are isolated (no shared state)
- Proper use of mocking

---

## Task 3: Async Migration

### Description
Migrate synchronous I/O code to async/await pattern.

### Input
- `data/api_client.py` - Synchronous API client using requests
- `data/file_handler.py` - Synchronous file operations

### Requirements
1. Convert to async using aiohttp for HTTP
2. Use aiofiles for file operations
3. Implement proper connection pooling
4. Add timeout handling
5. Maintain the same public interface (async versions)

### Success Criteria
- All operations are non-blocking
- Proper resource cleanup (context managers)
- Error handling preserved
- Performance improvement documented

---

## Task 4: Debug Failing Test Suite

### Description
Diagnose and fix a failing test suite with multiple issues.

### Input
- `data/calculator.py` - Calculator module
- `data/test_calculator.py` - Failing test suite (5 failures)

### Requirements
1. Identify root cause of each failure
2. Determine if bug is in code or test
3. Fix the bugs (prefer code fixes over test changes)
4. Document each fix with explanation

### Success Criteria
- All 5 tests pass
- No test logic changes (unless test is clearly wrong)
- Bug fixes are minimal and focused
- Each fix is explained

---

## Task 5: API Endpoint Implementation

### Description
Implement a REST API from an OpenAPI specification.

### Input
- `data/openapi_spec.yaml` - OpenAPI 3.0 specification for a user management API
- `data/models_stub.py` - Pydantic model stubs

### Requirements
1. Implement all CRUD endpoints defined in the spec
2. Add input validation using Pydantic
3. Include proper error responses (400, 404, 422, 500)
4. Add pagination for list endpoints
5. Write integration tests for each endpoint

### Success Criteria
- All endpoints match the spec
- Validation rejects invalid input
- Error responses follow the spec format
- Pagination works correctly
- Tests cover happy path and error cases

---

## Evaluation Rubric

| Criterion | Weight | Description |
|-----------|--------|-------------|
| Correctness | 40% | Code works as specified |
| Code Quality | 25% | Clean, readable, maintainable |
| Best Practices | 20% | Follows Python conventions |
| Documentation | 15% | Clear explanations of changes |

## Time Limits

- Task 1: 15 minutes
- Task 2: 20 minutes
- Task 3: 20 minutes
- Task 4: 10 minutes
- Task 5: 25 minutes
