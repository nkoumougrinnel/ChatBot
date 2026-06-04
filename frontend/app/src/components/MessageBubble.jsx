import { useState } from 'react'
import { FeedbackBar } from './FeedbackBar'
import { IconBot, IconCopy } from './Icons'

function TypingDots() {
  return (
    <span className="typing-dots" aria-hidden>
      <span />
      <span />
      <span />
    </span>
  )
}

export function MessageBubble({ message, onCopy, onSubmitFeedback, onToast }) {
  const [copied, setCopied] = useState(false)

  if (message.status === 'error') {
    return (
      <div className="msg-row msg-row--bot">
        <div className="bot-avatar bot-avatar--error" aria-hidden>
          <IconBot />
        </div>
        <div className="msg-body">
          <div className="bubble bubble--error">
            <p className="bubble-error-title">Connexion impossible</p>
            <div className="bubble-content">
              {message.content.split('\n').map((line, i) => (
                <p key={i}>{line}</p>
              ))}
            </div>
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
        <img src="/icon.png" alt="" className="bot-avatar__img" width={18} height={18} />
      </div>
      <div className="msg-body">
        <div className={`bubble bubble--bot ${loading ? 'bubble--loading' : ''}`}>
          {loading && (
            <p className="status-line">
              <TypingDots />
              {message.statusLabel || 'Réflexion…'}
            </p>
          )}

          {(streaming || message.status === 'done') && message.content && (
            <div className="bubble-content">
              {message.content.split('\n').map((line, i) => (
                <p key={i}>{line}</p>
              ))}
              {streaming && <span className="stream-cursor" aria-hidden />}
            </div>
          )}

          {message.mode === 'low' && (
            <ul className="hint-list">
              <li>Reformuler votre question avec des mots plus précis</li>
              <li>Contacter le secrétariat SUP&apos;PTIC</li>
            </ul>
          )}
        </div>

        {message.status === 'done' && message.content && message.mode !== 'low' && (
          <FeedbackBar
            faqId={message.faqId}
            userQuestion={message.userQuestion}
            score={message.score}
            onSubmitFeedback={onSubmitFeedback}
            onToast={onToast}
          />
        )}

        {message.status === 'done' && message.content && (
          <div className="bubble-actions">
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
      </div>
    </div>
  )
}
