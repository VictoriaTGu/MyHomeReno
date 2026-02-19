# Phase 3 Testing Guide

## Overview

This document explains the test suite for Phase 3 (Plan Generation using RAG), including unit tests, integration tests, and how to run them.

## Test Files

### 1. `test_rag_search.py`
**Unit tests for RAG functionality**

Tests the core plan generation logic in `rag_search.py`:
- Configuration functions (`get_persist_dir()`, `get_rag_llm()`, `get_embedding_model()`)
- `generate_plan()` function with mocked OpenAI API and ChromaDB
- JSON parsing and error handling
- Edge cases (empty lists, missing keys, markdown code blocks)

**Key Tests:**
- `test_generate_plan_success` - Valid plan generation
- `test_generate_plan_with_markdown_code_blocks` - Handles wrapped JSON responses
- `test_generate_plan_invalid_json_raises_error` - JSON parsing errors
- `test_generate_plan_uses_configured_models` - Settings-based configuration
- `test_generate_plan_handles_*_exception` - Error handling

### 2. `test_plan_generation_api.py`
**Integration tests for the API endpoint**

Tests the `PlanGenerationView` endpoint:
- Authentication requirements
- Request validation (required fields, length constraints)
- Successful plan generation
- Error responses (400, 500 status codes)
- HTTP method restrictions
- Unicode and special character handling

**Key Tests:**
- `test_generate_plan_requires_authentication` - Auth checks
- `test_generate_plan_success` - Successful response structure
- `test_generate_plan_validation_error` - Error handling
- `test_generate_plan_response_structure_validation` - Response validation
- `test_generate_plan_performs_http_post_not_get` - HTTP method validation

### 3. `test_plan_serializers.py`
**Unit tests for request/response serializers**

Tests validation and serialization:
- `PlanRequestSerializer` - Plan description validation
- `PlanMaterialSerializer` - Material structure validation
- `PlanResponseSerializer` - Full plan response validation

**Key Tests:**
- Description length constraints (10-2000 characters)
- Required field validation
- Data type validation
- Unicode and special character handling
- Edge cases (empty lists, missing fields)

## Running Tests

### Run All Phase 3 Tests
```bash
cd /Users/lunayou/Documents/MyHomeReno
python mybackend/manage.py test planner.tests.test_rag_search planner.tests.test_plan_generation_api planner.tests.test_plan_serializers -v 2
```

### Run Specific Test Class
```bash
python mybackend/manage.py test planner.tests.test_rag_search.RAGConfigurationsTests -v 2
```

### Run Single Test Method
```bash
python mybackend/manage.py test planner.tests.test_rag_search.GeneratePlanTests.test_generate_plan_success -v 2
```

### Run with Coverage (if coverage.py is installed)
```bash
coverage run --source='planner' mybackend/manage.py test planner.tests.test_rag_search planner.tests.test_plan_generation_api planner.tests.test_plan_serializers
coverage report
coverage html  # Generate HTML report
```

### Run All Planner Tests (Including Phase 2)
```bash
python mybackend/manage.py test planner -v 2
```

## Test Coverage

### RAG Search Tests (test_rag_search.py)
- **17 tests** covering plan generation logic
- Mocks: `Chroma`, `ChatOpenAI`, `OpenAIEmbeddings`
- Coverage: Configuration, JSON parsing, error handling, edge cases

### API Integration Tests (test_plan_generation_api.py)
- **15 tests** covering endpoint behavior
- Mocks: `generate_plan()` function
- Coverage: Authentication, validation, error responses, special characters

### Serializer Tests (test_plan_serializers.py)
- **18 tests** covering request/response validation
- No mocks (pure validation tests)
- Coverage: Field validation, constraints, edge cases, unicode handling

**Total: 50+ unit and integration tests**

## Test Patterns

### Mocking OpenAI API

Tests use `@patch` decorator to mock OpenAI calls:

