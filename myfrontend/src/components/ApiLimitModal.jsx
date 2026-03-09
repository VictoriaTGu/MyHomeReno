import React from 'react';
import './ApiLimitModal.css';

/**
 * Modal that displays when a user exceeds their daily API call limit.
 * 
 * Props:
 * - isOpen: boolean, whether the modal is visible
 * - onClose: callback when closing the modal
 * - service: string, which service hit the limit ('serpapi' or 'openai')
 * - status: object with limit information
 *   - {
 *       service: string,
 *       limit: number,
 *       used: number,
 *       remaining: number,
 *       reset_time: string (ISO datetime),
 *       limit_exceeded: boolean
 *     }
 */
export default function ApiLimitModal({ isOpen, onClose, service, status }) {
  if (!isOpen || !status) return null;

  const getServiceName = (svc) => {
    const names = {
      'serpapi': 'Store Search',
      'openai': 'AI Project Planning'
    };
    return names[svc] || svc;
  };

  const getServiceDescription = (svc) => {
    const descriptions = {
      'serpapi': 'You have reached your daily limit for product store searches.',
      'openai': 'You have reached your daily limit for AI-generated project plans.'
    };
    return descriptions[svc] || 'You have reached your daily API limit.';
  };

  const resetTime = new Date(status.reset_time);
  const resetTimeStr = resetTime.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    hour12: true
  });

  return (
    <div className="api-limit-modal-overlay" onClick={onClose}>
      <div className="api-limit-modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="api-limit-modal-header">
          <h2>⏱️ Daily Limit Reached</h2>
          <button 
            className="api-limit-modal-close" 
            onClick={onClose}
            aria-label="Close modal"
          >
            ✕
          </button>
        </div>

        <div className="api-limit-modal-body">
          <p className="api-limit-service-name">
            {getServiceName(service)}
          </p>
          
          <p className="api-limit-description">
            {getServiceDescription(service)}
          </p>

          <div className="api-limit-stats">
            <div className="api-limit-stat">
              <span className="api-limit-stat-label">Calls Used Today:</span>
              <span className="api-limit-stat-value">{status.used} / {status.limit}</span>
            </div>
            
            <div className="api-limit-stat">
              <span className="api-limit-stat-label">Remaining:</span>
              <span className="api-limit-stat-value api-limit-remaining-zero">
                {status.remaining}
              </span>
            </div>

            <div className="api-limit-stat">
              <span className="api-limit-stat-label">Resets at:</span>
              <span className="api-limit-stat-value">{resetTimeStr} UTC</span>
            </div>
          </div>

          <div className="api-limit-info-box">
            <p>
              💡 <strong>Pro Tip:</strong> Come back after midnight UTC to use 
              {' '}{getServiceName(service).toLowerCase()} again!
            </p>
          </div>
        </div>

        <div className="api-limit-modal-footer">
          <button 
            className="api-limit-button api-limit-button-primary"
            onClick={onClose}
          >
            Got It, I'll Try Again Later
          </button>
        </div>
      </div>
    </div>
  );
}
