import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import AnalysisComparison from './AnalysisComparison';
import { useAppContext } from '../contexts/AppContext';

// Mock the useAppContext hook
vi.mock('../contexts/AppContext', () => ({
  useAppContext: vi.fn(),
}));

describe('AnalysisComparison', () => {
  const mockAnalysisResults = [
    { id: 1, summary: 'Summary 1', file_count: 10, commit_count: 5, languages: { JS: 10 }, created_at: new Date().toISOString() },
    { id: 2, summary: 'Summary 2', file_count: 12, commit_count: 6, languages: { JS: 12 }, created_at: new Date().toISOString() },
  ];

  beforeEach(() => {
    vi.mocked(useAppContext).mockReturnValue({
      analysisResults: [],
      selectedForComparison: [],
    });
  });

  it('renders nothing if less than 2 analyses are selected', () => {
    const { container } = render(<AnalysisComparison />);
    expect(container.firstChild).toBeNull();

    vi.mocked(useAppContext).mockReturnValue({
      analysisResults: mockAnalysisResults,
      selectedForComparison: [1],
    });
    render(<AnalysisComparison />);
    expect(container.firstChild).toBeNull();
  });

  it('renders a comparison table when 2 analyses are selected', () => {
    vi.mocked(useAppContext).mockReturnValue({
      analysisResults: mockAnalysisResults,
      selectedForComparison: [1, 2],
    });

    render(<AnalysisComparison />);
    expect(screen.getByRole('heading', { name: /comparison/i })).toBeInTheDocument();
    expect(screen.getByRole('table')).toBeInTheDocument();
    
    // Check for headers
    expect(screen.getByText('Metric')).toBeInTheDocument();
    
    // Check for data
    expect(screen.getByText('Summary 1')).toBeInTheDocument();
    expect(screen.getByText('Summary 2')).toBeInTheDocument();
    expect(screen.getByText('10')).toBeInTheDocument();
    expect(screen.getByText('12')).toBeInTheDocument();
  });
});
