import { useCallback, useEffect, useRef, useState } from 'react'
import { ask, fetchHealth, getSuggestions } from '../api/client'

let idCounter = 0
const nextId = () => `msg-${++idCounter}-${Date.now()}`

export function useChat() {
  const [messages, setMessages] = useState([])
  const [suggestions, setSuggestions] = useState([])
  const [isProcessing, setIsProcessing] = useState(false)
  const [online, setOnline] = useState(null)
  const [gen3Available, setGen3Available] = useState(false)
  const [pipelineLabel, setPipelineLabel] = useState('…')
  const [toast, setToast] = useState('')
  const listRef = useRef(null)
  const userScrolledRef = useRef(false)

  const showWelcome = messages.length === 0

  const refreshHealth = useCallback(async () => {
    try {
      const data = await fetchHealth()
      setOnline(true)
      setGen3Available(Boolean(data.gen3?.available))
      if (data.phase1 === 'indexing_required') {
        setPipelineLabel('Indexation requise')
      } else if (data.gen3?.available) {
        setPipelineLabel('Pipeline IA')
      } else {
        setPipelineLabel('FAQ intelligente')
      }
    } catch {
      setOnline(false)
      setGen3Available(false)
      setPipelineLabel('Hors ligne')
    }
  }, [])

  useEffect(() => {
    refreshHealth()
    getSuggestions().then(setSuggestions)
  }, [refreshHealth])

  const scrollToBottom = useCallback((force = false) => {
    if (!force && userScrolledRef.current) return
    const el = listRef.current
    if (el) el.scrollTo({ top: el.scrollHeight, behavior: 'smooth' })
  }, [])

  const showToastMsg = useCallback((msg) => {
    setToast(msg)
    setTimeout(() => setToast(''), 2800)
  }, [])

  const resetChat = useCallback(() => {
    setMessages([])
    userScrolledRef.current = false
    showToastMsg('Nouvelle conversation')
  }, [showToastMsg])

  const sendMessage = useCallback(
    async (text) => {
      const question = text.trim()
      if (!question || isProcessing) return

      setIsProcessing(true)
      userScrolledRef.current = false

      const userMsg = { id: nextId(), role: 'user', content: question }
      setMessages((m) => [...m, userMsg])
      scrollToBottom(true)

      const botId = nextId()
      setMessages((m) => [
        ...m,
        { id: botId, role: 'bot', status: 'loading', statusLabel: 'Réflexion…', content: '' },
      ])

      try {
        const result = await ask(question, {
          gen3Available,
          onEvent: (ev) => {
            if (ev.type === 'status') {
              setMessages((m) =>
                m.map((msg) =>
                  msg.id === botId ? { ...msg, statusLabel: ev.label } : msg,
                ),
              )
            } else if (ev.type === 'meta') {
              setMessages((m) =>
                m.map((msg) =>
                  msg.id === botId
                    ? { ...msg, status: 'streaming', method: ev.method, statusLabel: null }
                    : msg,
                ),
              )
            } else if (ev.type === 'token') {
              setMessages((m) =>
                m.map((msg) =>
                  msg.id === botId
                    ? {
                        ...msg,
                        status: 'streaming',
                        statusLabel: null,
                        content: ev.answer,
                        mode: 'gen3',
                      }
                    : msg,
                ),
              )
              scrollToBottom()
            }
          },
        })

        setMessages((m) =>
          m.map((msg) => {
            if (msg.id !== botId) return msg
            if (result.mode === 'gen3') {
              return {
                ...msg,
                status: 'done',
                statusLabel: null,
                content: result.answer,
                method: result.method,
                mode: 'gen3',
                elapsedMs: result.elapsedMs,
              }
            }
            if (result.mode === 'faq') {
              return {
                ...msg,
                status: 'done',
                statusLabel: null,
                content: result.text,
                faqQuestion: result.question,
                category: result.category,
                score: result.score,
                faqId: result.faqId,
                mode: 'faq',
              }
            }
            return {
              ...msg,
              status: 'done',
              statusLabel: null,
              content: result.text,
              mode: result.mode,
            }
          }),
        )
        setOnline(true)
      } catch {
        setMessages((m) =>
          m.map((msg) =>
            msg.id === botId
              ? {
                  ...msg,
                  status: 'error',
                  statusLabel: null,
                  content:
                    "Impossible de joindre le serveur. Vérifiez que le backend tourne sur le port 8000.",
                }
              : msg,
          ),
        )
        setOnline(false)
        setPipelineLabel('Hors ligne')
      } finally {
        setIsProcessing(false)
        scrollToBottom(true)
      }
    },
    [gen3Available, isProcessing, scrollToBottom],
  )

  const onListScroll = useCallback(() => {
    const el = listRef.current
    if (!el) return
    const atBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 100
    userScrolledRef.current = !atBottom
  }, [])

  return {
    messages,
    suggestions,
    isProcessing,
    online,
    gen3Available,
    pipelineLabel,
    toast,
    showWelcome,
    listRef,
    sendMessage,
    resetChat,
    refreshHealth,
    onListScroll,
    scrollToBottom: () => scrollToBottom(true),
    userScrolledRef,
    showToastMsg,
  }
}
