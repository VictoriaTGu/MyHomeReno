"""
Integration tests for Plan Generation API endpoint (Phase 3).

Tests the PlanGenerationView endpoint with mocked RAG chain,
ensuring proper request validation, response formatting, and error handling.
"""

import json
from unittest.mock import patch, MagicMock
from django.test import TestCase, override_settings
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from rest_framework import status

from planner.models import ShoppingList, Material


class PlanGenerationViewTests(TestCase):
    """Integration tests for the plan generation API endpoint."""

    def setUp(self):
        """Set up test client, user, and authentication."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')

    def test_generate_plan_requires_authentication(self):
        """Test that unauthenticated requests are rejected."""
        client = APIClient()
        response = client.post('/api/generate-plan/', {
            'description': 'Replace copper pipe with PEX'
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_generate_plan_missing_description(self):
        """Test that missing description field returns 400."""
        response = self.client.post('/api/generate-plan/', {}, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('description', response.data or {})

    def test_generate_plan_empty_description(self):
        """Test that empty description returns 400."""
        response = self.client.post('/api/generate-plan/', {
            'description': ''
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_generate_plan_description_too_short(self):
        """Test that description shorter than minimum length returns 400."""
        response = self.client.post('/api/generate-plan/', {
            'description': 'Fix pipe'  # Less than 10 characters
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_generate_plan_description_too_long(self):
        """Test that description longer than maximum length returns 400."""
        long_description = 'x' * 2001  # Over 2000 character limit
        response = self.client.post('/api/generate-plan/', {
            'description': long_description
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('planner.views.generate_plan')
    def test_generate_plan_success(self, mock_generate_plan):
        """Test successful plan generation returns 200 with correct structure."""
        mock_generate_plan.return_value = {
            'materials': [
                {
                    'name': 'PEX tubing',
                    'quantity': 50,
                    'unit': 'ft',
                    'category': 'pipe'
                },
                {
                    'name': 'Fittings',
                    'quantity': 4,
                    'unit': 'piece',
                    'category': 'fitting'
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
            'steps': ['Step 1: Turn off water', 'Step 2: Remove old pipe'],
            'warnings': ['Turn off water supply first', 'Check for leaks after']
        }

        response = self.client.post('/api/generate-plan/', {
            'description': 'Replace copper pipe with PEX under kitchen sink'
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data

        # Verify response structure
        self.assertIn('materials', data)
        self.assertIn('tools', data)
        self.assertIn('steps', data)
        self.assertIn('warnings', data)

        # Verify materials
        self.assertEqual(len(data['materials']), 2)
        self.assertEqual(data['materials'][0]['name'], 'PEX tubing')
        self.assertEqual(data['materials'][0]['quantity'], 50)

        # Verify tools
        self.assertEqual(len(data['tools']), 2)
        tool_names = [t['name'] for t in data['tools']]
        self.assertIn('Adjustable wrench', tool_names)
        self.assertEqual(data['tools'][0]['category'], 'tool')

        # Verify steps
        self.assertEqual(len(data['steps']), 2)

        # Verify warnings
        self.assertEqual(len(data['warnings']), 2)

    @patch('planner.views.generate_plan')
    def test_generate_plan_with_empty_lists(self, mock_generate_plan):
        """Test plan generation with empty materials/tools/steps/warnings."""
        mock_generate_plan.return_value = {
            'materials': [],
            'tools': [],
            'steps': [],
            'warnings': []
        }

        response = self.client.post('/api/generate-plan/', {
            'description': 'Simple project description'
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data

        self.assertEqual(data['materials'], [])
        self.assertEqual(data['tools'], [])
        self.assertEqual(data['steps'], [])
        self.assertEqual(data['warnings'], [])

    @patch('planner.views.generate_plan')
    def test_generate_plan_validation_error(self, mock_generate_plan):
        """Test handling of ValueError from generate_plan."""
        mock_generate_plan.side_effect = ValueError('Failed to parse plan response from AI model')

        response = self.client.post('/api/generate-plan/', {
            'description': 'Replace copper pipe with PEX under kitchen sink'
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('detail', response.data)

    @patch('planner.views.generate_plan')
    def test_generate_plan_general_error(self, mock_generate_plan):
        """Test handling of general exceptions from generate_plan."""
        mock_generate_plan.side_effect = Exception('OpenAI API connection failed')

        response = self.client.post('/api/generate-plan/', {
            'description': 'Replace copper pipe with PEX under kitchen sink'
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn('detail', response.data)

    @patch('planner.views.generate_plan')
    def test_generate_plan_with_various_descriptions(self, mock_generate_plan):
        """Test plan generation with various valid descriptions."""
        descriptions = [
            'Install a ceiling fan in the master bedroom',
            'Repair drywall damage in the living room wall',
            'Replace kitchen cabinet hardware with new stainless steel handles',
            'Install weatherstripping around exterior doors to reduce drafts',
        ]

        mock_generate_plan.return_value = {
            'materials': [{'name': 'Item', 'quantity': 1, 'unit': 'piece', 'category': 'other'}],
            'tools': [{'name': 'Tool', 'quantity': 1, 'unit': 'piece', 'category': 'tool'}],
            'steps': ['Step'],
            'warnings': ['Warning']
        }

        for description in descriptions:
            response = self.client.post('/api/generate-plan/', {
                'description': description
            }, format='json')

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            mock_generate_plan.assert_called()

    @patch('planner.views.generate_plan')
    def test_generate_plan_response_structure_validation(self, mock_generate_plan):
        """Test that response validates against PlanResponseSerializer."""
        mock_generate_plan.return_value = {
            'materials': [
                {
                    'name': 'Copper pipe',
                    'quantity': 20,
                    'unit': 'ft',
                    'category': 'pipe'
                }
            ],
            'tools': [
                {
                    'name': 'Pipe wrench',
                    'quantity': 1,
                    'unit': 'piece',
                    'category': 'tool'
                },
                {
                    'name': 'Torch',
                    'quantity': 1,
                    'unit': 'piece',
                    'category': 'tool'
                }
            ],
            'steps': [
                'Remove old pipe',
                'Install new pipe',
                'Test connections'
            ],
            'warnings': [
                'Requires proper ventilation for torch use',
                'High temperature risk'
            ]
        }

        response = self.client.post('/api/generate-plan/', {
            'description': 'Install copper piping for water line'
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Validate all required fields are present and correct types
        data = response.data
        self.assertIsInstance(data['materials'], list)
        self.assertIsInstance(data['tools'], list)
        self.assertIsInstance(data['steps'], list)
        self.assertIsInstance(data['warnings'], list)

        # Validate material structure
        if data['materials']:
            material = data['materials'][0]
            self.assertIn('name', material)
            self.assertIn('quantity', material)
            self.assertIn('unit', material)
            self.assertIn('category', material)

        # Validate tool structure
        if data['tools']:
            tool = data['tools'][0]
            self.assertIn('name', tool)
            self.assertIn('quantity', tool)
            self.assertIn('unit', tool)
            self.assertIn('category', tool)

    @patch('planner.views.generate_plan')
    def test_generate_plan_multiple_requests_independent(self, mock_generate_plan):
        """Test that multiple plan generation requests are independent."""
        description1 = 'Replace copper pipe with PEX'
        description2 = 'Install ceiling fan'

        plans = [
            {
                'materials': [{'name': 'PEX', 'quantity': 50, 'unit': 'ft', 'category': 'pipe'}],
                'tools': [{'name': 'Wrench', 'quantity': 1, 'unit': 'piece', 'category': 'tool'}],
                'steps': ['Remove old pipe'],
                'warnings': ['Turn off water']
            },
            {
                'materials': [{'name': 'Fan', 'quantity': 1, 'unit': 'piece', 'category': 'fixture'}],
                'tools': [{'name': 'Screwdriver', 'quantity': 1, 'unit': 'piece', 'category': 'tool'}, {'name': 'Drill', 'quantity': 1, 'unit': 'piece', 'category': 'tool'}],
                'steps': ['Install bracket', 'Mount fan'],
                'warnings': ['Turn off power']
            }
        ]

        mock_generate_plan.side_effect = plans

        # First request
        response1 = self.client.post('/api/generate-plan/', {
            'description': description1
        }, format='json')
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        self.assertEqual(response1.data['materials'][0]['name'], 'PEX')

        # Second request
        response2 = self.client.post('/api/generate-plan/', {
            'description': description2
        }, format='json')
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertEqual(response2.data['materials'][0]['name'], 'Fan')

    @patch('planner.views.generate_plan')
    def test_generate_plan_with_special_characters_in_description(self, mock_generate_plan):
        """Test plan generation with special characters in description."""
        mock_generate_plan.return_value = {
            'materials': [{'name': 'Item', 'quantity': 1, 'unit': 'piece', 'category': 'other'}],
            'tools': [],
            'steps': [],
            'warnings': []
        }

        special_descriptions = [
            'Install 1/2" copper pipe with 90° elbows',
            'Replace PEX tubing (25 ft) under sink & cabinet',
            'Cut drywall @ 45°, install insulation (R-13/R-15)',
            'Add electrical outlet—GFCI protected for wet areas',
        ]

        for description in special_descriptions:
            response = self.client.post('/api/generate-plan/', {
                'description': description
            }, format='json')
            self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch('planner.views.generate_plan')
    def test_generate_plan_performs_http_post_not_get(self, mock_generate_plan):
        """Test that only POST requests are accepted."""
        mock_generate_plan.return_value = {
            'materials': [],
            'tools': [],
            'steps': [],
            'warnings': []
        }

        # GET request should not be allowed
        response = self.client.get('/api/generate-plan/')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        # DELETE request should not be allowed
        response = self.client.delete('/api/generate-plan/')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    @patch('planner.views.generate_plan')
    def test_generate_plan_with_unicode_characters(self, mock_generate_plan):
        """Test plan generation handles unicode characters properly."""
        mock_generate_plan.return_value = {
            'materials': [{'name': 'Item', 'quantity': 1, 'unit': 'piece', 'category': 'other'}],
            'tools': [],
            'steps': [],
            'warnings': []
        }

        # Unicode descriptions
        descriptions = [
            'Replace the kitchen faucet — aesthetic and functional upgrade',
            'Install new showerhead (high-flow or water-saving)',
            'Add weatherstripping to prevent air leaks & reduce energy costs',
        ]

        for description in descriptions:
            response = self.client.post('/api/generate-plan/', {
                'description': description
            }, format='json')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
