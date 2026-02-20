import React from 'react';
import './ItemDetailsPanel.css';

export default function ItemDetailsPanel({ material, onClose }) {
  if (!material) return null;
  return (
    <div className="item-details-panel slide-out">
      <div className="product-card">
        {material.product_image_url && (
          <div className="product-img">
            <img src={material.product_image_url} alt={material.product_title} />
          </div>
        )}
        <div className="product-info">
          <div className="product-text">
            <h1>{material.product_title}</h1>
            <h2>{material.store}</h2>
            {material.product_url && (
              <a href={material.product_url} target="_blank" rel="noopener noreferrer" className="item-details-link">View in store ↗</a>
            )}
          </div>
          <div className="product-price">
            <p><span>{material.price}</span>$</p>
          </div>
        </div>
        <button className="close-btn" onClick={onClose}>&times;</button>
      </div>
    </div>
  );
}
