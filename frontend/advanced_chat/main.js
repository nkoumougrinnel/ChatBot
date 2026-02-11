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

// Éléments du DOM
const thread = document.getElementById("thread");
const form = document.getElementById("composer");
const input = document.getElementById("input");
const sendBtn = document.getElementById("send");
const topk = document.getElementById("topk");
const toast = document.getElementById("toast");
const charCount = document.getElementById("charCount");
const suggestionsGrid = document.getElementById("suggestions");

// État de l'application
let isProcessing = false;
let lastUserQuestion = ""; // Pour stocker la question de l'utilisateur

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
 * Ajoute une bulle de message dans le thread
 */
function appendBubble(text, who = "bot") {
  const bubble = document.createElement("div");
  bubble.className = `bubble ${who}`;
  bubble.innerHTML = text;
  // determine if we should auto-scroll: only when user is already near bottom
  const shouldScroll =
    thread.scrollHeight - thread.scrollTop - thread.clientHeight < 40;
  thread.appendChild(bubble);

  // Scroll fluide vers le bas si l'utilisateur est en bas
  if (shouldScroll) {
    requestAnimationFrame(() => {
      thread.scrollTo({ top: thread.scrollHeight, behavior: "smooth" });
    });
  }

  return bubble;
}

/**
 * Masque la grille de suggestions
 */
function hideSuggestions() {
  if (suggestionsGrid) {
    suggestionsGrid.style.opacity = "0";
    suggestionsGrid.style.transform = "translateY(10px)";
    setTimeout(() => {
      suggestionsGrid.style.display = "none";
    }, 300);
  }
}

/**
 * Formate les résultats de la FAQ
 */
function formatResults(results) {
  if (!results || results.length === 0) {
    return '<span class="muted">Aucun résultat trouvé dans la FAQ.</span>';
  }

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
}

/**
 * Envoie une question à l'API
 */
async function ask(question, topK) {
  if (isProcessing) return;

  isProcessing = true;
  sendBtn.disabled = true;
  hideSuggestions();

  // Stocke la question pour le feedback
  lastUserQuestion = question.trim();

  // Affiche la question de l'utilisateur
  appendBubble(question, "user");

  // Affiche l'indicateur de chargement
  const loadingBubble = appendBubble(
    '<span class="muted"><i class="bi bi-search"></i> Recherche dans la FAQ...</span>',
    "bot",
  );

  try {
    const response = await fetch(API_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify({
        question: question.trim(),
        top_k: Number(topK),
      }),
    });

    // Supprime l'indicateur de chargement
    loadingBubble.remove();

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({
        error: `Erreur ${response.status}: ${response.statusText}`,
      }));
      throw new Error(errorData.error || response.statusText);
    }

    const data = await response.json();

    // Affiche les résultats avec animation de saisie (chars/sec) tout en préservant le style
    const resultsHTML = formatResults(data.results);
    const botBubble = appendBubble("", "bot");

    // typing settings: characters per second
    const CHARS_PER_SEC = 30; // adjust for slower/faster typing

    // Render HTML progressively: for element nodes keep structure, for text nodes reveal characters
    async function typeHtml(targetElement, htmlString, cps) {
      const tmp = document.createElement("div");
      tmp.innerHTML = htmlString;

      const delay = 1000 / cps;

      async function processNode(node, parent, noDelay = false) {
        if (node.nodeType === Node.ELEMENT_NODE) {
          const el = document.createElement(node.tagName);
          // copy attributes
          for (let i = 0; i < node.attributes.length; i++) {
            const attr = node.attributes[i];
            el.setAttribute(attr.name, attr.value);
          }
          parent.appendChild(el);

          // if this element is meta or feedback, show children without per-char delay
          const childNoDelay =
            noDelay ||
            node.classList.contains("result-meta") ||
            node.classList.contains("feedback");

          for (let i = 0; i < node.childNodes.length; i++) {
            await processNode(node.childNodes[i], el, childNoDelay);
          }
        } else if (node.nodeType === Node.TEXT_NODE) {
          const text = node.textContent || "";
          const textNode = document.createTextNode("");
          parent.appendChild(textNode);

          if (noDelay || text.trim() === "") {
            // immediate
            textNode.data = text;
            return;
          }

          for (let i = 1; i <= text.length; i++) {
            textNode.data = text.slice(0, i);
            await new Promise((res) => setTimeout(res, delay));
          }
        }
      }

      // clear target and start
      targetElement.innerHTML = "";
      for (let i = 0; i < tmp.childNodes.length; i++) {
        await processNode(tmp.childNodes[i], targetElement, false);
      }
    }

    await typeHtml(botBubble, resultsHTML, CHARS_PER_SEC);

    // Move feedback buttons outside the bubble: render one wrapper per result
    const feedbackNodes = Array.from(botBubble.querySelectorAll(".feedback"));
    let last = botBubble;
    feedbackNodes.forEach((fb) => {
      const wrapper = document.createElement("div");
      wrapper.className = "feedback-wrapper";
      // move node into wrapper (this removes it from bubble)
      wrapper.appendChild(fb);
      last.parentNode.insertBefore(wrapper, last.nextSibling);
      last = wrapper;
    });
  } catch (error) {
    console.error("Erreur lors de la requête:", error);

    // Supprime l'indicateur de chargement s'il existe encore
    if (loadingBubble.parentNode) {
      loadingBubble.remove();
    }

    // Affiche l'erreur
    const errorMessage = error.message.includes("Failed to fetch")
      ? '<i class="bi bi-x-circle-fill"></i> Impossible de se connecter au serveur. Vérifiez que l\'API est démarrée.'
      : `<i class=\"bi bi-x-circle-fill\"></i> ${error.message}`;

    appendBubble(`<span class="muted">${errorMessage}</span>`, "bot");
    showToast(errorMessage, 4000);
  } finally {
    isProcessing = false;
    sendBtn.disabled = false;
    input.focus();
  }
}

