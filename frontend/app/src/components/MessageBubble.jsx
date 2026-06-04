import { useState } from 'react'
import { IconBot, IconCopy, IconPin } from './Icons'

function TypingDots() {
  return (
    <span className="typing-dots" aria-hidden>
      <span />
      <span />
      <span />
    </span>
  )
}

const METHOD_CLASS = {
  CONV: 'method-tag--conv',
  DIRECT: 'method-tag--direct',
  'TF-IDF': 'method-tag--tfidf',
  LLM: 'method-tag--llm',
  OFFBASE: 'method-tag--offbase',
}

export function MessageBubble({ message, onCopy }) {
  const [copied, setCopied] = useState(false)

  if (message.status === 'error') {
    return (
      <div className="msg-row msg-row--bot">
        <div className="bot-avatar bot-avatar--error" aria-hidden>
          <IconBot />
        </div>
        <div className="bubble bubble--error">
          <p className="bubble-error-title">Connexion impossible</p>
          <div className="bubble-content">
            {message.content.split('\n').map((line, i) => (
              <p key={i}>{line}</p>
            ))}
          </div>
        </div>
      </div>
    )
  }

  if (message.role === 'user') {
    return (
      <div className="msg-row msg-row--user">
        <div className="bubble bubble--user">
          <div className="bubble-content">
            {message.content.split('\n').map((line, i) => (
              <p key={i}>{line}</p>
            ))}
          </div>
        </div>
      </div>
    )
  }

  const loading = message.status === 'loading'
  const streaming = message.status === 'streaming'
  const methodClass = METHOD_CLASS[message.method] || ''

  const handleCopy = async () => {
    if (!message.content) return
    try {
      await navigator.clipboard.writeText(message.content)
      setCopied(true)
      onCopy?.()
      setTimeout(() => setCopied(false), 2000)
    } catch {
      /* ignore */
    }
  }

  return (
    <div className="msg-row msg-row--bot">
      <div className="bot-avatar" aria-hidden>
        <IconBot />
      </div>
      <div className={`bubble bubble--bot ${loading ? 'bubble--loading' : ''}`}>
        {loading && (
          <p className="status-line">
            <TypingDots />
            {message.statusLabel || 'Réflexion…'}
          </p>
        )}

        {message.method && !loading && (
          <span className={`method-tag ${methodClass}`}>{message.method}</span>
        )}

        {message.mode === 'faq' && message.faqQuestion && (
          <p className="faq-question">
            <IconPin /> {message.faqQuestion}
          </p>
        )}

        {(streaming || message.status === 'done' || message.status === 'error') && message.content && (
          <div className="bubble-content">
            {message.content.split('\n').map((line, i) => (
              <p key={i}>{line}</p>
            ))}
            {streaming && <span className="stream-cursor" aria-hidden />}
          </div>
        )}

        {message.mode === 'faq' && message.category && (
          <footer className="bubble-meta">
            <span>{message.category}</span>
            {message.score != null && <span>Score {Number(message.score).toFixed(2)}</span>}
          </footer>
        )}

        {message.status === 'done' && message.content && (
          <div className="bubble-actions">
            {message.elapsedMs != null && (
              <span className="bubble-time">{message.elapsedMs} ms</span>
            )}
            <button
              type="button"
              className="bubble-copy"
              onClick={handleCopy}
              aria-label="Copier la réponse"
            >
              <IconCopy />
              {copied ? 'Copié' : 'Copier'}
            </button>
          </div>
        )}

        {message.mode === 'low' && (
          <ul className="hint-list">
            <li>Reformuler votre question</li>
            <li>Contacter le support SUP&apos;ONE</li>
          </ul>
        )}
      </div>
    </div>
  )
}
