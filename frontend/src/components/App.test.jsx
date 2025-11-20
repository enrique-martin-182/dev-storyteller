import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import App from './App';
import { AppProvider } from '../../src/contexts/AppContext'; // Correct path

describe('App', () => {
  it('renders the main heading and fetches repositories', async () => {
    render(
      <AppProvider>
        <App />
      </AppProvider>
    );
    
    // Check for the main heading
    const heading = screen.getByRole('heading', { name: /dev storyteller/i, level: 1 });
    expect(heading).toBeInTheDocument();

    // Check if the mocked repositories are rendered
    // The `findAllBy` queries are useful for async operations
    const repo1 = await screen.findByText('mock-repo-1');
    const repo2 = await screen.findByText('mock-repo-2');

    expect(repo1).toBeInTheDocument();
    expect(repo2).toBeInTheDocument();
  });
});
