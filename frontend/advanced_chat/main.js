// Detect API endpoint based on current location
<<<<<<< HEAD
=======
// If frontend is served from ngrok, call backend via ngrok
// If frontend is served from local IP, use that IP for API
// Otherwise, use localhost for local development
>>>>>>> backend
const API_BASE = (() => {
  const host = window.location.hostname;

  // If on ngrok frontend, call backend via ngrok
  if (host.includes("ngrok-free.dev")) {
    return "https://patternable-felicitously-shaunta.ngrok-free.dev";
<<<<<<< HEAD
  }

  // If on Netlify, call backend via ngrok
  if (host.includes("netlify.app")) {
    return "https://chatbot-production-5202.up.railway.app";
=======
>>>>>>> backend
  }

  // Network IP detected, use same IP for API
  if (host.includes("192.168") || host.includes("10.")) {
    return `http://${host}:8000`;
  }

  // Local development
  return "http://localhost:8000";
})();

const API_URL = `${API_BASE}/api/chatbot/ask/`;
const API_FEEDBACK_URL = `${API_BASE}/api/feedback/`;
const API_STATS_URL = `${API_BASE}/api/stats/`;
<<<<<<< HEAD

// Seuils de confiance pour les réponses (0-1)
const CONFIDENCE_THRESHOLD_LOW = 0.5;   // En dessous: aucune réponse
const CONFIDENCE_THRESHOLD_MED = 0.7;   // Entre 0.5-0.7: suggestion
=======
>>>>>>> backend

// Éléments du DOM
const thread = document.getElementById("thread");
const form = document.getElementById("composer");
const input = document.getElementById("input");
const sendBtn = document.getElementById("send");
const toast = document.getElementById("toast");
const suggestionsGrid = document.getElementById("suggestions");
const welcomeSection = document.getElementById("welcome-section");

