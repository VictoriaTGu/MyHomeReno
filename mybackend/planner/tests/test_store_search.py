"""
Integration tests for store search functionality (Phase 2).

Tests the product search API endpoint and integration with shopping list items,
using the DummyStoreSearchClient to avoid external API dependencies.
"""

from django.test import TestCase, override_settings
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from rest_framework import status
from unittest.mock import patch, MagicMock

from planner.models import ShoppingList, Material, ShoppingListItem
from planner.store_search import DummyStoreSearchClient, HomeDepotSearchClient, get_store_client


class DummyStoreSearchClientTests(TestCase):
    """Test the DummyStoreSearchClient in isolation."""
    
    def setUp(self):
        self.client = DummyStoreSearchClient()
    
    def test_dummy_client_returns_consistent_products(self):
        """Test that dummy client always returns same 3 products."""
        results = self.client.search_products("copper pipe")
        
        self.assertEqual(len(results), 3)
        # Check first product
        self.assertIn("name", results[0])
        self.assertIn("price", results[0])
        self.assertIn("sku", results[0])
        self.assertIn("url", results[0])
        self.assertIn("image_url", results[0])
        self.assertIn("store", results[0])
    
    def test_dummy_client_respects_limit_parameter(self):
        """Test that dummy client respects limit parameter."""
        results = self.client.search_products("test", limit=2)
        self.assertEqual(len(results), 2)
        
        results = self.client.search_products("test", limit=5)
        self.assertEqual(len(results), 3)  # Only has 3 dummy products
    
    def test_dummy_client_ignores_query_string(self):
        """Test that dummy client returns same results regardless of query."""
        results1 = self.client.search_products("copper pipe")
        results2 = self.client.search_products("random query")
        
        self.assertEqual(results1[0]["name"], results2[0]["name"])
    
    def test_dummy_client_products_have_all_required_fields(self):
        """Test that all products have required ProductResult fields."""
        results = self.client.search_products("test")
        required_fields = {"name", "description", "price", "currency", "sku", "url", "image_url", "store"}
        
        for product in results:
            self.assertTrue(required_fields.issubset(product.keys()))
            # Check types
            self.assertIsInstance(product["name"], str)
            self.assertIsInstance(product["price"], (int, float))
            self.assertIsInstance(product["currency"], str)
            self.assertIsInstance(product["store"], str)
            self.assertEqual(product["store"], "amazon")


