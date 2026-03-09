import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import ProjectSelection from '../components/ProjectSelection';
import PlanDisplay from '../components/PlanDisplay';
import ApiLimitModal from '../components/ApiLimitModal';
import '../components/ai-plan-section.css';
import { getProjects, createShoppingList, getShoppingListsForUser } from '../services/api';
import { getUserId } from '../services/api';

// Mock user ID - in a real app, this would come from authentication
// const MOCK_USER_ID = 1;

export default function ProjectSelectionPage() {
  const [projects, setProjects] = useState([]);
  const [shoppingLists, setShoppingLists] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isCreating, setIsCreating] = useState(false);
  const [planInput, setPlanInput] = useState("");
  const [planResult, setPlanResult] = useState(null);
  const [isGeneratingPlan, setIsGeneratingPlan] = useState(false);
  const [apiLimitError, setApiLimitError] = useState(null);
  const [showApiLimitModal, setShowApiLimitModal] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchData = async () => {
      const uid = getUserId();
      if (!uid) {
        navigate('/login');
        return;
      }

      try {
        const [projectsResponse, listsResponse] = await Promise.all([
          getProjects(),
          getShoppingListsForUser(uid),
        ]);
        setProjects(projectsResponse.data);
        setShoppingLists(listsResponse.data);
      } catch (err) {
        setError('Failed to load projects');
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, [navigate]);

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

      navigate(`/shopping-list/${newId}`, { state: { userId: getUserId() } });
    } catch (err) {
      alert('Failed to create shopping list');
      console.error(err);
      setIsCreating(false);
    }
  };

  const handleEditShoppingList = (listId) => {
    navigate(`/shopping-list/${listId}`, { state: { userId: getUserId() } });
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
      <ApiLimitModal
        isOpen={showApiLimitModal}
        onClose={() => setShowApiLimitModal(false)}
        service={apiLimitError?.service}
        status={apiLimitError?.status}
      />
      <div className="ai-plan-section">
        <h2>AI-Powered Project Planning</h2>
        <label htmlFor="plan-input">
          Don’t see your project below? Describe what you’re trying to do and materials/sizes you're working with (e.g., 'replace ½ inch copper pipe leaking under kitchen sink with PEX')
        </label>
        <textarea
          id="plan-input"
          value={planInput}
          onChange={e => setPlanInput(e.target.value)}
          rows={4}
          placeholder="Describe your project..."
        />
        <button
          onClick={async () => {
            if (!planInput.trim()) return;
            setIsGeneratingPlan(true);
            setPlanResult(null);
            setApiLimitError(null);
            try {
              const { generatePlan } = await import('../services/api');
              const response = await generatePlan(planInput);
              setPlanResult(response.data?.plan || response.data);
            } catch (err) {
              // Check if it's an API limit exceeded error (429 status)
              if (err.response?.status === 429) {
                const limitData = err.response?.data;
                setApiLimitError({
                  service: limitData?.service,
                  status: limitData?.status
                });
                setShowApiLimitModal(true);
                // Don't set planResult error - let ApiLimitModal handle the display
              } else {
                setPlanResult({ error: 'Failed to generate plan. See console.' });
              }
              console.error(err);
            } finally {
              setIsGeneratingPlan(false);
            }
          }}
          disabled={isGeneratingPlan || !planInput.trim()}
        >
          {isGeneratingPlan ? 'Generating...' : 'Generate Plan'}
        </button>
        {planResult && (
          <div style={{ marginTop: '1rem' }}>
            {planResult.error ? (
              <p style={{ color: 'red' }}>{planResult.error}</p>
            ) : (
              <>
                <PlanDisplay plan={planResult} />
                <button
                  className="start-project-btn"
                  disabled={isCreating || !planResult.materials || planResult.materials.length === 0}
                  style={{ marginTop: '1rem' }}
                  onClick={async () => {
                    setIsCreating(true);
                    try {
                      const { createProject, createShoppingList, getUserId } = await import('../services/api');
                      // For now, combine materials and tools into one list
                      // Add category=`material` for the materials and category=`tool` for the tools 
                      // so we can separate them in the UI if we want to in the future
                      const combinedMaterials = [
                        ...(planResult.materials || []).map(item => ({ ...item, category: 'material' })),
                        ...(planResult.tools || []).map(item => ({ ...item, category: 'tool' })),
                      ];
                      // Prepare project payload
                      const projectPayload = {
                        name: planResult.title || 'AI Generated Project',
                        description: planResult.description || planInput,
                        materials: combinedMaterials,
                        steps: planResult.steps || [],
                      };
                      // Create project
                      const projectRes = await createProject(projectPayload);
                      const project = projectRes.data.project;
                      if (!project || !project.id) throw new Error('Project creation failed');
                      // Create shopping list
                      const shoppingListPayload = {
                        project: project.id,
                        name: `${project.name} Shopping List`,
                      };
                      const shoppingListRes = await createShoppingList(shoppingListPayload);
                      const shoppingList = shoppingListRes.data;
                      if (!shoppingList || !shoppingList.id) throw new Error('Shopping list creation failed');
                      // Navigate to shopping list page
                      navigate(`/shopping-list/${shoppingList.id}`, { state: { userId: getUserId() } });
                    } catch (err) {
                      alert('Failed to start project or create shopping list. See console.');
                      console.error(err);
                    } finally {
                      setIsCreating(false);
                    }
                  }}
                >
                  {isCreating ? 'Starting Project...' : 'Start Project'}
                </button>
              </>
            )}
          </div>
        )}
      </div>
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
