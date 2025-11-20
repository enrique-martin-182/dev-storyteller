import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import AnalysisHistory from './AnalysisHistory';
import { useAppContext } from '../contexts/AppContext';

// Mock the useAppContext hook
vi.mock('../contexts/AppContext', () => ({
  useAppContext: vi.fn(),
}));

describe('AnalysisHistory', () => {
  const handleComparisonSelectMock = vi.fn();
  const mockResults = [
    { id: 1, created_at: '2023-10-27T10:00:00.000Z' },
    { id: 2, created_at: '2023-10-26T10:00:00.000Z' },
  ];

  const defaultContext = {
    analysisResults: [],
    selectedForComparison: [],
    handleComparisonSelect: handleComparisonSelectMock,
  };

  beforeEach(() => {
    vi.mocked(useAppContext).mockReturnValue(defaultContext);
    vi.clearAllMocks();
  });

  it('renders nothing if there is one or zero analysis results', () => {
    const { container, rerender } = render(<AnalysisHistory />);
    expect(container.firstChild).toBeNull();

    vi.mocked(useAppContext).mockReturnValue({
      ...defaultContext,
      analysisResults: [mockResults[0]],
    });
    rerender(<AnalysisHistory />);
    expect(container.firstChild).toBeNull();
  });

  it('renders a list of analysis dates with checkboxes', () => {
    vi.mocked(useAppContext).mockReturnValue({
      ...defaultContext,
      analysisResults: mockResults,
    });

    render(<AnalysisHistory />);
    expect(screen.getByRole('heading', { name: /analysis history/i })).toBeInTheDocument();
    expect(screen.getAllByRole('checkbox')).toHaveLength(2);
  });

  it('calls handleComparisonSelect when a checkbox is clicked', () => {
    vi.mocked(useAppContext).mockReturnValue({
      ...defaultContext,
      analysisResults: mockResults,
    });

    render(<AnalysisHistory />);
    const checkbox1 = screen.getByLabelText(`Analyzed on: ${new Date(mockResults[0].created_at).toLocaleString()}`);
    fireEvent.click(checkbox1);
    expect(handleComparisonSelectMock).toHaveBeenCalledWith(mockResults[0].id);
  });

  it('checkbox is checked if it is in selectedForComparison', () => {
    vi.mocked(useAppContext).mockReturnValue({
      ...defaultContext,
      analysisResults: mockResults,
      selectedForComparison: [mockResults[0].id],
    });

    render(<AnalysisHistory />);
    const checkbox1 = screen.getByLabelText(`Analyzed on: ${new Date(mockResults[0].created_at).toLocaleString()}`);
    const checkbox2 = screen.getByLabelText(`Analyzed on: ${new Date(mockResults[1].created_at).toLocaleString()}`);
    
    expect(checkbox1).toBeChecked();
    expect(checkbox2).not.toBeChecked();
  });
});
