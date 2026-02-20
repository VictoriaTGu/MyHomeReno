import React, { useState } from 'react';
import { searchProducts, updateMaterialStoreMapping } from '../services/api';
import './ProductSearchModal.css';

/**
 * Reusable ProductSearchModal component for store search and product selection.
 * Used by both AddItemForm (initial search) and ShoppingList (per-item search).
 * 
 * Props:
 * - isOpen: boolean, whether the modal is visible
 * - onClose: callback when closing without selection
 * - onSelect: callback when product is selected (receives { product, material })
 * - materialName: string, material name to search for
 * - materialId: number (optional), material ID to update with store mapping
 * - onceSelected: optional callback for analytics/logging
 */
export default function ProductSearchModal({ 
  isOpen, 
  onClose, 
  onSelect, 
  materialName, 
  materialId = null,
  onceSelected = null 
}) {
  const [searchResults, setSearchResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const [error, setError] = useState(null);
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [isUpdatingMaterial, setIsUpdatingMaterial] = useState(false);

  React.useEffect(() => {
    if (isOpen && materialName && !searchResults.length) {
      performSearch();
    }
  }, [isOpen, materialName]);

  const performSearch = async () => {
    if (!materialName) return;
    setIsSearching(true);
    setError(null);
    try {
      const response = await searchProducts(materialName);
      setSearchResults(response.data || []);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to search products');
    } finally {
      setIsSearching(false);
    }
  };

  const handleSelectProduct = async (product) => {
    setSelectedProduct(product);
    setIsUpdatingMaterial(true);
    setError(null);

    try {
      // If materialId provided, update the material with store mapping
      if (materialId) {
        const updatePayload = {
          store: product.store,
          sku: product.sku,
          product_title: product.name,
          product_url: product.url,
          product_image_url: product.image_url,
          price: product.price,
        };
        const response = await updateMaterialStoreMapping(materialId, updatePayload);
        // Notify parent with the selected product and updated material
        if (onceSelected) {
          onceSelected(product, response.data);
        }
        onSelect(product, response.data);
      } else {
        // No materialId, just return the product
        if (onceSelected) {
          onceSelected(product, null);
        }
        onSelect(product, null);
      }

      // Reset state
      setSearchResults([]);
      setSelectedProduct(null);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to update material');
    } finally {
      setIsUpdatingMaterial(false);
    }
  };

  const handleClose = () => {
    setSearchResults([]);
    setSelectedProduct(null);
    setError(null);
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="product-search-modal-overlay" onClick={handleClose}>
      <div className="product-search-modal" onClick={(e) => e.stopPropagation()}>
        <div className="product-search-header">
          <h2>Search Products for "{materialName}"</h2>
          <button className="close-btn" onClick={handleClose}>✕</button>
        </div>

        {error && <div className="error-message">{error}</div>}

        {isSearching ? (
          <div className="searching-indicator">Searching for products...</div>
        ) : searchResults.length === 0 ? (
          <div className="no-results">No products found</div>
        ) : (
          <div className="product-search-grid">
            {searchResults.map((product, idx) => (
              <div key={idx} className="product-match-card">
                {product.image_url && (
                  <img src={product.image_url} alt={product.name} className="product-thumb" />
                )}
                <h4>{product.name}</h4>
                <p className="description">{product.description}</p>
                <p className="price">${product.price} {product.currency}</p>
                {product.store && <p className="store-label">{product.store}</p>}
                <button
                  className="select-btn"
                  onClick={() => handleSelectProduct(product)}
                  disabled={isUpdatingMaterial}
                >
                  {isUpdatingMaterial && selectedProduct === product ? 'Selecting...' : 'Select'}
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
