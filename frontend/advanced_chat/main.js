// Detect API endpoint based on current location
// If frontend is served from ngrok, call backend via ngrok
// If frontend is served from local IP, use that IP for API
// Otherwise, use localhost for local development
const API_BASE = (() => {
  const host = window.location.hostname;

  // If on ngrok frontend, call backend via ngrok
  if (host.includes("ngrok-free.dev")) {
    return "https://patternable-felicitously-shaunta.ngrok-free.dev";
  }

  // If on Netlify, call backend via Railway
  if (host.includes("netlify.app")) {
    return "https://chatbot-production-5202.up.railway.app";
  }

  // Network IP detected, use same IP for API
  if (host.includes("192.168") || host.includes("10.")) {
    return `http://${host}:8001`;
  }

  // Local development
  return "http://localhost:8001";
})();

const API_URL = `${API_BASE}/api/chatbot/ask/`;
const API_V2_URL = `${API_BASE}/api/v2/chatbot/ask/`;
const API_HEALTH_URL = `${API_BASE}/api/health/`;
const API_FEEDBACK_URL = `${API_BASE}/api/feedback/`;
const API_STATS_URL = `${API_BASE}/api/stats/`;

const STATUS_LABELS = {
  thinking: "Réflexion en cours",
  searching: "Recherche dans la base de connaissances",
  generating: "Génération de la réponse",
};

// Seuils de confiance pour les réponses (0-1)
const CONFIDENCE_THRESHOLD_LOW = 0.5;   // En dessous: aucune réponse
const CONFIDENCE_THRESHOLD_MED = 0.7;   // Entre 0.5-0.7: suggestion

// Éléments du DOM
const thread = document.getElementById("thread");
const form = document.getElementById("composer");
const input = document.getElementById("input");
const sendBtn = document.getElementById("send");
const toast = document.getElementById("toast");
const suggestionsGrid = document.getElementById("suggestions");
const welcomeSection = document.getElementById("welcome-section");
const connectionStatus = document.getElementById("connection-status");
const statusDot = document.querySelector(".status-dot");
const pipelineBadge = document.getElementById("pipeline-badge");
const charCounter = document.getElementById("char-counter");
const scrollBottomBtn = document.getElementById("scroll-bottom-btn");
const newChatBtn = document.getElementById("new-chat-btn");

// État de l'application
let isProcessing = false;
let gen3Available = false;
let questionCount = 0;
let lastUserQuestion = "";
let hasAskedQuestion = false;
let activeFeedbackStates = new Map();
let userHasScrolledManually = false; // Flag pour détecter si l'utilisateur a scrollé manuellement
let scrollTimeout = null; // Timeout pour réinitialiser le flag

/**
 * Affiche un toast de notification
 */
