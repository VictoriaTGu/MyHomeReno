import React from 'react';
import './ItemDetailsPanel.css';

export default function ItemDetailsPanel({ material, onClose }) {
  if (!material) return null;
  return (
    <div className="item-details-panel slide-out">
      <div className="item-details-header">
        <div className="item-details-title">
          <strong>📦 {material.product_title}</strong>
          <span className="item-details-store">{material.store}</span>
        </div>
        <button className="close-btn" onClick={onClose}>&times;</button>
      </div>
      <div className="item-details-content">
        <p className="item-details-price"><strong>Price:</strong> <span>${material.price}</span></p>
        {material.product_url && (
          <a href={material.product_url} target="_blank" rel="noopener noreferrer" className="item-details-link">View in store ↗</a>
        )}
      </div>
      {material.product_image_url && (
        <div className="item-details-image">
          <img src={material.product_image_url} alt={material.product_title} />
        </div>
      )}
    </div>
  );
}
