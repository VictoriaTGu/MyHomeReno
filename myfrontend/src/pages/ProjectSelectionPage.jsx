import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import ProjectSelection from '../components/ProjectSelection';
import { getProjects, createShoppingList, getShoppingListsForUser } from '../services/api';

// Mock user ID - in a real app, this would come from authentication
const MOCK_USER_ID = 1;

export default function ProjectSelectionPage() {
  const [projects, setProjects] = useState([]);
  const [shoppingLists, setShoppingLists] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isCreating, setIsCreating] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [projectsResponse, listsResponse] = await Promise.all([
          getProjects(),
          getShoppingListsForUser(MOCK_USER_ID),
        ]);
        setProjects(projectsResponse.data);
        setShoppingLists(listsResponse.data);
        console.log('Shopping Lists Response:', listsResponse.data);
      } catch (err) {
        setError('Failed to load projects');
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, []);

  const handleSelectProject = async (project) => {
    setIsCreating(true);
    try {
      const response = await createShoppingList({
        project: project.id,
        name: `${project.name} Shopping List`,
      });

      // Ensure we received a created object with an id before navigating
      const created = response && response.data;
      const newId = created && created.id;
      if (!newId) {
        console.error('createShoppingList returned unexpected response:', response);
        alert('Could not create shopping list. See console for details.');
        setIsCreating(false);
        return;
      }

      navigate(`/shopping-list/${newId}`, { state: { userId: MOCK_USER_ID } });
    } catch (err) {
      alert('Failed to create shopping list');
      console.error(err);
      setIsCreating(false);
    }
  };

  const handleEditShoppingList = (listId) => {
    navigate(`/shopping-list/${listId}`, { state: { userId: MOCK_USER_ID } });
  };

  if (error) {
    return (
      <div style={{ padding: '2rem', textAlign: 'center' }}>
        <p style={{ color: 'red' }}>{error}</p>
      </div>
    );
  }

  return (
    <div>
      <ProjectSelection
        projects={projects}
        shoppingLists={shoppingLists}
        onSelectProject={handleSelectProject}
        onEditShoppingList={handleEditShoppingList}
        isLoading={isLoading || isCreating}
      />
    </div>
  );
}
