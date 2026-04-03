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
    expect(result.current.loading).toBe(true);
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

  it('updates user info', async () => {
    const { result } = renderHook(() => useAuth(), {
      wrapper: AuthProvider,
    });

    const newUser = { id: 2, email: 'new@example.com', name: 'New User' };

    act(() => {
      result.current.setUser(newUser);
    });

    expect(result.current.user).toEqual(newUser);
    expect(localStorage.setItem).toHaveBeenCalledWith(
      'adajoon_user',
      JSON.stringify(newUser)
    );
  });
});