// État de l'application
let isProcessing = false;
<<<<<<< HEAD
let lastUserQuestion = "";
let hasAskedQuestion = false;
let activeFeedbackStates = new Map();
let userHasScrolledManually = false; // Flag pour détecter si l'utilisateur a scrollé manuellement
let scrollTimeout = null; // Timeout pour réinitialiser le flag
=======
let lastUserQuestion = ""; // Pour stocker la question de l'utilisateur
>>>>>>> backend

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

    // Créer les cartes de suggestions
    suggestionsGrid.innerHTML = positiveFeedbacks
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
  suggestionsGrid.innerHTML = `
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
  const suggestionCards = suggestionsGrid.querySelectorAll(".suggestion-card");
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

    if (welcomeSection) {
      welcomeSection.style.opacity = "0";
      welcomeSection.style.transform = "translateY(-10px)";
      setTimeout(() => {
        welcomeSection.style.display = "none";
      }, 300);
    }

    if (suggestionsGrid) {
      suggestionsGrid.style.opacity = "0";
      suggestionsGrid.style.transform = "translateY(10px)";
      setTimeout(() => {
        suggestionsGrid.classList.add("hidden");
      }, 300);
    }
  }
}

/**
 * Crée le HTML pour une réponse avec faible confiance (< 0.5)
 */
function createNoAnswerResponseText() {
  return "Je n'ai pas trouvé d'information précise concernant votre question dans la FAQ.";
}

<<<<<<< HEAD
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
=======
  return results
    .map((r, index) => {
      const questionText = r.question || "";
      const answerText = r.answer || "";
      const categoryText = r.category || "";
      const scoreNum = Number(r.score);
      const scoreText = Number.isFinite(scoreNum) ? scoreNum.toFixed(2) : "—";
      const faqId = r.faq_id || "";

      return `
    <div class="result-item" data-faq-id="${faqId}">
      <div class="result-question"><i class="bi bi-pin-angle-fill"></i> ${questionText}</div>
      <div class="result-answer">${answerText}</div>
      <div class="result-meta">
        <span><i class="bi bi-tags"></i> ${categoryText}</span>
        <span><i class="bi bi-star-fill"></i> Score: ${scoreText}</span>
      </div>
      <div class="feedback">
        <button class="feedback-btn up" aria-label="like" data-faq-id="${faqId}"><i class="bi bi-hand-thumbs-up"></i></button>
        <button class="feedback-btn down" aria-label="dislike" data-faq-id="${faqId}"><i class="bi bi-hand-thumbs-down"></i></button>
        <button class="feedback-btn copy" aria-label="copy" data-faq-id="${faqId}"><i class="bi bi-clipboard"></i></button>
        <button class="feedback-btn share" aria-label="share" data-faq-id="${faqId}"><i class="bi bi-share"></i></button>
      </div>
    </div>
  `;
    })
    .join("");
>>>>>>> backend
}

/**
 * Envoie une question à l'API
 */
async function ask(question) {
  if (isProcessing) return;

  isProcessing = true;
  sendBtn.disabled = true;
  hideWelcomeAndSuggestions();

<<<<<<< HEAD
  lastUserQuestion = question.trim();
=======
  // Stocke la question pour le feedback
  lastUserQuestion = question.trim();

  // Affiche la question de l'utilisateur
>>>>>>> backend
  appendBubble(question, "user");

  // Animation de recherche avec typing effect
  const loadingBubble = appendBubble('<span class="muted"><i class="bi bi-search"></i> </span>', "bot");
  const loadingTextSpan = loadingBubble.querySelector('.muted');
  
  // Animation de typing pour le texte de recherche (sans attendre la fin)
  typeText(loadingTextSpan, 'Recherche dans la FAQ...', 30);

  const startTime = Date.now();

  try {
    const response = await fetch(API_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify({ question, top_k: 1 }), // On demande 1 seul résultat
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const data = await response.json();

    // S'assurer qu'au moins 1 seconde s'est écoulée
    const elapsed = Date.now() - startTime;
    const minDelay = 1000; // 1 seconde minimum
    if (elapsed < minDelay) {
      await new Promise((resolve) => setTimeout(resolve, minDelay - elapsed));
    }

    loadingBubble.remove();

    // Vérifier la confiance de la réponse
    const topResult = data.results && data.results[0];
    const confidence = topResult ? Number(topResult.score) : 0;

    // ============================================
    // LOGIQUE DES 3 SEUILS
    // ============================================
    
    if (confidence < CONFIDENCE_THRESHOLD_LOW) {
      // SEUIL 1: 0 - 0.5 → Aucune réponse trouvée
      const lowConfBubble = appendBubble("", "bot");
      await typeText(lowConfBubble, createNoAnswerResponseText(), 10);

      // Ajouter les actions suggérées
      lowConfBubble.insertAdjacentHTML(
        "beforeend",
        `
        <div class="low-confidence-actions">
          <ul>
            <li><i class="bi bi-arrow-repeat"></i> Reformuler votre question</li>
            <li><i class="bi bi-envelope"></i> Contacter le support SUP'ONE</li>
            <li><i class="bi bi-book"></i> Consulter la FAQ complète</li>
          </ul>
        </div>
        `,
      );
    } else if (confidence < CONFIDENCE_THRESHOLD_MED) {
      // SEUIL 2: 0.5 - 0.7 → Suggestion (hésitation)
      const medConfBubble = appendBubble("", "bot");
      const medResponse = createMediumConfidenceResponse(topResult);
      
      // Animation de typing avec HTML en temps réel
      await typeHTML(medConfBubble, medResponse, 10);

      // Pas de boutons de feedback dans ce cas
    } else {
      // SEUIL 3: > 0.7 → Réponse complète avec boutons
      const botBubble = appendBubble("", "bot");

      // Ajouter data-faq-id à la bulle principale
      botBubble.setAttribute('data-faq-id', topResult.faq_id);

      // Question
      botBubble.innerHTML = `<div class="result-question"><i class="bi bi-pin-angle-fill"></i> ${topResult.question}</div>`;
      await new Promise((r) => setTimeout(r, 300));

      // Réponse avec animation
      botBubble.insertAdjacentHTML(
        "beforeend",
        `<div class="result-answer"></div>`,
      );
      await typeText(
        botBubble.querySelector(".result-answer"),
        topResult.answer,
        10,
      );

      // Extraire les métadonnées
      const categoryText = topResult.category || "";
      const scoreNum = Number(topResult.score);
      const scoreText = Number.isFinite(scoreNum) ? scoreNum.toFixed(2) : "—";
      const faqId = topResult.faq_id || "";

      // Ajouter meta + feedback
      botBubble.insertAdjacentHTML(
        "beforeend",
        `
        <div class="result-meta">
          <span><i class="bi bi-tags"></i> ${categoryText}</span>
          <span><i class="bi bi-star-fill"></i> Score: ${scoreText}</span>
        </div>
        <div class="feedback">
          <button class="feedback-btn up" aria-label="like" data-faq-id="${faqId}"><i class="bi bi-hand-thumbs-up"></i></button>
          <button class="feedback-btn down" aria-label="dislike" data-faq-id="${faqId}"><i class="bi bi-hand-thumbs-down"></i></button>
          <button class="feedback-btn copy" aria-label="copy" data-faq-id="${faqId}"><i class="bi bi-clipboard"></i></button>
          <button class="feedback-btn share" aria-label="share" data-faq-id="${faqId}"><i class="bi bi-share"></i></button>
        </div>
        `,
      );

      // Attacher les événements aux boutons de feedback APRÈS l'animation
      attachFeedbackListeners();
    }
  } catch (error) {
    console.error("Erreur lors de la requête:", error);

    // S'assurer que le délai minimum est respecté même en cas d'erreur
    const elapsed = Date.now() - startTime;
    const minDelay = 1000;
    if (elapsed < minDelay) {
      await new Promise((resolve) => setTimeout(resolve, minDelay - elapsed));
    }

    loadingBubble.remove();

    const errorBubble = appendBubble('<span class="muted"><i class="bi bi-x-circle"></i> </span>', "bot");
    const errorTextSpan = errorBubble.querySelector('.muted');
    await typeText(
      errorTextSpan,
      'Une erreur est survenue. Veuillez réessayer.',
      10,
    );
  } finally {
    isProcessing = false;
    sendBtn.disabled = false;
    input.focus();
  }
}

/**
<<<<<<< HEAD
 * Gère les clics sur les boutons de feedback (like, dislike, copy, share)
=======
 * Envoie un feedback (like uniquement) pour une réponse FAQ
 */
async function sendFeedback(faqId, isPositive, lastQuestion = "") {
  try {
    const payload = {
      faq: faqId,
      feedback_type: isPositive ? "positif" : "negatif",
      question_utilisateur: lastQuestion,
      score_similarite: isPositive ? 1 : 0,
      comment: isPositive ? "Réponse utile" : "Réponse peu utile",
    };

    console.log("Envoi du feedback:", payload);

    const response = await fetch(API_FEEDBACK_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify(payload),
    });

    const responseData = await response.json();
    console.log("Réponse API:", response.status, responseData);

    if (response.ok) {
      console.log("Feedback enregistré avec succès");
    } else {
      throw new Error(
        `Erreur ${response.status}: ${JSON.stringify(responseData)}`,
      );
    }
  } catch (error) {
    console.error("Erreur feedback:", error);
    showToast("Erreur lors de l'enregistrement du feedback", 3000);
  }
}

/**
 * Charge et affiche les statistiques des FAQs
 */
async function loadStats() {
  try {
    const response = await fetch(API_STATS_URL);
    if (!response.ok)
      throw new Error("Erreur lors de la récupération des statistiques");

    const stats = await response.json();
    displayStats(stats);
  } catch (error) {
    console.error("Erreur stats:", error);
    showToast("Impossible de charger les statistiques", 3000);
  }
}

/**
 * Affiche les statistiques dans le panel
 */
function displayStats(stats) {
  const statsContent = document.getElementById("stats-content");

  if (!stats || stats.length === 0) {
    statsContent.innerHTML = "<p>Aucun feedback enregistré pour l'instant.</p>";
    return;
  }

  let html = `
    <table>
      <thead>
        <tr>
          <th>FAQ</th>
          <th>Score Moy.</th>
          <th>Feedbacks</th>
        </tr>
      </thead>
      <tbody>
  `;

  stats.forEach((stat) => {
    const avgScore = stat.avg_score || 0;
    const scoreClass =
      avgScore >= 0.7
        ? "score-good"
        : avgScore >= 0.4
          ? "score-medium"
          : "score-poor";

    html += `
      <tr>
        <td title="${stat.question}" style="max-width: 150px; overflow: hidden; text-overflow: ellipsis;">
          ${stat.question.substring(0, 25)}...
        </td>
        <td><span class="score-badge ${scoreClass}">${avgScore.toFixed(2)}</span></td>
        <td>${stat.count}</td>
      </tr>
    `;
  });

  html += `
      </tbody>
    </table>
  `;

  statsContent.innerHTML = html;
}

/**
 * Bascule le panel de statistiques
 */
function toggleStatsPanel() {
  const statsPanel = document.getElementById("stats-panel");
  const showStatsBtn = document.getElementById("show-stats-btn");

  if (statsPanel.classList.contains("show")) {
    statsPanel.classList.remove("show");
  } else {
    loadStats();
    statsPanel.classList.add("show");
  }
}

/**
 * Attache les événements de feedback aux boutons
 */
let feedbackListenersAttached = false;
function attachFeedbackListeners() {
  // Éviter d'attacher plusieurs fois les mêmes listeners
  if (feedbackListenersAttached) return;
  feedbackListenersAttached = true;

  console.log("Attachement des event listeners de feedback...");

  // Observer les nouveaux éléments dynamiquement ajoutés
  document.addEventListener("click", (e) => {
    const feedbackBtn = e.target.closest(".feedback-btn");
    if (!feedbackBtn) return;

    console.log("Clic sur bouton feedback:", feedbackBtn.className);

    // Extraire l'ID FAQ depuis l'attribut data du bouton
    const faqId = feedbackBtn.dataset.faqId;
    console.log("FAQ ID from button:", faqId);

    if (!faqId) {
      console.error("FAQ ID non trouvé sur le bouton");
      return;
    }

    // Récupérer le result-item pour accéder aux textes
    const resultItem =
      feedbackBtn.closest(".result-item") ||
      document.querySelector(`[data-faq-id="${faqId}"]`);
    console.log("Result item trouvé:", resultItem ? "oui" : "non");

    if (feedbackBtn.classList.contains("up")) {
      console.log("Feedback POSITIF pour FAQ:", faqId);
      // Feedback positif
      feedbackBtn.classList.add("active");
      feedbackBtn.disabled = true;
      feedbackBtn.style.opacity = "0.6";
      feedbackBtn.style.cursor = "not-allowed";

      sendFeedback(faqId, true, lastUserQuestion);

      showToast("Merci d'avoir apprécié cette réponse!", 2000);
    } else if (feedbackBtn.classList.contains("down")) {
      console.log("Feedback NÉGATIF pour FAQ:", faqId);
      // Feedback négatif - afficher un formulaire
      feedbackBtn.classList.add("active");
      feedbackBtn.style.opacity = "0.6";
      feedbackBtn.style.cursor = "not-allowed";

      showFeedbackForm(faqId);
    } else if (feedbackBtn.classList.contains("copy")) {
      console.log("Copie de la réponse");
      // Copier la réponse
      if (resultItem) {
        const answerText =
          resultItem.querySelector(".result-answer")?.textContent || "";
        navigator.clipboard.writeText(answerText).then(() => {
          showToast("Réponse copiée!", 2000);
        });
      }
    } else if (feedbackBtn.classList.contains("share")) {
      console.log("Partage de la réponse");
      // Partager
      if (resultItem) {
        const questionText =
          resultItem.querySelector(".result-question")?.textContent || "";
        const answerText =
          resultItem.querySelector(".result-answer")?.textContent || "";
        const shareText = `Q: ${questionText}\nR: ${answerText}`;

        if (navigator.share) {
          navigator.share({
            title: "SUP'PTIC Assistant",
            text: shareText,
          });
        } else {
          navigator.clipboard.writeText(shareText).then(() => {
            showToast("Contenu copié pour partage!", 2000);
          });
        }
      }
    }
  });
}

/**
 * Affiche un formulaire modal pour le feedback négatif
 */
function showFeedbackForm(faqId) {
  console.log("Affichage du formulaire de feedback pour FAQ:", faqId);

  const suggestions = [
    "La réponse n'est pas claire",
    "La réponse ne répond pas à ma question",
    "La réponse est incorrecte",
  ];

  const suggestionsHTML = suggestions
    .map(
      (sugg) => `
    <button type="button" class="suggestion-btn" data-suggestion="${sugg}">
      ${sugg}
    </button>
  `,
    )
    .join("");

  const formHTML = `
    <div class="feedback-modal-overlay" id="modal-overlay-${faqId}">
      <div class="feedback-modal">
        <h3>Nous aider à nous améliorer</h3>
        <p>Dites-nous ce qui n'a pas fonctionné</p>
        <form id="feedback-form-${faqId}" class="feedback-form">
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
  console.log("Modal HTML inséré");

  const overlay = document.getElementById(`modal-overlay-${faqId}`);
  const form = document.getElementById(`feedback-form-${faqId}`);
  const cancelBtn = form.querySelector(".btn-cancel");
  const textarea = document.getElementById(`feedback-text-${faqId}`);
  const suggestionBtns = form.querySelectorAll(".suggestion-btn");

  console.log("Overlay trouvé:", overlay ? "oui" : "non");
  console.log("Form trouvée:", form ? "oui" : "non");

  // Ajouter les suggestions au commentaire
  suggestionBtns.forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.preventDefault();
      const suggestion = btn.getAttribute("data-suggestion");
      textarea.value = suggestion;
      btn.style.backgroundColor = "#3b82f6";
      btn.style.color = "white";
      // Enlever les autres boutons actifs
      suggestionBtns.forEach((b) => {
        if (b !== btn) {
          b.style.backgroundColor = "";
          b.style.color = "";
        }
      });
    });
  });

  cancelBtn.addEventListener("click", () => {
    console.log("Clic sur Annuler");
    overlay.remove();
  });

  overlay.addEventListener("click", (e) => {
    if (e.target === overlay) {
      console.log("Clic sur overlay (fermeture)");
      overlay.remove();
    }
  });

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    console.log("Submit du formulaire de feedback");

    const comment = document.getElementById(`feedback-text-${faqId}`).value;
    console.log("Commentaire:", comment);
    console.log("FAQ ID pour submit:", faqId);

    try {
      const payload = {
        faq: faqId,
        feedback_type: "negatif",
        question_utilisateur: lastUserQuestion,
        score_similarite: 0,
        comment: comment || "Réponse peu utile",
      };

      console.log("Payload à envoyer:", payload);

      const response = await fetch(API_FEEDBACK_URL, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
        },
        body: JSON.stringify(payload),
      });

      console.log("Réponse API:", response.status, response.statusText);

      if (response.ok) {
        overlay.remove();
        showToast(
          "Merci pour votre feedback! Nous l'utilisons pour nous améliorer.",
          3000,
        );
      } else {
        throw new Error("Erreur lors de l'envoi");
      }
    } catch (error) {
      console.error("Erreur:", error);
      showToast("Erreur lors de l'envoi du feedback", 3000);
    }
  });
}

