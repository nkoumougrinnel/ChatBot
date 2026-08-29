/** Seuils alignés sur le backend Phase 1 (cohérence question ↔ réponse) */
const THRESH_LOW = 0.52
const THRESH_MED = 0.68

const STATUS_LABELS = {
  thinking:   'Réflexion…',
  searching:  'Recherche dans la base…',
  generating: 'Génération de la réponse…',
}

/** Durée de vie du cache threads : 30 minutes */
const THREAD_CACHE_TTL_MS = 30 * 60 * 1000
/** Nombre max de threads mis en cache */
const THREAD_CACHE_MAX = 20
/** Timeout par défaut pour les appels API (ms) */
const DEFAULT_TIMEOUT_MS = 12_000

// ─── Helpers ─────────────────────────────────────────────────────────────────

function normalizeBase(url) {
  return url ? String(url).replace(/\/$/, '') : ''
}

/** Récupère le token d'authentification */
function getAuthToken() {
  return localStorage.getItem('supone-token') || null
}

/** Headers communs aux appels authentifiés */
function authHeaders() {
  const token = getAuthToken()
  return token
    ? { Authorization: `Token ${token}`, Accept: 'application/json' }
    : { Accept: 'application/json' }
}

/** Lit et parse le localStorage sans jamais lever d'erreur */
function safeRead(key, fallback = null) {
  try {
    const raw = localStorage.getItem(key)
    return raw ? JSON.parse(raw) : fallback
  } catch {
    return fallback
  }
}

/** Écrit dans le localStorage sans jamais lever d'erreur */
function safeWrite(key, value) {
  try {
    localStorage.setItem(key, JSON.stringify(value))
  } catch {
    // quota dépassé ou mode privé
  }
}

// ─── Base URL ────────────────────────────────────────────────────────────────

export function getApiBase() {
  const host       = window.location.hostname
  const isNative   = window.Capacitor?.isNativePlatform?.() === true
  const configured = normalizeBase(import.meta.env.VITE_API_URL)

  if (isNative) return configured || 'http://10.0.2.2:8001'

  if (import.meta.env.DEV && (host === 'localhost' || host === '127.0.0.1')) return ''

  if (configured) return configured

  if (host.includes('192.168') || host.startsWith('10.')) return `http://${host}:8001`

  return ''
}

// ─── Santé ───────────────────────────────────────────────────────────────────

export async function fetchHealth() {
  const base = getApiBase()
  const res  = await fetch(`${base}/api/health/`, {
    signal: AbortSignal.timeout(DEFAULT_TIMEOUT_MS),
    cache: 'no-store',
  })
  if (!res.ok) throw new Error(`health ${res.status}`)
  const data = await res.json()
  if (data.phase1 === 'indexing_required') {
    console.warn("[SUP'ONE] Index TF-IDF incomplet — exécutez : python manage.py rebuild_vectors")
  }
  return data
}

/** @returns {'checking'|'online'|'degraded'|'offline'} */
export function resolveServerStatus(healthData, fetchFailed = false) {
  if (fetchFailed || !healthData)                                       return 'offline'
  if (!healthData.database || healthData.status === 'error')           return 'offline'
  if (healthData.phase1 === 'indexing_required' || healthData.phase1 === 'empty') {
    return 'degraded'
  }
  return 'online'
}

// ─── Feedback ────────────────────────────────────────────────────────────────

export async function submitFeedback({
  faqId,
  feedbackType,
  question,
  score = null,
  comment = '',
}) {
  const base    = getApiBase()
  const payload = {
    feedback_type:       feedbackType,
    question_utilisateur: question,
    comment:             comment || '',
    // On n'envoie score_similarite que si c'est un nombre valide
    ...(typeof score === 'number' && isFinite(score) ? { score_similarite: score } : {}),
  }
  if (faqId != null) payload.faq = faqId

  const res = await fetch(`${base}/api/feedback/`, {
    method:  'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    body:    JSON.stringify(payload),
    signal:  AbortSignal.timeout(DEFAULT_TIMEOUT_MS),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || `Feedback ${res.status}`)
  }
  return res.json()
}

