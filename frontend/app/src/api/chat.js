/**
 * SUP'ONE AI - Chat API Client
 * Service de communication avec le backend Django
 */

const API_BASE = (() => {
  const host = window.location.hostname;
  const configured = import.meta.env.VITE_API_URL;

  // Si on est en développement local, on force localhost pour éviter CORS production
  if (host === "localhost" || host === "127.0.0.1") {
    return "http://localhost:8001";
  }
  if (configured) return configured.replace(/\/$/, "");
  if (host.includes("192.168") || host.startsWith("10.")) {
    return `http://${host}:8001`;
  }
  return "";
})();

function getAuthHeaders() {
  const token = localStorage.getItem('supone-token');
  const headers = { "Content-Type": "application/json" };
  if (token) headers['Authorization'] = `Token ${token}`;
  return headers;
}

/**
 * Effectue l'appel réseau pour vérifier la santé du serveur
 */
export async function fetchHealth() {
  const res = await fetch(`${API_BASE}/api/health/`, { 
    cache: 'no-store',
    signal: AbortSignal.timeout(5000) 
  });
  if (!res.ok) throw new Error("Serveur injoignable");
  return await res.json();
}

/**
 * Résout l'état du serveur en fonction des données de santé (synchrone)
 */
export function resolveServerStatus(healthData, fetchFailed = false) {
  if (fetchFailed || !healthData) return 'offline';
  if (!healthData.database || healthData.status === 'error') return 'offline';
  if (healthData.phase1 === 'indexing_required' || healthData.phase1 === 'empty') {
    return 'degraded';
  }
  return 'online';
}

/**
 * Récupère les suggestions basées sur les questions les plus populaires
 */
export async function getSuggestions() {
  try {
    const res = await fetch(`${API_BASE}/api/stats/`, { signal: AbortSignal.timeout(3000) });
    if (!res.ok) throw new Error();
    const stats = await res.json();
    return stats
      .filter(s => s.question)
      .sort((a, b) => (b.count || 0) - (a.count || 0))
      .slice(0, 4)
      .map(s => s.question);
  } catch (e) {
    return ["Quelle est l'histoire de SUP'PTIC ?", "Comment s'inscrire ?", "Dates des examens"];
  }
}

/**
 * Envoie un feedback (positif/négatif) sur une réponse
 */
export async function submitFeedback(payload) {
  try {
    const res = await fetch(`${API_BASE}/api/feedback/`, {
      method: "POST",
      signal: AbortSignal.timeout(5000),
      headers: getAuthHeaders(),
      body: JSON.stringify(payload),
    });
    return res.ok;
  } catch (e) {
    return false;
  }
}

/**
 * Pose une question via le pipeline Phase 1 (FAQ TF-IDF)
 */
export async function askV1(question) {
  const res = await fetch(`${API_BASE}/api/chatbot/ask/`, {
    method: "POST",
    signal: AbortSignal.timeout(15000),
    headers: getAuthHeaders(),
    body: JSON.stringify({ question }),
  });
  if (!res.ok) throw new Error("Erreur lors de la recherche FAQ");
  return await res.json();
}

/**
 * Pose une question via le pipeline Gen3 (Streaming AI)
 */
export async function askV2Stream(question, onEvent) {
  const res = await fetch(`${API_BASE}/api/v2/chatbot/ask/`, {
    method: "POST",
    headers: {
      ...getAuthHeaders(),
      "Accept": "text/event-stream"
    },
    body: JSON.stringify({ question, stream: true }),
  });

  if (!res.ok) throw new Error("Erreur lors de la génération IA");
  if (!res.body) throw new Error("No body");

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let fullAnswer = "";
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";

    for (const line of lines) {
      if (line.startsWith("data: ")) {
        const jsonStr = line.substring(6).trim();
        if (!jsonStr) continue;
        try {
          const data = JSON.parse(jsonStr);
          if (data.type === "status") onEvent?.({ type: 'status', label: data.status });
          if (data.type === "token") {
            fullAnswer += data.content;
            onEvent?.({ type: 'token', content: data.content, answer: fullAnswer });
          }
          if (data.type === "meta") onEvent?.({ type: 'meta', method: data.method });
          if (data.type === "error") throw new Error(data.message);
        } catch (e) {
          // Fin du stream ou chunk incomplet
        }
      }
    }
  }
  return { answer: fullAnswer, mode: 'gen3' };
}

/**
 * Fonction orchestratrice principale requise par useChat.js
 * Bascule entre Gen3 (Streaming) et V1 (FAQ) selon la disponibilité.
 */
export async function ask(question, { gen3Available, onEvent }) {
  if (gen3Available) {
    try {
      return await askV2Stream(question, onEvent);
    } catch (e) {
      console.warn("Échec du streaming Gen3, repli sur Phase 1:", e);
      onEvent?.({ type: 'status', label: 'Recherche dans la FAQ…' });
    }
  }
  const data = await askV1(question);
  const top = data.results?.[0];
  const score = top ? Number(top.score) : 0;

  if (score < 0.52) {
    return {
      mode: 'low',
      text: "Je n'ai pas trouvé d'information correspondant à votre question dans notre base. Reformulez avec des termes plus précis ou contactez le secrétariat SUP'PTIC."
    };
  }
  if (score < 0.68) {
    return {
      mode: 'medium',
      text: "Votre question est proche de plusieurs sujets de notre base, mais la correspondance n'est pas assez fiable. Merci de préciser votre demande."
    };
  }

  return {
    mode: 'faq',
    text: top.answer,
    question: top.question,
    category: top.category,
    score: score,
    faqId: top.faq_id
  };
}

/**
 * Récupère la liste des conversations (threads) de l'utilisateur
 */
export async function fetchHistory() {
  try {
    const res = await fetch(`${API_BASE}/api/history/`, {
      signal: AbortSignal.timeout(4000),
      headers: {
        ...getAuthHeaders(),
        "Accept": "application/json"
      },
    });
    if (res.status === 404 || res.status === 501) return [];
    if (!res.ok) return [];
    return await res.json();
  } catch (e) {
    return [];
  }
}

/**
 * Supprime tout l'historique de l'utilisateur
 */
export async function deleteHistory() {
  try {
    const res = await fetch(`${API_BASE}/api/history/`, {
      method: 'DELETE',
      headers: getAuthHeaders(),
      signal: AbortSignal.timeout(5000)
    });
    return res.ok;
  } catch (e) {
    return false;
  }
}

/**
 * Récupère tous les messages d'une conversation spécifique
 */
export async function fetchThreadMessages(threadId) {
  try {
    const res = await fetch(`${API_BASE}/api/history/${threadId}/`, {
      signal: AbortSignal.timeout(4000),
      headers: getAuthHeaders(),
    });
    if (res.status === 404 || res.status === 501) return [];
    if (!res.ok) return [];
    const data = await res.json();
    return Array.isArray(data) ? data : (data.messages || []);
  } catch (e) {
    return [];
  }
}