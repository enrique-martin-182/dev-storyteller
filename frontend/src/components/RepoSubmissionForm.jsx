import React from 'react';
import { useAppContext } from '../contexts/AppContext';

function RepoSubmissionForm() {
  const { repoUrl, setRepoUrl, handleSubmit } = useAppContext();

  return (
    <form onSubmit={handleSubmit}>
      <input
        type="text"
        value={repoUrl}
        onChange={(e) => setRepoUrl(e.target.value)}
        placeholder="e.g., https://github.com/octocat/Spoon-Knife"
        size="50"
        required
      />
      <button type="submit">Analyze Repository</button>
    </form>
  );
}

export default RepoSubmissionForm;
