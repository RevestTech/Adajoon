import * as Sentry from '@sentry/react';

// Error tracking - optional. No-op unless VITE_SENTRY_DSN is set at build
// time, so leaving it unset is a no-op, not a broken integration.
const dsn = import.meta.env.VITE_SENTRY_DSN;

export function initSentry() {
  if (!dsn) return;
  Sentry.init({
    dsn,
    environment: import.meta.env.MODE,
    tracesSampleRate: 0.1,
  });
}

export function reportError(error, errorInfo) {
  if (!dsn) return;
  Sentry.captureException(error, { extra: { componentStack: errorInfo?.componentStack } });
}
