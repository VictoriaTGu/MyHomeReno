import React, { useState } from 'react';
import { addShoppingListItem } from '../services/api';
import './AddItemForm.css';

export default function AddItemForm({ listId, onItemAdded }) {
  const [formData, setFormData] = useState({
    name: '',
    category: '',
    unit: 'piece',
    quantity: 1,
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState(null);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: name === 'quantity' ? parseFloat(value) || 0 : value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    if (!formData.name || !formData.category) {
      setError('Name and category are required');
      return;
    }

    setIsSubmitting(true);
    try {
      const response = await addShoppingListItem(listId, {
        name: formData.name,
        category: formData.category,
        unit: formData.unit,
        quantity: formData.quantity,
      });
      onItemAdded(response.data);
      setFormData({
        name: '',
        category: '',
        unit: 'piece',
        quantity: 1,
      });
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to add item');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form className="add-item-form" onSubmit={handleSubmit}>
      <h3>Add New Item</h3>

      {error && <div className="error-message">{error}</div>}

      <div className="form-group">
        <label htmlFor="name">Material Name *</label>
        <input
          id="name"
          type="text"
          name="name"
          placeholder="e.g., 1/2 copper pipe"
          value={formData.name}
          onChange={handleChange}
          disabled={isSubmitting}
          required
        />
      </div>

      <div className="form-group">
        <label htmlFor="category">Category *</label>
        <input
          id="category"
          type="text"
          name="category"
          placeholder="e.g., pipe, fitting, tool"
          value={formData.category}
          onChange={handleChange}
          disabled={isSubmitting}
          required
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
          onChange={handleChange}
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
          onChange={handleChange}
          disabled={isSubmitting}
        />
      </div>

      <button type="submit" disabled={isSubmitting} className="submit-btn">
        {isSubmitting ? 'Adding...' : 'Add Item'}
      </button>
    </form>
  );
}
