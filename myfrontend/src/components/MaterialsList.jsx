import React from 'react';

export default function MaterialsList({ materials }) {
  if (!materials || materials.length === 0) {
    return <p className="empty">No materials in plan</p>;
  }
  return (
    <div className="materials-list">
      {materials.map((material, idx) => (
        <div key={idx} className="material-item">
          <div className="material-info">
            <span className="material-name">{material.name}</span>
            <span className="material-quantity">
              {material.quantity} {material.quantity > 1 ? material.unit + 's' : material.unit}
            </span>
            <span className="material-category">({material.category})</span>
          </div>
        </div>
      ))}
    </div>
  );
}
