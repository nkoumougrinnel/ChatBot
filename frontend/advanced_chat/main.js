/**
 * SUP'ONE AI - Advanced Chat Engine
 * Architecture: State-Driven Vanilla JS
 * Features: Auth Gate, Sidebar History, Streaming Gen3, Offline Overlay, Modular API
 */

console.log("SUP'ONE AI Engine v2.0 - Initialized");
console.log("SUP'ONE AI Engine v2.0 - UI/UX Reloaded");

import { AuthManager } from './auth.js'; // Assuming modularization for production
import { fetchHealth, fetchStats, fetchAskV1, fetchAskV2Stream, sendFeedbackApi, loginUser, signupUser } from './api.js';

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
const offlineScreen = document.getElementById("offline-screen");
const authModal = document.getElementById("auth-modal");
const menuBtn = document.getElementById("menu-btn");
const sidebar = document.getElementById("sidebar");
const closeSidebarBtn = document.getElementById("close-sidebar");

// Nouveaux éléments pour les stats
const statsContainer = document.getElementById("stats-container");
const showStatsBtn = document.getElementById("show-stats-btn");
const closeStatsBtn = document.getElementById("close-stats");
const statsContent = document.getElementById("stats-content");
const statsPanel = document.getElementById("stats-panel");

const state = {
  isProcessing: false,
  isOnline: true,
  gen3Available: false,
  activeFeedback: new Map(),
  user: null
};

let hasAskedQuestion = false;
let userHasScrolledManually = false;

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
/**
 * Modernized Connectivity Handling
 */
function toggleOfflineOverlay(isOffline) {
  if (!offlineScreen) return;
  state.isOnline = !isOffline;
  offlineScreen.style.display = isOffline ? "flex" : "none";
  form.querySelectorAll("input, button").forEach(el => el.disabled = isOffline);
}

