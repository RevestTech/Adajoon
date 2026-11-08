/** Lets a card's own Enter/Space activate it like a click, without also
 * firing when the key event bubbles up from a nested focusable child
 * (e.g. the favorite button) that already handles its own activation. */
export function handleCardKey(onClick) {
  return (e) => {
    if (e.target !== e.currentTarget) return;
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      onClick(e);
    }
  };
}
