const VOTE_BUTTONS = [
  { type: "like",        icon: "👍", label: "Like",        color: "#4caf50" },
  { type: "dislike",     icon: "👎", label: "Dislike",     color: "#ef5350" },
  { type: "works",       icon: "✅", label: "Works",       color: "#66bb6a" },
  { type: "slow",        icon: "🐌", label: "Slow",        color: "#ffa726" },
  { type: "bad_quality", icon: "📉", label: "Bad Quality", color: "#ff7043" },
  { type: "broken",      icon: "💔", label: "Broken",      color: "#e53935" },
];

export default function FeedbackBar({
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

  return (
    <div className="feedback-bar">
      <span className="feedback-label">Rate this {itemType === "tv" ? "channel" : "station"}:</span>
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
              style={active ? { borderColor: btn.color, background: `${btn.color}22` } : undefined}
            >
              <span className="feedback-icon">{btn.icon}</span>
              <span className="feedback-btn-label">{btn.label}</span>
              {count > 0 && <span className="feedback-count">{count}</span>}
            </button>
          );
        })}
      </div>
    </div>
  );
}
