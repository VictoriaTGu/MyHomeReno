import React, { useState, useEffect } from 'react';
import ItemDetailsPanel from './ItemDetailsPanel';
import AddItemForm from './AddItemForm';
import ProductSearchModal from './ProductSearchModal';
import ApiLimitModal from './ApiLimitModal';
import { getShoppingList, getUserMaterials, createUserMaterial, updateUserMaterial, deleteUserMaterial, updateShoppingListItem, deleteShoppingListItem, addShoppingListItem } from '../services/api';
import './ShoppingList.css';

function SimpleRow({ item, isOwned, onMarkOwned, onUpdateItem, onDeleteItem, onSearchProducts, isDetailsOpen, onOpenDetails, onCloseDetails }) {
  const [qty, setQty] = useState(item.quantity);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  // Autosave on quantity change
  useEffect(() => {
    if (qty !== item.quantity) {
      setSaving(true);
      setError(null);
      onUpdateItem(qty)
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
  // Handle edge cases for units
    function getDisplayUnit(quantity, unit) {
      const normalized = unit.toLowerCase();
      // Square feet
      if (["sq ft", "sq feet", "sqft", "square feet", "square foot"].includes(normalized)) {
        return quantity === 1 ? "square foot" : "square feet";
      }
      // Square meters
      if (["sq m", "sq meter", "sq meters", "sqm", "square meter", "square meters"].includes(normalized)) {
        return quantity === 1 ? "square meter" : "square meters";
      }
      // Feet
      if (["ft", "feet"].includes(normalized)) {
        return quantity === 1 ? "foot" : "feet";
      }
      // Meters
      if (["m", "meter", "meters"].includes(normalized)) {
        return quantity === 1 ? "meter" : "meters";
      }
      // Piece
      if (normalized === "piece") {
        return quantity === 1 ? "piece" : "pieces";
      }
      // Default pluralization
      return quantity === 1 ? unit : unit + "s";
    }
  const displayUnit = getDisplayUnit(qty, unit);

  // Check if material has store mapping
  const hasStoreMapping = item.material?.store && item.material?.sku;

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
        {!hasStoreMapping && <h4>{item.material?.name}</h4>}
        {hasStoreMapping && (
          <p className="product-info" onClick={isDetailsOpen ? onCloseDetails : onOpenDetails} style={{ cursor: 'pointer', color: '#3182ce', fontWeight: 500 }}>
            📦 {item.material.product_title} ({item.material.store}) - ${item.material.price}
          </p>
        )}
      </div>
      <div className="list-row-actions">
        <input className="quantity-input" type="number" min="0" step="1" value={Number.isNaN(qty) ? '' : Math.floor(qty)} onChange={(e) => setQty(Math.max(0, Math.floor(parseFloat(e.target.value) || 0)))} disabled={saving} />
        <p className="item-meta">{displayUnit}</p>
        {!hasStoreMapping && (
          <button className="search-btn" onClick={() => onSearchProducts(item)}>Search Stores</button>
        )}
        <button className="delete-btn" onClick={onDeleteItem}>Delete</button>
      </div>
      {error && <div className="error-message" style={{ color: 'red', marginTop: 4 }}>{error}</div>}
    </div>
  );
}

export default function ShoppingList({ listId, userId, onBack }) {
    // Track which item is open for details
    const [openDetailsItemId, setOpenDetailsItemId] = useState(null);
  const [list, setList] = useState(null);
  const [userMaterials, setUserMaterials] = useState({});
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Product search modal state
  const [modalOpen, setModalOpen] = useState(false);
  const [selectedItemForSearch, setSelectedItemForSearch] = useState(null);
  
  // API limit modal state
  const [apiLimitError, setApiLimitError] = useState(null);
  const [showApiLimitModal, setShowApiLimitModal] = useState(false);
  
  // Checkout modal
  const [checkoutModalOpen, setCheckoutModalOpen] = useState(false);

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

  const handleSearchProducts = (item) => {
    setSelectedItemForSearch(item);
    setModalOpen(true);
  };

  const handleProductSearch = async (product, updatedMaterial) => {
    // If material was updated with store mapping, refresh the shopping list
    if (updatedMaterial && selectedItemForSearch) {
      setList((prev) => ({
        ...prev,
        items: prev.items.map((item) => 
          item.id === selectedItemForSearch.id 
            ? { ...item, material: updatedMaterial }
            : item
        ),
      }));
    }
    setModalOpen(false);
    setSelectedItemForSearch(null);
  };

  const handleCloseModal = () => {
    setModalOpen(false);
    setSelectedItemForSearch(null);
  };

  // Calculate totals
  const totalItems = list ? list.items.length : 0;
  const totalPrice = list ? list.items.reduce((sum, item) => {
    const price = item.material?.price || 0;
    return sum + (price * item.quantity);
  }, 0) : 0;

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

      {list.project && list.project.steps && list.project.steps.length > 0 && (
        <div className="list-section">
          <h2>Project Steps</h2>
          <ol className="steps-list">
            {list.project.steps.map((step, index) => (
              <li key={index} className="step-item">
                {typeof step === 'string' ? step : step.description || step.title || JSON.stringify(step)}
              </li>
            ))}
          </ol>
        </div>
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
                <div key={item.id}>
                  <SimpleRow
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
                    onSearchProducts={handleSearchProducts}
                    isDetailsOpen={openDetailsItemId === item.id}
                    onOpenDetails={() => setOpenDetailsItemId(item.id)}
                    onCloseDetails={() => setOpenDetailsItemId(null)}
                  />
                  {openDetailsItemId === item.id && item.material?.store && item.material?.sku && (
                    <ItemDetailsPanel material={item.material} onClose={() => setOpenDetailsItemId(null)} />
                  )}
                </div>
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
                  <div key={item.id}>
                    <SimpleRow
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
                      onSearchProducts={handleSearchProducts}
                      isDetailsOpen={openDetailsItemId === item.id}
                      onOpenDetails={() => setOpenDetailsItemId(item.id)}
                      onCloseDetails={() => setOpenDetailsItemId(null)}
                    />
                    {openDetailsItemId === item.id && item.material?.store && item.material?.sku && (
                      <ItemDetailsPanel material={item.material} onClose={() => setOpenDetailsItemId(null)} />
                    )}
                  </div>
                );
              })}
          </div>
        </>
      ) : (
        <p className="empty-message">No items in this list yet.</p>
      )}

      {/* Totals Section */}
      <div className="totals-section" style={{ marginTop: '24px', padding: '16px', background: '#f8f9fa', borderRadius: '8px', textAlign: 'center' }}>
        <p style={{ margin: '8px 0' }}><strong>Total Items:</strong> {totalItems}</p>
        <p style={{ margin: '8px 0', fontSize: '18px', fontWeight: 'bold', color: '#3182ce' }}><strong>Total Price:</strong> ${totalPrice.toFixed(2)}</p>
      </div>

      {/* Checkout Button */}
      <button 
        onClick={() => setCheckoutModalOpen(true)} 
        style={{ marginTop: '16px', width: '100%', padding: '12px', fontSize: '16px', fontWeight: 'bold', background: '#27ae60', color: 'white', border: 'none', borderRadius: '8px', cursor: 'pointer' }}
      >
        Checkout
      </button>

      {/* Checkout Modal */}
      {checkoutModalOpen && (
        <div className="checkout-modal-overlay" onClick={() => setCheckoutModalOpen(false)} style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.6)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}>
          <div className="checkout-modal" onClick={(e) => e.stopPropagation()} style={{ background: 'white', borderRadius: '12px', padding: '32px', maxWidth: '500px', textAlign: 'center' }}>
            <h2 style={{ marginBottom: '16px' }}>💳 Become a DIY Member</h2>
            <p style={{ marginBottom: '24px', color: '#666' }}>Use Cart Checkout to track your project and manage orders across stores.</p>
            <div style={{ display: 'flex', gap: '12px', justifyContent: 'center' }}>
              <button 
                onClick={() => setCheckoutModalOpen(false)}
                style={{ padding: '10px 24px', borderRadius: '6px', background: '#e0e0e0', border: 'none', cursor: 'pointer', fontWeight: 600 }}
              >Close</button>
              <a 
                href="#" 
                onClick={(e) => { e.preventDefault(); }}
                style={{ padding: '10px 24px', borderRadius: '6px', background: '#3182ce', color: 'white', border: 'none', cursor: 'pointer', fontWeight: 600, textDecoration: 'none' }}
              >Learn More</a>
            </div>
          </div>
        </div>
      )}

      <AddItemForm listId={listId} onItemAdded={handleItemAdded} />

      {/* API Limit Modal */}
      <ApiLimitModal
        isOpen={showApiLimitModal}
        onClose={() => setShowApiLimitModal(false)}
        service={apiLimitError?.service}
        status={apiLimitError?.status}
      />

      {/* Product Search Modal */}
      {selectedItemForSearch && (
        <ProductSearchModal
          isOpen={modalOpen}
          onClose={handleCloseModal}
          onSelect={handleProductSearch}
          materialName={selectedItemForSearch.material?.name}
          materialId={selectedItemForSearch.material?.id}
          onApiLimitError={(errorData) => {
            setApiLimitError(errorData);
            setShowApiLimitModal(true);
            // Close the search modal, but keep ApiLimitModal visible
            setModalOpen(false);
          }}
        />
      )}
    </div>
  );
}
