import React from 'react';
import { useAppContext } from '../contexts/AppContext';

function AnalysisComparison() {
  const { analysisResults, selectedForComparison } = useAppContext();

  if (selectedForComparison.length < 2) {
    return null; // Don't show comparison table if less than 2 are selected
  }

  const selectedAnalyses = analysisResults.filter((result) =>
    selectedForComparison.includes(result.id)
  );

  return (
    <div className="analysis-comparison">
      <h3>Comparison</h3>
      <table className="comparison-table">
        <thead>
          <tr>
            <th>Metric</th>
            {selectedAnalyses.map((analysis) => (
              <th key={analysis.id}>
                {new Date(analysis.created_at).toLocaleDateString()}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          <tr>
            <td><strong>Summary</strong></td>
            {selectedAnalyses.map((analysis) => (
              <td key={analysis.id}>{analysis.summary}</td>
            ))}
          </tr>
          <tr>
            <td><strong>Files</strong></td>
            {selectedAnalyses.map((analysis) => (
              <td key={analysis.id}>{analysis.file_count}</td>
            ))}
          </tr>
          <tr>
            <td><strong>Commits</strong></td>
            {selectedAnalyses.map((analysis) => (
              <td key={analysis.id}>{analysis.commit_count}</td>
            ))}
          </tr>
          <tr>
            <td><strong>Languages</strong></td>
            {selectedAnalyses.map((analysis) => (
              <td key={analysis.id}>
                <ul>
                  {Object.entries(analysis.languages).map(([lang, count]) => (
                    <li key={lang}>{lang}: {count} files</li>
                  ))}
                </ul>
              </td>
            ))}
          </tr>
        </tbody>
      </table>
    </div>
  );
}

export default AnalysisComparison;
