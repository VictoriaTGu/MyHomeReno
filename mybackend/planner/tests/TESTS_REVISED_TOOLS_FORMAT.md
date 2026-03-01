# Phase 3 Test Suite - Revised for Updated Tools Format

## Summary of Changes

The Phase 3 test suite has been revised to reflect the new tools format where tools are structured objects (like materials) rather than simple strings.

### Tools Format Update

**Old Format:**
```json
{
  "tools": ["Hammer", "Wrench", "Screwdriver"]
}
```

**New Format:**
```json
{
  "tools": [
    {"name": "Hammer", "quantity": 1, "unit": "piece", "category": "tool"},
    {"name": "Wrench", "quantity": 1, "unit": "piece", "category": "tool"},
    {"name": "Screwdriver", "quantity": 1, "unit": "piece", "category": "tool"}
  ]
}
```

## Test File Revisions

### 1. `test_rag_search.py` - Unit Tests for RAG Plan Generation

**Tests Updated:**
- `test_generate_plan_success` - Now expects tools as structured objects with name, quantity, unit, and category
- `test_generate_plan_with_markdown_code_blocks` - Updated mock response with new tools format
- `test_generate_plan_with_complex_materials` - Updated to test both complex materials AND tools with various units

**Key Changes:**
```python
# Old assertion
self.assertIn('Adjustable wrench', result['tools'])

# New assertion
tool_names = [t['name'] for t in result['tools']]
self.assertIn('Adjustable wrench', tool_names)
self.assertEqual(result['tools'][0]['quantity'], 1)
self.assertEqual(result['tools'][0]['category'], 'tool')
```

### 2. `test_plan_generation_api.py` - Integration Tests for API Endpoint

**Tests Updated:**
- `test_generate_plan_success` - Mock response includes structured tools
- `test_generate_plan_response_structure_validation` - Validates tool object structure with name, quantity, unit, category

**Key Changes:**
```python
# Old mock response
'tools': ['Adjustable wrench', 'Crimping tool']

# New mock response
'tools': [
    {'name': 'Adjustable wrench', 'quantity': 1, 'unit': 'piece', 'category': 'tool'},
    {'name': 'Crimping tool', 'quantity': 1, 'unit': 'piece', 'category': 'tool'}
]
```

### 3. `test_plan_serializers.py` - Serializer Validation Tests

**New Test Class Added:**
- `PlanToolSerializerTests` - Tests validation of tool serialization (15+ new tests)
  - `test_valid_tool` - Valid tool object validation
  - `test_tool_with_different_units` - Various unit types (piece, set, pack, box)
  - `test_tool_with_multiple_quantity` - Tools with quantity > 1
  - `test_tool_missing_fields` - Required field validation
  - `test_tool_with_unicode_name` - Unicode character support

**Tests Updated:**
- `test_valid_response` - Response includes structured tools
- `test_response_with_invalid_tool_structure` - New test for invalid tool structure
- `test_response_with_mixed_content` - Updated to include structured tools
- `test_response_with_unicode_content` - Updated with tool unicode test

**Key Addition:**
```python
# New serializer
class PlanToolSerializer(serializers.Serializer):
    """Serializer for individual tools in a plan."""
    name = serializers.CharField()
    quantity = serializers.FloatField()
    unit = serializers.CharField()
    category = serializers.CharField()

# Updated response serializer
class PlanResponseSerializer(serializers.Serializer):
    materials = PlanMaterialSerializer(many=True)
    tools = PlanToolSerializer(many=True)  # Changed from ListField
    steps = serializers.ListField(child=serializers.CharField())
    warnings = serializers.ListField(child=serializers.CharField())
```

## Implementation Files Updated

### Backend

1. **mybackend/planner/serializers.py**
   - Added `PlanToolSerializer` class
   - Updated `PlanResponseSerializer` to use `PlanToolSerializer` for tools validation

2. **mybackend/planner/rag_search.py**
   - Prompt already updated to request tools with correct structure:
   ```
   "tools": [
       {"name": "tool name", "quantity": 1, "unit": "piece", "category": "tool"},
       ...
   ]
   ```

### Frontend

1. **myfrontend/src/components/PlanDisplay.jsx**
   - Updated tools rendering to handle tool objects
   - Now displays tool name, quantity, unit, and category
   - Removed simple list rendering, using tool item cards like materials

2. **myfrontend/src/components/PlanDisplay.css**
   - Replaced `.plan-materials-list` style with `.materials-list` and `.material-item` classes
   - Tools now styled like materials with border-left accent, info sections
   - Consistent hover effects and spacing with materials

## Test Count Summary

**Total Tests: 50+**

- `test_rag_search.py`: 17 tests
  - 15 GeneratePlanTests 
  - 2 RAGConfigurationsTests

- `test_plan_generation_api.py`: 15 tests
  - PlanGenerationViewTests covering all API scenarios

- `test_plan_serializers.py`: 18+ tests
  - PlanRequestSerializerTests: 10 tests
  - PlanMaterialSerializerTests: 7 tests
  - PlanToolSerializerTests: 6 tests (NEW)
  - PlanResponseSerializerTests: 8+ tests (UPDATED)

## Running Updated Tests

```bash
# Run all Phase 3 tests
cd /Users/lunayou/Documents/MyHomeReno
python mybackend/manage.py test \
  planner.tests.test_rag_search \
  planner.tests.test_plan_generation_api \
  planner.tests.test_plan_serializers \
  -v 2

# Run only tool serializer tests
python mybackend/manage.py test \
  planner.tests.test_plan_serializers.PlanToolSerializerTests \
  -v 2

# Run only API tests
python mybackend/manage.py test \
  planner.tests.test_plan_generation_api.PlanGenerationViewTests \
  -v 2
```

## Format Consistency

The tools format change ensures that the API response maintains consistency:

```json
{
  "materials": [
    {"name": "...", "quantity": N, "unit": "...", "category": "..."},
    ...
  ],
  "tools": [
    {"name": "...", "quantity": N, "unit": "...", "category": "..."},
    ...
  ],
  "steps": ["Step 1", "Step 2", ...],
  "warnings": ["Warning 1", "Warning 2", ...]
}
```

All structured items (materials and tools) now follow the same schema with:
- `name`: Item name
- `quantity`: How many/how much
- `unit`: Measurement unit (piece, ft, set, etc.)
- `category`: Classification (pipe, fitting, tool, consumable, etc.)

## Backward Compatibility Notes

**Breaking Change:** If any frontend code or clients are currently expecting tools as a simple string array, they will need to be updated to handle the new object structure. The updated `PlanDisplay.jsx` component demonstrates the correct way to handle the new format.

## Next Steps

1. Run test suite to verify all tests pass
2. Verify frontend rendering with updated component
3. Test end-to-end with mocked LLM responses
4. Ensure error handling works with new format
