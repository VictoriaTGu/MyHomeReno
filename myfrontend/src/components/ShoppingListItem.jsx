import React, { useState } from 'react';
import { deleteShoppingListItem, updateShoppingListItem } from '../services/api';
import './ShoppingListItem.css';

export default function ShoppingListItem({
  item,
  userHasQuantity,
  onUpdate,
  onDelete,
}) {
  const [quantity, setQuantity] = useState(item.quantity);
  const [isUpdating, setIsUpdating] = useState(false);

  const handleQuantityChange = (e) => {
    setQuantity(parseFloat(e.target.value) || 0);
  };

  const handleSave = async () => {
    if (quantity !== item.quantity) {
      setIsUpdating(true);
      try {
        await updateShoppingListItem(item.id, { quantity });
        onUpdate(item.id, { ...item, quantity });
      } catch (error) {
        console.error('Failed to update item:', error);
        setQuantity(item.quantity);
      } finally {
        setIsUpdating(false);
      }
    }
  };

  const handleDelete = async () => {
    if (window.confirm('Are you sure you want to remove this item?')) {
      try {
        await deleteShoppingListItem(item.id);
        onDelete(item.id);
      } catch (error) {
        console.error('Failed to delete item:', error);
      }
    }
  };

  return (
    <div className="shopping-list-item">
      <div className="item-checkbox">
        <input
          type="checkbox"
          checked={userHasQuantity}
          disabled
          title="Checked if you have the required quantity"
        />
      </div>

      <div className="item-details">
        <h4>{item.material?.name}</h4>
        <p className="item-meta">
          Category: {item.material?.category} | Unit: {item.material?.unit}
        </p>
      </div>

      <div className="item-quantity">
        <label htmlFor={`qty-${item.id}`}>Quantity:</label>
        <input
          id={`qty-${item.id}`}
          type="number"
          min="0"
          step="0.1"
          value={quantity}
          onChange={handleQuantityChange}
          disabled={isUpdating}
        />
        <button
          className="save-btn"
          onClick={handleSave}
          disabled={isUpdating || quantity === item.quantity}
        >
          {isUpdating ? 'Saving...' : 'Update'}
        </button>
      </div>

      <button className="delete-btn" onClick={handleDelete} title="Remove item">
        Delete
      </button>
    </div>
  );
}
