export default function VoteIndicator({ summary }) {
  if (!summary) return null;
  const likes = summary.like || 0;
  const dislikes = summary.dislike || 0;
  const broken = summary.broken || 0;
  if (likes === 0 && dislikes === 0 && broken === 0) return null;

  return (
    <span className="vote-indicator" title={`${likes} likes, ${dislikes} dislikes${broken ? `, ${broken} reported broken` : ""}`}>
      {likes > 0 && <span className="vi-like">👍 {likes}</span>}
      {dislikes > 0 && <span className="vi-dislike">👎 {dislikes}</span>}
      {broken > 0 && <span className="vi-broken">💔 {broken}</span>}
    </span>
  );
}
