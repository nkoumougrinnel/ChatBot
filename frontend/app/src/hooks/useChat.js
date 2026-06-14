import { useCallback, useEffect, useRef, useState } from 'react';
import {
  ask,
  fetchHealth,
  fetchHistory,
  fetchThreadMessages,
  getSuggestions,
  deleteHistory,
  resolveServerStatus,
  submitFeedback,
} from '../api/chat';

const HEALTH_POLL_MS = 25000;
const LOCAL_HISTORY_KEY = 'supone-history';
const MAX_LOCAL_HISTORY = 50;

const nextId = () => Math.random().toString(36).substr(2, 9);

// ─── Helpers historique ──────────────────────────────────────────────────────

/** Normalise un item brut (backend ou local) en {id, title, source, raw} */
function normalizeItem(it, index, source = 'backend') {
  return {
    id: it.id ?? it.thread_id ?? `local-${index}`,
    title:
      it.title ??
      it.summary ??
      (it.messages?.[0]
        ? (it.messages[0].content ?? it.messages[0].text ?? '').slice(0, 120)
        : it.name || 'Discussion sans titre'),
    source, // 'backend' | 'local'
    createdAt: it.created_at ?? it.createdAt ?? Date.now(),
    raw: it,
  };
}

/** Lit l'historique local depuis localStorage (ne lève jamais d'erreur) */
function readLocalHistory() {
  try {
    const raw = localStorage.getItem(LOCAL_HISTORY_KEY);
    const parsed = raw ? JSON.parse(raw) : [];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

/** Persiste l'historique local dans localStorage */
function writeLocalHistory(entries) {
  try {
    localStorage.setItem(LOCAL_HISTORY_KEY, JSON.stringify(entries.slice(0, MAX_LOCAL_HISTORY)));
  } catch {
    // quota dépassé ou mode privé — on ignore silencieusement
  }
}

/**
 * Fusionne les entrées backend et locales en supprimant les doublons.
 * Les entrées backend sont prioritaires ; les locales comblent les trous
 * (ex. : discussions créées hors ligne).
 */
function mergeHistory(backendItems, localItems) {
  const backendIds = new Set(backendItems.map((i) => i.id));
  const uniqueLocals = localItems.filter((i) => !backendIds.has(i.id));
  // Backend en tête, puis locaux non encore synchronisés
  return [...backendItems, ...uniqueLocals].sort(
    (a, b) => (b.createdAt ?? 0) - (a.createdAt ?? 0)
  );
}

// ─── Hook principal ──────────────────────────────────────────────────────────

export function useChat() {
  const [messages, setMessages]           = useState([]);
  const [history, setHistory]             = useState([]);
  const [suggestions, setSuggestions]     = useState([]);
  const [isProcessing, setIsProcessing]   = useState(false);
  const [serverStatus, setServerStatus]   = useState('checking');
  const [gen3Available, setGen3Available] = useState(false);
  const [pipelineLabel, setPipelineLabel] = useState('…');
  const [healthInfo, setHealthInfo]       = useState(null);
  const [toast, setToast]                 = useState('');

  const listRef            = useRef(null);
  const userScrolledRef    = useRef(false);
  const lastUserQuestionRef = useRef('');
  /** Garde la trace de l'id de l'entrée locale en attente de sync backend */
  const pendingLocalIdRef  = useRef(null);

  const showWelcome = messages.length === 0;
  const online = serverStatus === 'online' || serverStatus === 'degraded';

  // ── Santé ────────────────────────────────────────────────────────────────

  const refreshHealth = useCallback(async () => {
    setServerStatus('checking');
    try {
      const data   = await fetchHealth();
      const status = resolveServerStatus(data, false);
      setServerStatus(status);
      setHealthInfo(data);
      setGen3Available(Boolean(data.gen3?.available));

      if (status === 'offline')                    setPipelineLabel('Hors ligne');
      else if (data.phase1 === 'indexing_required') setPipelineLabel('Indexation requise');
      else if (data.phase1 === 'empty')             setPipelineLabel('Base vide');
      else if (data.gen3?.available)                setPipelineLabel('Pipeline IA actif');
      else                                          setPipelineLabel('FAQ intelligente');

      return status;
    } catch {
      setServerStatus('offline');
      setGen3Available(false);
      setHealthInfo(null);
      setPipelineLabel('Hors ligne');
      return 'offline';
    }
  }, []);

  // ── Historique ───────────────────────────────────────────────────────────

  /**
   * Recharge l'historique depuis le backend et fusionne avec le local.
   * Nettoie les entrées locales dont le backend a pris le relais.
   */
  const refreshHistory = useCallback(async () => {
    const localRaw     = readLocalHistory();
    const localItems   = localRaw.map((it, i) => normalizeItem(it, i, 'local'));

    try {
      const data         = await fetchHistory();
      const arr          = Array.isArray(data) ? data : [];
      const backendItems = arr.map((it, i) => normalizeItem(it, i, 'backend'));

      // Supprime du localStorage les entrées maintenant présentes côté backend
      const backendIds = new Set(backendItems.map((i) => i.id));
      const survivingLocals = localRaw.filter(
        (it) => !backendIds.has(it.id ?? it.thread_id)
      );
      if (survivingLocals.length !== localRaw.length) {
        writeLocalHistory(survivingLocals);
      }

      const merged = mergeHistory(backendItems, localItems.filter((i) => !backendIds.has(i.id)));
      setHistory(merged);
      return merged;
    } catch {
      // Offline : on affiche ce qu'on a en local
      setHistory(localItems);
      return localItems;
    }
  }, []);

  /**
   * Ajoute une entrée dans le localStorage et met à jour l'état en mémoire.
   * Retourne l'id local généré pour permettre une éventuelle mise à jour ultérieure.
   */
  const addLocalHistoryEntry = useCallback((title) => {
    const localId = `local-${Date.now()}`;
    const entry   = { id: localId, title, created_at: Date.now() };

    const existing = readLocalHistory();
    writeLocalHistory([entry, ...existing]);

    const normalized = normalizeItem(entry, 0, 'local');
    setHistory((prev) => {
      const ids = new Set(prev.map((i) => i.id));
      return ids.has(localId) ? prev : [normalized, ...prev];
    });

    return localId;
  }, []);

  /**
   * Met à jour le titre d'une entrée locale existante (ex. : quand la vraie
   * question est connue après validation).
   */
  const updateLocalHistoryEntry = useCallback((localId, newTitle) => {
    const existing = readLocalHistory();
    const updated  = existing.map((it) =>
      it.id === localId ? { ...it, title: newTitle } : it
    );
    writeLocalHistory(updated);

    setHistory((prev) =>
      prev.map((it) => (it.id === localId ? { ...it, title: newTitle } : it))
    );
  }, []);

  // ── Init ─────────────────────────────────────────────────────────────────

  useEffect(() => {
    refreshHealth();
    refreshHistory();
    getSuggestions().then(setSuggestions);

    const id = setInterval(refreshHealth, HEALTH_POLL_MS);
    return () => clearInterval(id);
  }, [refreshHealth, refreshHistory]);

  // ── Scroll ───────────────────────────────────────────────────────────────

  const scrollToBottom = useCallback((force = false) => {
    if (!force && userScrolledRef.current) return;
    const el = listRef.current;
    if (el) el.scrollTo({ top: el.scrollHeight, behavior: 'smooth' });
  }, []);

  const onListScroll = useCallback(() => {
    const el = listRef.current;
    if (!el) return;
    userScrolledRef.current = el.scrollHeight - el.scrollTop - el.clientHeight >= 100;
  }, []);

  // ── Toast ────────────────────────────────────────────────────────────────

  const showToastMsg = useCallback((msg) => {
    setToast(msg);
    setTimeout(() => setToast(''), 2800);
  }, []);

  // ── Reset / nouvelle conversation ────────────────────────────────────────

  /**
   * Vide la conversation en cours. N'ajoute PAS d'entrée dans l'historique :
   * celle-ci sera créée lorsque l'utilisateur enverra son premier message.
   */
  const resetChat = useCallback(() => {
    setMessages([]);
    userScrolledRef.current   = false;
    lastUserQuestionRef.current = '';
    pendingLocalIdRef.current   = null;
    showToastMsg('Nouvelle conversation');
  }, [showToastMsg]);

  /**
   * Supprime l'historique complet (backend + local)
   */
  const clearHistory = useCallback(async () => {
    if (!window.confirm("Voulez-vous supprimer tout votre historique ?")) return;
    const success = await deleteHistory();
    if (success) {
      localStorage.removeItem(LOCAL_HISTORY_KEY);
      setHistory([]);
      showToastMsg("Historique supprimé");
    } else {
      showToastMsg("Erreur lors de la suppression");
    }
  }, [showToastMsg]);

  // ── Feedback ─────────────────────────────────────────────────────────────

  const sendFeedback = useCallback(
    async ({ faqId, feedbackType, question, score, comment }) =>
      submitFeedback({
        faqId,
        feedbackType,
        question: question || lastUserQuestionRef.current,
        score,
        comment,
      }),
    []
  );

  // ── Envoi d'un message ───────────────────────────────────────────────────

  const sendMessage = useCallback(
    async (text) => {
      const question = text.trim();
      if (!question || isProcessing) return;

      setIsProcessing(true);
      userScrolledRef.current   = false;
      lastUserQuestionRef.current = question;

      // Message utilisateur
      const userMsg = { id: nextId(), role: 'user', content: question };
      setMessages((m) => [...m, userMsg]);
      scrollToBottom(true);

      // Bulle "en cours" du bot
      const botId = nextId();
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
      ]);

      // ── Entrée locale : créée dès le premier message de la session ────────
      // Si aucune entrée n'est encore en attente (nouvelle session), on en crée une.
      if (!pendingLocalIdRef.current) {
        const localId = addLocalHistoryEntry(question);
        pendingLocalIdRef.current = localId;
      } else {
        // Mise à jour du titre avec la question courante (la dernière question
        // est la plus représentative de la conversation en cours)
        updateLocalHistoryEntry(pendingLocalIdRef.current, question);
      }

      try {
        const result = await ask(question, {
          gen3Available,
          onEvent: (ev) => {
            if (ev.type === 'status') {
              setMessages((m) =>
                m.map((msg) =>
                  msg.id === botId ? { ...msg, statusLabel: ev.label } : msg
                )
              );
            } else if (ev.type === 'meta') {
              setMessages((m) =>
                m.map((msg) =>
                  msg.id === botId
                    ? { ...msg, status: 'streaming', statusLabel: null }
                    : msg
                )
              );
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
                    : msg
                )
              );
              scrollToBottom();
            }
          },
        });

        // Finalisation du message bot
        setMessages((m) =>
          m.map((msg) => {
            if (msg.id !== botId) return msg;

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
              };
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
              };
            }

            return {
              ...msg,
              status: 'done',
              statusLabel: null,
              content: result.text,
              mode: result.mode,
              userQuestion: question,
            };
          })
        );

        // Re-sync : le backend a peut-être créé un vrai thread ; on nettoie le local
        await refreshHistory();
        // Après refreshHistory, pendingLocalIdRef peut pointer vers une entrée
        // maintenant gérée côté backend — on le remet à null pour la prochaine session.
        pendingLocalIdRef.current = null;
      } catch {
        setMessages((m) =>
          m.map((msg) =>
            msg.id === botId
              ? {
                  ...msg,
                  status: 'error',
                  statusLabel: null,
                  content:
                    'Impossible de joindre le serveur. Vérifiez que le backend tourne sur le port 8001.',
                }
              : msg
          )
        );
        setServerStatus('offline');
        setPipelineLabel('Hors ligne');
        // L'entrée locale est déjà en place ; pas besoin de la recréer.
      } finally {
        setIsProcessing(false);
        scrollToBottom(true);
      }
    },
    [
      gen3Available,
      isProcessing,
      scrollToBottom,
      refreshHistory,
      addLocalHistoryEntry,
      updateLocalHistoryEntry,
    ]
  );

  // ── Chargement d'un thread existant ─────────────────────────────────────

  const loadThread = useCallback(
    async (threadId) => {
      // Thread local (pas de vrai ID backend) : on vide juste la vue
      if (String(threadId).startsWith('local-')) {
        setMessages([]);
        userScrolledRef.current   = false;
        lastUserQuestionRef.current = '';
        pendingLocalIdRef.current   = threadId; // on le reprend comme session en cours
        showToastMsg('Discussion locale chargée');
        return [];
      }

      try {
        const payload = await fetchThreadMessages(threadId);
        const msgs    = (Array.isArray(payload) ? payload : payload.messages ?? []).map(
          (m) => ({
            id: nextId(),
            role: m.role ?? (m.sender === 'user' ? 'user' : 'bot'),
            status: 'done',
            content: m.content ?? m.text ?? m.answer ?? '',
          })
        );

        setMessages(msgs);
        userScrolledRef.current   = false;
        pendingLocalIdRef.current   = null; // thread backend = plus besoin d'entrée locale
        scrollToBottom(true);

        const lastUser = [...msgs].reverse().find((x) => x.role === 'user');
        if (lastUser) lastUserQuestionRef.current = lastUser.content;

        return msgs;
      } catch (e) {
        showToastMsg('Erreur lors du chargement du thread');
        throw e;
      }
    },
    [scrollToBottom, showToastMsg]
  );

  // ── API publique ─────────────────────────────────────────────────────────

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
    history,
    refreshHistory,
    loadThread,
    clearHistory,
    listRef,
    sendMessage,
    resetChat,
    refreshHealth,
    sendFeedback,
    onListScroll,
    scrollToBottom: () => scrollToBottom(true),
    userScrolledRef,
    showToastMsg,
    lastUserQuestion: () => lastUserQuestionRef.current,
  };
}