// ─── Suggestions ─────────────────────────────────────────────────────────────

const DEFAULT_SUGGESTIONS = [
  "Comment m'inscrire à SUP'ONE ?",
  "Quels programmes propose SUP'ONE ?",
  "Comment contacter le secrétariat ?",
  "Quelles sont les dates des examens ?",
]

async function fetchSuggestions() {
  const base = getApiBase()
  try {
    const res = await fetch(`${base}/api/stats/`, {
      signal: AbortSignal.timeout(8_000),
    })
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

export async function getSuggestions() {
  const dynamic = await fetchSuggestions()
  return dynamic?.length ? dynamic : DEFAULT_SUGGESTIONS
}

// ─── Historique ───────────────────────────────────────────────────────────────
//
// Responsabilité de ce module : uniquement communiquer avec le backend.
// La normalisation et la fusion avec le localStorage sont gérées dans useChat.js.

/**
 * Récupère les conversations du backend.
 * En cas d'échec réseau, lève l'erreur — le hook gère le fallback local.
 */
export async function fetchHistory() {
  const token = getAuthToken()
  // Pas de token = pas de session = historique vide côté backend
  if (!token) return []

  const base = getApiBase()
  const res  = await fetch(`${base}/api/history/`, {
    headers: authHeaders(),
    signal:  AbortSignal.timeout(DEFAULT_TIMEOUT_MS),
  })
  if (!res.ok) throw new Error(`history ${res.status}`)
  return res.json()
}

/**
 * Supprime tout l'historique de l'utilisateur
 */
export async function deleteHistory() {
  const token = getAuthToken()
  if (!token) return false

  const base = getApiBase()
  const res  = await fetch(`${base}/api/history/`, {
    method: 'DELETE',
    headers: authHeaders(),
    signal:  AbortSignal.timeout(DEFAULT_TIMEOUT_MS),
  })
  return res.ok
}

// ─── Cache threads ────────────────────────────────────────────────────────────

const THREADS_CACHE_KEY = 'supone-threads'

function readThreadsCache() {
  return safeRead(THREADS_CACHE_KEY, {})
}

function writeThreadCache(threadId, data) {
  const cache   = readThreadsCache()
  const ids     = Object.keys(cache)

  // Eviction FIFO si le cache dépasse la taille max
  if (ids.length >= THREAD_CACHE_MAX && !(threadId in cache)) {
    // Retire l'entrée la plus ancienne
    const oldest = ids.sort((a, b) => (cache[a].cachedAt ?? 0) - (cache[b].cachedAt ?? 0))[0]
    delete cache[oldest]
  }

  cache[threadId] = { data, cachedAt: Date.now() }
  safeWrite(THREADS_CACHE_KEY, cache)
}

function readThreadCache(threadId) {
  const cache = readThreadsCache()
  const entry = cache[threadId]
  if (!entry) return null
  // TTL expiré
  if (Date.now() - (entry.cachedAt ?? 0) > THREAD_CACHE_TTL_MS) {
    delete cache[threadId]
    safeWrite(THREADS_CACHE_KEY, cache)
    return null
  }
  return entry.data
}

/**
 * Récupère les messages d'un thread (backend puis cache local).
 * Lève une erreur si les deux sources échouent.
 */
export async function fetchThreadMessages(threadId) {
  const base  = getApiBase()
  const token = getAuthToken()

  try {
    const res = await fetch(`${base}/api/history/${threadId}/`, {
      headers: authHeaders(),
      signal:  AbortSignal.timeout(DEFAULT_TIMEOUT_MS),
    })
    if (res.ok) {
      const data = await res.json()
      writeThreadCache(threadId, data)
      return data
    }
  } catch {
    // réseau indisponible — on tente le cache
  }

  const cached = readThreadCache(threadId)
  if (cached) return cached

  throw new Error(`thread:${threadId} introuvable`)
}

// ─── SSE ─────────────────────────────────────────────────────────────────────

async function* parseSSE(reader) {
  const decoder = new TextDecoder()
  let buffer    = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() ?? ''   // conserve le fragment en cours

    for (const line of lines) {
      if (!line.startsWith('data: ')) continue
      try {
        yield JSON.parse(line.slice(6))
      } catch {
        // chunk malformé — on ignore
      }
    }
  }

  // Flush du buffer résiduel (dernier chunk non terminé par \n)
  if (buffer.startsWith('data: ')) {
    try {
      yield JSON.parse(buffer.slice(6))
    } catch {
      // fragment incomplet — on ignore
    }
  }
}

// ─── Pipeline Gen3 (SSE) ─────────────────────────────────────────────────────

export async function askGen3Stream(question, onEvent) {
  const base = getApiBase()
  const res  = await fetch(`${base}/api/v2/chatbot/ask/`, {
    method:  'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'text/event-stream' },
    body:    JSON.stringify({ question, stream: true }),
  })
  if (!res.ok) throw new Error(`Gen3 ${res.status}`)

  // Garde contre un body null (ex. réponse 204 ou bug navigateur)
  const body = res.body
  if (!body) throw new Error('Gen3 : corps de réponse vide')

  let answer    = ''
  let elapsedMs = null

  for await (const payload of parseSSE(body.getReader())) {
    switch (payload.type) {
      case 'status':
        onEvent?.({ type: 'status', label: STATUS_LABELS[payload.status] || payload.status })
        break
      case 'meta':
        onEvent?.({ type: 'meta' })
        break
      case 'token':
        if (payload.content) {
          answer += payload.content
          onEvent?.({ type: 'token', content: payload.content, answer })
        }
        break
      case 'done':
        elapsedMs = payload.elapsed_ms ?? null
        break
      case 'error':
        throw new Error(payload.message || 'Erreur pipeline')
      default:
        break
    }
  }

  if (!answer.trim()) throw new Error('Réponse Gen3 vide')
  return { answer, mode: 'gen3', elapsedMs }
}

// ─── Pipeline Phase 1 (FAQ) ───────────────────────────────────────────────────

export async function askPhase1(question) {
  const base = getApiBase()
  const res  = await fetch(`${base}/api/chatbot/ask/`, {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify({ question, top_k: 1 }),
    signal:  AbortSignal.timeout(DEFAULT_TIMEOUT_MS),
  })
  if (!res.ok) throw new Error(`Phase1 HTTP ${res.status}`)
  const data  = await res.json()
  const top   = data.results?.[0]
  const score = top ? Number(top.score) : 0

  if (score < THRESH_LOW) {
    return {
      mode: 'low',
      text:
        "Je n'ai pas trouvé d'information correspondant à votre question dans notre base. " +
        "Reformulez avec des termes plus précis (inscription, frais, filière…) ou contactez le secrétariat SUP'PTIC.",
    }
  }
  if (score < THRESH_MED) {
    return {
      mode: 'medium',
      text:
        "Votre question est proche de plusieurs sujets de notre base, mais la correspondance n'est pas assez fiable. " +
        "Merci de préciser votre demande (par exemple : inscription Licence, frais de scolarité, dates d'examen).",
    }
  }
  return {
    mode:     'faq',
    text:     top.answer,
    question: top.question,
    category: top.category,
    score,
    faqId:    top.faq_id,
  }
}

// ─── Point d'entrée principal ────────────────────────────────────────────────

export async function ask(question, { gen3Available, onEvent }) {
  if (gen3Available) {
    try {
      return await askGen3Stream(question, onEvent)
    } catch (err) {
      console.warn("[SUP'ONE] Gen3 indisponible, repli Phase 1 :", err)
    }
  }
  onEvent?.({ type: 'status', label: 'Recherche dans la FAQ…' })
  return askPhase1(question)
}

export { THRESH_LOW, THRESH_MED }