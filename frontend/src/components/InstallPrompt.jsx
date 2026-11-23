import { useEffect, useState } from "react";

const DISMISSED_KEY = "adajoon_install_prompt_dismissed";

function isStandalone() {
  return (
    window.matchMedia?.("(display-mode: standalone)").matches ||
    window.navigator.standalone === true
  );
}

function wasDismissed() {
  try {
    return localStorage.getItem(DISMISSED_KEY) === "1";
  } catch {
    return false;
  }
}

function markDismissed() {
  try {
    localStorage.setItem(DISMISSED_KEY, "1");
  } catch {
    /* ignore */
  }
}

/**
 * iOS/iPadOS Safari never fires `beforeinstallprompt` - there's no
 * programmatic install API, "Add to Home Screen" only lives in the
 * Share sheet. Other iOS browsers (Chrome/Firefox/Edge-for-iOS, all
 * WebKit under the hood per Apple's rules) can't install PWAs at all,
 * even though their UA strings often still contain "Safari" - excluded
 * via their own UA tokens so we don't show Safari-only instructions
 * to someone who has no Share-sheet install option at all.
 */
function isIosSafari() {
  const ua = window.navigator.userAgent;
  const isIosDevice =
    /iPad|iPhone|iPod/.test(ua) ||
    // iPadOS 13+ reports as "Macintosh" but is touch-capable, unlike a real Mac.
    (/Macintosh/.test(ua) && navigator.maxTouchPoints > 1);
  const isOtherIosBrowser = /CriOS|FxiOS|EdgiOS|OPiOS|mercury/.test(ua);
  return isIosDevice && !isOtherIosBrowser;
}

export default function InstallPrompt() {
  const [deferredPrompt, setDeferredPrompt] = useState(null);
  const [visible, setVisible] = useState(false);
  const [platform, setPlatform] = useState("android");

  useEffect(() => {
    if (isStandalone() || wasDismissed()) return undefined;

    if (isIosSafari()) {
      // No event to wait for - Safari never tells us installability,
      // so just show the manual instructions right away.
      setPlatform("ios");
      setVisible(true);
      return undefined;
    }

    const onBeforeInstallPrompt = (e) => {
      e.preventDefault();
      setPlatform("android");
      setDeferredPrompt(e);
      setVisible(true);
    };
    const onAppInstalled = () => {
      setVisible(false);
      setDeferredPrompt(null);
    };

    window.addEventListener("beforeinstallprompt", onBeforeInstallPrompt);
    window.addEventListener("appinstalled", onAppInstalled);
    return () => {
      window.removeEventListener("beforeinstallprompt", onBeforeInstallPrompt);
      window.removeEventListener("appinstalled", onAppInstalled);
    };
  }, []);

  const handleInstall = async () => {
    if (!deferredPrompt) return;
    deferredPrompt.prompt();
    await deferredPrompt.userChoice;
    setDeferredPrompt(null);
    setVisible(false);
  };

  const handleDismiss = () => {
    markDismissed();
    setVisible(false);
  };

  if (!visible) return null;

  if (platform === "ios") {
    return (
      <div className="install-prompt" role="dialog" aria-label="Install Adajoon">
        <div className="install-prompt-text">
          <strong>Install Adajoon</strong>
          <span>
            Tap{" "}
            <svg
              className="install-prompt-ios-share-icon"
              width="14"
              height="14"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden
            >
              <path d="M12 3v12" />
              <path d="M8 7l4-4 4 4" />
              <path d="M5 12v7a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-7" />
            </svg>{" "}
            Share, then "Add to Home Screen" for full-screen access.
          </span>
        </div>
        <div className="install-prompt-actions">
          <button
            type="button"
            className="install-prompt-dismiss"
            onClick={handleDismiss}
            aria-label="Dismiss install prompt"
          >
            ×
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="install-prompt" role="dialog" aria-label="Install Adajoon">
      <div className="install-prompt-text">
        <strong>Install Adajoon</strong>
        <span>Add it to your home screen for quick, full-screen access.</span>
      </div>
      <div className="install-prompt-actions">
        <button type="button" className="install-prompt-btn" onClick={handleInstall}>
          Install
        </button>
        <button
          type="button"
          className="install-prompt-dismiss"
          onClick={handleDismiss}
          aria-label="Dismiss install prompt"
        >
          ×
        </button>
      </div>
    </div>
  );
}