/**
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
 */
function autoResizeTextarea() {
  // no-op for single-line input
}

/**
 * Met à jour le compteur de caractères
 */
function updateCharCount() {
  if (!charCount) return; // guard: charCount element may not exist
  const count = input.value.length;
  charCount.textContent = count;

  if (count > 450) {
    charCount.style.color = "var(--warning)";
  } else {
    charCount.style.color = "var(--text-muted)";
  }
}

/**
 * Gestion de la soumission du formulaire
 */
form.addEventListener("submit", (e) => {
  e.preventDefault();

  const question = input.value.trim();
  if (!question || isProcessing) return;

  ask(question, topk.value);

  // Reset du formulaire
  input.value = "";
  autoResizeTextarea();

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
 * Auto-resize et compteur lors de la saisie
 */
input.addEventListener("input", () => {
  // toggle send button active state when input is not empty
  if (input.value.trim().length > 0) {
    sendBtn.classList.add("has-text");
  } else {
    sendBtn.classList.remove("has-text");
  }
});

/**
 * Gestion des clics sur les suggestions
 */
if (suggestionsGrid) {
  const suggestionCards = suggestionsGrid.querySelectorAll(".suggestion-card");

  suggestionCards.forEach((card) => {
    card.addEventListener("click", () => {
      const question = card.getAttribute("data-question");
      if (question && !isProcessing) {
        input.value = question;
        if (input.value.trim().length > 0) sendBtn.classList.add("has-text");

        // Envoie automatiquement la question
        setTimeout(() => {
          form.requestSubmit();
        }, 100);
      }
    });
  });
}

/**
 * Gestion du changement de top_k
 */
topk.addEventListener("change", () => {
  const value = topk.value;
  showToast(`Nombre de résultats : ${value}`, 2000);
});
/**
 * Focus automatique sur l'input au chargement
 */
window.addEventListener("load", () => {
  input.focus();
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

// Export pour les tests (si besoin)
if (typeof module !== "undefined" && module.exports) {
  module.exports = {
    ask,
    appendBubble,
    formatResults,
    showToast,
  };
}
