from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from rest_framework import status
from planner.models import Project, Material, ProjectMaterial

class ProjectCreationApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')

    def test_create_project_with_existing_materials(self):
        mat1 = Material.objects.create(name='Copper pipe', category='pipe', unit='ft')
        mat2 = Material.objects.create(name='PEX fitting', category='fitting', unit='piece')
        payload = {
            'name': 'Replace pipe',
            'description': 'Replace copper pipe with PEX',
            'materials': [
                {'material_id': mat1.id, 'quantity': 10},
                {'material_id': mat2.id, 'quantity': 4}
            ]
        }
        response = self.client.post('/api/projects/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('project', response.data)
        self.assertIn('project_materials', response.data)
        self.assertEqual(len(response.data['project_materials']), 2)

    def test_create_project_with_new_materials(self):
        payload = {
            'name': 'Install vanity',
            'description': 'Install new bathroom vanity',
            'materials': [
                {'name': 'Vanity', 'category': 'fixture', 'unit': 'piece', 'quantity': 1},
                {'name': 'Drain pipe', 'category': 'pipe', 'unit': 'ft', 'quantity': 5}
            ]
        }
        response = self.client.post('/api/projects/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(response.data['project_materials']), 2)
        mat_names = [pm['material']['name'] for pm in response.data['project_materials']]
        self.assertIn('Vanity', mat_names)
        self.assertIn('Drain pipe', mat_names)

    def test_create_project_with_mixed_materials(self):
        mat1 = Material.objects.create(name='Copper pipe', category='pipe', unit='ft')
        payload = {
            'name': 'Repair pipe',
            'description': 'Repair copper pipe and add new fitting',
            'materials': [
                {'material_id': mat1.id, 'quantity': 5},
                {'name': 'PEX fitting', 'category': 'fitting', 'unit': 'piece', 'quantity': 2}
            ]
        }
        response = self.client.post('/api/projects/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(response.data['project_materials']), 2)
        mat_names = [pm['material']['name'] for pm in response.data['project_materials']]
        self.assertIn('Copper pipe', mat_names)
        self.assertIn('PEX fitting', mat_names)

    def test_create_project_invalid_material(self):
        payload = {
            'name': 'Bad project',
            'description': 'Should fail',
            'materials': [
                {'material_id': 999, 'quantity': 1}
            ]
        }
        response = self.client.post('/api/projects/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('materials', response.data)

    def test_create_project_missing_material_fields(self):
        payload = {
            'name': 'Missing fields',
            'description': 'Should fail',
            'materials': [
                {'quantity': 1}
            ]
        }
        response = self.client.post('/api/projects/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('materials', response.data)