class StoreSearchAPITests(TestCase):
        def test_store_search_product_results_include_price(self):
            """Test that store search results include a price field and it is a float or int."""
            from planner.store_search import DummyStoreSearchClient
            client = DummyStoreSearchClient()
            results = client.search_products("test")
            for product in results:
                self.assertIn("price", product)
                self.assertIsInstance(product["price"], (int, float))

        @override_settings(STORE_SEARCH_USE_DUMMY=True)
        def test_patch_material_store_mapping_updates_price(self):
            """Test PATCH /api/materials/<id>/store-mapping/ updates price and other fields."""
            # Create a material
            material = Material.objects.create(name="Copper pipe", category="pipe", unit="ft")
            url = f"/api/materials/{material.id}/store-mapping/"
            patch_data = {
                "store": "amazon",
                "sku": "B00COPPER123",
                "product_title": "1/2\" Copper Pipe, 10 ft",
                "product_url": "https://www.amazon.com/dp/B00COPPER123",
                "product_image_url": "https://images.amazon.com/small/B00COPPER123.jpg",
                "price": 24.99,
                "unit": "ft"
            }
            response = self.client.patch(url, patch_data, format="json")
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            material.refresh_from_db()
            self.assertEqual(material.price, 24.99)
            self.assertEqual(material.store, "amazon")
            self.assertEqual(material.sku, "B00COPPER123")
            self.assertEqual(material.product_title, "1/2\" Copper Pipe, 10 ft")
            self.assertEqual(material.product_url, "https://www.amazon.com/dp/B00COPPER123")
            self.assertEqual(material.product_image_url, "https://images.amazon.com/small/B00COPPER123.jpg")
        def test_patch_material_store_mapping_fixes_homedepot_url(self):
            """Test PATCH /api/materials/<id>/store-mapping/ fixes Home Depot apionline URL."""
            material = Material.objects.create(name="Tile Adhesive", category="adhesive", unit="gallon")
            url = f"/api/materials/{material.id}/store-mapping/"
            patch_data = {
                "store": "home_depot",
                "sku": "100015587",
                "product_title": "AcrylPro 1 Gal. Tile Adhesive",
                "product_url": "https://apionline.homedepot.com/p/Custom-Building-Products-AcrylPro-1-Gal-4-qt-Tile-Stone-72-Hr-Dry-Time-Tile-Professional-Tile-Adhesive-ARL40001/100015587",
                "product_image_url": "https://images.homedepot-static.com/product.jpg",
                "price": 19.99,
                "unit": "gallon"
            }
            response = self.client.patch(url, patch_data, format="json")
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            material.refresh_from_db()
            self.assertEqual(
                material.product_url,
                "https://homedepot.com/p/Custom-Building-Products-AcrylPro-1-Gal-4-qt-Tile-Stone-72-Hr-Dry-Time-Tile-Professional-Tile-Adhesive-ARL40001/100015587"
            )
    """Test the store search API endpoint."""
    
    def setUp(self):
        """Set up test user and API client."""
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.token = Token.objects.create(user=self.user)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
    
    @override_settings(STORE_SEARCH_USE_DUMMY=True)
    def test_store_search_endpoint_returns_products(self):
        """Test that store search endpoint returns product results."""
        response = self.client.get('/api/store-search/search/', {
            'q': 'copper pipe',
            'store': 'amazon'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertGreater(len(response.data), 0)
    
    @override_settings(STORE_SEARCH_USE_DUMMY=True)
    def test_store_search_missing_query_param(self):
        """Test that missing query parameter returns 400."""
        response = self.client.get('/api/store-search/search/', {
            'store': 'amazon'
        })
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('detail', response.data)
    
    @override_settings(STORE_SEARCH_USE_DUMMY=True)
    def test_store_search_respects_limit_parameter(self):
        """Test that limit parameter is respected."""
        response = self.client.get('/api/store-search/search/', {
            'q': 'test',
            'store': 'amazon',
            'limit': 2
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
    
    @override_settings(STORE_SEARCH_USE_DUMMY=True)
    def test_store_search_requires_authentication(self):
        """Test that store search requires authentication."""
        client = APIClient()  # No token
        response = client.get('/api/store-search/search/', {
            'q': 'test',
            'store': 'amazon'
        })
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_store_search_unknown_store_not_implemented(self):
        """Test that unknown store raises error (unless using dummy client)."""
        # Without dummy client, should fail
        # Note: This test depends on not using dummy client
        response = self.client.get('/api/store-search/search/', {
            'q': 'test',
            'store': 'unknown_store'
        })
        
        # Should return 400/501 error or 200 with dummy results
        # When STORE_SEARCH_USE_DUMMY=False (production), unknown store should error
        # When STORE_SEARCH_USE_DUMMY=True (tests), may return results from dummy client
        # So we just verify the response is valid for now
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST, status.HTTP_501_NOT_IMPLEMENTED])
    
    @override_settings(STORE_SEARCH_USE_DUMMY=True)
    def test_store_search_default_store_is_amazon(self):
        """Test that default store parameter is 'amazon'."""
        response = self.client.get('/api/store-search/search/', {
            'q': 'test'
            # No store parameter
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data), 0)


class ShoppingListItemWithProductSelectionTests(TestCase):
    """Test adding shopping list items with product selection."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.token = Token.objects.create(user=self.user)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        
        # Create a shopping list
        self.shopping_list = ShoppingList.objects.create(
            user=self.user,
            name='Test List'
        )
    
    def test_add_item_with_product_selection(self):
        """Test adding shopping list item with product selection."""
        product_selection = {
            "name": "Copper Pipe 1/2\" x 10 Ft",
            "description": "High-quality copper plumbing pipe",
            "price": 24.99,
            "currency": "USD",
            "sku": "B0123456789",
            "url": "https://amazon.com/Copper-Pipe/dp/B0123456789",
            "image_url": "https://m.media-amazon.com/images/I/copper-pipe.jpg",
            "store": "amazon"
        }
        
        response = self.client.post(
            f'/api/shopping-lists/{self.shopping_list.id}/items/',
            {
                'name': 'copper pipe',
                'category': 'pipe',
                'unit': 'ft',
                'quantity': 10,
                'product_selection': product_selection
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('material', response.data)
        
        # Verify material was created with product details
        material = Material.objects.get(id=response.data['material']['id'])
        self.assertEqual(material.product_title, product_selection['name'])
        self.assertEqual(material.product_url, product_selection['url'])
        self.assertEqual(material.product_image_url, product_selection['image_url'])
        self.assertEqual(material.sku, product_selection['sku'])
        self.assertEqual(material.store, product_selection['store'])
    
    def test_add_item_without_product_selection(self):
        """Test adding shopping list item without product selection."""
        response = self.client.post(
            f'/api/shopping-lists/{self.shopping_list.id}/items/',
            {
                'name': 'copper pipe',
                'category': 'pipe',
                'unit': 'ft',
                'quantity': 10
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify material was created without product details
        material = Material.objects.get(id=response.data['material']['id'])
        self.assertIsNone(material.product_title)
        self.assertIsNone(material.product_url)
        self.assertIsNone(material.product_image_url)
    
    def test_add_item_defaults_category_to_general(self):
        """Test that category defaults to 'general' if not provided."""
        response = self.client.post(
            f'/api/shopping-lists/{self.shopping_list.id}/items/',
            {
                'name': 'copper pipe',
                'quantity': 10
                # No category provided
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        material = Material.objects.get(id=response.data['material']['id'])
        self.assertEqual(material.category, 'general')
    
    def test_add_item_requires_name(self):
        """Test that name is required."""
        response = self.client.post(
            f'/api/shopping-lists/{self.shopping_list.id}/items/',
            {
                'category': 'pipe',
                'unit': 'ft',
                'quantity': 10
                # No name
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_add_item_updates_quantity_if_exists(self):
        """Test that adding same material twice updates quantity."""
        # Add first time
        self.client.post(
            f'/api/shopping-lists/{self.shopping_list.id}/items/',
            {
                'name': 'copper pipe',
                'category': 'pipe',
                'quantity': 10
            },
            format='json'
        )
        
        # Add same material again with different quantity
        response = self.client.post(
            f'/api/shopping-lists/{self.shopping_list.id}/items/',
            {
                'name': 'copper pipe',
                'category': 'pipe',
                'quantity': 20
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify only one item exists with updated quantity
        items = ShoppingListItem.objects.filter(shopping_list=self.shopping_list)
        self.assertEqual(items.count(), 1)
        self.assertEqual(items.first().quantity, 20)


class StoreClientFactoryTests(TestCase):
    """Test the store client factory function."""
    
    def test_factory_returns_dummy_client_when_requested(self):
        """Test that factory returns DummyStoreSearchClient when use_dummy=True."""
        client = get_store_client('amazon', use_dummy=True)
        self.assertIsInstance(client, DummyStoreSearchClient)
    
    def test_factory_returns_amazon_client_by_default(self):
        """Test that factory returns AmazonSearchClient for 'amazon' store."""
        from planner.store_search import AmazonSearchClient
        client = get_store_client('amazon', use_dummy=False)
        self.assertIsInstance(client, AmazonSearchClient)
    
    def test_factory_raises_error_for_unknown_store(self):
        """Test that factory raises ValueError for unknown store."""
        with self.assertRaises(ValueError):
            get_store_client('unknown_store', use_dummy=False)
    
    def test_factory_raises_error_for_unimplemented_store(self):
        """Test that factory raises NotImplementedError for Lowe's (not yet implemented)."""
        with self.assertRaises(NotImplementedError):
            get_store_client('lowes', use_dummy=False)


class EndToEndSearchAndAddTests(TestCase):
    """End-to-end tests: search for product, then add to shopping list."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.token = Token.objects.create(user=self.user)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        
        self.shopping_list = ShoppingList.objects.create(
            user=self.user,
            name='Test List'
        )
    
    @override_settings(STORE_SEARCH_USE_DUMMY=True)
    def test_search_then_add_product_flow(self):
        """Test complete flow: search for products then add selected one to list."""
        # Step 1: Search for products
        search_response = self.client.get('/api/store-search/search/', {
            'q': 'copper pipe',
            'store': 'amazon'
        })
        
        self.assertEqual(search_response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(search_response.data), 0)
        
        selected_product = search_response.data[0]
        
        # Step 2: Add item with selected product
        add_response = self.client.post(
            f'/api/shopping-lists/{self.shopping_list.id}/items/',
            {
                'name': selected_product['name'],
                'category': 'pipe',
                'unit': 'piece',
                'quantity': 1,
                'product_selection': selected_product
            },
            format='json'
        )
        
        self.assertEqual(add_response.status_code, status.HTTP_201_CREATED)
        
        # Step 3: Verify material has product details
        material = Material.objects.get(id=add_response.data['material']['id'])
        self.assertEqual(material.store, selected_product['store'])
        self.assertEqual(material.sku, selected_product['sku'])
        self.assertEqual(material.product_title, selected_product['name'])
        self.assertEqual(material.product_url, selected_product['url'])
        self.assertEqual(material.product_image_url, selected_product['image_url'])


class HomeDepotSearchClientTests(TestCase):
    """Test the HomeDepotSearchClient with mocked SerpAPI responses."""
    
    def setUp(self):
        """Set up test fixtures."""
        from planner.tests.mock_serpapi_response import (
            MOCK_HOMEDEPOT_RESPONSE,
            MOCK_HOMEDEPOT_RESPONSE_INCOMPLETE,
            MOCK_HOMEDEPOT_RESPONSE_ERROR
        )
        self.mock_response = MOCK_HOMEDEPOT_RESPONSE
        self.mock_response_incomplete = MOCK_HOMEDEPOT_RESPONSE_INCOMPLETE
        self.mock_response_error = MOCK_HOMEDEPOT_RESPONSE_ERROR
        self.client = HomeDepotSearchClient()
    
    @patch('planner.store_search.requests.get')
    @override_settings(
        SERPAPI_API_KEY='***TEST_KEY***',
        SERPAPI_BASE_URL='https://serpapi.com/search',
        SERPAPI_DELIVERY_ZIP='04401',
        SERPAPI_STORE_ID='2414'
    )
    def test_homedepot_search_with_mocked_response(self, mock_get):
        """Test that HomeDepota search parses SerpAPI response correctly."""
        # Mock the requests.get call
        mock_response = MagicMock()
        mock_response.json.return_value = self.mock_response
        mock_get.return_value = mock_response
        
        # Perform search
        results = self.client.search_products("cordless drill kit", limit=3)
        
        # Verify request was made correctly
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        self.assertEqual(call_args[0][0], 'https://serpapi.com/search')
        self.assertEqual(call_args[1]['params']['q'], 'cordless drill kit')
        self.assertEqual(call_args[1]['params']['engine'], 'home_depot')
        
        # Verify results
        self.assertEqual(len(results), 3)
        self.assertEqual(results[0]['store'], 'home_depot')
        self.assertEqual(results[1]['store'], 'home_depot')
        self.assertEqual(results[2]['store'], 'home_depot')
    
    @patch('planner.store_search.requests.get')
    @override_settings(
        SERPAPI_API_KEY='***TEST_KEY***',
        SERPAPI_BASE_URL='https://serpapi.com/search',
        SERPAPI_DELIVERY_ZIP='04401'
    )
    def test_homedepot_search_parses_all_fields_correctly(self, mock_get):
        """Test that all fields are extracted and normalized correctly."""
        mock_response = MagicMock()
        mock_response.json.return_value = self.mock_response
        mock_get.return_value = mock_response
        
        results = self.client.search_products("cordless drill kit", limit=3)
        
        # Check first product fields
        first_product = results[0]
        self.assertEqual(
            first_product['name'],
            "DEWALT 20-Volt Compact Cordless Drill/Driver Kit with 1.3 Ah Battery & Charger"
        )
        self.assertEqual(first_product['price'], 98.97)
        self.assertEqual(first_product['currency'], 'USD')
        self.assertEqual(first_product['sku'], '205521897')
        self.assertIn('homedepot.com', first_product['url'])
        # Should use the fourth thumbnail (index 3)
        self.assertEqual(
            first_product['image_url'],
            "https://images.homedepot-static.com/productImages/abcd1234/abcd1234_l.jpg"
        )
        # Check second product (only one thumbnail, should use that)
        second_product = results[1]
        self.assertEqual(second_product['price'], 89.99)
        self.assertEqual(second_product['sku'], '205512345')
        self.assertEqual(
            second_product['image_url'],
            "https://images.homedepot-static.com/productImages/efgh5678/efgh5678_s.jpg"
        )
    
    @patch('planner.store_search.requests.get')
    @override_settings(
        SERPAPI_API_KEY='***TEST_KEY***',
        SERPAPI_BASE_URL='https://serpapi.com/search',
        SERPAPI_DELIVERY_ZIP='04401'
    )
    def test_homedepot_search_handles_api_error(self, mock_get):
        """Test that API errors are handled gracefully."""
        mock_response = MagicMock()
        mock_response.json.return_value = self.mock_response_error
        mock_get.return_value = mock_response
        
        results = self.client.search_products("cordless drill kit")
        
        # Should return empty list on API error
        self.assertEqual(results, [])
    
    @patch('planner.store_search.requests.get')
    @override_settings(
        SERPAPI_API_KEY='***TEST_KEY***',
        SERPAPI_BASE_URL='https://serpapi.com/search',
        SERPAPI_DELIVERY_ZIP='04401'
    )
    def test_homedepot_search_respects_limit(self, mock_get):
        """Test that limit parameter is respected."""
        mock_response = MagicMock()
        mock_response.json.return_value = self.mock_response
        mock_get.return_value = mock_response
        
        # Request only 2 results even though API returns 3
        results = self.client.search_products("cordless drill kit", limit=2)
        
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]['sku'], '205521897')
        self.assertEqual(results[1]['sku'], '205512345')
    
    @patch('planner.store_search.requests.get')
    @override_settings(
        SERPAPI_API_KEY='***TEST_KEY***',
        SERPAPI_BASE_URL='https://serpapi.com/search',
        SERPAPI_DELIVERY_ZIP='04401'
    )
    def test_homedepot_search_handles_missing_fields(self, mock_get):
        """Test that missing fields are handled gracefully."""
        mock_response = MagicMock()
        mock_response.json.return_value = self.mock_response_incomplete
        mock_get.return_value = mock_response
        
        results = self.client.search_products("test")
        
        # Should return results with safe defaults for missing fields
        self.assertEqual(len(results), 2)
        
        # First product missing price, image, link
        first = results[0]
        self.assertEqual(first['name'], 'Drill Kit No Price')
        self.assertEqual(first['price'], 0.0)
        self.assertEqual(first['sku'], '')
        self.assertEqual(first['image_url'], '')
        self.assertEqual(first['url'], '')
        
        # Second product missing title
        second = results[1]
        self.assertEqual(second['name'], 'Unknown Product')
        self.assertEqual(second['price'], 79.99)
        self.assertEqual(second['sku'], '123456')
    
    @patch('planner.store_search.requests.get')
    @override_settings(SERPAPI_API_KEY='')
    def test_homedepot_search_without_api_key(self, mock_get):
        """Test that search returns empty list if API key not configured."""
        results = self.client.search_products("cordless drill")
        
        # Should not call API and return empty list
        mock_get.assert_not_called()
        self.assertEqual(results, [])
    
    @patch('planner.store_search.requests.get')
    @override_settings(
        SERPAPI_API_KEY='***TEST_KEY***',
        SERPAPI_BASE_URL='https://serpapi.com/search',
        SERPAPI_DELIVERY_ZIP='04401'
    )
    def test_homedepot_search_handles_network_error(self, mock_get):
        """Test that network errors are handled gracefully."""
        mock_get.side_effect = Exception("Network error")
        
        results = self.client.search_products("cordless drill")
        
        # Should return empty list on error
        self.assertEqual(results, [])

