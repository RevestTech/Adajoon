import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import Header from '../components/Header';

function makeProps(overrides = {}) {
  return {
    mode: 'tv',
    onModeSwitch: vi.fn(),
    search: '',
    onSearch: vi.fn(),
    sidebarOpen: false,
    onToggleSidebar: vi.fn(),
    user: null,
    onLogin: vi.fn(),
    onLogout: vi.fn(),
    showFavorites: false,
    onToggleFavorites: vi.fn(),
    favoritesCount: 0,
    isGuest: true,
    onGuestNotice: vi.fn(),
    onOpenAISearch: vi.fn(),
    onOpenAdmin: vi.fn(),
    onOpenSettings: vi.fn(),
    onOpenPricing: vi.fn(),
    onOpenWhatsNew: vi.fn(),
    hasUnseenWhatsNew: false,
    theme: 'dark',
    onToggleTheme: vi.fn(),
    ...overrides,
  };
}

describe('Header', () => {
  it('renders the app title', () => {
    render(<Header {...makeProps()} />);

    // The logo's text is split across a text node ("Ada") and a child
    // <span> ("joon") - getByText's default string/regex matcher only
    // checks a node's own direct text, not descendants, so it needs a
    // custom matcher function here to see the combined "Adajoon".
    const title = screen.getByText(
      (_, element) => element?.className === 'logo' && element.textContent === 'Adajoon'
    );
    expect(title).toBeInTheDocument();
  });

  it('shows the TV mode button as active when mode is tv', () => {
    render(<Header {...makeProps({ mode: 'tv' })} />);

    const tvButton = screen.getByRole('button', { name: 'Television' });
    expect(tvButton.className).toContain('active');
  });

  it('calls onModeSwitch with the clicked mode', () => {
    const onModeSwitch = vi.fn();
    render(<Header {...makeProps({ mode: 'tv', onModeSwitch })} />);

    fireEvent.click(screen.getByRole('button', { name: 'Radio' }));

    expect(onModeSwitch).toHaveBeenCalledWith('radio');
  });
});
