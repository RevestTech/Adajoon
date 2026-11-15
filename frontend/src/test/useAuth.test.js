import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { AuthProvider, useAuth } from '../hooks/useAuth';

describe('useAuth', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    global.fetch.mockClear();
  });

  it('initializes with no user', () => {
    const { result } = renderHook(() => useAuth(), {
      wrapper: AuthProvider,
    });

    expect(result.current.user).toBeNull();
    // user is now read synchronously from localStorage at mount - loading
    // only flips true during an actual login attempt, not on initial read.
    expect(result.current.loading).toBe(false);
  });

  it('loads user from localStorage', async () => {
    const mockUser = { id: 1, email: 'test@example.com', name: 'Test User' };
    localStorage.getItem.mockReturnValue(JSON.stringify(mockUser));

    const { result } = renderHook(() => useAuth(), {
      wrapper: AuthProvider,
    });

    await waitFor(() => {
      expect(result.current.user).toEqual(mockUser);
      expect(result.current.loading).toBe(false);
    });
  });

  it('handles logout', async () => {
    const mockUser = { id: 1, email: 'test@example.com' };
    localStorage.getItem.mockReturnValue(JSON.stringify(mockUser));
    
    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ status: 'logged_out' }),
    });

    const { result } = renderHook(() => useAuth(), {
      wrapper: AuthProvider,
    });

    await waitFor(() => {
      expect(result.current.user).toEqual(mockUser);
    });

    await act(async () => {
      await result.current.logout();
    });

    expect(result.current.user).toBeNull();
    expect(localStorage.removeItem).toHaveBeenCalledWith('adajoon_user');
  });

  it('updates user info after a successful dev login', async () => {
    // setUser isn't part of the public API - the only way the hook updates
    // `user` is through a real login flow (or the background /me refresh).
    // No CSRF cookie exists in jsdom, so authenticatedFetch fetches one
    // first - keyed by URL (not call order) since analytics also calls
    // fetch independently (e.g. its own batched page-view send).
    global.fetch.mockImplementation((url) => {
      if (String(url).includes('/api/csrf/token')) {
        return Promise.resolve({
          ok: true,
          json: async () => ({ csrf_token: 'test-csrf-token' }),
        });
      }
      if (String(url).includes('/dev-login')) {
        return Promise.resolve({
          ok: true,
          json: async () => ({
            user: { id: 2, email: 'new@example.com', name: 'New User' },
          }),
        });
      }
      // Anything else (e.g. the background /me refresh effect) fails
      // closed rather than resolving ok with {} - that effect does
      // setUser(data) unconditionally and would stomp the login above.
      return Promise.resolve({ ok: false, json: async () => ({}) });
    });

    const { result } = renderHook(() => useAuth(), {
      wrapper: AuthProvider,
    });

    await act(async () => {
      await result.current.loginWithDev('new@example.com');
    });

    const newUser = { id: 2, email: 'new@example.com', name: 'New User' };
    expect(result.current.user).toEqual(newUser);
    expect(localStorage.setItem).toHaveBeenCalledWith(
      'adajoon_user',
      JSON.stringify(newUser)
    );
  });
});
