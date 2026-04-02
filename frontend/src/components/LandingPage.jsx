import { useEffect, useRef, useCallback, useState } from "react";

let gsiInitialized = false;

export default function LandingPage({
  onGoogleLogin,
  onAppleLogin,
  onPasskeyLogin,
  googleClientId,
  appleClientId,
  onSkip,
}) {
  const googleBtnRef = useRef(null);
  const callbackRef = useRef(onGoogleLogin);
  callbackRef.current = onGoogleLogin;
  const [passkeyError, setPasskeyError] = useState("");
  const [passkeySupported, setPasskeySupported] = useState(false);

  useEffect(() => {
    if (window.PublicKeyCredential) {
      PublicKeyCredential.isUserVerifyingPlatformAuthenticatorAvailable?.()
        .then((available) => setPasskeySupported(available))
        .catch(() => {});
    }
  }, []);

  const initGsi = useCallback(() => {
    if (!googleClientId || !window.google?.accounts?.id || !googleBtnRef.current) return;
    if (!gsiInitialized) {
      window.google.accounts.id.initialize({
        client_id: googleClientId,
        callback: (response) => callbackRef.current(response.credential),
      });
      gsiInitialized = true;
    }
    googleBtnRef.current.innerHTML = "";
    window.google.accounts.id.renderButton(googleBtnRef.current, {
      theme: "filled_black",
      size: "large",
      width: 320,
      text: "signin_with",
      shape: "pill",
    });
  }, [googleClientId]);

  useEffect(() => { initGsi(); }, [initGsi]);

  const handleAppleLogin = async () => {
    if (!window.AppleID?.auth) return;
    try {
      AppleID.auth.init({
        clientId: appleClientId,
        scope: "name email",
        redirectURI: window.location.origin,
        usePopup: true,
      });
      const response = await AppleID.auth.signIn();
      const idToken = response.authorization?.id_token;
      const user = response.user;
      const userName = user
        ? [user.name?.firstName, user.name?.lastName].filter(Boolean).join(" ")
        : "";
      if (idToken) {
        onAppleLogin(idToken, userName);
      }
    } catch (err) {
      if (err.error !== "popup_closed_by_user") {
        console.error("Apple sign-in error:", err);
      }
    }
  };

  const handlePasskeyLogin = async () => {
    setPasskeyError("");
    try {
      await onPasskeyLogin();
    } catch (err) {
      if (err.name !== "NotAllowedError") {
        setPasskeyError("Passkey login failed. Try another method.");
      }
    }
  };

  return (
    <div className="landing-page">
      <div className="landing-bg">
        <div className="landing-orb landing-orb-1" />
        <div className="landing-orb landing-orb-2" />
        <div className="landing-orb landing-orb-3" />
      </div>

      <div className="landing-content">
        <div className="landing-logo">
          Ada<span>joon</span>
        </div>
        <h1 className="landing-title">TV & Radio from Around the World</h1>
        <p className="landing-subtitle">
          Stream 39,000+ TV channels and 50,000+ radio stations.
          <br />
          Save your favorites and sync across all your devices.
        </p>

        <div className="landing-card">
          <div className="landing-features">
            <div className="landing-feature">
              <div className="landing-feature-icon">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <rect x="2" y="7" width="20" height="15" rx="2" ry="2" /><polyline points="17 2 12 7 7 2" />
                </svg>
              </div>
              <div>
                <strong>Live TV</strong>
                <span>Channels from 250 countries</span>
              </div>
            </div>
            <div className="landing-feature">
              <div className="landing-feature-icon">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="12" cy="12" r="2" />
                  <path d="M16.24 7.76a6 6 0 0 1 0 8.49" />
                  <path d="M19.07 4.93a10 10 0 0 1 0 14.14" />
                  <path d="M7.76 16.24a6 6 0 0 1 0-8.49" />
                  <path d="M4.93 19.07a10 10 0 0 1 0-14.14" />
                </svg>
              </div>
              <div>
                <strong>World Radio</strong>
                <span>Every genre, every country</span>
              </div>
            </div>
            <div className="landing-feature">
              <div className="landing-feature-icon">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" />
                </svg>
              </div>
              <div>
                <strong>Sync Favorites</strong>
                <span>Sign in and never lose them</span>
              </div>
            </div>
          </div>

          <div className="landing-signin">
            {/* Google */}
            <div ref={googleBtnRef} className="landing-google-btn" />

            {/* Apple */}
            {appleClientId && window.AppleID?.auth && (
              <button className="landing-apple-btn" onClick={handleAppleLogin}>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M17.05 20.28c-.98.95-2.05.88-3.08.4-1.09-.5-2.08-.48-3.24 0-1.44.62-2.2.44-3.06-.4C2.79 15.25 3.51 7.59 9.05 7.31c1.35.07 2.29.74 3.08.8 1.18-.24 2.31-.93 3.57-.84 1.51.12 2.65.72 3.4 1.8-3.12 1.87-2.38 5.98.48 7.13-.57 1.5-1.31 2.99-2.54 4.09zM12.03 7.25c-.15-2.23 1.66-4.07 3.74-4.25.29 2.58-2.34 4.5-3.74 4.25z" />
                </svg>
                Sign in with Apple
              </button>
            )}

            {/* Passkey / Biometric */}
            {passkeySupported && (
              <button className="landing-passkey-btn" onClick={handlePasskeyLogin}>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
                  <path d="M7 11V7a5 5 0 0 1 10 0v4" />
                </svg>
                Sign in with Passkey
              </button>
            )}

            {passkeyError && <div className="landing-error">{passkeyError}</div>}
          </div>
        </div>

        <div className="landing-divider">
          <span>or</span>
        </div>

        <button className="landing-skip" onClick={onSkip}>
          Continue as guest
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="9 18 15 12 9 6" />
          </svg>
        </button>
      </div>
    </div>
  );
}