function showToast(msg, duration = 3000) {
  toast.textContent = msg;
  toast.classList.add("show");
  setTimeout(() => {
    toast.classList.remove("show");
  }, duration);
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

function formatMessageHtml(text) {
  return escapeHtml(text).replace(/\n/g, "<br>");
}

function updateCharCounter() {
  if (!charCounter) return;
  const len = input.value.length;
  charCounter.textContent = `${len} / 500`;
  charCounter.classList.toggle("near-limit", len > 450);
}

function setConnectionState(online, label) {
  if (connectionStatus) connectionStatus.textContent = label;
  if (statusDot) {
    statusDot.style.background = online ? "var(--success)" : "var(--warning)";
  }
}

function setPipelineBadge(label) {
  if (pipelineBadge) pipelineBadge.textContent = label;
}

async function checkBackendHealth() {
  try {
    const res = await fetch(API_HEALTH_URL, { signal: AbortSignal.timeout(5000) });
    if (!res.ok) throw new Error("health failed");
    const data = await res.json();
    gen3Available = Boolean(data.gen3?.available);
    setConnectionState(true, gen3Available ? "En ligne · IA avancée" : "En ligne");
    setPipelineBadge(gen3Available ? "Pipeline IA" : "FAQ intelligente");
    return data;
  } catch {
    gen3Available = false;
    setConnectionState(false, "Hors ligne");
    setPipelineBadge("Mode local");
    return null;
  }
}

function createStatusBubble(initialText = "Réflexion en cours") {
  const bubble = appendBubble(
    `<div class="status-line"><span class="typing-dots"><span></span><span></span><span></span></span> <span class="status-text">${escapeHtml(initialText)}</span></div>`,
    "bot",
  );
  bubble.classList.add("status-bubble");
  return bubble;
}

function updateStatusBubble(bubble, text) {
  const el = bubble?.querySelector(".status-text");
  if (el) el.textContent = text;
}

function removeStatusBubble(bubble) {
  bubble?.remove();
}

function showScrollBottomIfNeeded() {
  if (!scrollBottomBtn) return;
  scrollBottomBtn.hidden = isUserAtBottom();
}

function resetConversation() {
  const keepWelcome = `
    <div class="welcome-message" id="welcome-section">
      <div class="welcome-icon"><i class="bi bi-chat-heart-fill"></i></div>
      <h2>Bienvenue sur SUP'ONE AI</h2>
      <p>Votre assistant pour l'histoire, les admissions, la vie étudiante et bien plus.</p>
    </div>
    <div class="suggestions-grid" id="suggestions"></div>`;
  thread.innerHTML = keepWelcome;
  hasAskedQuestion = false;
  userHasScrolledManually = false;
  activeFeedbackStates.clear();
  loadDynamicSuggestions();
  input.focus();
  showToast("Nouvelle conversation");
}

/**
 * Gestion de la modal de profil
 */
function openProfileModal() {
  const modal = document.getElementById("profile-modal");
  if (modal) {
    console.log("[Profile] Ouverture de la modal");
    modal.classList.add("show");
    document.body.style.overflow = "hidden";
  }
}

function closeProfileModal() {
  const modal = document.getElementById("profile-modal");
  if (modal) {
    console.log("[Profile] Fermeture de la modal");
    modal.classList.remove("show");
    document.body.style.overflow = "";
  }
}

/**
 * Initialiser les événements de la modal de profil
 */
function initProfileModal() {
  const modal = document.getElementById("profile-modal");
  const toggleBtn = document.getElementById("profile-toggle");
  const closeBtn = document.getElementById("close-profile-btn");
  
  console.log("[Profile] Initialisation", { modal: !!modal, toggleBtn: !!toggleBtn, closeBtn: !!closeBtn });
  
  // Bouton d'ouverture
  if (toggleBtn) {
    toggleBtn.addEventListener("click", (e) => {
      e.preventDefault();
      e.stopPropagation();
      console.log("[Profile] Clic sur bouton profil");
      openProfileModal();
    });
  }
  
  // Bouton de fermeture X
  if (closeBtn) {
    closeBtn.addEventListener("click", (e) => {
      e.preventDefault();
      e.stopPropagation();
      console.log("[Profile] Clic sur bouton fermer");
      closeProfileModal();
    });
  }
  
  // Fermer en cliquant sur l'overlay
  if (modal) {
    modal.addEventListener("click", (e) => {
      if (e.target === modal) {
        console.log("[Profile] Clic sur overlay");
        closeProfileModal();
      }
    });
    
    // Empêcher la fermeture en cliquant sur le contenu
    const modalContent = modal.querySelector(".profile-modal");
    if (modalContent) {
      modalContent.addEventListener("click", (e) => {
        e.stopPropagation();
      });
    }
  }
  
  // Fermer avec la touche Échap
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && modal && modal.classList.contains("show")) {
      console.log("[Profile] Fermeture avec Échap");
      closeProfileModal();
    }
  });
}

/**
 * Charge les suggestions dynamiques depuis l'API feedback (top 3 feedbacks positifs)
 */
