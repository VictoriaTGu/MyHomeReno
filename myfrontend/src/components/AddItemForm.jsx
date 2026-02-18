import React, { useState } from 'react';
import { addShoppingListItem, searchProducts } from '../services/api';
import './AddItemForm.css';

export default function AddItemForm({ listId, onItemAdded }) {
  // Track form stages: 'input', 'searching', 'results', 'confirming'
  const [stage, setStage] = useState('input');
  
  // Search input
  const [searchQuery, setSearchQuery] = useState('');
  
  // Form data
  const [formData, setFormData] = useState({
    name: '',
    category: '',
    unit: 'piece',
    quantity: 1,
  });
  
  // Search results
  const [searchResults, setSearchResults] = useState([]);
  const [selectedProduct, setSelectedProduct] = useState(null);
  
  // Loading and error states
  const [isSearching, setIsSearching] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState(null);

  const handleSearchChange = (e) => {
    setSearchQuery(e.target.value);
  };

  const handleFormChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: name === 'quantity' ? parseFloat(value) || 0 : value,
    }));
  };

  const handleSearch = async (e) => {
    e.preventDefault();
    setError(null);

    if (!searchQuery.trim()) {
      setError('Please enter a search query');
      return;
    }

    setIsSearching(true);
    try {
      const response = await searchProducts(searchQuery);
      setSearchResults(response.data || []);
      setStage('results');
      
      // Pre-fill material name from search query for fallback
      setFormData((prev) => ({
        ...prev,
        name: searchQuery,
      }));
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to search products');
      setStage('input');
    } finally {
      setIsSearching(false);
    }
  };

  const handleSelectProduct = (product) => {
    setSelectedProduct(product);
    setStage('confirming');
  };

  const handleSkipSearch = () => {
    // Go back to input form to add manually
    setStage('input');
    setSearchResults([]);
    setSelectedProduct(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    if (!formData.name) {
      setError('Material name is required');
      return;
    }

    setIsSubmitting(true);
    try {
      const payload = {
        name: formData.name,
        category: formData.category || 'general',
        unit: formData.unit,
        quantity: formData.quantity,
      };

      // If product was selected, include it in the payload
      if (selectedProduct) {
        payload.product_selection = selectedProduct;
      }

      const response = await addShoppingListItem(listId, payload);
      onItemAdded(response.data);
      
      // Reset form
      setStage('input');
      setFormData({
        name: '',
        category: '',
        unit: 'piece',
        quantity: 1,
      });
      setSearchQuery('');
      setSearchResults([]);
      setSelectedProduct(null);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to add item');
    } finally {
      setIsSubmitting(false);
    }
  };

  // ===== RENDER STAGES =====

  // Stage 1: Input - Search or skip to manual entry
  if (stage === 'input') {
    return (
      <form className="add-item-form" onSubmit={handleSearch}>
        <h3>Add New Item</h3>

        {error && <div className="error-message">{error}</div>}

        <div className="form-group">
          <label htmlFor="search-query">Material Name</label>
          <div className="search-group">
            <input
              id="search-query"
              type="text"
              placeholder="e.g., 1/2 copper pipe"
              value={searchQuery}
              onChange={handleSearchChange}
              disabled={isSearching}
              required
            />
            <button
              type="submit"
              disabled={isSearching || !searchQuery.trim()}
              className="search-btn"
            >
              {isSearching ? 'Searching...' : 'Search'}
            </button>
          </div>
        </div>

        <div className="divider">or</div>

        <button
          type="button"
          className="skip-btn"
          onClick={() => setStage('manual')}
        >
          Add Without Product Search
        </button>
      </form>
    );
  }

  // Stage 2: Results - Show search results
  if (stage === 'results') {
    return (
      <div className="add-item-form">
        <h3>Found Products</h3>

        {error && <div className="error-message">{error}</div>}

        {searchResults.length === 0 ? (
          <div className="no-results">
            <p>No products found for "{searchQuery}"</p>
            <button
              type="button"
              className="back-btn"
              onClick={handleSkipSearch}
            >
              Back
            </button>
          </div>
        ) : (
          <div className="products-list">
            {searchResults.map((product, idx) => (
              <div key={idx} className="product-card">
                {product.image_url && (
                  <img
                    src={product.image_url}
                    alt={product.name}
                    className="product-image"
                  />
                )}
                <div className="product-info">
                  <h4>{product.name}</h4>
                  <p className="product-description">{product.description}</p>
                  <p className="product-price">
                    ${product.price} {product.currency}
                  </p>
                </div>
                <button
                  type="button"
                  className="select-btn"
                  onClick={() => handleSelectProduct(product)}
                >
                  Select
                </button>
              </div>
            ))}
          </div>
        )}

        <div className="results-actions">
          <button
            type="button"
            className="back-btn"
            onClick={handleSkipSearch}
          >
            Back
          </button>
          <button
            type="button"
            className="skip-btn"
            onClick={() => setStage('manual')}
          >
            Can't Find It? Add Manually
          </button>
        </div>
      </div>
    );
  }

  // Stage 3: Confirming - Show selected product with quantity
  if (stage === 'confirming') {
    return (
      <form className="add-item-form confirm-form" onSubmit={handleSubmit}>
        <h3>Confirm Item</h3>

        {error && <div className="error-message">{error}</div>}

        {selectedProduct && (
          <div className="selected-product">
            {selectedProduct.image_url && (
              <img
                src={selectedProduct.image_url}
                alt={selectedProduct.name}
                className="product-image"
              />
            )}
            <div className="product-details">
              <h4>{selectedProduct.name}</h4>
              <p>${selectedProduct.price} {selectedProduct.currency}</p>
              <p className="product-sku">SKU: {selectedProduct.sku}</p>
            </div>
          </div>
        )}

        <div className="form-group">
          <label htmlFor="quantity">Quantity</label>
          <input
            id="quantity"
            type="number"
            name="quantity"
            min="0"
            step="0.1"
            value={formData.quantity}
            onChange={handleFormChange}
            disabled={isSubmitting}
          />
        </div>

        <div className="confirm-actions">
          <button
            type="button"
            className="back-btn"
            onClick={() => setStage('results')}
            disabled={isSubmitting}
          >
            Back
          </button>
          <button
            type="submit"
            disabled={isSubmitting}
            className="submit-btn"
          >
            {isSubmitting ? 'Adding...' : 'Add Item'}
          </button>
        </div>
      </form>
    );
  }

  // Stage 4: Manual entry - Traditional form for manual entry
  if (stage === 'manual') {
    return (
      <form className="add-item-form" onSubmit={handleSubmit}>
        <h3>Add Item Manually</h3>

        {error && <div className="error-message">{error}</div>}

        <div className="form-group">
          <label htmlFor="name">Material Name *</label>
          <input
            id="name"
            type="text"
            name="name"
            placeholder="e.g., 1/2 copper pipe"
            value={formData.name}
            onChange={handleFormChange}
            disabled={isSubmitting}
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="category">Category</label>
          <input
            id="category"
            type="text"
            name="category"
            placeholder="e.g., pipe, fitting, tool"
            value={formData.category}
            onChange={handleFormChange}
            disabled={isSubmitting}
          />
        </div>

        <div className="form-group">
          <label htmlFor="unit">Unit</label>
          <input
            id="unit"
            type="text"
            name="unit"
            placeholder="e.g., piece, ft, m"
            value={formData.unit}
            onChange={handleFormChange}
            disabled={isSubmitting}
          />
        </div>

        <div className="form-group">
          <label htmlFor="quantity">Quantity</label>
          <input
            id="quantity"
            type="number"
            name="quantity"
            min="0"
            step="0.1"
            value={formData.quantity}
            onChange={handleFormChange}
            disabled={isSubmitting}
          />
        </div>

        <div className="manual-actions">
          <button
            type="button"
            className="back-btn"
            onClick={() => setStage('input')}
            disabled={isSubmitting}
          >
            Back
          </button>
          <button
            type="submit"
            disabled={isSubmitting}
            className="submit-btn"
          >
            {isSubmitting ? 'Adding...' : 'Add Item'}
          </button>
        </div>
      </form>
    );
  }
}
