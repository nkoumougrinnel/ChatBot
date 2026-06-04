import { useEffect, useRef, useState } from 'react'
import { IconSend } from './Icons'

const MAX = 500

export function Composer({ disabled, onSend, compact = false }) {
  const [value, setValue] = useState('')
  const textareaRef = useRef(null)

  useEffect(() => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = `${Math.min(el.scrollHeight, 200)}px`
  }, [value])

  const submit = (e) => {
    e.preventDefault()
    const text = value.trim()
    if (!text || disabled) return
    onSend(text)
    setValue('')
  }

  const onKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      submit(e)
    }
  }

  const len = value.length
  const canSend = len > 0 && !disabled

  return (
    <div className="composer-area">
      <div className="composer-area__inner">
        <footer className="composer-wrap">
          <form className="composer" onSubmit={submit}>
            <textarea
              ref={textareaRef}
              value={value}
              onChange={(e) => setValue(e.target.value.slice(0, MAX))}
              onKeyDown={onKeyDown}
              placeholder="Envoyer un message…"
              disabled={disabled}
              maxLength={MAX}
              rows={1}
              aria-label="Votre message"
              autoComplete="off"
            />
            <button
              type="submit"
              className={`composer-send ${canSend ? 'active' : ''}`}
              disabled={!canSend}
              aria-label="Envoyer"
            >
              <IconSend />
            </button>
          </form>
          <div className={`composer-meta ${compact ? 'composer-meta--compact' : ''}`}>
            {!compact && <span>SUP&apos;ONE peut faire des erreurs. Vérifiez les informations importantes.</span>}
            <span className={len > 450 ? 'warn' : ''}>{len} / {MAX}</span>
          </div>
        </footer>
      </div>
    </div>
  )
}
