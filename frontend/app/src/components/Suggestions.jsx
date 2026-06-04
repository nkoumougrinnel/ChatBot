const ICONS = ['📚', '🎓', '🎯', '📋']

export function Suggestions({ items, disabled, onSelect }) {
  if (!items?.length) return null
  return (
    <div className="suggestions">
      {items.map((text, i) => (
        <button
          key={text}
          type="button"
          className="suggestion-chip"
          style={{ animationDelay: `${i * 60}ms` }}
          disabled={disabled}
          onClick={() => onSelect(text)}
        >
          <span className="suggestion-chip__icon" aria-hidden>
            {ICONS[i % ICONS.length]}
          </span>
          <span className="suggestion-chip__text">{text}</span>
        </button>
      ))}
    </div>
  )
}
