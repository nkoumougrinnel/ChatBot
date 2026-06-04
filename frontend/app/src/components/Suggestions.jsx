export function Suggestions({ items, disabled, onSelect }) {
  if (!items?.length) return null
  return (
    <div className="suggestions">
      {items.map((text, i) => (
        <button
          key={text}
          type="button"
          className="suggestion-chip"
          style={{ animationDelay: `${i * 50}ms` }}
          disabled={disabled}
          onClick={() => onSelect(text)}
        >
          {text}
        </button>
      ))}
    </div>
  )
}