/**
 * Auto-resize du textarea
>>>>>>> backend
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
  // Vérifier si l'utilisateur a scrollé vers le haut (pas en bas)
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
});

/**
 * Initialisation au chargement
 */
window.addEventListener("load", () => {
  input.focus();
<<<<<<< HEAD
  console.log("SUP'ONE AI initialisé");
  console.log("API:", API_URL);

  // Charger les suggestions dynamiques
  loadDynamicSuggestions();
  
  // Initialiser la modal de profil
  initProfileModal();
=======
  console.log("SUP'PTIC Assistant initialisé");
  console.log("API:", API_URL);
  console.log("API Feedback URL:", API_FEEDBACK_URL);

  // Initialiser les event listeners pour le feedback
  console.log("Appel de attachFeedbackListeners()");
  attachFeedbackListeners();
  console.log("attachFeedbackListeners() terminé");

  // Afficher le container de statistiques et attacher les événements
  const statsContainer = document.getElementById("stats-container");
  if (statsContainer) {
    statsContainer.style.display = "block";

    const showStatsBtn = document.getElementById("show-stats-btn");
    const closeStatsBtn = document.getElementById("close-stats");
    const statsPanel = document.getElementById("stats-panel");

    if (showStatsBtn) {
      showStatsBtn.addEventListener("click", toggleStatsPanel);
    }

    if (closeStatsBtn) {
      closeStatsBtn.addEventListener("click", () => {
        statsPanel.classList.remove("show");
      });
    }
  }
>>>>>>> backend
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