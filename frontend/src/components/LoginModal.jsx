import { useEffect, useRef } from "react";

export default function LoginModal({ onClose, onGoogleLogin, googleClientId }) {
  const googleBtnRef = useRef(null);

  useEffect(() => {
    if (!googleClientId || !window.google?.accounts?.id) return;

    window.google.accounts.id.initialize({
      client_id: googleClientId,
      callback: (response) => {
        onGoogleLogin(response.credential);
      },
    });

    window.google.accounts.id.renderButton(googleBtnRef.current, {
      theme: "filled_black",
      size: "large",
      width: 300,
      text: "signin_with",
      shape: "pill",
    });
  }, [googleClientId, onGoogleLogin]);

  useEffect(() => {
    const handleKey = (e) => { if (e.key === "Escape") onClose(); };
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, [onClose]);

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content login-modal" onClick={(e) => e.stopPropagation()}>
        <button className="modal-close" onClick={onClose}>×</button>
        <div className="login-modal-body">
          <div className="login-logo">Ada<span>joon</span></div>
          <p className="login-subtitle">Sign in to sync your favorites across devices</p>

          <div className="login-providers">
            <div ref={googleBtnRef} className="google-btn-wrap" />

            {!googleClientId && (
              <div className="login-note">
                Google Sign-In is not configured yet.
              </div>
            )}
          </div>

          <p className="login-footer">
            Your favorites are currently saved in this browser.
            Sign in to keep them synced everywhere.
          </p>
        </div>
      </div>
    </div>
  );
}
