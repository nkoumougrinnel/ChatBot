import { useCallback, useEffect, useRef, useState } from 'react'

import {

  ask,

  fetchHealth,

  getSuggestions,

  resolveServerStatus,

  submitFeedback,

} from '../api/client'



let idCounter = 0

const nextId = () => `msg-${++idCounter}-${Date.now()}`



const HEALTH_POLL_MS = 25000



export function useChat() {

  const [messages, setMessages] = useState([])

  const [suggestions, setSuggestions] = useState([])

  const [isProcessing, setIsProcessing] = useState(false)

  const [serverStatus, setServerStatus] = useState('checking')

  const [gen3Available, setGen3Available] = useState(false)

  const [pipelineLabel, setPipelineLabel] = useState('…')

  const [healthInfo, setHealthInfo] = useState(null)

  const [toast, setToast] = useState('')

  const listRef = useRef(null)

  const userScrolledRef = useRef(false)

  const lastUserQuestionRef = useRef('')



  const showWelcome = messages.length === 0

  const online = serverStatus === 'online' || serverStatus === 'degraded'



  const refreshHealth = useCallback(async () => {

    setServerStatus('checking')

    try {

      const data = await fetchHealth()

      const status = resolveServerStatus(data, false)

      setServerStatus(status)

      setHealthInfo(data)

      setGen3Available(Boolean(data.gen3?.available))



      if (status === 'offline') {

        setPipelineLabel('Hors ligne')

      } else if (data.phase1 === 'indexing_required') {

        setPipelineLabel('Indexation requise')

      } else if (data.phase1 === 'empty') {

        setPipelineLabel('Base vide')

      } else if (data.gen3?.available) {

        setPipelineLabel('Pipeline IA actif')

      } else {

        setPipelineLabel('FAQ intelligente')

      }

      return status

    } catch {

      setServerStatus('offline')

      setGen3Available(false)

      setHealthInfo(null)

      setPipelineLabel('Hors ligne')

      return 'offline'

    }

  }, [])



  useEffect(() => {

    refreshHealth()

    getSuggestions().then(setSuggestions)

    const id = setInterval(refreshHealth, HEALTH_POLL_MS)

    return () => clearInterval(id)

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

    lastUserQuestionRef.current = ''

    showToastMsg('Nouvelle conversation')

  }, [showToastMsg])



  const sendFeedback = useCallback(

    async ({ faqId, feedbackType, question, score, comment }) => {

      return submitFeedback({

        faqId,

        feedbackType,

        question: question || lastUserQuestionRef.current,

        score,

        comment,

      })

    },

    [],

  )



  const sendMessage = useCallback(

    async (text) => {

      const question = text.trim()

      if (!question || isProcessing) return



      setIsProcessing(true)

      userScrolledRef.current = false

      lastUserQuestionRef.current = question



      const userMsg = { id: nextId(), role: 'user', content: question }

      setMessages((m) => [...m, userMsg])

      scrollToBottom(true)



      const botId = nextId()

      setMessages((m) => [

        ...m,

        {

          id: botId,

          role: 'bot',

          status: 'loading',

          statusLabel: 'Réflexion…',

          content: '',

          userQuestion: question,

        },

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

                    ? { ...msg, status: 'streaming', statusLabel: null }

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

                mode: 'gen3',

                elapsedMs: result.elapsedMs,

                userQuestion: question,

                score: null,

                faqId: result.faqId ?? null,

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

                userQuestion: question,

                mode: 'faq',

              }

            }

            return {

              ...msg,

              status: 'done',

              statusLabel: null,

              content: result.text,

              mode: result.mode,

              userQuestion: question,

            }

          }),

        )

        await refreshHealth()

      } catch {

        setMessages((m) =>

          m.map((msg) =>

            msg.id === botId

              ? {

                  ...msg,

                  status: 'error',

                  statusLabel: null,

                  content:

                    "Impossible de joindre le serveur. Vérifiez que le backend tourne sur le port 8001.",

                }

              : msg,

          ),

        )

        setServerStatus('offline')

        setPipelineLabel('Hors ligne')

      } finally {

        setIsProcessing(false)

        scrollToBottom(true)

      }

    },

    [gen3Available, isProcessing, scrollToBottom, refreshHealth],

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

    serverStatus,

    gen3Available,

    pipelineLabel,

    healthInfo,

    toast,

    showWelcome,

    listRef,

    sendMessage,

    resetChat,

    refreshHealth,

    sendFeedback,

    onListScroll,

    scrollToBottom: () => scrollToBottom(true),

    userScrolledRef,

    showToastMsg,

    lastUserQuestion: lastUserQuestionRef.current,

  }

}

