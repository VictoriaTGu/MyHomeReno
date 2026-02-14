import React from 'react';
import './ProjectSelection.css';

export default function ProjectSelection({ projects, onSelectProject, isLoading }) {
  if (isLoading) {
    return <div className="project-selection"><p>Loading projects...</p></div>;
  }
  // Normalize projects prop to an array in case a paginated response object
  // or other non-array value is passed in by mistake.
  const projectsList = Array.isArray(projects) ? projects : (projects && projects.results) ? projects.results : [];

  if (projectsList.length === 0) {
    return <div className="project-selection"><p>No projects available.</p></div>;
  }

  return (
    <div className="project-selection">
      <h2>Select a Project</h2>
      <div className="projects-grid">
        {projectsList.map((project) => (
          <div key={project.id} className="project-card">
            {project.img && <img src={project.img} alt={project.name} className="project-img" />}
            <h3>{project.name}</h3>
            {project.description && <p>{project.description}</p>}
            <button
              className="select-btn"
              onClick={() => onSelectProject(project)}
            >
              Start Project
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
