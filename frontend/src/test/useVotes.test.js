import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useVotes } from '../hooks/useVotes';

describe('useVotes', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  it('initializes with empty votes', () => {
    const { result } = renderHook(() => useVotes());

    expect(result.current.votes).toEqual({});
  });

  it('records upvote', () => {
    const { result } = renderHook(() => useVotes());

    act(() => {
      result.current.vote('tv', 'ch1', 'upvote');
    });

    expect(result.current.votes['tv:ch1']).toBe('upvote');
  });

  it('records downvote', () => {
    const { result } = renderHook(() => useVotes());

    act(() => {
      result.current.vote('tv', 'ch1', 'downvote');
    });

    expect(result.current.votes['tv:ch1']).toBe('downvote');
  });

  it('changes vote from upvote to downvote', () => {
    const { result } = renderHook(() => useVotes());

    act(() => {
      result.current.vote('tv', 'ch1', 'upvote');
    });
    expect(result.current.votes['tv:ch1']).toBe('upvote');

    act(() => {
      result.current.vote('tv', 'ch1', 'downvote');
    });
    expect(result.current.votes['tv:ch1']).toBe('downvote');
  });

  it('removes vote when clicking same vote type', () => {
    const { result } = renderHook(() => useVotes());

    act(() => {
      result.current.vote('tv', 'ch1', 'upvote');
    });
    expect(result.current.votes['tv:ch1']).toBe('upvote');

    act(() => {
      result.current.vote('tv', 'ch1', 'upvote');
    });
    expect(result.current.votes['tv:ch1']).toBeUndefined();
  });

  it('handles multiple items', () => {
    const { result } = renderHook(() => useVotes());

    act(() => {
      result.current.vote('tv', 'ch1', 'upvote');
      result.current.vote('tv', 'ch2', 'downvote');
      result.current.vote('radio', 'st1', 'upvote');
    });

    expect(result.current.votes['tv:ch1']).toBe('upvote');
    expect(result.current.votes['tv:ch2']).toBe('downvote');
    expect(result.current.votes['radio:st1']).toBe('upvote');
  });

  it('persists votes to localStorage', () => {
    const { result } = renderHook(() => useVotes());

    act(() => {
      result.current.vote('tv', 'ch1', 'upvote');
    });

    expect(localStorage.setItem).toHaveBeenCalled();
    const calls = localStorage.setItem.mock.calls;
    const voteCall = calls.find(c => c[0] === 'adajoon_votes');
    expect(voteCall).toBeDefined();
  });
});
