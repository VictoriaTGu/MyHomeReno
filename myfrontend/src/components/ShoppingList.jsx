import React, { useState, useEffect } from 'react';
import AddItemForm from './AddItemForm';
import PlanDisplay from './PlanDisplay';
import { getShoppingList, getUserMaterials, createUserMaterial, updateUserMaterial, deleteUserMaterial, updateShoppingListItem, deleteShoppingListItem, generatePlan, addShoppingListItem } from '../services/api';
import './ShoppingList.css';

function SimpleRow({ item, isOwned, onMarkOwned, onUpdateItem, onDeleteItem }) {
  const [qty, setQty] = useState(item.quantity);
  const [saving, setSaving] = useState(false);

  const handleSave = async () => {
    if (qty === item.quantity) return;
    setSaving(true);
    try {
      await onUpdateItem(qty);
    } finally {
      setSaving(false);
    }
  };

  const handleCheckboxChange = (e) => {
    onMarkOwned(e.target.checked);
  };
  const unit = item.material?.unit || 'unit';
  const displayUnit = item.quantity > 1 ? unit + "s" : unit;

  return (
    <div className={`list-row ${isOwned ? 'have' : ''}`}>
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
      <div className="list-row-main">
        <h4>{item.material?.name}</h4>
        
      </div>
      <div className="list-row-actions">
        <input className="quantity-input" type="number" min="0" step="1" value={qty} onChange={(e) => setQty(parseFloat(e.target.value) || 0)} />
        <p className="item-meta">{displayUnit}</p>
        <button className="save-btn" onClick={handleSave} disabled={saving || qty === item.quantity}>{saving ? 'Saving...' : 'Save'}</button>
        <button className="delete-btn" onClick={onDeleteItem}>Delete</button>
      </div>
    </div>
  );
}

