/**
 * Catch fatal JS errors before React mounts and show a diagnostic message
 * in the loading fallback instead of a blank page.
 */
window.onerror = function (msg, url, line, col, err) {
  var el = document.getElementById('loading-fallback');
  if (el) {
    el.style.flexDirection = 'column';
    el.innerHTML =
      '<div style="color:#e94560;margin-bottom:8px;">Error loading app</div><div style="font-size:12px;max-width:90vw;word-break:break-all;color:#a0a0b8;">' +
      msg +
      ' (' +
      url +
      ':' +
      line +
      ')</div>';
  }
};
