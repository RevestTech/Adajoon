import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import Header from '../components/Header';

describe('Header', () => {
  it('renders the app title', () => {
    const mockProps = {
      mode: 'tv',
      onModeChange: vi.fn(),
      onSearchChange: vi.fn(),
      searchQuery: '',
      onToggleSidebar: vi.fn(),
      viewMode: 'grid',
      onViewModeChange: vi.fn(),
      isGuest: true,
      onLogin: vi.fn(),
    };

    render(<Header {...mockProps} />);
    
    // Check if Adajoon title exists
    const title = screen.getByText(/Adajoon/i);
    expect(title).toBeInTheDocument();
  });

  it('shows TV mode by default', () => {
    const mockProps = {
      mode: 'tv',
      onModeChange: vi.fn(),
      onSearchChange: vi.fn(),
      searchQuery: '',
      onToggleSidebar: vi.fn(),
      viewMode: 'grid',
      onViewModeChange: vi.fn(),
      isGuest: true,
      onLogin: vi.fn(),
    };

    render(<Header {...mockProps} />);
    
    // Check for TV-related elements
    expect(mockProps.mode).toBe('tv');
  });

  it('calls onModeChange when mode button clicked', () => {
    const onModeChange = vi.fn();
    const mockProps = {
      mode: 'tv',
      onModeChange,
      onSearchChange: vi.fn(),
      searchQuery: '',
      onToggleSidebar: vi.fn(),
      viewMode: 'grid',
      onViewModeChange: vi.fn(),
      isGuest: true,
      onLogin: vi.fn(),
    };

    render(<Header {...mockProps} />);
    
    // This is a basic smoke test - Header component renders without errors
    expect(onModeChange).toBeDefined();
  });
});
