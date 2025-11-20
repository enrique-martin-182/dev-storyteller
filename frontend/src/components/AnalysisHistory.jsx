import React from 'react';
import { useAppContext } from '../contexts/AppContext';

function AnalysisHistory() {
  const { analysisResults, selectedForComparison, handleComparisonSelect } = useAppContext();

  if (analysisResults.length <= 1) {
    return null; // Don't show history if there's only one or zero results
  }

  return (
    <div className="analysis-history">
      <h4>Analysis History</h4>
      <p>Select up to 2 analyses to compare.</p>
      <ul>
        {analysisResults.map((result) => (
          <li key={result.id}>
            <input
              type="checkbox"
              id={`compare-${result.id}`}
              checked={selectedForComparison.includes(result.id)}
              onChange={() => handleComparisonSelect(result.id)}
            />
            <label htmlFor={`compare-${result.id}`}>
              Analyzed on: {new Date(result.created_at).toLocaleString()}
            </label>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default AnalysisHistory;
