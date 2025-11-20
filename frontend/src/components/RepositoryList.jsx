import React from 'react';
import { useAppContext } from '../contexts/AppContext';

function RepositoryList() {
  const { repositories, selectedRepo, handleRepoClick } = useAppContext();

  return (
    <section className="repository-list">
      <h2>Analyzed Repositories</h2>
      {repositories.length === 0 ? (
        <p>No repositories analyzed yet.</p>
      ) : (
        <ul>
          {repositories.map((repo) => (
            <li
              key={repo.id}
              onClick={() => handleRepoClick(repo)}
              className={selectedRepo && selectedRepo.id === repo.id ? 'selected-repo' : ''}
            >
              <a href={repo.url} target="_blank" rel="noopener noreferrer">
                {repo.name}
              </a>{' '}
              - Status: {repo.status}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

export default RepositoryList;
