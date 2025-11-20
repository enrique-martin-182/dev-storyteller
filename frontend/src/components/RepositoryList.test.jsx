import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import RepositoryList from './RepositoryList';
import { AppProvider, useAppContext } from '../../src/contexts/AppContext';

// Mock the useAppContext hook
vi.mock('../../src/contexts/AppContext', () => ({
  useAppContext: vi.fn(),
  AppProvider: ({ children }) => children, // Render children directly for testing purposes
}));

describe('RepositoryList', () => {
  const mockRepositories = [
    { id: 1, name: 'repo1', url: 'http://repo1.com', status: 'completed' },
    { id: 2, name: 'repo2', url: 'http://repo2.com', status: 'pending' },
  ];
  const handleRepoClickMock = vi.fn();

  const defaultContext = {
    repositories: [],
    selectedRepo: null,
    handleRepoClick: handleRepoClickMock,
    repoUrl: '',
    setRepoUrl: vi.fn(),
    message: '',
    error: '',
    analysisResults: [],
    handleSubmit: vi.fn(),
  };

  beforeEach(() => {
    // Reset the mock before each test
    vi.mocked(useAppContext).mockReturnValue(defaultContext);
  });

  it('renders "No repositories analyzed yet." when repositories array is empty', () => {
    render(<RepositoryList />);
    expect(screen.getByText(/no repositories analyzed yet./i)).toBeInTheDocument();
  });

  it('renders a list of repositories when provided', () => {
    vi.mocked(useAppContext).mockReturnValue({
      ...defaultContext,
      repositories: mockRepositories,
    });

    render(<RepositoryList />);
    expect(screen.getByText('repo1')).toBeInTheDocument();
    expect(screen.getByText('repo2')).toBeInTheDocument();
    expect(screen.queryByText(/no repositories analyzed yet./i)).not.toBeInTheDocument();
  });

  it('calls handleRepoClick when a repository is clicked', () => {
    vi.mocked(useAppContext).mockReturnValue({
      ...defaultContext,
      repositories: mockRepositories,
    });

    render(<RepositoryList />);
    fireEvent.click(screen.getByText('repo1'));
    expect(handleRepoClickMock).toHaveBeenCalledWith(mockRepositories[0]);
  });

  it('applies "selected-repo" class to the selected repository', () => {
    vi.mocked(useAppContext).mockReturnValue({
      ...defaultContext,
      repositories: mockRepositories,
      selectedRepo: mockRepositories[0],
    });

    render(<RepositoryList />);
    const selectedListItem = screen.getByText('repo1').closest('li');
    expect(selectedListItem).toHaveClass('selected-repo');

    const unselectedListItem = screen.getByText('repo2').closest('li');
    expect(unselectedListItem).not.toHaveClass('selected-repo');
  });
});