export default function ShoppingList({ listId, userId, onBack }) {
  const [list, setList] = useState(null);
  const [userMaterials, setUserMaterials] = useState({});
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [plan, setPlan] = useState(null);
  const [planDescription, setPlanDescription] = useState('');
  const [isGeneratingPlan, setIsGeneratingPlan] = useState(false);
  const [planError, setPlanError] = useState(null);

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
          materialMap[um.material.id] = um;
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

  const handleAddUserMaterial = async (item) => {
    try {
      const res = await createUserMaterial(userId, { material: item.material.id, quantity: item.quantity });
      // store in map
      setUserMaterials((prev) => ({ ...prev, [item.material.id]: res.data }));
    } catch (err) {
      console.error('Failed to add user material:', err);
      alert('Failed to mark as owned');
    }
  };

  const handleRemoveUserMaterial = async (materialId) => {
    try {
      await deleteUserMaterial(userId, materialId);
      setUserMaterials((prev) => {
        const copy = { ...prev };
        delete copy[materialId];
        return copy;
      });
    } catch (err) {
      console.error('Failed to remove user material:', err);
      alert('Failed to remove ownership');
    }
  };

  const handleUpdateUserMaterial = async (materialId, quantity) => {
    try {
      const res = await updateUserMaterial(userId, materialId, { quantity });
      setUserMaterials((prev) => ({ ...prev, [materialId]: res.data }));
    } catch (err) {
      console.error('Failed to update user material:', err);
      alert('Failed to update quantity');
    }
  };

  const handleGeneratePlan = async () => {
    if (!planDescription.trim()) {
      setPlanError('Please describe your project.');
      return;
    }

    setIsGeneratingPlan(true);
    setPlanError(null);
    try {
      const res = await generatePlan(planDescription);
      setPlan(res.data);
      setPlanDescription('');
    } catch (err) {
      console.error('Failed to generate plan:', err);
      setPlanError(err.response?.data?.detail || 'Failed to generate plan. Make sure OpenAI API is configured.');
    } finally {
      setIsGeneratingPlan(false);
    }
  };

  const handleAddMaterialFromPlan = async (material) => {
    try {
      const materialData = {
        name: material.name,
        category: material.category,
        unit: material.unit,
        store: 'unknown',
      };
      
      const res = await addShoppingListItem(listId, {
        quantity: material.quantity,
        material_data: materialData,
      });
      
      handleItemAdded(res.data);
    } catch (err) {
      console.error('Failed to add material from plan:', err);
      alert(`Failed to add ${material.name} to shopping list`);
    }
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

      {/* Plan Generation Section - Phase 3 */}
      <div className="plan-generation-section">
        <h2>✨ Generate a Project Plan</h2>
        <p className="section-desc">Describe a project and we'll create a detailed plan with materials, tools, and steps.</p>
        <div className="plan-input-group">
          <textarea
            className="plan-description-input"
            placeholder="e.g., Replace ½ inch copper pipe leaking under kitchen sink with PEX"
            value={planDescription}
            onChange={(e) => setPlanDescription(e.target.value)}
            rows="3"
            disabled={isGeneratingPlan}
          />
          <button
            className="generate-plan-btn"
            onClick={handleGeneratePlan}
            disabled={isGeneratingPlan || !planDescription.trim()}
          >
            {isGeneratingPlan ? 'Generating...' : 'Generate Plan'}
          </button>
        </div>
        {planError && <div className="plan-error-message">{planError}</div>}
      </div>

      {/* Display Generated Plan */}
      {plan && (
        <PlanDisplay
          plan={plan}
          listId={listId}
          onItemAdded={handleItemAdded}
          onClose={() => setPlan(null)}
        />
      )}

      {list.items && list.items.length > 0 ? (
        <>
          <div className="list-section">
            <h2>Shopping List</h2>
            {list.items.filter((it) => !checkUserHasQuantity(it)).length === 0 && (
              <p className="empty-message">No items to buy — you have everything.</p>
            )}
            {list.items
              .filter((it) => !checkUserHasQuantity(it))
              .map((item) => (
                <SimpleRow
                  key={item.id}
                  item={item}
                  isOwned={false}
                  onMarkOwned={(isOwned) => {
                    if (isOwned) {
                      handleAddUserMaterial(item);
                    }
                  }}
                  onUpdateItem={async (quantity) => {
                    try {
                      const res = await updateShoppingListItem(item.id, { quantity });
                      handleItemUpdate(item.id, { ...item, quantity: res.data.quantity });
                    } catch (err) {
                      console.error('Failed to update shopping list item:', err);
                      alert('Failed to update item quantity');
                    }
                  }}
                  onDeleteItem={async () => {
                    if (!window.confirm('Remove this item from the shopping list?')) return;
                    try {
                      await deleteShoppingListItem(item.id);
                      handleItemDelete(item.id);
                    } catch (err) {
                      console.error('Failed to delete shopping list item:', err);
                      alert('Failed to delete item');
                    }
                  }}
                />
              ))}
          </div>

          <div className="list-section">
            <h2>Already Have</h2>
            {list.items.filter((it) => checkUserHasQuantity(it)).length === 0 && (
              <p className="empty-message">Click on checkboxes if you already own a material or tool.</p>
            )}
            {list.items
              .filter((it) => checkUserHasQuantity(it))
              .map((item) => {
                const userMat = userMaterials[item.material?.id];
                return (
                  <SimpleRow
                    key={item.id}
                    item={item}
                    isOwned={true}
                    onMarkOwned={(isOwned) => {
                      if (!isOwned) {
                        handleRemoveUserMaterial(item.material.id);
                      }
                    }}
                    onUpdateItem={async (quantity) => {
                      try {
                        const res = await updateShoppingListItem(item.id, { quantity });
                        handleItemUpdate(item.id, { ...item, quantity: res.data.quantity });
                      } catch (err) {
                        console.error('Failed to update shopping list item:', err);
                        alert('Failed to update item quantity');
                      }
                    }}
                    onDeleteItem={async () => {
                      if (!window.confirm('Remove this item from the shopping list?')) return;
                      try {
                        await deleteShoppingListItem(item.id);
                        handleItemDelete(item.id);
                      } catch (err) {
                        console.error('Failed to delete shopping list item:', err);
                        alert('Failed to delete item');
                      }
                    }}
                  />
                );
              })}
          </div>
        </>
      ) : (
        <p className="empty-message">No items in this list yet.</p>
      )}

      <AddItemForm listId={listId} onItemAdded={handleItemAdded} />
    </div>
  );
}
