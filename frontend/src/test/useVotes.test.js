import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { useVotes } from '../hooks/useVotes';
import { authenticatedFetch } from '../utils/csrf';

vi.mock('../utils/csrf', () => ({
  authenticatedFetch: vi.fn(),
}));

function jsonResponse(body, ok = true) {
  return { ok, json: async () => body };
}

describe('useVotes', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('initializes with no votes or summaries loaded', () => {
    const { result } = renderHook(() => useVotes());

    expect(result.current.getMyVotesFor('tv', 'ch1')).toEqual([]);
    expect(result.current.getSummaryFor('tv', 'ch1')).toEqual({});
  });

  it('loadMyVotes populates per-item votes from the server', async () => {
    authenticatedFetch.mockResolvedValueOnce(
      jsonResponse({ ch1: ['like'] })
    );
    const { result } = renderHook(() => useVotes());

    await act(async () => {
      await result.current.loadMyVotes('tv');
    });

    expect(authenticatedFetch).toHaveBeenCalledWith(
      '/api/auth/votes/me?item_type=tv'
    );
    expect(result.current.getMyVotesFor('tv', 'ch1')).toEqual(['like']);
  });

  it('loadMyVotes only fetches once per item type until resetLoaded', async () => {
    authenticatedFetch.mockResolvedValue(jsonResponse({}));
    const { result } = renderHook(() => useVotes());

    await act(async () => {
      await result.current.loadMyVotes('tv');
      await result.current.loadMyVotes('tv');
    });
    expect(authenticatedFetch).toHaveBeenCalledTimes(1);

    act(() => {
      result.current.resetLoaded();
    });
    await act(async () => {
      await result.current.loadMyVotes('tv');
    });
    expect(authenticatedFetch).toHaveBeenCalledTimes(2);
  });

  it('submitVote adds a vote and updates the summary optimistically', async () => {
    authenticatedFetch.mockResolvedValueOnce(jsonResponse({ status: 'added' }));
    const { result } = renderHook(() => useVotes());

    await act(async () => {
      await result.current.submitVote('tv', 'ch1', 'like');
    });

    expect(authenticatedFetch).toHaveBeenCalledWith(
      '/api/auth/votes',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({
          item_type: 'tv',
          item_id: 'ch1',
          vote_type: 'like',
        }),
      })
    );
    expect(result.current.getMyVotesFor('tv', 'ch1')).toEqual(['like']);
    expect(result.current.getSummaryFor('tv', 'ch1')).toEqual({ like: 1 });
  });

  it('submitVote removes a vote (toggle off) when the server reports removed', async () => {
    authenticatedFetch.mockResolvedValueOnce(jsonResponse({ status: 'added' }));
    const { result } = renderHook(() => useVotes());

    await act(async () => {
      await result.current.submitVote('tv', 'ch1', 'like');
    });
    expect(result.current.getMyVotesFor('tv', 'ch1')).toEqual(['like']);

    authenticatedFetch.mockResolvedValueOnce(jsonResponse({ status: 'removed' }));
    await act(async () => {
      await result.current.submitVote('tv', 'ch1', 'like');
    });

    expect(result.current.getMyVotesFor('tv', 'ch1')).toEqual([]);
    expect(result.current.getSummaryFor('tv', 'ch1')).toEqual({ like: 0 });
  });

  it('submitVote returns null and leaves state unchanged on a failed request', async () => {
    authenticatedFetch.mockResolvedValueOnce(jsonResponse({}, false));
    const { result } = renderHook(() => useVotes());

    let returned;
    await act(async () => {
      returned = await result.current.submitVote('tv', 'ch1', 'like');
    });

    expect(returned).toBeNull();
    expect(result.current.getMyVotesFor('tv', 'ch1')).toEqual([]);
  });

  it('loadSummary populates vote counts for multiple items', async () => {
    authenticatedFetch.mockResolvedValueOnce(
      jsonResponse({ ch1: { like: 3, dislike: 1 }, ch2: { like: 0 } })
    );
    const { result } = renderHook(() => useVotes());

    await act(async () => {
      await result.current.loadSummary('tv', ['ch1', 'ch2']);
    });

    await waitFor(() => {
      expect(result.current.getSummaryFor('tv', 'ch1')).toEqual({
        like: 3,
        dislike: 1,
      });
    });
    expect(result.current.getSummaryFor('tv', 'ch2')).toEqual({ like: 0 });
  });

  it('tracks votes for different item types independently', async () => {
    authenticatedFetch
      .mockResolvedValueOnce(jsonResponse({ status: 'added' }))
      .mockResolvedValueOnce(jsonResponse({ status: 'added' }));
    const { result } = renderHook(() => useVotes());

    await act(async () => {
      await result.current.submitVote('tv', 'ch1', 'like');
      await result.current.submitVote('radio', 'st1', 'dislike');
    });

    expect(result.current.getMyVotesFor('tv', 'ch1')).toEqual(['like']);
    expect(result.current.getMyVotesFor('radio', 'st1')).toEqual(['dislike']);
  });
});
