import React, { useState, useEffect } from 'react';
import ShoppingListItem from './ShoppingListItem';
import AddItemForm from './AddItemForm';
import { getShoppingList, getUserMaterials } from '../services/api';
import './ShoppingList.css';

export default function ShoppingList({ listId, userId, onBack }) {
  const [list, setList] = useState(null);
  const [userMaterials, setUserMaterials] = useState({});
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      // Defensive: avoid calling API with invalid id
      if (!listId || String(listId) === 'undefined') {
        setError('Invalid shopping list id');
        setIsLoading(false);
        return;
      }

      setIsLoading(true);
      setError(null);
      try {
        const [listResponse, userMatResponse] = await Promise.all([
          getShoppingList(listId),
          getUserMaterials(userId),
        ]);
        setList(listResponse.data);
        // Create a map of material_id -> UserMaterial for quick lookup
        const materialMap = {};
        userMatResponse.data.forEach((um) => {
          materialMap[um.material] = um;
        });
        setUserMaterials(materialMap);
      } catch (err) {
        setError('Failed to load shopping list');
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, [listId, userId]);

  const handleItemUpdate = (itemId, updatedItem) => {
    setList((prev) => ({
      ...prev,
      items: prev.items.map((item) => (item.id === itemId ? updatedItem : item)),
    }));
  };

  const handleItemDelete = (itemId) => {
    setList((prev) => ({
      ...prev,
      items: prev.items.filter((item) => item.id !== itemId),
    }));
  };

  const handleItemAdded = (newItem) => {
    setList((prev) => ({
      ...prev,
      items: [...prev.items, newItem],
    }));
  };

  const checkUserHasQuantity = (item) => {
    const userMat = userMaterials[item.material?.id];
    if (!userMat) return false;
    return userMat.quantity >= item.quantity;
  };

  if (isLoading) {
    return <div className="shopping-list loading">Loading shopping list...</div>;
  }

  if (error) {
    return (
      <div className="shopping-list error">
        <p>{error}</p>
        <button onClick={onBack}>Go Back</button>
      </div>
    );
  }

  if (!list) {
    return <div className="shopping-list">No shopping list found</div>;
  }

  return (
    <div className="shopping-list">
      <div className="list-header">
        <button className="back-btn" onClick={onBack}>
          ← Back to Projects
        </button>
        <h1>{list.name}</h1>
        <p className="meta">Created: {new Date(list.created_at).toLocaleDateString()}</p>
      </div>

      {list.items && list.items.length > 0 ? (
        <div className="list-items">
          <h2>Items ({list.items.length})</h2>
          {list.items.map((item) => (
            <ShoppingListItem
              key={item.id}
              item={item}
              userHasQuantity={checkUserHasQuantity(item)}
              onUpdate={handleItemUpdate}
              onDelete={handleItemDelete}
            />
          ))}
        </div>
      ) : (
        <p className="empty-message">No items in this list yet.</p>
      )}

      <AddItemForm listId={listId} onItemAdded={handleItemAdded} />
    </div>
  );
}
