import { useState, useRef, useEffect } from "react";
import { useAuth } from "../hooks/useAuth";

export default function UserMenu({ user, onLogout, onLogin }) {
  const [open, setOpen] = useState(false);
  const [passkeyMsg, setPasskeyMsg] = useState("");
  const menuRef = useRef(null);
  const auth = useAuth();

  useEffect(() => {
    const handleClick = (e) => {
      if (menuRef.current && !menuRef.current.contains(e.target)) setOpen(false);
    };
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  const handleRegisterPasskey = async () => {
    setPasskeyMsg("");
    try {
      await auth.registerPasskey("My Passkey");
      setPasskeyMsg("Passkey saved!");
      setTimeout(() => setPasskeyMsg(""), 3000);
    } catch (err) {
      if (err.name !== "NotAllowedError") {
        setPasskeyMsg("Failed to set up passkey");
        setTimeout(() => setPasskeyMsg(""), 3000);
      }
    }
  };

  if (!user) {
    return (
      <button className="user-login-btn" onClick={onLogin}>
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
          <circle cx="12" cy="7" r="4" />
        </svg>
        Sign In
      </button>
    );
  }

  return (
    <div className="user-menu" ref={menuRef}>
      <button className="user-avatar-btn" onClick={() => setOpen((v) => !v)}>
        {user.picture ? (
          <img src={user.picture} alt={user.name} className="user-avatar" referrerPolicy="no-referrer" />
        ) : (
          <div className="user-avatar-placeholder">
            {(user.name || user.email || "?").charAt(0).toUpperCase()}
          </div>
        )}
      </button>
      {open && (
        <div className="user-dropdown">
          <div className="user-dropdown-header">
            <span className="user-dropdown-name">{user.name}</span>
            <span className="user-dropdown-email">{user.email}</span>
          </div>
          <div className="user-dropdown-divider" />
          {window.PublicKeyCredential && (
            <button className="user-dropdown-item" onClick={handleRegisterPasskey}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
                <path d="M7 11V7a5 5 0 0 1 10 0v4" />
              </svg>
              {user.has_passkey ? "Add Another Passkey" : "Set Up Passkey"}
            </button>
          )}
          {passkeyMsg && (
            <div className="user-dropdown-msg">{passkeyMsg}</div>
          )}
          <button className="user-dropdown-item" onClick={() => { setOpen(false); onLogout(); }}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
              <polyline points="16 17 21 12 16 7" />
              <line x1="21" y1="12" x2="9" y2="12" />
            </svg>
            Sign Out
          </button>
        </div>
      )}
    </div>
  );
}