async function checkBackendHealth() {
  try {
    const data = await fetchHealth();
    state.gen3Available = Boolean(data.gen3?.available);
    setConnectionState(true, state.gen3Available ? "En ligne · IA avancée" : "En ligne");
    setPipelineBadge(state.gen3Available ? "Pipeline IA" : "FAQ intelligente");
    toggleOfflineOverlay(false);
    return data;
  } catch (error) {
    console.error("Backend health check failed:", error);
    state.gen3Available = false;
    setConnectionState(false, "Hors ligne");
    setPipelineBadge("Mode local");
    toggleOfflineOverlay(true);
    // Optionally show a toast or other UI feedback for health check failure
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
      <h2>Comment puis-je vous aider aujourd'hui ?</h2>
    </div>
    <div class="suggestions-grid" id="suggestions"></div>`;
  thread.innerHTML = keepWelcome;
  hasAskedQuestion = false;
  userHasScrolledManually = false;
  state.activeFeedback.clear();
  loadDynamicSuggestions();
  input.focus();
  showToast("Nouvelle conversation");
}

/**
 * AUTHENTICATION SYSTEM
 */
function handleAuthGate() {
  const token = localStorage.getItem('access_token');
  if (!token) {
    openAuthModal();
    return false;
  }
  return true;
}

function openAuthModal() {
  if (authModal) {
    authModal.classList.add("show");
    // Toggle between Login/Signup forms logic here
  }
}

async function handleLogin(email, password) {
  try {
    const userData = await loginUser(email, password);
    state.user = userData.user; // Assuming API returns user data
    localStorage.setItem('access_token', userData.access); // Store JWT
    // Hide modal, show success toast, update UI
    console.log("Login successful:", userData);
    showToast("Connexion réussie !");
    // closeAuthModal(); // Implement this function
  } catch (error) {
    console.error("Login failed:", error.message);
    showToast(`Erreur de connexion: ${error.message}`);
  }
}

async function handleSignUp(name, email, password) {
  try {
    const userData = await signupUser(name, email, password);
    console.log("Signup successful:", userData);
    showToast("Compte créé avec succès ! Veuillez vous connecter.");
  } catch (error) {
    console.error("Signup failed:", error.message);
    showToast(`Erreur d'inscription: ${error.message}`);
  }
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
    const data = await fetchStats();

    // If fetchStats throws an error, it will be caught, so no need for response.ok check here.
    // If data is empty or malformed, handle it.
    if (!data || data.length === 0) throw new Error("No dynamic suggestions data");

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
    // This catch block handles errors from fetchStats and the custom "No dynamic suggestions data" error
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
      if (question && !state.isProcessing) {
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
 * Bascule l'affichage du panel de statistiques
 */
function toggleStatsPanel() {
  if (!statsPanel) return;
  const isShowing = statsPanel.classList.toggle("show");
  statsContainer.style.display = isShowing ? "flex" : "block"; 
  if (isShowing) loadStats();
}

/**
 * Charge les statistiques depuis l'API
 */
async function loadStats() {
  if (!statsContent) return;
  statsContent.innerHTML = '<div class="loader">Chargement...</div>';
  try {
    const data = await fetchStats();
    displayStats(data);
  } catch (error) {
    console.error("Erreur stats:", error);
    statsContent.innerHTML = `<p class="error">Erreur lors du chargement des statistiques.</p>`;
  }
}

/**
 * Affiche les statistiques dans le tableau
 */
function displayStats(stats) {
  if (!stats || stats.length === 0) {
    statsContent.innerHTML = "<p>Aucune donnée disponible.</p>";
    return;
  }

  const rows = stats.map(item => {
    const score = Number(item.avg_score || 0);
    let badgeClass = "score-poor";
    if (score >= 0.7) badgeClass = "score-good";
    else if (score >= 0.4) badgeClass = "score-medium";

    return `
      <tr>
        <td>${escapeHtml(item.question)}</td>
        <td><span class="score-badge ${badgeClass}">${(score * 100).toFixed(0)}%</span></td>
        <td>${item.count}</td>
      </tr>
    `;
  }).join("");

  statsContent.innerHTML = `
    <table>
      <thead><tr><th>Question</th><th>Score Moyen</th><th>Feedbacks</th></tr></thead>
      <tbody>${rows}</tbody>
    </table>
  `;
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
  let answerBubble = null;
  let fullAnswer = "";
  let method = "";

  await fetchAskV2Stream(
    question,
    (status) => updateStatusBubble(statusBubble, STATUS_LABELS[status] || status),
    (token) => {
      if (!answerBubble) {
        removeStatusBubble(statusBubble);
        answerBubble = appendBubble("", "bot");
      }
      fullAnswer += token;
      let contentEl = answerBubble.querySelector(".stream-content");
      if (!contentEl) {
        contentEl = document.createElement("div");
        contentEl.className = "stream-content";
        answerBubble.appendChild(contentEl);
      }
      contentEl.innerHTML = formatMessageHtml(fullAnswer);
      autoScrollIfNeeded();
    },
    (metaMethod) => {
      method = metaMethod || "";
      removeStatusBubble(statusBubble);
      answerBubble = appendBubble("", "bot");
      if (method) {
        answerBubble.insertAdjacentHTML(
          "beforeend",
          `<div class="pipeline-tag"><i class="bi bi-cpu"></i> ${escapeHtml(method)}</div>`,
        );
      }
    }
  );

  if (!answerBubble && !fullAnswer) throw new Error("Réponse vide");
  return { method, answer: fullAnswer };
}

/**
 * Pipeline Phase 1 — FAQ TF-IDF avec seuils de confiance
 */
async function askViaPhase1(question, statusBubble) {
  updateStatusBubble(statusBubble, "Recherche dans la FAQ...");

  const data = await fetchAskV1(question);
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
  if (!handleAuthGate()) return;
  if (state.isProcessing || !state.isOnline) return;

  state.isProcessing = true;
  sendBtn.disabled = true;
  hideWelcomeAndSuggestions();
  
  // const cleanQuestion = question.trim(); // This variable was not used after being defined
  let questionCount = parseInt(localStorage.getItem('q_count') || "0") + 1;
  localStorage.setItem('q_count', questionCount);

  const statQuestions = document.getElementById("stat-questions");
  if (statQuestions) statQuestions.textContent = String(questionCount);

  appendBubble(escapeHtml(question), "user");
  const statusBubble = createStatusBubble();
  const startTime = Date.now();

  try {
    if (state.gen3Available) {
      try {
        await askViaGen3(question, statusBubble);
      } catch {
        state.gen3Available = false;
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
    state.isProcessing = false;
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
    const currentState = state.activeFeedback.get(faqId);
    const feedback = btn.closest(".feedback");
    const upBtn = feedback.querySelector(".feedback-btn.up");
    const downBtn = feedback.querySelector(".feedback-btn.down");

    // Si on clique sur le même bouton déjà actif, on le désactive
    if (currentState === (isUp ? "up" : "down")) {
      btn.classList.remove("active");
      state.activeFeedback.delete(faqId);
      upBtn.classList.remove("disabled");
      downBtn.classList.remove("disabled");
      return;
    }

    // Désactiver l'autre bouton et activer celui-ci
    if (isUp) {
      upBtn.classList.add("active");
      downBtn.classList.remove("active");
      downBtn.classList.add("disabled");
      state.activeFeedback.set(faqId, "up");
      await sendFeedback(faqId, "positif", null);
    } else {
      downBtn.classList.add("active");
      upBtn.classList.remove("active");
      upBtn.classList.add("disabled");
      state.activeFeedback.set(faqId, "down");
      showNegativeFeedbackModal(faqId);
    }
  }
}

/**
 * Envoie le feedback à l'API
 */
async function sendFeedback(faqId, feedbackType, comment = null) {
  try {
    await sendFeedbackApi({
      faq: faqId,
      feedback_type: feedbackType,
      question_utilisateur: "...", // Retrieve from bubble context
      score_similarite: 0,
      comment: comment || "",
    });

    showToast(
      feedbackType === "positif"
        ? "Merci pour votre feedback positif !"
        : "Merci pour votre feedback !",
      2000,
    );

    // Refresh stats if panel is open
    if (statsPanel && statsPanel.classList.contains("show")) loadStats();

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
      state.activeFeedback.delete(faqId);
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
        state.activeFeedback.delete(faqId);
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
  if (!question || state.isProcessing) return;

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
    if (input.value.trim() && !state.isProcessing) {
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
    if (!state.isProcessing) resetConversation();
  });
}

if (scrollBottomBtn) {
  scrollBottomBtn.addEventListener("click", () => {
    userHasScrolledManually = false;
    thread.scrollTo({ top: thread.scrollHeight, behavior: "smooth" });
    scrollBottomBtn.hidden = true;
  });
}

if (menuBtn) {
  menuBtn.addEventListener("click", () => {
    sidebar.classList.toggle("open");
  });
}

// Event listeners pour les stats
if (showStatsBtn) {
  showStatsBtn.addEventListener("click", toggleStatsPanel);
}
if (closeStatsBtn) {
  closeStatsBtn.addEventListener("click", toggleStatsPanel);
}
if (statsContainer) {
  statsContainer.addEventListener("click", (e) => {
    if (e.target === statsContainer) toggleStatsPanel();
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

  // Afficher le bouton de stats au chargement
  if (statsContainer) statsContainer.style.display = "block";
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