import { useState } from 'react'
import { IconThumbsDown, IconThumbsUp } from './Icons'

export function FeedbackBar({
  faqId,
  userQuestion,
  score,
  onSubmitFeedback,
  onToast,
  disabled,
}) {
  const [vote, setVote] = useState(null)
  const [submitting, setSubmitting] = useState(false)
  const [showComment, setShowComment] = useState(false)
  const [comment, setComment] = useState('')

  const send = async (type, extraComment = '') => {
    if (submitting || vote) return
    setSubmitting(true)
    try {
      await onSubmitFeedback({
        faqId,
        feedbackType: type,
        question: userQuestion,
        score,
        comment: extraComment,
      })
      setVote(type)
      onToast?.(
        type === 'positif'
          ? 'Merci pour votre retour positif !'
          : 'Merci, votre retour nous aide à améliorer les réponses.',
      )
      setShowComment(false)
    } catch {
      onToast?.('Impossible d\'envoyer le feedback')
    } finally {
      setSubmitting(false)
    }
  }

  const handleDown = () => {
    if (vote) return
    setShowComment(true)
  }

  const handleCommentSubmit = (e) => {
    e.preventDefault()
    send('negatif', comment.trim())
  }

  if (!userQuestion) return null

  return (
    <div className="feedback-bar">
      <span className="feedback-bar__label">Cette réponse vous a-t-elle aidé ?</span>
      <div className="feedback-bar__actions">
        <button
          type="button"
          className={`feedback-btn ${vote === 'positif' ? 'feedback-btn--active-up' : ''}`}
          onClick={() => send('positif')}
          disabled={disabled || submitting || Boolean(vote)}
          aria-label="Réponse utile"
        >
          <IconThumbsUp />
          <span>Utile</span>
        </button>
        <button
          type="button"
          className={`feedback-btn ${vote === 'negatif' ? 'feedback-btn--active-down' : ''}`}
          onClick={handleDown}
          disabled={disabled || submitting || Boolean(vote)}
          aria-label="Réponse peu utile"
        >
          <IconThumbsDown />
          <span>Peu utile</span>
        </button>
      </div>

      {showComment && !vote && (
        <form className="feedback-comment" onSubmit={handleCommentSubmit}>
          <textarea
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            placeholder="Qu'est-ce qui pourrait être amélioré ? (optionnel)"
            rows={2}
            maxLength={500}
          />
          <div className="feedback-comment__actions">
            <button type="button" className="feedback-comment__cancel" onClick={() => setShowComment(false)}>
              Annuler
            </button>
            <button type="submit" className="feedback-comment__send" disabled={submitting}>
              Envoyer
            </button>
          </div>
        </form>
      )}
    </div>
  )
}