```python
@patch('planner.rag_search.Chroma')
@patch('planner.rag_search.ChatOpenAI')
def test_generate_plan_success(self, mock_chat_openai, mock_chroma):
    # Setup mocks
    mock_vectorstore = MagicMock()
    mock_vectorstore.as_retriever.return_value = mock_retriever
    mock_chroma.return_value = mock_vectorstore
    
    # Configure LLM response
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = json.dumps(valid_response)
    mock_chat_openai.return_value = mock_llm
    
    # Test
    result = generate_plan("Test description")
```

### Settings Overrides

Tests override Django settings for configuration testing:

```python
@override_settings(RAG_MODEL='gpt-4-turbo')
def test_generate_plan_uses_configured_models(self, ...):
    # Test that configured model is used
```

### API Client Setup

Integration tests use APIClient with token authentication:

```python
def setUp(self):
    self.user = User.objects.create_user(...)
    self.token = Token.objects.create(user=self.user)
    self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
```

## Example Test Output

```
test_rag_search (planner.tests.test_rag_search.RAGConfigurationsTests.test_get_persist_dir_default) ... ok
test_rag_search (planner.tests.test_rag_search.GeneratePlanTests.test_generate_plan_success) ... ok
test_plan_generation_api (planner.tests.test_plan_generation_api.PlanGenerationViewTests.test_generate_plan_requires_authentication) ... ok
test_plan_serializers (planner.tests.test_plan_serializers.PlanRequestSerializerTests.test_valid_request) ... ok

...

Ran 50 tests in 0.425s

OK
```

## Mocking Strategy

### What Gets Mocked

1. **OpenAI API (`ChatOpenAI`)** - Replaces actual LLM calls with controlled responses
2. **ChromaDB (`Chroma`)** - Mocks vector store to avoid initialization
3. **`generate_plan()` function** - Mocked in API tests to isolate endpoint testing

### What Doesn't Get Mocked

1. **Django ORM** - Uses real test database
2. **DRF Serializers** - Tests actual validation logic
3. **API Framework** - Tests real HTTP handling (via APIClient)

## CI/CD Integration

To integrate tests into CI/CD pipelines:

```yaml
# Example GitHub Actions
- name: Run Phase 3 Tests
  run: |
    cd mybackend
    python manage.py test planner.tests.test_rag_search \
                           planner.tests.test_plan_generation_api \
                           planner.tests.test_plan_serializers -v 2
```

## Common Issues

### Issue: Import Errors
**Solution:** Ensure you're running from the project root and have activated the venv:
```bash
source .venv/bin/activate
cd mybackend
python manage.py test ...
```

### Issue: Tests Timeout
**Solution:** Some tests may hang if OpenAI API is called without mocking. Verify all patches are applied:
```bash
python -m pytest planner/tests/test_rag_search.py -v --tb=short
```

### Issue: Database Errors
**Solution:** Django test runner creates temporary test database. Ensure permissions:
```bash
python manage.py test --keepdb  # Reuse test database
```

## Test Maintenance

### Adding New Tests
1. Create test method in appropriate test file
2. Follow naming convention: `test_<feature>_<scenario>`
3. Use descriptive docstrings
4. Mock external dependencies (OpenAI, etc.)
5. Run tests: `python manage.py test planner.tests -v 2`

### Updating Tests
When modifying Phase 3 implementation:
1. Update corresponding tests
2. Ensure all tests pass
3. Check coverage hasn't decreased
4. Update this README if needed

## Performance Notes

- **Total test runtime:** ~0.5 seconds (most mocked)
- **Slowest tests:** API integration tests (~50ms each)
- **Fastest tests:** Serializer validation tests (~1ms each)

## References

- [Django Testing Documentation](https://docs.djangoproject.com/en/stable/topics/testing/)
- [Django REST Framework Testing](https://www.django-rest-framework.org/api-guide/testing/)
- [unittest.mock Documentation](https://docs.python.org/3/library/unittest.mock.html)
- [pytest-django](https://pytest-django.readthedocs.io/)
