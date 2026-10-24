/**
 * Service Worker Registration - DISABLED temporarily
 * Will re-enable after domain routing is stable.
 */
if ('serviceWorker' in navigator) {
  // Unregister any existing service workers
  navigator.serviceWorker.getRegistrations().then(function (registrations) {
    for (let registration of registrations) {
      registration.unregister();
      console.log('[SW] Unregistered:', registration.scope);
    }
  });

  // Clear all caches
  if ('caches' in window) {
    caches.keys().then(function (names) {
      for (let name of names) {
        caches.delete(name);
        console.log('[Cache] Deleted:', name);
      }
    });
  }
}
