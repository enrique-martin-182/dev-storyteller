import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import Header from './Header';

describe('Header', () => {
  it('renders the main heading and description', () => {
    render(<Header />);
    expect(screen.getByRole('heading', { name: /dev storyteller/i, level: 1 })).toBeInTheDocument();
    expect(screen.getByText(/enter a github repository url to start the analysis./i)).toBeInTheDocument();
  });
});
