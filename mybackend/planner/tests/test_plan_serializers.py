"""
Unit tests for Plan Generation serializers (Phase 3).

Tests validation and serialization of plan generation request/response data.
"""

from django.test import TestCase
from planner.serializers import (
    PlanRequestSerializer,
    PlanMaterialSerializer,
    PlanToolSerializer,
    PlanResponseSerializer
)


class PlanRequestSerializerTests(TestCase):
    """Test the PlanRequestSerializer."""

    def test_valid_request(self):
        """Test serialization of valid plan request."""
        data = {
            'description': 'Replace copper pipe with PEX under kitchen sink'
        }
        serializer = PlanRequestSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_missing_description(self):
        """Test that missing description fails validation."""
        data = {}
        serializer = PlanRequestSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('description', serializer.errors)

    def test_empty_description(self):
        """Test that empty description fails validation."""
        data = {'description': ''}
        serializer = PlanRequestSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('description', serializer.errors)

    def test_description_too_short(self):
        """Test that description under 10 characters fails."""
        data = {'description': 'Fix pipe'}  # 8 characters
        serializer = PlanRequestSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('description', serializer.errors)

    def test_description_minimum_valid(self):
        """Test that description at minimum length validates."""
        data = {'description': 'Fix pipes'}  # Exactly 9 characters
        serializer = PlanRequestSerializer(data=data)
        self.assertFalse(serializer.is_valid())  # Still too short (< 10)

        data = {'description': 'Fix a pipe'}  # 10 characters
        serializer = PlanRequestSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_description_maximum_valid(self):
        """Test that description at maximum length validates."""
        # Create string with exactly 2000 characters
        description = 'x' * 2000
        data = {'description': description}
        serializer = PlanRequestSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_description_over_maximum(self):
        """Test that description over 2000 characters fails."""
        description = 'x' * 2001
        data = {'description': description}
        serializer = PlanRequestSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('description', serializer.errors)

    def test_description_with_whitespace(self):
        """Test that whitespace-only description fails."""
        data = {'description': '     '}
        serializer = PlanRequestSerializer(data=data)
        self.assertFalse(serializer.is_valid())

    def test_description_with_unicode(self):
        """Test that unicode characters in description are accepted."""
        data = {'description': 'Installez une pompe – très important'}
        serializer = PlanRequestSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_description_with_special_characters(self):
        """Test that special characters are accepted."""
        data = {
            'description': 'Install 1/2" copper pipe with 90° elbows (PEX alternatives)'
        }
        serializer = PlanRequestSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_request_with_extra_fields_ignored(self):
        """Test that extra fields in request are ignored."""
        data = {
            'description': 'Replace copper pipe with PEX',
            'extra_field': 'should be ignored',
            'another_field': 123
        }
        serializer = PlanRequestSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertNotIn('extra_field', serializer.validated_data)


class PlanMaterialSerializerTests(TestCase):
    """Test the PlanMaterialSerializer."""

    def test_valid_material(self):
        """Test serialization of valid material."""
        data = {
            'name': 'PEX tubing',
            'quantity': 50,
            'unit': 'ft',
            'category': 'pipe'
        }
        serializer = PlanMaterialSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_material_with_different_units(self):
        """Test materials with various unit types."""
        units = ['piece', 'ft', 'm', 'pack', 'roll', 'box', 'can', 'gallon']
        
        for unit in units:
            data = {
                'name': 'Test item',
                'quantity': 5,
                'unit': unit,
                'category': 'test'
            }
            serializer = PlanMaterialSerializer(data=data)
            self.assertTrue(serializer.is_valid(), f"Failed for unit: {unit}")

    def test_material_with_decimal_quantity(self):
        """Test material with decimal quantity."""
        data = {
            'name': 'Paint',
            'quantity': 2.5,
            'unit': 'gallon',
            'category': 'finish'
        }
        serializer = PlanMaterialSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_material_with_zero_quantity(self):
        """Test material with zero quantity."""
        data = {
            'name': 'Item',
            'quantity': 0,
            'unit': 'piece',
            'category': 'other'
        }
        serializer = PlanMaterialSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_material_missing_fields(self):
        """Test that missing required fields fail validation."""
        required_fields = ['name', 'quantity', 'unit', 'category']
        
        for missing_field in required_fields:
            data = {
                'name': 'Item',
                'quantity': 5,
                'unit': 'piece',
                'category': 'test'
            }
            del data[missing_field]
            
            serializer = PlanMaterialSerializer(data=data)
            self.assertFalse(serializer.is_valid())
            self.assertIn(missing_field, serializer.errors)

    def test_material_with_unicode_name(self):
        """Test material with unicode characters in name."""
        data = {
            'name': '½" copper pipe – type M',
            'quantity': 20,
            'unit': 'ft',
            'category': 'pipe'
        }
        serializer = PlanMaterialSerializer(data=data)
        self.assertTrue(serializer.is_valid())


