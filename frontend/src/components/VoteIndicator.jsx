const ThumbUp = () => (
  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3H14z" /><path d="M7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3" />
  </svg>
);

const ThumbDown = () => (
  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M10 15V19a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3H10z" /><path d="M17 2h2.67A2.31 2.31 0 0 1 22 4v7a2.31 2.31 0 0 1-2.33 2H17" />
  </svg>
);

const CheckIcon = () => (
  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="20 6 9 17 4 12" />
  </svg>
);

const ClockIcon = () => (
  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="10" /><polyline points="12 6 12 12 16 14" />
  </svg>
);

const SignalIcon = () => (
  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
  </svg>
);

const XCircle = () => (
  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="10" /><line x1="15" y1="9" x2="9" y2="15" /><line x1="9" y1="9" x2="15" y2="15" />
  </svg>
);

export default function VoteIndicator({ summary }) {
  if (!summary) return null;
  
  const votes = [
    { type: 'works', count: summary.works || 0, icon: CheckIcon, className: 'vi-works', label: 'works' },
    { type: 'like', count: summary.like || 0, icon: ThumbUp, className: 'vi-like', label: 'likes' },
    { type: 'dislike', count: summary.dislike || 0, icon: ThumbDown, className: 'vi-dislike', label: 'dislikes' },
    { type: 'slow', count: summary.slow || 0, icon: ClockIcon, className: 'vi-slow', label: 'slow' },
    { type: 'bad_quality', count: summary.bad_quality || 0, icon: SignalIcon, className: 'vi-bad-quality', label: 'bad quality' },
    { type: 'broken', count: summary.broken || 0, icon: XCircle, className: 'vi-broken', label: 'broken' },
  ];
  
  const activeVotes = votes.filter(v => v.count > 0);
  if (activeVotes.length === 0) return null;

  const tooltipText = activeVotes.map(v => `${v.count} ${v.label}`).join(', ');

  return (
    <span className="vote-indicator" title={tooltipText}>
      {activeVotes.map(({ type, count, icon: Icon, className }) => (
        <span key={type} className={className}>
          <Icon /> {count}
        </span>
      ))}
    </span>
  );
}
