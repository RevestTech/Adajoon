import { describe, it, expect, beforeEach, vi } from 'vitest';
import { readUrlParams, writeUrlParams, pushPlayerState, popPlayerState } from '../hooks/useUrlState';

describe('useUrlState', () => {
  beforeEach(() => {
    // Reset window location
    delete window.location;
    window.location = {
      href: 'http://localhost:3000/',
      pathname: '/',
      search: '',
      hash: '',
    };
    
    // Mock history
    window.history = {
      pushState: vi.fn(),
      replaceState: vi.fn(),
      back: vi.fn(),
      state: null,
    };
  });

  describe('readUrlParams', () => {
    it('reads default params', () => {
      const params = readUrlParams();
      
      expect(params.mode).toBe('tv');
      expect(params.q).toBe('');
      expect(params.cat).toEqual([]);
      expect(params.page).toBe(1);
      expect(params.fav).toBe(false);
    });

    it('reads mode from query string', () => {
      window.location.search = '?mode=radio';
      const params = readUrlParams();
      
      expect(params.mode).toBe('radio');
    });

    it('reads search query', () => {
      window.location.search = '?q=CNN';
      const params = readUrlParams();
      
      expect(params.q).toBe('CNN');
    });

    it('reads multiple categories', () => {
      window.location.search = '?cat=News,Sports';
      const params = readUrlParams();
      
      expect(params.cat).toEqual(['News', 'Sports']);
    });

    it('reads page number', () => {
      window.location.search = '?page=3';
      const params = readUrlParams();
      
      expect(params.page).toBe(3);
    });

    it('reads channel from path', () => {
      window.location.pathname = '/tv/channel/abc123';
      const params = readUrlParams();
      
      expect(params.mode).toBe('tv');
      expect(params.channel).toBe('abc123');
    });

    it('reads station from path', () => {
      window.location.pathname = '/radio/station/xyz789';
      const params = readUrlParams();
      
      expect(params.mode).toBe('radio');
      expect(params.station).toBe('xyz789');
    });
  });

  describe('writeUrlParams', () => {
    it('writes mode to URL', () => {
      writeUrlParams({ mode: 'radio' });
      
      expect(window.history.replaceState).toHaveBeenCalled();
    });

    it('writes search query', () => {
      writeUrlParams({ mode: 'tv', q: 'BBC' });
      
      const call = window.history.replaceState.mock.calls[0];
      expect(call[2]).toContain('q=BBC');
    });

    it('writes multiple filters', () => {
      writeUrlParams({
        mode: 'tv',
        cat: ['News', 'Sports'],
        country: ['US', 'GB'],
      });
      
      const call = window.history.replaceState.mock.calls[0];
      expect(call[2]).toContain('cat=News,Sports');
      expect(call[2]).toContain('country=US,GB');
    });

    it('omits default values', () => {
      writeUrlParams({ mode: 'tv', page: 1, fav: false });
      
      const call = window.history.replaceState.mock.calls[0];
      // Page 1 and fav=false should not be in URL
      expect(call[2]).not.toContain('page=');
      expect(call[2]).not.toContain('fav=');
    });
  });

  describe('pushPlayerState', () => {
    it('pushes TV channel URL', () => {
      pushPlayerState('tv', 'channel123');
      
      expect(window.history.pushState).toHaveBeenCalled();
      const call = window.history.pushState.mock.calls[0];
      expect(call[2]).toBe('/tv/channel/channel123');
    });

    it('pushes radio station URL', () => {
      pushPlayerState('radio', 'station456');
      
      const call = window.history.pushState.mock.calls[0];
      expect(call[2]).toBe('/radio/station/station456');
    });

    it('preserves query params', () => {
      window.location.search = '?view=list&cat=News';
      pushPlayerState('tv', 'ch1');
      
      const call = window.history.pushState.mock.calls[0];
      expect(call[2]).toContain('?view=list&cat=News');
    });
  });

  describe('popPlayerState', () => {
    it('navigates back from player URL', () => {
      window.location.pathname = '/tv/channel/123';
      
      popPlayerState();
      
      expect(window.history.pushState).toHaveBeenCalledWith(null, '', '/?');
    });

    it('preserves filters when returning to listing', () => {
      window.location.pathname = '/tv/channel/123';
      window.location.search = '?cat=News&country=US';
      
      popPlayerState();
      
      const call = window.history.pushState.mock.calls[0];
      expect(call[2]).toContain('cat=News');
      expect(call[2]).toContain('country=US');
    });
  });
});
