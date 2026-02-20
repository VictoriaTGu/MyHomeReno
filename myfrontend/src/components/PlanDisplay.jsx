import React, { useState } from 'react';
import './PlanDisplay.css';

export default function PlanDisplay({ plan, onAddMaterial, isAddingMaterial }) {
  if (!plan) return null;

  return (
    <div className="plan-display">
      <div className="plan-section">
        <h3>Materials</h3>
        {plan.materials && plan.materials.length > 0 ? (
          <div className="materials-list">
            {plan.materials.map((material, idx) => (
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
        ) : (
          <p className="empty">No materials in plan</p>
        )}
      </div>

      {plan.tools && plan.tools.length > 0 && (
        <div className="plan-section">
          <h3>Tools Needed</h3>
          <div className="tools-list">
            {plan.tools.map((tool, idx) => (
              <div key={idx} className="tool-item">
                <div className="tool-info">
                  <span className="tool-name">{tool.name}</span>
                  <span className="tool-quantity">
                    {tool.quantity} {tool.quantity > 1 ? tool.unit + 's' : tool.unit}
                  </span>
                  <span className="tool-category">({tool.category})</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {plan.steps && plan.steps.length > 0 && (
        <div className="plan-section">
          <h3>Steps</h3>
          <ol className="steps-list">
            {plan.steps.map((step, idx) => (
              <li key={idx}>{step}</li>
            ))}
          </ol>
        </div>
      )}

      {plan.warnings && plan.warnings.length > 0 && (
        <div className="plan-section warnings">
          <h3>⚠️ Safety & Warnings</h3>
          <ul className="warnings-list">
            {plan.warnings.map((warning, idx) => (
              <li key={idx}>{warning}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