class PlanToolSerializerTests(TestCase):
    """Test the PlanToolSerializer."""

    def test_valid_tool(self):
        """Test serialization of valid tool."""
        data = {
            'name': 'Adjustable wrench',
            'quantity': 1,
            'unit': 'piece',
            'category': 'tool'
        }
        serializer = PlanToolSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_tool_with_different_units(self):
        """Test tools with various unit types."""
        units = ['piece', 'set', 'pack', 'box']
        
        for unit in units:
            data = {
                'name': 'Test tool',
                'quantity': 1,
                'unit': unit,
                'category': 'tool'
            }
            serializer = PlanToolSerializer(data=data)
            self.assertTrue(serializer.is_valid(), f"Failed for unit: {unit}")

    def test_tool_with_multiple_quantity(self):
        """Test tool with quantity > 1."""
        data = {
            'name': 'Wrench set',
            'quantity': 5,
            'unit': 'piece',
            'category': 'tool'
        }
        serializer = PlanToolSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_tool_missing_fields(self):
        """Test that missing required fields fail validation."""
        required_fields = ['name', 'quantity', 'unit', 'category']
        
        for missing_field in required_fields:
            data = {
                'name': 'Wrench',
                'quantity': 1,
                'unit': 'piece',
                'category': 'tool'
            }
            del data[missing_field]
            
            serializer = PlanToolSerializer(data=data)
            self.assertFalse(serializer.is_valid())
            self.assertIn(missing_field, serializer.errors)

    def test_tool_with_unicode_name(self):
        """Test tool with unicode characters in name."""
        data = {
            'name': '⅜" Socket wrench – metric',
            'quantity': 1,
            'unit': 'piece',
            'category': 'tool'
        }
        serializer = PlanToolSerializer(data=data)
        self.assertTrue(serializer.is_valid())


