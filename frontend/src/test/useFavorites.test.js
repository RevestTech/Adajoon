import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import useFavorites from '../hooks/useFavorites';

describe('useFavorites', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  it('initializes with empty favorites', () => {
    const { result } = renderHook(() => useFavorites());

    expect(result.current.favorites).toEqual({});
    expect(result.current.favoritesList).toEqual([]);
    expect(result.current.favoritesCount).toBe(0);
  });

  it('toggles favorite on', () => {
    const { result } = renderHook(() => useFavorites());
    
    const channel = { id: 'ch1', name: 'Test Channel' };

    act(() => {
      result.current.toggleFavorite(channel);
    });

    expect(result.current.isFavorite('ch1')).toBe(true);
    expect(result.current.favoritesCount).toBe(1);
  });

  it('toggles favorite off', () => {
    const { result } = renderHook(() => useFavorites());
    
    const channel = { id: 'ch1', name: 'Test Channel' };

    act(() => {
      result.current.toggleFavorite(channel);
    });
    expect(result.current.isFavorite('ch1')).toBe(true);

    act(() => {
      result.current.toggleFavorite(channel);
    });
    expect(result.current.isFavorite('ch1')).toBe(false);
    expect(result.current.favoritesCount).toBe(0);
  });

  it('maintains multiple favorites', () => {
    const { result } = renderHook(() => useFavorites());
    
    const ch1 = { id: 'ch1', name: 'Channel 1' };
    const ch2 = { id: 'ch2', name: 'Channel 2' };

    act(() => {
      result.current.toggleFavorite(ch1);
      result.current.toggleFavorite(ch2);
    });

    expect(result.current.favoritesCount).toBe(2);
    expect(result.current.isFavorite('ch1')).toBe(true);
    expect(result.current.isFavorite('ch2')).toBe(true);
  });

  it('persists favorites to localStorage', () => {
    const { result } = renderHook(() => useFavorites());
    
    const channel = { id: 'ch1', name: 'Test Channel', logo: 'http://example.com/logo.png' };

    act(() => {
      result.current.toggleFavorite(channel);
    });

    expect(localStorage.setItem).toHaveBeenCalled();
    const calls = localStorage.setItem.mock.calls;
    const favCall = calls.find(c => c[0] === 'adajoon_favorites');
    expect(favCall).toBeDefined();
  });

  it('checks isFavorite correctly', () => {
    const { result } = renderHook(() => useFavorites());

    expect(result.current.isFavorite('nonexistent')).toBe(false);

    act(() => {
      result.current.toggleFavorite({ id: 'ch1', name: 'Test' });
    });

    expect(result.current.isFavorite('ch1')).toBe(true);
    expect(result.current.isFavorite('ch2')).toBe(false);
  });
});
