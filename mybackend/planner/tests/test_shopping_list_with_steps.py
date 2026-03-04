"""
Tests for shopping list retrieval with project steps included in response
"""
from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from rest_framework import status
from planner.models import Project, Material, ShoppingList, ShoppingListItem


class ShoppingListWithStepsTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')

    def test_shopping_list_includes_project_steps(self):
        """Test that retrieving a shopping list includes project steps"""
        # Create a project with steps
        steps = [
            'Turn off the main water valve',
            'Drain the lines',
            'Remove old copper pipe',
            'Install new PEX pipe'
        ]
        project = Project.objects.create(
            name='Replace copper pipe',
            description='Replace copper pipe with PEX',
            steps=steps
        )
        
        # Create a material for the project
        mat = Material.objects.create(name='PEX pipe', category='pipe', unit='ft')
        
        # Create shopping list for the project
        shopping_list = ShoppingList.objects.create(
            user=self.user,
            project=project,
            name='Pipe replacement supplies'
        )
        
        # Add items to shopping list
        ShoppingListItem.objects.create(
            shopping_list=shopping_list,
            material=mat,
            quantity=10
        )
        
        # Retrieve the shopping list
        response = self.client.get(f'/api/shopping-lists/{shopping_list.id}/', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify project and steps are in response
        self.assertIn('project', response.data)
        self.assertEqual(response.data['project']['steps'], steps)

    def test_shopping_list_without_project_steps(self):
        """Test shopping list when project has no steps"""
        # Create a project without steps
        project = Project.objects.create(
            name='Simple project',
            description='A project without steps'
        )
        
        # Create a material
        mat = Material.objects.create(name='Pipe', category='pipe', unit='ft')
        
        # Create shopping list
        shopping_list = ShoppingList.objects.create(
            user=self.user,
            project=project,
            name='Simple supplies'
        )
        
        # Add items
        ShoppingListItem.objects.create(
            shopping_list=shopping_list,
            material=mat,
            quantity=5
        )
        
        # Retrieve shopping list
        response = self.client.get(f'/api/shopping-lists/{shopping_list.id}/', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify steps is None or empty
        self.assertIn(response.data['project']['steps'], [None, [], []])

    def test_shopping_list_with_complex_steps_objects(self):
        """Test shopping list with complex step objects"""
        steps = [
            {
                'number': 1,
                'title': 'Prepare',
                'description': 'Turn off water',
                'materials': ['wrench']
            },
            {
                'number': 2,
                'title': 'Install',
                'description': 'Install new pipe',
                'materials': ['PEX pipe', 'fittings']
            }
        ]
        project = Project.objects.create(
            name='Pipe installation',
            description='Install new plumbing',
            steps=steps
        )
        
        mat = Material.objects.create(name='PEX pipe', category='pipe', unit='ft')
        
        shopping_list = ShoppingList.objects.create(
            user=self.user,
            project=project,
            name='Installation supplies'
        )
        
        ShoppingListItem.objects.create(
            shopping_list=shopping_list,
            material=mat,
            quantity=20
        )
        
        # Retrieve shopping list
        response = self.client.get(f'/api/shopping-lists/{shopping_list.id}/', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify complex steps are preserved
        self.assertEqual(response.data['project']['steps'], steps)
        self.assertEqual(len(response.data['project']['steps']), 2)
        self.assertEqual(response.data['project']['steps'][0]['title'], 'Prepare')

    def test_shopping_list_without_project(self):
        """Test shopping list without an associated project"""
        # Create shopping list without project
        shopping_list = ShoppingList.objects.create(
            user=self.user,
            project=None,
            name='Generic supplies'
        )
        
        mat = Material.objects.create(name='Generic item', category='misc', unit='piece')
        
        ShoppingListItem.objects.create(
            shopping_list=shopping_list,
            material=mat,
            quantity=1
        )
        
        # Retrieve shopping list
        response = self.client.get(f'/api/shopping-lists/{shopping_list.id}/', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # project should be None
        self.assertIsNone(response.data['project'])
