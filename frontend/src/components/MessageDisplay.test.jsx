import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import MessageDisplay from './MessageDisplay';
import { AppProvider, useAppContext } from '../../src/contexts/AppContext';

// Mock the useAppContext hook
vi.mock('../../src/contexts/AppContext', () => ({
  useAppContext: vi.fn(),
  AppProvider: ({ children }) => children, // Render children directly for testing purposes
}));

describe('MessageDisplay', () => {
  const defaultContext = {
    message: '',
    error: '',
    repoUrl: '',
    setRepoUrl: vi.fn(),
    repositories: [],
    selectedRepo: null,
    analysisResults: [],
    handleSubmit: vi.fn(),
    handleRepoClick: vi.fn(),
  };

  beforeEach(() => {
    // Reset the mock before each test
    vi.mocked(useAppContext).mockReturnValue(defaultContext);
  });

  it('renders success message when provided', () => {
    vi.mocked(useAppContext).mockReturnValue({
      ...defaultContext,
      message: 'Success!',
    });

    render(<MessageDisplay />);
    expect(screen.getByText('Success!')).toBeInTheDocument();
    expect(screen.queryByText('Error!')).not.toBeInTheDocument();
  });

  it('renders error message when provided', () => {
    vi.mocked(useAppContext).mockReturnValue({
      ...defaultContext,
      error: 'Error!',
    });

    render(<MessageDisplay />);
    expect(screen.getByText('Error!')).toBeInTheDocument();
    expect(screen.queryByText('Success!')).not.toBeInTheDocument();
  });

  it('renders both messages when both are provided', () => {
    vi.mocked(useAppContext).mockReturnValue({
      ...defaultContext,
      message: 'Success!',
      error: 'Error!',
    });

    render(<MessageDisplay />);
    expect(screen.getByText('Success!')).toBeInTheDocument();
    expect(screen.getByText('Error!')).toBeInTheDocument();
  });

  it('renders nothing when no messages are provided', () => {
    render(<MessageDisplay />); // Uses defaultContext from beforeEach
    expect(screen.queryByText('Success!')).not.toBeInTheDocument();
    expect(screen.queryByText('Error!')).not.toBeInTheDocument();
  });
});
