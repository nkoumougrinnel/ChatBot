const THRESH_LOW = 0.5
const THRESH_MED = 0.7

const STATUS_LABELS = {
  thinking: 'Réflexion…',
  searching: 'Recherche dans la base…',
  generating: 'Génération de la réponse…',
}

export function getApiBase() {
  const host = window.location.hostname
  const isNative = window.Capacitor?.isNativePlatform?.() === true

  if (isNative) {
    return import.meta.env.VITE_API_URL || 'http://10.0.2.2:8000'
  }

  if (import.meta.env.DEV && (host === 'localhost' || host === '127.0.0.1')) {
    return ''
  }
  if (host.includes('ngrok-free.dev')) {
    return 'https://patternable-felicitously-shaunta.ngrok-free.dev'
  }
  if (host.includes('netlify.app')) {
    return 'https://chatbot-production-5202.up.railway.app'
  }
  if (host.includes('192.168') || host.startsWith('10.')) {
    return `http://${host}:8000`
  }
  return import.meta.env.VITE_API_URL || 'http://localhost:8000'
}

export async function fetchHealth() {
  const base = getApiBase()
  const res = await fetch(`${base}/api/health/`, { signal: AbortSignal.timeout(8000) })
  if (!res.ok) throw new Error('health')
  const data = await res.json()
  if (data.phase1 === 'indexing_required') {
    console.warn(
      "[SUP'ONE] Index TF-IDF incomplet — exécutez : python manage.py rebuild_vectors",
    )
  }
  return data
}

export async function fetchSuggestions() {
  const base = getApiBase()
  try {
    const res = await fetch(`${base}/api/stats/`, { signal: AbortSignal.timeout(8000) })
    if (!res.ok) return null
    const data = await res.json()
    return data
      .filter((item) => item.question)
      .sort((a, b) => (b.count || 0) - (a.count || 0))
      .slice(0, 4)
      .map((item) => item.question)
  } catch {
    return null
  }
}

const DEFAULT_SUGGESTIONS = [
  "Où se trouve SUP'PTIC ?",
  'Quels sont les frais d\'inscription ?',
  'Comment rejoindre le Club Informatique ?',
  'Heures d\'ouverture de l\'école ?',
]

export async function getSuggestions() {
  const dynamic = await fetchSuggestions()
  return dynamic?.length ? dynamic : DEFAULT_SUGGESTIONS
}

async function* parseSSE(reader) {
  const decoder = new TextDecoder()
  let buffer = ''
  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() || ''
    for (const line of lines) {
      if (!line.startsWith('data: ')) continue
      try {
        yield JSON.parse(line.slice(6))
      } catch {
        /* ignore malformed chunks */
      }
    }
  }
}

export async function askGen3Stream(question, onEvent) {
  const base = getApiBase()
  const res = await fetch(`${base}/api/v2/chatbot/ask/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'text/event-stream' },
    body: JSON.stringify({ question, stream: true }),
  })
  if (!res.ok) throw new Error(`Gen3 ${res.status}`)

  let answer = ''
  let method = ''
  let elapsedMs = null

  for await (const payload of parseSSE(res.body.getReader())) {
    if (payload.type === 'status') {
      onEvent?.({ type: 'status', label: STATUS_LABELS[payload.status] || payload.status })
    } else if (payload.type === 'meta') {
      method = payload.method || ''
      onEvent?.({ type: 'meta', method })
    } else if (payload.type === 'token' && payload.content) {
      answer += payload.content
      onEvent?.({ type: 'token', content: payload.content, answer })
    } else if (payload.type === 'done') {
      elapsedMs = payload.elapsed_ms ?? null
    } else if (payload.type === 'error') {
      throw new Error(payload.message || 'Erreur pipeline')
    }
  }

  if (!answer.trim()) throw new Error('Réponse vide')
  return { answer, method, mode: 'gen3', elapsedMs }
}

export async function askPhase1(question) {
  const base = getApiBase()
  const res = await fetch(`${base}/api/chatbot/ask/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, top_k: 1 }),
  })
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  const data = await res.json()
  const top = data.results?.[0]
  const score = top ? Number(top.score) : 0

  if (score < THRESH_LOW) {
    return {
      mode: 'low',
      text: "Je n'ai pas trouvé d'information précise. Reformulez votre question ou contactez le support SUP'ONE.",
    }
  }
  if (score < THRESH_MED) {
    const q = (top.question || '').replace(/\?$/, '')
    return {
      mode: 'medium',
      text: `Je ne suis pas totalement sûr — vouliez-vous dire : « ${q} » ?`,
    }
  }
  return {
    mode: 'faq',
    text: top.answer,
    question: top.question,
    category: top.category,
    score,
    faqId: top.faq_id,
  }
}

export async function ask(question, { gen3Available, onEvent }) {
  if (gen3Available) {
    try {
      return await askGen3Stream(question, onEvent)
    } catch {
      /* fallback Phase 1 */
    }
  }
  onEvent?.({ type: 'status', label: 'Recherche dans la FAQ…' })
  return askPhase1(question)
}

export { THRESH_LOW, THRESH_MED }
