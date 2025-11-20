import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest'; // Import vi
import App from './App';
import { AppProvider } from '../../src/contexts/AppContext'; // Correct path

// Mock the WebSocket constructor globally for tests
const mockWebSocket = vi.fn(() => ({
  send: vi.fn(),
  close: vi.fn(),
  addEventListener: vi.fn(),
  removeEventListener: vi.fn(),
}));

vi.stubGlobal('WebSocket', mockWebSocket);

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
