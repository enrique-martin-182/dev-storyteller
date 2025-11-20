import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import AnalysisResults from './AnalysisResults';
import { useAppContext } from '../../src/contexts/AppContext';

// Mock the useAppContext hook
vi.mock('../../src/contexts/AppContext', () => ({
  useAppContext: vi.fn(),
}));

// Mock the AnalysisHistory component
vi.mock('./AnalysisHistory', () => ({
  default: () => <div data-testid="analysis-history"></div>,
}));

// Mock the LanguageDistributionChart component
vi.mock('./LanguageDistributionChart', () => ({
  default: () => <div data-testid="language-distribution-chart"></div>,
}));

describe('AnalysisResults', () => {
  const mockSelectedRepo = { id: 1, name: 'test-repo' };
  const mockAnalysisResults = [
    {
      id: 1,
      summary: 'Latest summary',
      file_count: 10,
      commit_count: 5,
      languages: { 'JavaScript': 10, 'HTML': 5 },
      created_at: new Date().toISOString(),
    },
    {
      id: 2,
      summary: 'Older summary',
      file_count: 8,
      commit_count: 4,
      languages: { 'JavaScript': 8, 'HTML': 4 },
      created_at: new Date(Date.now() - 86400000).toISOString(), // 1 day ago
    },
  ];

  const defaultContext = {
    selectedRepo: null,
    analysisResults: [],
    selectedForComparison: [], // Add this line
  };

  beforeEach(() => {
    vi.mocked(useAppContext).mockReturnValue(defaultContext);
  });

  it('renders nothing if no selectedRepo is provided', () => {
    render(<AnalysisResults />);
    expect(screen.queryByRole('heading', { name: /analysis results/i })).not.toBeInTheDocument();
  });

  it('renders "No analysis results available yet" if analysisResults is empty', () => {
    vi.mocked(useAppContext).mockReturnValue({
      ...defaultContext,
      selectedRepo: mockSelectedRepo,
    });

    render(<AnalysisResults />);
    expect(screen.getByText(/no analysis results available yet for this repository./i)).toBeInTheDocument();
  });

  it('renders only the latest analysis result and the history component', () => {
    vi.mocked(useAppContext).mockReturnValue({
      ...defaultContext,
      selectedRepo: mockSelectedRepo,
      analysisResults: mockAnalysisResults,
    });

    render(<AnalysisResults />);
    
    // Check for the main heading
    expect(screen.getByRole('heading', { name: /analysis results for test-repo/i })).toBeInTheDocument();
    
    // Check that only the LATEST summary is present
    expect(screen.getByRole('heading', { name: /summary \(latest\)/i })).toBeInTheDocument();
    expect(screen.getByText('Latest summary')).toBeInTheDocument();
    expect(screen.getByText('Files:', { selector: 'strong' }).closest('p')).toHaveTextContent(/Files:\s*10/i);
    
    // Check that the OLDER summary is NOT present
    expect(screen.queryByText('Older summary')).not.toBeInTheDocument();

    // Check that the mocked AnalysisHistory component is rendered
    expect(screen.getByTestId('analysis-history')).toBeInTheDocument();
  });
});
