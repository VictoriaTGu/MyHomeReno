"""
Store API abstraction layer for product search.

Provides a unified interface for searching products across multiple stores (Amazon, Lowe's, etc.)
while hiding store-specific implementation details.
"""

import logging
from typing import Protocol, List, TypedDict
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class ProductResult(TypedDict):
    """Normalized product result from a store search."""
    name: str
    description: str
    price: float
    currency: str
    sku: str
    url: str
    image_url: str
    store: str  # e.g. "amazon", "lowes", "home_depot"


class StoreSearchClient(ABC):
    """Abstract base class for store search clients."""
    
    @abstractmethod
    def search_products(self, query: str, *, limit: int = 5) -> List[ProductResult]:
        """Search for products by query string.
        
        Args:
            query: Search term
            limit: Maximum number of results to return (default 5)
            
        Returns:
            List of ProductResult dictionaries
        """
        pass


class AmazonSearchClient(StoreSearchClient):
    """Amazon Product API search client."""
    
    def search_products(self, query: str, *, limit: int = 5) -> List[ProductResult]:
        """Search Amazon for products matching the query.
        
        Note: This is a placeholder implementation. In production, this would:
        1. Use boto3 or a third-party wrapper to call the Amazon Product API
        2. Parse results and extract product information
        3. Transform to ProductResult format
        
        For now, this returns an empty list to avoid hard dependency on AWS credentials.
        """
        # TODO: Implement real Amazon API integration
        # from amazon.api import AmazonAPI
        # products = api.search_product(query, limit=limit)
        # return [self._format_product(p) for p in products]
        logger.warning(f"Amazon search not yet implemented for query: {query}")
        return []
    
    def _format_product(self, product) -> ProductResult:
        """Convert Amazon product to ProductResult format."""
        # Placeholder - would extract real fields from Amazon product object
        return {
            "name": "",
            "description": "",
            "price": 0.0,
            "currency": "USD",
            "sku": "",
            "url": "",
            "image_url": "",
            "store": "amazon"
        }


class DummyStoreSearchClient(StoreSearchClient):
    """Dummy store search client for testing. Always returns consistent results."""
    
    def __init__(self):
        """Initialize with dummy product data."""
        self.dummy_products = [
            {
                "name": "Copper Pipe 1/2\" x 10 Ft",
                "description": "High-quality copper plumbing pipe, half inch diameter, 10 foot length",
                "price": 24.99,
                "currency": "USD",
                "sku": "B0123456789",
                "url": "https://amazon.com/Copper-Pipe-Premium-Plumbing/dp/B0123456789",
                "image_url": "https://m.media-amazon.com/images/I/61FzQ-bmE3L._AC_SY300_SX300_QL70_FMwebp_.jpg",
                "store": "amazon"
            },
            {
                "name": "PVC Fitting - 1/2\" Tee",
                "description": "PVC tee fitting for 1/2 inch pipe, white color, durable plastic",
                "price": 3.49,
                "currency": "USD",
                "sku": "B0987654321",
                "url": "https://amazon.com/PVC-Fitting-Tee-1-2-Inch/dp/B0987654321",
                "image_url": "https://m.media-amazon.com/images/I/41Xzep0u2JL._AC_SY300_SX300_QL70_FMwebp_.jpg",
                "store": "amazon"
            },
            {
                "name": "Professional Pipe Cutter Tool",
                "description": "Heavy-duty pipe cutter for copper and PVC pipes up to 1-5/8 inch diameter",
                "price": 18.99,
                "currency": "USD",
                "sku": "B1111111111",
                "url": "https://amazon.com/Professional-Pipe-Cutter-Heavy-Duty/dp/B1111111111",
                "image_url": "https://m.media-amazon.com/images/I/91JwEThzI7L._AC_SY300_SX300_QL70_FMwebp_.jpg",
                "store": "amazon"
            }
        ]
    
    def search_products(self, query: str, *, limit: int = 5) -> List[ProductResult]:
        """Return dummy products for testing.
        
        Always returns the same products regardless of query.
        Useful for testing without hitting real APIs.
        """
        # Return up to 'limit' dummy products
        return self.dummy_products[:limit]


def get_store_client(store: str = "amazon", use_dummy: bool = False) -> StoreSearchClient:
    """Factory function to get appropriate store search client.
    
    Args:
        store: Store name (e.g., "amazon", "lowes", "home_depot")
        use_dummy: If True, return DummyStoreSearchClient for testing
        
    Returns:
        StoreSearchClient instance
        
    Raises:
        ValueError: If store is not recognized
    """
    if use_dummy:
        return DummyStoreSearchClient()
    
    if store.lower() == "amazon":
        return AmazonSearchClient()
    elif store.lower() in ["lowes", "lowe's"]:
        # TODO: Implement LowesSearchClient
        raise NotImplementedError(f"Store {store} not yet implemented")
    elif store.lower() == "home_depot":
        # TODO: Implement HomeDepotSearchClient
        raise NotImplementedError(f"Store {store} not yet implemented")
    else:
        raise ValueError(f"Unknown store: {store}")
