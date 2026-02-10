# Coding Benchmark - Expected Outputs

## Task 1: Python Module Refactoring

### Expected Structure
```python
from dataclasses import dataclass
from typing import List, Dict, Optional, Any

@dataclass
class ProcessorConfig:
    batch_size: int = 100
    timeout: float = 30.0
    retry_count: int = 3

class DataProcessor:
    def __init__(self, config: Optional[ProcessorConfig] = None) -> None:
        self.config = config or ProcessorConfig()

    def process(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        ...

# Backward compatibility
def process_data(data):
    return DataProcessor().process(data)
```

### Evaluation Checklist
- [ ] Class-based design implemented
- [ ] Type hints on all public methods
- [ ] f-strings used throughout
- [ ] Config extracted to dataclass
- [ ] Legacy function wrappers preserved
- [ ] mypy passes with --strict
- [ ] Pylint >= 9.0

---

## Task 2: Add Unit Tests

### Expected Test Structure
```python
import pytest
from unittest.mock import Mock, patch, MagicMock

class TestUserService:
    @pytest.fixture
    def mock_db(self):
        return Mock()

    @pytest.fixture
    def service(self, mock_db):
        return UserService(mock_db)

    def test_create_user_success(self, service, mock_db):
        ...

    def test_create_user_duplicate_email(self, service, mock_db):
        ...

    def test_get_user_not_found(self, service, mock_db):
        ...
```

### Evaluation Checklist
- [ ] >= 80% coverage achieved
- [ ] All public methods tested
- [ ] Edge cases covered (empty inputs, None values)
- [ ] Error conditions tested (exceptions, invalid data)
- [ ] Database mocked correctly
- [ ] Tests are independent
- [ ] Fixtures used appropriately

---

## Task 3: Async Migration

### Expected Async Client
```python
import aiohttp
import aiofiles
from contextlib import asynccontextmanager
from typing import Optional, Dict, Any

class AsyncAPIClient:
    def __init__(self, base_url: str, timeout: float = 30.0):
        self.base_url = base_url
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self._session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        self._session = aiohttp.ClientSession(timeout=self.timeout)
        return self

    async def __aexit__(self, *args):
        if self._session:
            await self._session.close()

    async def get(self, endpoint: str) -> Dict[str, Any]:
        async with self._session.get(f"{self.base_url}{endpoint}") as resp:
            return await resp.json()
```

### Evaluation Checklist
- [ ] aiohttp used for HTTP
- [ ] aiofiles used for file I/O
- [ ] Context managers for resource cleanup
- [ ] Connection pooling via session reuse
- [ ] Timeout handling implemented
- [ ] Same public interface (async versions)
- [ ] Proper exception handling

---

## Task 4: Debug Failing Tests

### Expected Fixes

**Bug 1: Division by zero**
- Location: `calculator.py:45`
- Fix: Add zero check in `divide()` method

**Bug 2: Float precision**
- Location: `calculator.py:23`
- Fix: Use `math.isclose()` or `Decimal` for comparisons

**Bug 3: Off-by-one error**
- Location: `calculator.py:67`
- Fix: Change `range(n)` to `range(n+1)`

**Bug 4: Incorrect operator precedence**
- Location: `calculator.py:89`
- Fix: Add parentheses to enforce correct order

**Bug 5: Unhandled None input**
- Location: `calculator.py:12`
- Fix: Add None check with appropriate error

### Evaluation Checklist
- [ ] All 5 tests now pass
- [ ] Fixes are in code, not tests (unless test is wrong)
- [ ] Each fix is minimal
- [ ] Explanations provided for each fix
- [ ] No regression in other functionality

---

## Scoring Guide

### Per Task Scoring (0-100)

| Score | Description |
|-------|-------------|
| 90-100 | Exceeds expectations, production-ready |
| 80-89 | Meets all requirements, minor issues |
| 70-79 | Mostly complete, some gaps |
| 60-69 | Partial completion, notable issues |
| 50-59 | Significant gaps, but shows understanding |
| < 50 | Major issues or incomplete |

---

## Task 5: API Endpoint Implementation

### Expected Structure
```python
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI()

@app.get("/users", response_model=PaginatedResponse)
async def list_users(page: int = Query(1, ge=1), size: int = Query(20, ge=1, le=100)):
    ...

@app.post("/users", response_model=User, status_code=201)
async def create_user(user: UserCreate):
    ...

@app.get("/users/{user_id}", response_model=User)
async def get_user(user_id: int):
    ...
```

### Evaluation Checklist
- [ ] All CRUD endpoints implemented
- [ ] Input validation with proper error messages
- [ ] 400/404/422/500 error responses
- [ ] Pagination with page and size parameters
- [ ] Integration tests for each endpoint
- [ ] Tests cover error cases
- [ ] Response models match OpenAPI spec

### Aggregate Score
- Total = (Task1 + Task2 + Task3 + Task4 + Task5) / 5
