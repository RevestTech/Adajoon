import { useEffect, useCallback, useRef } from "react";

const KEYCODES = {
  LEFT: 37,
  UP: 38,
  RIGHT: 39,
  DOWN: 40,
  ENTER: 13,
  BACK: 10009,
  BACK_TIZEN: 10009,
  BACK_WEBOS: 461,
  EXIT: 10182,
  PLAY: 415,
  PAUSE: 19,
  STOP: 413,
  REWIND: 412,
  FAST_FORWARD: 417,
  RED: 403,
  GREEN: 404,
  YELLOW: 405,
  BLUE: 406,
};

export function useTVNavigation({ onBack, onSelect, onNavigate, enabled = true } = {}) {
  const handlersRef = useRef({ onBack, onSelect, onNavigate });

  useEffect(() => {
    handlersRef.current = { onBack, onSelect, onNavigate };
  }, [onBack, onSelect, onNavigate]);

  useEffect(() => {
    if (!enabled) return;

    const handleKeyDown = (e) => {
      const { onBack, onSelect, onNavigate } = handlersRef.current;

      switch (e.keyCode) {
        case KEYCODES.LEFT:
          e.preventDefault();
          if (onNavigate) onNavigate('left');
          break;
        case KEYCODES.UP:
          e.preventDefault();
          if (onNavigate) onNavigate('up');
          break;
        case KEYCODES.RIGHT:
          e.preventDefault();
          if (onNavigate) onNavigate('right');
          break;
        case KEYCODES.DOWN:
          e.preventDefault();
          if (onNavigate) onNavigate('down');
          break;
        case KEYCODES.ENTER:
          e.preventDefault();
          if (onSelect) onSelect();
          break;
        case KEYCODES.BACK:
        case KEYCODES.BACK_TIZEN:
        case KEYCODES.BACK_WEBOS:
          e.preventDefault();
          if (onBack) onBack();
          break;
        default:
          break;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [enabled]);

  return {
    KEYCODES,
  };
}

export function useTVFocusManagement() {
  const focusableElements = useRef([]);
  const currentFocusIndex = useRef(0);

  const registerFocusable = useCallback((element) => {
    if (element && !focusableElements.current.includes(element)) {
      focusableElements.current.push(element);
    }
  }, []);

  const unregisterFocusable = useCallback((element) => {
    focusableElements.current = focusableElements.current.filter(el => el !== element);
  }, []);

  const focusNext = useCallback(() => {
    if (focusableElements.current.length === 0) return;
    currentFocusIndex.current = (currentFocusIndex.current + 1) % focusableElements.current.length;
    focusableElements.current[currentFocusIndex.current]?.focus();
  }, []);

  const focusPrev = useCallback(() => {
    if (focusableElements.current.length === 0) return;
    currentFocusIndex.current = currentFocusIndex.current - 1;
    if (currentFocusIndex.current < 0) {
      currentFocusIndex.current = focusableElements.current.length - 1;
    }
    focusableElements.current[currentFocusIndex.current]?.focus();
  }, []);

  const focusCurrent = useCallback(() => {
    if (focusableElements.current.length > 0) {
      focusableElements.current[currentFocusIndex.current]?.focus();
    }
  }, []);

  return {
    registerFocusable,
    unregisterFocusable,
    focusNext,
    focusPrev,
    focusCurrent,
  };
}

export function useTVRemoteButton(keyCode, handler, enabled = true) {
  const handlerRef = useRef(handler);

  useEffect(() => {
    handlerRef.current = handler;
  }, [handler]);

  useEffect(() => {
    if (!enabled) return;

    const handleKeyDown = (e) => {
      if (e.keyCode === keyCode) {
        e.preventDefault();
        handlerRef.current?.(e);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [keyCode, enabled]);
}

export { KEYCODES };