async function loadDynamicSuggestions() {
  const grid = document.getElementById("suggestions");
  if (!grid) return;
  try {
    const response = await fetch(API_STATS_URL);
    if (!response.ok) {
      console.warn("Impossible de charger les suggestions dynamiques");
      loadDefaultSuggestions();
      return;
    }

    const data = await response.json();

    // Trier par nombre de feedbacks positifs (count) et prendre les 3 meilleurs
    const positiveFeedbacks = data
      .filter((item) => item.count >= 0)
      .sort((a, b) => b.count - a.count)
      .slice(0, 3);

    if (positiveFeedbacks.length === 0) {
      loadDefaultSuggestions();
      return;
    }

    grid.innerHTML = positiveFeedbacks
      .map((item, index) => {
        const icons = ["bi-star-fill", "bi-heart-fill", "bi-lightbulb-fill"];
        const icon = icons[index] || "bi-chat-dots-fill";
        return `
          <button class="suggestion-card" data-question="${item.question}">
            <span class="suggestion-icon"><i class="bi ${icon}"></i></span>
            <span class="suggestion-text">${item.question}</span>
          </button>
        `;
      })
      .join("");

    attachSuggestionListeners();
  } catch (error) {
    console.error("Erreur lors du chargement des suggestions:", error);
    loadDefaultSuggestions();
  }
}

/**
 * Charge les suggestions par défaut si l'API échoue
 */
function loadDefaultSuggestions() {
  const grid = document.getElementById("suggestions");
  if (!grid) return;
  grid.innerHTML = `
    <button class="suggestion-card" data-question="Quelle est l'histoire de SUP'ONE ?">
      <span class="suggestion-icon"><i class="bi bi-book"></i></span>
      <span class="suggestion-text">Quelle est l'histoire de SUP'ONE ?</span>
    </button>
    <button class="suggestion-card" data-question="Comment louer une chambre universitaire ?">
      <span class="suggestion-icon"><i class="bi bi-house"></i></span>
      <span class="suggestion-text">Comment louer une chambre universitaire ?</span>
    </button>
    <button class="suggestion-card" data-question="Quels sont les clubs disponibles ?">
      <span class="suggestion-icon"><i class="bi bi-bullseye"></i></span>
      <span class="suggestion-text">Quels sont les clubs disponibles ?</span>
    </button>
  `;
  attachSuggestionListeners();
}

/**
 * Attache les événements de clic aux suggestions
 */
function attachSuggestionListeners() {
  const grid = document.getElementById("suggestions");
  if (!grid) return;
  const suggestionCards = grid.querySelectorAll(".suggestion-card");
  suggestionCards.forEach((card) => {
    card.addEventListener("click", () => {
      const question = card.getAttribute("data-question");
      if (question && !isProcessing) {
        input.value = question;
        if (input.value.trim().length > 0) sendBtn.classList.add("has-text");
        setTimeout(() => form.requestSubmit(), 100);
      }
    });
  });
}

/**
 * Vérifie si l'utilisateur est en bas du scroll
 */
function isUserAtBottom() {
  const threshold = 150; // Augmenté pour plus de tolérance
  return (
    thread.scrollHeight - thread.scrollTop - thread.clientHeight < threshold
  );
}

/**
 * Scroll vers le bas SEULEMENT si l'utilisateur n'a pas scrollé manuellement
 */
function autoScrollIfNeeded() {
  // Ne pas scroller si l'utilisateur a pris le contrôle du scroll
  if (userHasScrolledManually) {
    return;
  }
  
  requestAnimationFrame(() => {
    thread.scrollTo({ top: thread.scrollHeight, behavior: "smooth" });
  });
}

/**
 * Ajoute une bulle de message dans le thread
 */
function appendBubble(text, who = "bot") {
  const bubble = document.createElement("div");
  bubble.className = `bubble ${who}`;
  bubble.innerHTML = text;

  const wasAtBottom = isUserAtBottom();
  thread.appendChild(bubble);

  // Auto-scroll SEULEMENT si l'utilisateur était en bas ET n'a pas scrollé manuellement
  if (wasAtBottom && !userHasScrolledManually) {
    autoScrollIfNeeded();
  }

  return bubble;
}

/**
 * Animation de frappe (typing effect)
 * @param {HTMLElement} element - L'élément où afficher le texte
 * @param {string} text - Le texte à afficher
 * @param {number} speed - Vitesse en ms par caractère
 */
async function typeText(element, text, speed = 20) {
  element.textContent = ""; // Vider l'élément (textContent pour éviter problèmes HTML)
  let index = 0;

  return new Promise((resolve) => {
    const interval = setInterval(() => {
      if (index < text.length) {
        element.textContent += text.charAt(index);
        index++;

        // Auto-scroll pendant la frappe SEULEMENT si l'utilisateur n'a pas scrollé manuellement
        if (isUserAtBottom() && !userHasScrolledManually) {
          autoScrollIfNeeded();
        }
      } else {
        clearInterval(interval);
        resolve();
      }
    }, speed);
  });
}

