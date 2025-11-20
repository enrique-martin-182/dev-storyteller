import React from 'react';
import { useAppContext } from '../contexts/AppContext';
import AnalysisHistory from './AnalysisHistory';
import AnalysisComparison from './AnalysisComparison'; // Import the new component
import LanguageDistributionChart from './LanguageDistributionChart'; // Import the new chart component

function AnalysisResults() {
  const { selectedRepo, analysisResults } = useAppContext();

  if (!selectedRepo) {
    return null;
  }

  // Get the latest analysis result (assuming the first one is the latest)
  const latestResult = analysisResults.length > 0 ? analysisResults[0] : null;

  return (
    <section className="analysis-results">
      <h2>Analysis Results for {selectedRepo.name}</h2>
      {analysisResults.length === 0 ? (
        <p>No analysis results available yet for this repository.</p>
      ) : (
        <div>
          {latestResult && (
            <div className="analysis-card">
              <h3>Summary (Latest)</h3>
              <p>{latestResult.summary}</p>
              <h3>Narrative (Latest)</h3>
              <p>{latestResult.narrative}</p>
              <p><strong>Files:</strong> {latestResult.file_count}</p>
              <p><strong>Commits:</strong> {latestResult.commit_count}</p>
              <p><strong>Open Issues:</strong> {latestResult.open_issues_count}</p>
              <p><strong>Open Pull Requests:</strong> {latestResult.open_pull_requests_count}</p>
              <p><strong>Contributors:</strong> {latestResult.contributors ? latestResult.contributors.join(', ') : 'N/A'}</p>
              <LanguageDistributionChart languages={latestResult.languages} />
              <p>Analyzed on: {new Date(latestResult.created_at).toLocaleString()}</p>
            </div>
          )}
          <AnalysisHistory />
          <AnalysisComparison />
        </div>
      )}
    </section>
  );
}

export default AnalysisResults;
