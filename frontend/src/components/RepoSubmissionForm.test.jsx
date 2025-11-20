import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import RepoSubmissionForm from './RepoSubmissionForm';
import { AppProvider, useAppContext } from '../../src/contexts/AppContext';

// Mock the useAppContext hook
vi.mock('../../src/contexts/AppContext', () => ({
  useAppContext: vi.fn(),
  AppProvider: ({ children }) => children, // Render children directly for testing purposes
}));

describe('RepoSubmissionForm', () => {
  const setRepoUrlMock = vi.fn();
  const handleSubmitMock = vi.fn();

  const defaultContext = {
    repoUrl: '',
    setRepoUrl: setRepoUrlMock,
    handleSubmit: handleSubmitMock,
    message: '',
    error: '',
    repositories: [],
    selectedRepo: null,
    analysisResults: [],
    handleRepoClick: vi.fn(),
  };

  beforeEach(() => {
    // Reset the mock before each test
    vi.mocked(useAppContext).mockReturnValue(defaultContext);
  });

  it('renders the input and button', () => {
    render(<RepoSubmissionForm />);
    expect(screen.getByPlaceholderText(/e.g., https:\/\/github.com\/octocat\/Spoon-Knife/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /analyze repository/i })).toBeInTheDocument();
  });

  it('calls setRepoUrl on input change', () => {
    render(<RepoSubmissionForm />);
    const input = screen.getByPlaceholderText(/e.g., https:\/\/github.com\/octocat\/Spoon-Knife/i);
    fireEvent.change(input, { target: { value: 'test-url' } });
    expect(setRepoUrlMock).toHaveBeenCalledWith('test-url');
  });

  it('calls handleSubmit on form submission', () => {
    vi.mocked(useAppContext).mockReturnValue({
      ...defaultContext,
      repoUrl: 'test-url',
    });

    render(<RepoSubmissionForm />);
    const button = screen.getByRole('button', { name: /analyze repository/i });
    fireEvent.click(button);
    expect(handleSubmitMock).toHaveBeenCalledTimes(1);
  });
});

