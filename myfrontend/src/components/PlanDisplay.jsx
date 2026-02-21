import React, { useState } from 'react';
import './PlanDisplay.css';
import MaterialsList from './MaterialsList';

export default function PlanDisplay({ plan, onAddMaterial, isAddingMaterial }) {
  if (!plan) return null;

  return (
    <div className="plan-display">
      <div className="plan-section">
        <h3>Materials</h3>
        <MaterialsList materials={plan.materials} />
      </div>

      {plan.tools && plan.tools.length > 0 && (
        <div className="plan-section">
          <h3>Tools Needed</h3>
          <MaterialsList materials={plan.tools} />
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
