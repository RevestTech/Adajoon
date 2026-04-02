const SvgIcon = ({ children, size = 16 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    {children}
  </svg>
);

const VOTE_BUTTONS = [
  {
    type: "like", label: "Like", color: "#4caf50",
    icon: <SvgIcon><path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3H14z" /><path d="M7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3" /></SvgIcon>,
  },
  {
    type: "dislike", label: "Dislike", color: "#ef5350",
    icon: <SvgIcon><path d="M10 15V19a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3H10z" /><path d="M17 2h2.67A2.31 2.31 0 0 1 22 4v7a2.31 2.31 0 0 1-2.33 2H17" /></SvgIcon>,
  },
  {
    type: "works", label: "Works", color: "#66bb6a",
    icon: <SvgIcon><polyline points="20 6 9 17 4 12" /></SvgIcon>,
  },
  {
    type: "slow", label: "Slow", color: "#ffa726",
    icon: <SvgIcon><circle cx="12" cy="12" r="10" /><polyline points="12 6 12 12 16 14" /></SvgIcon>,
  },
  {
    type: "bad_quality", label: "Bad Quality", color: "#ff7043",
    icon: <SvgIcon><polyline points="22 12 18 12 15 21 9 3 6 12 2 12" /></SvgIcon>,
  },
  {
    type: "broken", label: "Broken", color: "#e53935",
    icon: <SvgIcon><circle cx="12" cy="12" r="10" /><line x1="15" y1="9" x2="9" y2="15" /><line x1="9" y1="9" x2="15" y2="15" /></SvgIcon>,
  },
];

export default function FeedbackBar({
  variant,
  itemType,
  itemId,
  myVotes = [],
  summary = {},
  onVote,
  isGuest,
  onLogin,
}) {
  const handleClick = (voteType) => {
    if (isGuest) { onLogin?.(); return; }
    onVote?.(itemType, itemId, voteType);
  };

  const label =
    variant === "channel"
      ? "How does it feel?"
      : `Rate this ${itemType === "tv" ? "channel" : "station"}:`;

  return (
    <div className={`feedback-bar${variant === "channel" ? " feedback-bar--channel" : ""}`}>
      <span className="feedback-label">{label}</span>
      <div className="feedback-buttons">
        {VOTE_BUTTONS.map((btn) => {
          const active = myVotes.includes(btn.type);
          const count = summary[btn.type] || 0;
          return (
            <button
              key={btn.type}
              className={`feedback-btn ${active ? "active" : ""}`}
              onClick={() => handleClick(btn.type)}
              title={btn.label}
              aria-pressed={active}
              style={active ? { borderColor: btn.color, background: `${btn.color}22` } : undefined}
            >
              <span className="feedback-icon" style={active ? { color: btn.color } : undefined}>{btn.icon}</span>
              <span className="feedback-btn-label">{btn.label}</span>
              {count > 0 && <span className="feedback-count">{count}</span>}
            </button>
          );
        })}
      </div>
    </div>
  );
}
