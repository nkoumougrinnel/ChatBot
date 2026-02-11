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

      return `
    <div class="result-item">
      <div class="result-question"><i class="bi bi-pin-angle-fill"></i> ${questionText}</div>
      <div class="result-answer">${answerText}</div>
      <div class="result-meta">
        <span><i class="bi bi-tags"></i> ${categoryText}</span>
        <span><i class="bi bi-star-fill"></i> Score: ${scoreText}</span>
      </div>
      <div class="feedback">
        <button class="feedback-btn up" aria-label="like"><i class="bi bi-hand-thumbs-up"></i></button>
        <button class="feedback-btn down" aria-label="dislike"><i class="bi bi-hand-thumbs-down"></i></button>
        <button class="feedback-btn copy" aria-label="copy"><i class="bi bi-clipboard"></i></button>
        <button class="feedback-btn share" aria-label="share"><i class="bi bi-share"></i></button>
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
  console.log("✅ SUP'PTIC Assistant initialisé");
  console.log("🔗 API:", API_URL);
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