/**
 * Animation de frappe pour HTML (typing effect avec HTML)
 * @param {HTMLElement} element - L'élément où afficher le HTML
 * @param {string} htmlContent - Le contenu HTML à afficher
 * @param {number} speed - Vitesse en ms par caractère
 */
async function typeHTML(element, htmlContent, speed = 20) {
  element.innerHTML = "";
  
  // Créer un conteneur temporaire pour parser le HTML
  const tempDiv = document.createElement('div');
  tempDiv.innerHTML = htmlContent;
  
  let currentIndex = 0;
  const fullText = tempDiv.textContent || tempDiv.innerText;
  
  return new Promise((resolve) => {
    const interval = setInterval(() => {
      if (currentIndex < fullText.length) {
        currentIndex++;
        const displayText = fullText.substring(0, currentIndex);
        
        // Reconstruire le HTML avec le texte partiel
        let result = htmlContent;
        let textSoFar = 0;
        
        // Remplacer progressivement le contenu
        element.innerHTML = htmlContent.replace(/<strong>"([^"]+)"<\/strong>/, (match, p1) => {
          const beforeStrong = fullText.indexOf(p1);
          if (currentIndex <= beforeStrong) {
            // Pas encore arrivé au strong
            return '';
          } else if (currentIndex < beforeStrong + p1.length) {
            // On est dans le strong
            const partialStrong = p1.substring(0, currentIndex - beforeStrong);
            return `<strong>"${partialStrong}"</strong>`;
          } else {
            // Strong complet
            return match;
          }
        });
        
        // Méthode plus simple : afficher progressivement en remplaçant le texte dans le HTML
        const regex = /^(.*?)<strong>"([^"]+)"<\/strong>(.*)$/;
        const parts = htmlContent.match(regex);
        
        if (parts) {
          const before = parts[1];
          const strongText = parts[2];
          const after = parts[3];
          
          if (currentIndex <= before.length) {
            element.innerHTML = displayText;
          } else if (currentIndex <= before.length + strongText.length) {
            const strongPart = displayText.substring(before.length, currentIndex);
            element.innerHTML = before + '<strong>"' + strongPart + '"</strong>';
          } else {
            const afterPart = displayText.substring(before.length + strongText.length);
            element.innerHTML = before + '<strong>"' + strongText + '"</strong>' + afterPart;
          }
        } else {
          element.textContent = displayText;
        }

        // Auto-scroll pendant la frappe SEULEMENT si l'utilisateur n'a pas scrollé manuellement
        if (isUserAtBottom() && !userHasScrolledManually) {
          autoScrollIfNeeded();
        }
      } else {
        clearInterval(interval);
        element.innerHTML = htmlContent; // S'assurer que le HTML final est correct
        resolve();
      }
    }, speed);
  });
}

/**
 * Masque la section de bienvenue et les suggestions
 */
function hideWelcomeAndSuggestions() {
  if (!hasAskedQuestion) {
    hasAskedQuestion = true;
    const welcome = document.getElementById("welcome-section");
    const suggestions = document.getElementById("suggestions");

    if (welcome) {
      welcome.style.opacity = "0";
      welcome.style.transform = "translateY(-10px)";
      setTimeout(() => { welcome.style.display = "none"; }, 300);
    }

    if (suggestions) {
      suggestions.style.opacity = "0";
      suggestions.style.transform = "translateY(10px)";
      setTimeout(() => { suggestions.classList.add("hidden"); }, 300);
    }
  }
}

/**
 * Crée le HTML pour une réponse avec faible confiance (< 0.5)
 */
function createNoAnswerResponseText() {
  return "Je n'ai pas trouvé d'information précise concernant votre question dans la FAQ.";
}

/**
 * Crée le HTML pour une réponse avec confiance moyenne (0.5-0.7)
 */
function createMediumConfidenceResponse(topResult) {
  const questionText = topResult.question || "";
  // Enlever le ? à la fin de la question s'il existe
  const cleanQuestion = questionText.endsWith('?') ? questionText.slice(0, -1) : questionText;
  return `Je ne suis pas totalement sûr, mais vouliez-vous peut-être demander : <strong>"${cleanQuestion}"</strong> ?`;
}

