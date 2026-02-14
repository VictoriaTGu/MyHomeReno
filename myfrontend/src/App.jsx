import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import ProjectSelectionPage from './pages/ProjectSelectionPage';
import ShoppingListPage from './pages/ShoppingListPage';
import LoginPage from './pages/LoginPage';
import { getToken, logout } from './services/api';
import './App.css';

function App() {
  return (
    <Router>
      <div className="app">
        <header className="app-header">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <h1>🏠 DIY Project Planner</h1>
              <p>Organize your home improvement projects</p>
            </div>
            <div>
              {getToken() ? (
                <button onClick={() => { logout(); window.location.href = '/'; }}>
                  Logout
                </button>
              ) : (
                <a href="/login">Login</a>
              )}
            </div>
          </div>
        </header>
        <main className="app-main">
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/" element={<ProjectSelectionPage />} />
            <Route path="/shopping-list/:id" element={<ShoppingListPage />} />
          </Routes>
        </main>
        <footer className="app-footer">
          <p>&copy; 2026 DIY Project Planner. Phase 1.</p>
        </footer>
      </div>
    </Router>
  );
}

export default App;