class PlanResponseSerializerTests(TestCase):
    """Test the PlanResponseSerializer."""

    def test_valid_response(self):
        """Test serialization of valid plan response."""
        data = {
            'materials': [
                {
                    'name': 'PEX tubing',
                    'quantity': 50,
                    'unit': 'ft',
                    'category': 'pipe'
                },
                {
                    'name': 'Fitting',
                    'quantity': 4,
                    'unit': 'piece',
                    'category': 'connector'
                }
            ],
            'tools': [
                {
                    'name': 'Adjustable wrench',
                    'quantity': 1,
                    'unit': 'piece',
                    'category': 'tool'
                },
                {
                    'name': 'Crimping tool',
                    'quantity': 1,
                    'unit': 'piece',
                    'category': 'tool'
                }
            ],
            'steps': ['Step 1', 'Step 2', 'Step 3'],
            'warnings': ['Warning 1', 'Warning 2']
        }
        serializer = PlanResponseSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_response_with_empty_lists(self):
        """Test response with empty materials, tools, steps, warnings."""
        data = {
            'materials': [],
            'tools': [],
            'steps': [],
            'warnings': []
        }
        serializer = PlanResponseSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_response_missing_field(self):
        """Test that response missing required field fails."""
        required_fields = ['materials', 'tools', 'steps', 'warnings']
        
        for missing_field in required_fields:
            data = {
                'materials': [],
                'tools': [],
                'steps': [],
                'warnings': []
            }
            del data[missing_field]
            
            serializer = PlanResponseSerializer(data=data)
            self.assertFalse(serializer.is_valid())
            self.assertIn(missing_field, serializer.errors)

    def test_response_with_invalid_material_structure(self):
        """Test response with incorrectly structured material fails."""
        data = {
            'materials': [
                {
                    'name': 'PEX',
                    'quantity': 50,
                    # Missing 'unit' and 'category'
                }
            ],
            'tools': [],
            'steps': [],
            'warnings': []
        }
        serializer = PlanResponseSerializer(data=data)
        self.assertFalse(serializer.is_valid())

    def test_response_with_invalid_tool_structure(self):
        """Test response with incorrectly structured tool fails."""
        data = {
            'materials': [],
            'tools': [
                {
                    'name': 'Wrench',
                    # Missing 'quantity', 'unit', and 'category'
                }
            ],
            'steps': [],
            'warnings': []
        }
        serializer = PlanResponseSerializer(data=data)
        self.assertFalse(serializer.is_valid())

    def test_response_with_mixed_content(self):
        """Test response with various content types."""
        data = {
            'materials': [
                {'name': 'Item 1', 'quantity': 10, 'unit': 'piece', 'category': 'cat1'},
                {'name': 'Item 2', 'quantity': 5.5, 'unit': 'ft', 'category': 'cat2'},
            ],
            'tools': [
                {'name': 'Tool 1', 'quantity': 1, 'unit': 'piece', 'category': 'tool'},
                {'name': 'Tool 2', 'quantity': 2, 'unit': 'piece', 'category': 'tool'},
                {'name': 'Tool 3', 'quantity': 1, 'unit': 'set', 'category': 'tool'}
            ],
            'steps': [
                'First step',
                'Second step with details',
                'Final step – test and verify'
            ],
            'warnings': [
                'Important safety warning',
                'Another caution about specific hazard'
            ]
        }
        serializer = PlanResponseSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_response_with_long_text(self):
        """Test response with very long step/warning descriptions."""
        long_text = 'x' * 1000
        data = {
            'materials': [],
            'tools': [],
            'steps': [long_text],
            'warnings': [long_text]
        }
        serializer = PlanResponseSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_response_with_unicode_content(self):
        """Test response with unicode characters."""
        data = {
            'materials': [
                {
                    'name': '½" copper pipe – type M',
                    'quantity': 20,
                    'unit': 'ft',
                    'category': 'tubing'
                }
            ],
            'tools': [
                {
                    'name': 'Wrench – ¼" and ⅜" sockets',
                    'quantity': 1,
                    'unit': 'piece',
                    'category': 'tool'
                }
            ],
            'steps': ['Turn off water supply — critical step'],
            'warnings': ['High temperature risk — eye protection required']
        }
        serializer = PlanResponseSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_response_all_fields_optional_content(self):
        """Test that all response fields accept optional/empty content."""
        # All empty
        data = {
            'materials': [],
            'tools': [],
            'steps': [],
            'warnings': []
        }
        serializer = PlanResponseSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        # All populated
        data = {
            'materials': [{'name': 'X', 'quantity': 1, 'unit': 'u', 'category': 'c'}],
            'tools': [{'name': 'Y', 'quantity': 1, 'unit': 'u', 'category': 'tool'}],
            'steps': ['Z'],
            'warnings': ['W']
        }
        serializer = PlanResponseSerializer(data=data)
        self.assertTrue(serializer.is_valid())