/**
 * Attache les événements de feedback à tous les boutons
 */
function attachFeedbackListeners() {
  const feedbackButtons = thread.querySelectorAll(".feedback-btn");
  feedbackButtons.forEach((btn) => {
    // Retirer les anciens listeners pour éviter les doublons
    btn.replaceWith(btn.cloneNode(true));
  });

  // Réattacher les nouveaux listeners
  const newButtons = thread.querySelectorAll(".feedback-btn");
  newButtons.forEach((btn) => {
    btn.addEventListener("click", () => handleFeedbackClick(btn));
  });
}

/**
 * Pipeline Gen3 — réponse en streaming SSE
 */
async function askViaGen3(question, statusBubble) {
  const response = await fetch(API_V2_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
    body: JSON.stringify({ question, stream: true }),
  });

  if (!response.ok) throw new Error(`Gen3 HTTP ${response.status}`);

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let answerBubble = null;
  let fullAnswer = "";
  let method = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";

    for (const line of lines) {
      if (!line.startsWith("data: ")) continue;
      let payload;
      try {
        payload = JSON.parse(line.slice(6));
      } catch {
        continue;
      }

      if (payload.type === "status" && payload.status) {
        updateStatusBubble(statusBubble, STATUS_LABELS[payload.status] || payload.status);
      } else if (payload.type === "meta") {
        method = payload.method || "";
        removeStatusBubble(statusBubble);
        answerBubble = appendBubble("", "bot");
        if (method) {
          answerBubble.insertAdjacentHTML(
            "beforeend",
            `<div class="pipeline-tag"><i class="bi bi-cpu"></i> ${escapeHtml(method)}</div>`,
          );
        }
      } else if (payload.type === "token" && payload.content) {
        if (!answerBubble) {
          removeStatusBubble(statusBubble);
          answerBubble = appendBubble("", "bot");
        }
        fullAnswer += payload.content;
        let contentEl = answerBubble.querySelector(".stream-content");
        if (!contentEl) {
          contentEl = document.createElement("div");
          contentEl.className = "stream-content";
          answerBubble.appendChild(contentEl);
        }
        contentEl.innerHTML = formatMessageHtml(fullAnswer);
        autoScrollIfNeeded();
      } else if (payload.type === "error") {
        throw new Error(payload.message || "Erreur pipeline");
      }
    }
  }

  if (!answerBubble && !fullAnswer) throw new Error("Réponse vide");
  return { method, answer: fullAnswer };
}

/**
 * Pipeline Phase 1 — FAQ TF-IDF avec seuils de confiance
 */
async function askViaPhase1(question, statusBubble) {
  updateStatusBubble(statusBubble, "Recherche dans la FAQ...");

  const response = await fetch(API_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify({ question, top_k: 1 }),
  });

  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  const data = await response.json();
  removeStatusBubble(statusBubble);

  const topResult = data.results && data.results[0];
  const confidence = topResult ? Number(topResult.score) : 0;

  if (confidence < CONFIDENCE_THRESHOLD_LOW) {
    const lowConfBubble = appendBubble("", "bot");
    await typeText(lowConfBubble, createNoAnswerResponseText(), 10);
    lowConfBubble.insertAdjacentHTML(
      "beforeend",
      `<div class="low-confidence-actions"><ul>
        <li><i class="bi bi-arrow-repeat"></i> Reformuler votre question</li>
        <li><i class="bi bi-envelope"></i> Contacter le support SUP'ONE</li>
        <li><i class="bi bi-book"></i> Consulter la FAQ complète</li>
      </ul></div>`,
    );
  } else if (confidence < CONFIDENCE_THRESHOLD_MED) {
    const medConfBubble = appendBubble("", "bot");
    await typeHTML(medConfBubble, createMediumConfidenceResponse(topResult), 10);
  } else {
    const botBubble = appendBubble("", "bot");
    botBubble.setAttribute("data-faq-id", topResult.faq_id);
    botBubble.innerHTML = `<div class="result-question"><i class="bi bi-pin-angle-fill"></i> ${escapeHtml(topResult.question)}</div>`;
    await new Promise((r) => setTimeout(r, 200));
    botBubble.insertAdjacentHTML("beforeend", `<div class="result-answer"></div>`);
    await typeText(botBubble.querySelector(".result-answer"), topResult.answer, 10);

    const categoryText = topResult.category || "";
    const scoreText = Number(topResult.score).toFixed(2);
    const faqId = topResult.faq_id || "";
    botBubble.insertAdjacentHTML(
      "beforeend",
      `<div class="result-meta">
        <span><i class="bi bi-tags"></i> ${escapeHtml(categoryText)}</span>
        <span><i class="bi bi-star-fill"></i> Score: ${scoreText}</span>
      </div>
      <div class="feedback">
        <button class="feedback-btn up" aria-label="like" data-faq-id="${faqId}"><i class="bi bi-hand-thumbs-up"></i></button>
        <button class="feedback-btn down" aria-label="dislike" data-faq-id="${faqId}"><i class="bi bi-hand-thumbs-down"></i></button>
        <button class="feedback-btn copy" aria-label="copy" data-faq-id="${faqId}"><i class="bi bi-clipboard"></i></button>
        <button class="feedback-btn share" aria-label="share" data-faq-id="${faqId}"><i class="bi bi-share"></i></button>
      </div>`,
    );
    attachFeedbackListeners();
  }
}

