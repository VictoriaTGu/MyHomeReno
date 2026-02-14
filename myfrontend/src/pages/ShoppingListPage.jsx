import React from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import ShoppingList from '../components/ShoppingList';

export default function ShoppingListPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  
  // Get userId from route state, or default to mock user
  const userId = location.state?.userId || 1;

  const handleBack = () => {
    navigate('/');
  };

  return <ShoppingList listId={id} userId={userId} onBack={handleBack} />;
}
