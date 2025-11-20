import '@testing-library/jest-dom';
import { server } from '../src/mocks/server.js';
import { vi } from 'vitest';

// Mock the global WebSocket object
global.WebSocket = vi.fn(() => ({
  send: vi.fn(),
  close: vi.fn(),
  addEventListener: vi.fn(),
  removeEventListener: vi.fn(),
  onmessage: vi.fn(),
  onopen: vi.fn(),
  onclose: vi.fn(),
  onerror: vi.fn(),
}));


// Establish API mocking before all tests.
beforeAll(() => server.listen());

// Reset any request handlers that we may add during tests,
// so they don't affect other tests.
afterEach(() => {
  server.resetHandlers();
  // Clear all mocks
  vi.clearAllMocks();
});

// Clean up after the tests are finished.
afterAll(() => server.close());