/**
 * Envoie une question — Gen3 si disponible, sinon Phase 1
 */
async function ask(question) {
  if (isProcessing) return;

  isProcessing = true;
  sendBtn.disabled = true;
  hideWelcomeAndSuggestions();
  lastUserQuestion = question.trim();
  questionCount += 1;

  const statQuestions = document.getElementById("stat-questions");
  if (statQuestions) statQuestions.textContent = String(questionCount);

  appendBubble(escapeHtml(question), "user");
  const statusBubble = createStatusBubble();
  const startTime = Date.now();

  try {
    if (gen3Available) {
      try {
        await askViaGen3(question, statusBubble);
      } catch {
        gen3Available = false;
        setPipelineBadge("FAQ intelligente");
        await askViaPhase1(question, statusBubble);
      }
    } else {
      await askViaPhase1(question, statusBubble);
    }
  } catch (error) {
    console.error("Erreur lors de la requête:", error);
    removeStatusBubble(statusBubble);
    const errorBubble = appendBubble("", "bot");
    await typeText(
      errorBubble,
      "Impossible de joindre le serveur. Vérifiez que le backend est démarré, puis réessayez.",
      10,
    );
    setConnectionState(false, "Hors ligne");
  } finally {
    const elapsed = Date.now() - startTime;
    if (elapsed < 600) await new Promise((r) => setTimeout(r, 600 - elapsed));
    isProcessing = false;
    sendBtn.disabled = false;
    input.focus();
    showScrollBottomIfNeeded();
  }
}

/**
 * Gère les clics sur les boutons de feedback (like, dislike, copy, share)
 */
