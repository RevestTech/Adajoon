/** Registers the PWA service worker (public/sw.js) once the page has loaded. */
export function registerServiceWorker() {
  if (!("serviceWorker" in navigator)) return;

  window.addEventListener("load", () => {
    navigator.serviceWorker.register("/sw.js").catch((err) => {
      console.error("[SW] Registration failed:", err);
    });
  });
}
