// ─────────────────────────────────────────────────────────────────────────────
// api.ts — Client SSE pour le chatbot SUP'ONE
//
// Événements reçus du backend (dans l'ordre) :
//
//  { type: "status",  status: "thinking" | "searching" | "streaming" }
//      → animation frontend (loader, recherche, typing…)
//
//  { type: "meta",    method: "CONV" | "DIRECT" | "LLM",
//                     score: number,
//                     source: { question: string; categorie: string } | null }
//      → badge méthode RAG, score de confiance
//
//  { type: "token",   content: string }
//      → fragment de texte à ajouter dans la bulle (LLM streaming)
//
//  { type: "done",    elapsed_ms: number }
//      → fin de réponse
//
//  { type: "error",   message: string }
//      → erreur serveur
// ─────────────────────────────────────────────────────────────────────────────


// Utilise la config dynamique si disponible (client.ts), sinon fallback local
import { BACKEND_BASE_URL } from './client';

// ── Types des événements SSE ──────────────────────────────────────────────────

export type ChatbotStatus = {
  type: "status";
  status: "thinking" | "searching" | "streaming";
};

export type ChatbotMeta = {
  type: "meta";
  method: "CONV" | "DIRECT" | "LLM";
  score: number;
  source: { question: string; categorie: string } | null;
  // champs additionnels acceptés
  [key: string]: any;
};

export type ChatbotToken = {
  type: "token";
  content: string;
};

export type ChatbotDone = {
  type: "done";
  elapsed_ms: number;
};

export type ChatbotError = {
  type: "error";
  message: string;
};

export type ChatbotEvent =
  | ChatbotStatus
  | ChatbotMeta
  | ChatbotToken
  | ChatbotDone
  | ChatbotError;

// ── Streaming SSE ─────────────────────────────────────────────────────────────
/**
 * Consomme le flux SSE du chatbot et appelle les callbacks à chaque événement.
 *
 * @param question   - La question de l'utilisateur
 * @param onStatus   - Animation à afficher ("thinking" | "searching" | "streaming")
 * @param onMeta     - Méthode RAG utilisée + score de confiance
 * @param onToken    - Fragment de texte (LLM streaming)
 * @param onDone     - Fin du flux (reçoit la durée totale en ms)
 * @param onError    - Erreur serveur ou réseau
 */
export async function askChatbotStream(
  question: string,
  onStatus: (status: ChatbotStatus["status"]) => void,
  onMeta: (meta: ChatbotMeta) => void,
  onToken: (token: string) => void,
  onDone: (elapsed_ms: number) => void,
  onError: (error: string) => void,
): Promise<void> {
  let response: Response;

  try {
    response = await fetch(`${BACKEND_BASE_URL}/api/chatbot/ask/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });
  } catch (networkErr) {
    onError(`Impossible de joindre le serveur : ${networkErr}`);
    return;
  }

  if (!response.ok) {
    const body = await response.text().catch(() => "");
    onError(`Erreur API ${response.status}: ${body}`);
    return;
  }

  const reader = response.body?.getReader();
  if (!reader) {
    onError("Impossible de lire le flux SSE");
    return;
  }

  const decoder = new TextDecoder();
  let buffer = "";

  const processLine = (line: string) => {
    const trimmed = line.trim();
    if (!trimmed.startsWith("data: ")) return;

    const jsonStr = trimmed.slice(6);
    let event: ChatbotEvent;
    try {
      event = JSON.parse(jsonStr);
    } catch {
      // Ligne SSE malformée, on ignore
      return;
    }

    switch (event.type) {
      case "status":
        onStatus(event.status);
        break;
      case "meta":
        onMeta(event);
        break;
      case "token":
        onToken(event.content);
        break;
      case "done":
        onDone(event.elapsed_ms ?? 0);
        break;
      case "error":
        onError(event.message);
        break;
    }
  };

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const parts = buffer.split("\n\n");

      // Traite tous les événements complets
      for (let i = 0; i < parts.length - 1; i++) {
        processLine(parts[i]);
      }

      // Garde le fragment partiel pour la prochaine lecture
      buffer = parts[parts.length - 1];
    }

    // Traite d'éventuels derniers octets
    if (buffer.trim()) processLine(buffer);
  } catch (err) {
    onError(`Erreur lecture flux SSE : ${err}`);
  } finally {
    reader.releaseLock();
  }
}

// ── Vérification disponibilité Ollama ────────────────────────────────────────

export type LLMStatus = {
  available: boolean;
  model_loaded: boolean;
  model: string;
  error: string | null;
};

export async function checkLLMStatus(): Promise<LLMStatus> {
  const res = await fetch(`${BACKEND_BASE_URL}/api/chatbot/status/`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}