async function handleFeedbackClick(btn) {
  const faqId = btn.getAttribute("data-faq-id");
  const isUp = btn.classList.contains("up");
  const isDown = btn.classList.contains("down");
  const isCopy = btn.classList.contains("copy");
  const isShare = btn.classList.contains("share");

  // Trouver la bulle bot (qui contient data-faq-id maintenant)
  const botBubble = btn.closest('.bubble.bot');

  // Copier
  if (isCopy) {
    if (botBubble) {
      const question =
        botBubble.querySelector(".result-question")?.textContent || "";
      const answer =
        botBubble.querySelector(".result-answer")?.textContent || "";
      const textToCopy = `${question}\n\n${answer}`;

      try {
        await navigator.clipboard.writeText(textToCopy);
        showToast("Réponse copiée !");
        btn.classList.add("active");
        setTimeout(() => btn.classList.remove("active"), 1000);
      } catch (err) {
        showToast("Erreur lors de la copie");
      }
    }
    return;
  }

  // Partager
  if (isShare) {
    if (botBubble) {
      const question =
        botBubble.querySelector(".result-question")?.textContent || "";
      const answer =
        botBubble.querySelector(".result-answer")?.textContent || "";
      const shareText = `${question}\n\n${answer}`;

      if (navigator.share) {
        try {
          await navigator.share({ text: shareText });
          btn.classList.add("active");
          setTimeout(() => btn.classList.remove("active"), 1000);
        } catch (err) {
          console.log("Partage annulé");
        }
      } else {
        await navigator.clipboard.writeText(shareText);
        showToast("Lien copié !");
        btn.classList.add("active");
        setTimeout(() => btn.classList.remove("active"), 1000);
      }
    }
    return;
  }

  // Gestion exclusive des boutons like/dislike
  if (isUp || isDown) {
    const currentState = activeFeedbackStates.get(faqId);
    const feedback = btn.closest(".feedback");
    const upBtn = feedback.querySelector(".feedback-btn.up");
    const downBtn = feedback.querySelector(".feedback-btn.down");

    // Si on clique sur le même bouton déjà actif, on le désactive
    if (currentState === (isUp ? "up" : "down")) {
      btn.classList.remove("active");
      activeFeedbackStates.delete(faqId);
      upBtn.classList.remove("disabled");
      downBtn.classList.remove("disabled");
      return;
    }

    // Désactiver l'autre bouton et activer celui-ci
    if (isUp) {
      upBtn.classList.add("active");
      downBtn.classList.remove("active");
      downBtn.classList.add("disabled");
      activeFeedbackStates.set(faqId, "up");
      await sendFeedback(faqId, "positif", null);
    } else {
      downBtn.classList.add("active");
      upBtn.classList.remove("active");
      upBtn.classList.add("disabled");
      activeFeedbackStates.set(faqId, "down");
      showNegativeFeedbackModal(faqId);
    }
  }
}

/**
 * Envoie le feedback à l'API
 */
async function sendFeedback(faqId, feedbackType, comment = null) {
  try {
    const payload = {
      faq: faqId,
      feedback_type: feedbackType,
      question_utilisateur: lastUserQuestion,
      score_similarite: 0,
      comment: comment || "",
    };

    const response = await fetch(API_FEEDBACK_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify(payload),
    });

    if (response.ok) {
      showToast(
        feedbackType === "positif"
          ? "Merci pour votre feedback positif !"
          : "Merci pour votre feedback !",
        2000,
      );
    }
  } catch (error) {
    console.error("Erreur lors de l'envoi du feedback:", error);
  }
}

/**
 * Affiche le modal de feedback négatif
 */
function showNegativeFeedbackModal(faqId) {
  const suggestions = [
    "Réponse incorrecte",
    "Réponse incomplète",
    "Pas assez détaillée",
    "Hors sujet",
  ];

  const suggestionsHTML = suggestions
    .map(
      (s) =>
        `<button class="suggestion-btn" data-suggestion="${s}">${s}</button>`,
    )
    .join("");

  const formHTML = `
    <div class="feedback-modal-overlay" id="modal-overlay-${faqId}">
      <div class="feedback-modal">
        <form id="feedback-form-${faqId}" class="feedback-form">
          <h3>Aidez-nous à nous améliorer</h3>
          <p>Qu'est-ce qui n'allait pas avec cette réponse ?</p>
          <div class="suggestions-container">
            ${suggestionsHTML}
          </div>
          <textarea 
            id="feedback-text-${faqId}" 
            placeholder="Votre commentaire personnel..." 
            maxlength="500" 
            rows="4"></textarea>
          <label class="anon-label">
            <input type="checkbox" id="anon-${faqId}" checked>
            Envoyer en tant qu'anonyme
          </label>
          <div class="modal-actions">
            <button type="button" class="btn-cancel">Annuler</button>
            <button type="submit" class="btn-submit">Envoyer</button>
          </div>
        </form>
      </div>
    </div>
  `;

  document.body.insertAdjacentHTML("beforeend", formHTML);

  const overlay = document.getElementById(`modal-overlay-${faqId}`);
  const form = document.getElementById(`feedback-form-${faqId}`);
  const cancelBtn = form.querySelector(".btn-cancel");
  const textarea = document.getElementById(`feedback-text-${faqId}`);
  const suggestionBtns = form.querySelectorAll(".suggestion-btn");

  suggestionBtns.forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.preventDefault();
      const suggestion = btn.getAttribute("data-suggestion");
      textarea.value = suggestion;
      btn.style.backgroundColor = "#3b82f6";
      btn.style.color = "white";
      suggestionBtns.forEach((b) => {
        if (b !== btn) {
          b.style.backgroundColor = "";
          b.style.color = "";
        }
      });
    });
  });

  cancelBtn.addEventListener("click", () => {
    overlay.remove();
    const feedback = document
      .querySelector(`.feedback-btn.down[data-faq-id="${faqId}"]`)
      ?.closest(".feedback");
    if (feedback) {
      const upBtn = feedback.querySelector(".feedback-btn.up");
      const downBtn = feedback.querySelector(".feedback-btn.down");
      downBtn.classList.remove("active");
      upBtn.classList.remove("disabled");
      activeFeedbackStates.delete(faqId);
    }
  });

  overlay.addEventListener("click", (e) => {
    if (e.target === overlay) {
      overlay.remove();
      const feedback = document
        .querySelector(`.feedback-btn.down[data-faq-id="${faqId}"]`)
        ?.closest(".feedback");
      if (feedback) {
        const upBtn = feedback.querySelector(".feedback-btn.up");
        const downBtn = feedback.querySelector(".feedback-btn.down");
        downBtn.classList.remove("active");
        upBtn.classList.remove("disabled");
        activeFeedbackStates.delete(faqId);
      }
    }
  });

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const comment = textarea.value;
    await sendFeedback(faqId, "negatif", comment || "Réponse peu utile");
    overlay.remove();
  });
}

