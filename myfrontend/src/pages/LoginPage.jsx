import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { login } from '../services/api';
import './LoginPage.css';

export default function LoginPage() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const data = await login(username, password);
      if (data.token) {
        navigate('/');
      } else {
        setError('Login failed');
      }
    } catch (err) {
      setError('Login failed');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-card">
      <h2>Sign in</h2>
      <form onSubmit={handleSubmit}>
        <div className="login-field">
          <label>Username</label>
          <input
            autoFocus
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
            className="login-input"
          />
        </div>
        <div className="login-field">
          <label>Password</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            className="login-input"
          />
        </div>
        {error && <div className="login-error">{error}</div>}
        <div className="login-actions">
          <button type="submit" disabled={loading} className="login-submit">
            {loading ? 'Signing in…' : 'Sign in'}
          </button>
        </div>
      </form>
      <p className="login-dev-note">
        For development: use the seeded account <strong>testuser</strong> / <strong>testpass123</strong>
      </p>
      </div>
    </div>
  );
}
