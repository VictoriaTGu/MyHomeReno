import React from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import ShoppingList from '../components/ShoppingList';
import { getUserId } from '../services/api';
import { useEffect } from 'react';

export default function ShoppingListPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  
  // Get userId from route state, or fallback to logged-in user
  const userId = location.state?.userId || getUserId();

  useEffect(() => {
    if (!userId) {
      navigate('/login');
    }
  }, [userId, navigate]);

  const handleBack = () => {
    navigate('/');
  };

  return <ShoppingList listId={id} userId={userId} onBack={handleBack} />;
}