/**
 * Détecte quand l'utilisateur scroll manuellement pour désactiver l'auto-scroll
 */
thread.addEventListener('scroll', () => {
  showScrollBottomIfNeeded();
  if (!isUserAtBottom()) {
    userHasScrolledManually = true;
    
    // Réinitialiser le flag après 2 secondes d'inactivité
    if (scrollTimeout) {
      clearTimeout(scrollTimeout);
    }
    scrollTimeout = setTimeout(() => {
      // Réactiver l'auto-scroll après 2s d'inactivité, peu importe la position
      userHasScrolledManually = false;
    }, 2000);
  } else {
    // Si l'utilisateur est en bas, réactiver l'auto-scroll immédiatement
    userHasScrolledManually = false;
    if (scrollTimeout) {
      clearTimeout(scrollTimeout);
      scrollTimeout = null;
    }
  }
});

/**
 * Réinitialiser le flag de scroll manuel à chaque nouvelle question
 */
form.addEventListener("submit", (e) => {
  e.preventDefault();
  const question = input.value.trim();
  if (!question || isProcessing) return;

  // Réinitialiser le flag pour permettre l'auto-scroll sur la nouvelle réponse
  userHasScrolledManually = false;
  if (scrollTimeout) {
    clearTimeout(scrollTimeout);
    scrollTimeout = null;
  }

  ask(question);
  input.value = "";
  sendBtn.classList.remove("has-text");
});

/**
 * Gestion des touches du clavier
 */
input.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    if (input.value.trim() && !isProcessing) {
      form.requestSubmit();
    }
  }
});

/**
 * Mise à jour du bouton d'envoi
 */
input.addEventListener("input", () => {
  if (input.value.trim().length > 0) {
    sendBtn.classList.add("has-text");
  } else {
    sendBtn.classList.remove("has-text");
  }
  updateCharCounter();
});

if (newChatBtn) {
  newChatBtn.addEventListener("click", () => {
    if (!isProcessing) resetConversation();
  });
}

if (scrollBottomBtn) {
  scrollBottomBtn.addEventListener("click", () => {
    userHasScrolledManually = false;
    thread.scrollTo({ top: thread.scrollHeight, behavior: "smooth" });
    scrollBottomBtn.hidden = true;
  });
}

/**
 * Initialisation au chargement
 */
window.addEventListener("load", async () => {
  input.focus();
  updateCharCounter();
  await checkBackendHealth();
  loadDynamicSuggestions();
  initProfileModal();
});

/**
 * Gestion des erreurs globales
 */
window.addEventListener("error", (e) => {
  console.error("Erreur globale:", e.error);
});

window.addEventListener("unhandledrejection", (e) => {
  console.error("Promise rejetée:", e.reason);
});