import React, { useState, useEffect } from 'react';
import './ShoppingListItemRow.css';

/**
 * Consolidated shopping list item component that handles both "toBuy" and "alreadyOwned" modes.
 * Replaces the duplicate SimpleRow (nested in ShoppingList) and ShoppingListItem components.
 * 
 * Props:
 * - item: ShoppingListItem object with { id, material, quantity, ... }
 * - mode: 'toBuy' | 'alreadyOwned' (controls checkbox behavior and display)
 * - isOwned: boolean, whether user has this item
 * - onMarkOwned: (isOwned: boolean) => void, callback when checkbox changes
 * - onUpdateQuantity: (quantity: number) => Promise<void>, callback to save quantity
 * - onDeleteItem: () => Promise<void>, callback to delete item
 * - onSearchStores: (item: ShoppingListItem) => void, callback when Search Stores clicked
 * - isDetailsOpen: boolean (optional), whether details panel is open
 * - onOpenDetails: () => void (optional), callback to open details
 * - onCloseDetails: () => void (optional), callback to close details
 */
export default function ShoppingListItemRow({
  item,
  mode = 'toBuy', // 'toBuy' or 'alreadyOwned'
  isOwned = false,
  onMarkOwned,
  onUpdateQuantity,
  onDeleteItem,
  onSearchStores,
  isDetailsOpen = false,
  onOpenDetails = null,
  onCloseDetails = null,
}) {
  const [qty, setQty] = useState(item.quantity);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  // Autosave on quantity change
  useEffect(() => {
    if (qty !== item.quantity) {
      setSaving(true);
      setError(null);
      onUpdateQuantity(qty)
        .catch(() => {
          setError('Failed to update item quantity');
        })
        .finally(() => setSaving(false));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [qty]);

  const handleCheckboxChange = (e) => {
    onMarkOwned(e.target.checked);
  };

  const unit = item.material?.unit || 'unit';

  /**
   * Handles unit pluralization and special cases (sq ft, meter, etc.)
   */
  function getDisplayUnit(quantity, unit) {
    const normalized = unit.toLowerCase();
    // Square feet
    if (['sq ft', 'sq feet', 'sqft', 'square feet', 'square foot'].includes(normalized)) {
      return quantity === 1 ? 'square foot' : 'square feet';
    }
    // Square meters
    if (['sq m', 'sq meter', 'sq meters', 'sqm', 'square meter', 'square meters'].includes(normalized)) {
      return quantity === 1 ? 'square meter' : 'square meters';
    }
    // Feet
    if (['ft', 'feet'].includes(normalized)) {
      return quantity === 1 ? 'foot' : 'feet';
    }
    // Meters
    if (['m', 'meter', 'meters'].includes(normalized)) {
      return quantity === 1 ? 'meter' : 'meters';
    }
    // Piece
    if (normalized === 'piece') {
      return quantity === 1 ? 'piece' : 'pieces';
    }
    // Default pluralization
    return quantity === 1 ? unit : unit + 's';
  }

  const displayUnit = getDisplayUnit(qty, unit);

  // Check if material has store mapping
  const hasStoreMapping = item.material?.store && item.material?.sku;

  const handleDeleteClick = async () => {
    if (!window.confirm('Remove this item from the shopping list?')) return;
    try {
      await onDeleteItem();
    } catch (err) {
      console.error('Failed to delete shopping list item:', err);
      setError('Failed to delete item');
    }
  };

  return (
    <div className={`shopping-list-item-row ${isOwned ? 'have' : ''}`}>
      <div className="checkbox-wrapper">
        <label className="checkbox">
          <input
            className="checkbox__trigger visuallyhidden"
            type="checkbox"
            checked={isOwned}
            onChange={handleCheckboxChange}
          />
          <span className="checkbox__symbol">
            <svg aria-hidden="true" className="icon-checkbox" width="28px" height="28px" viewBox="0 0 28 28" version="1" xmlns="http://www.w3.org/2000/svg">
              <path d="M4 14l8 7L24 7"></path>
            </svg>
          </span>
        </label>
      </div>

      <div className="item-row-main">
        {!hasStoreMapping && <h4>{item.material?.name}</h4>}
        {hasStoreMapping && (
          <p
            className="product-info"
            onClick={isDetailsOpen ? onCloseDetails : onOpenDetails}
            style={{ cursor: 'pointer', color: '#3182ce', fontWeight: 500 }}
          >
            📦 {item.material.product_title} - ${item.material.price}
          </p>
        )}
      </div>

      <div className="item-row-actions">
        <input
          className="quantity-input"
          type="number"
          min="0"
          step="1"
          value={Number.isNaN(qty) ? '' : Math.floor(qty)}
          onChange={(e) => setQty(Math.max(0, Math.floor(parseFloat(e.target.value) || 0)))}
          disabled={saving}
        />
        <p className="item-meta">{displayUnit}</p>
        {!hasStoreMapping && (
          <button className="search-btn" onClick={() => onSearchStores(item)}>
            Search Stores
          </button>
        )}
        <button className="delete-btn" onClick={handleDeleteClick}>
          Delete
        </button>
      </div>

      {error && (
        <div className="error-message" style={{ color: 'red', marginTop: 4 }}>
          {error}
        </div>
      )}
    </div>
  );
}
