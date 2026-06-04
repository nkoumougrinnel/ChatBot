/**
 * SUP'ONE AI — Frontend léger connecté à l'API Django
 */
const API_BASE = (() => {
  const host = window.location.hostname;
  if (host.includes("ngrok-free.dev")) return "https://patternable-felicitously-shaunta.ngrok-free.dev";
  if (host.includes("netlify.app")) return "https://chatbot-production-5202.up.railway.app";
  if (host.includes("192.168") || host.startsWith("10.")) return `http://${host}:8000`;
  return "http://localhost:8000";
})();

const API_URL = `${API_BASE}/api/chatbot/ask/`;
const API_V2_URL = `${API_BASE}/api/v2/chatbot/ask/`;
const API_HEALTH_URL = `${API_BASE}/api/health/`;

const THRESH_LOW = 0.5;
const THRESH_MED = 0.7;

class SupOneAI {
  constructor() {
    this.chatBody = document.getElementById("chatContent");
    this.form = document.getElementById("messageForm");
    this.input = document.getElementById("userInput");
    this.sendBtn = document.getElementById("sendBtn");
    this.suggestions = document.getElementById("suggestionsBox");
    this.welcome = document.getElementById("welcomeBlock");
    this.statusLabel = document.getElementById("statusLabel");
    this.charCount = document.getElementById("charCount");
    this.scrollFab = document.getElementById("scrollFab");
    this.toast = document.getElementById("toast");
    this.isProcessing = false;
    this.gen3Available = false;
    this.init();
  }

  init() {
    this.form.addEventListener("submit", (e) => {
      e.preventDefault();
      this.sendMessage();
    });
    this.input.addEventListener("input", () => this.onInput());
    document.getElementById("newChatBtn")?.addEventListener("click", () => this.resetChat());
    this.scrollFab?.addEventListener("click", () => {
      this.chatBody.scrollTo({ top: this.chatBody.scrollHeight, behavior: "smooth" });
      this.scrollFab.hidden = true;
    });
    this.chatBody.addEventListener("scroll", () => this.updateScrollFab());
    this.suggestions?.querySelectorAll(".suggestion-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        const msg = btn.getAttribute("data-msg");
        if (msg && !this.isProcessing) {
          this.input.value = msg;
          this.onInput();
          this.sendMessage();
        }
      });
    });
    this.checkHealth();
    this.input.focus();
  }

  onInput() {
    const len = this.input.value.trim().length;
    this.sendBtn.disabled = len === 0 || this.isProcessing;
    this.sendBtn.classList.toggle("active", len > 0);
    if (this.charCount) this.charCount.textContent = `${this.input.value.length} / 500`;
  }

  async checkHealth() {
    try {
      const res = await fetch(API_HEALTH_URL, { signal: AbortSignal.timeout(4000) });
      const data = await res.json();
      this.gen3Available = Boolean(data.gen3?.available);
      this.setStatus(true, this.gen3Available ? "En ligne · IA" : "En ligne");
    } catch {
      this.gen3Available = false;
      this.setStatus(false, "Hors ligne");
    }
  }

  setStatus(ok, text) {
    if (!this.statusLabel) return;
    this.statusLabel.innerHTML = `<span class="status-dot" style="background:${ok ? "#10b981" : "#f59e0b"}"></span> ${text}`;
  }

  showToast(msg) {
    if (!this.toast) return;
    this.toast.textContent = msg;
    this.toast.classList.add("show");
    setTimeout(() => this.toast.classList.remove("show"), 2800);
  }

  hideWelcome() {
    if (this.welcome) {
      this.welcome.style.opacity = "0";
      setTimeout(() => (this.welcome.style.display = "none"), 250);
    }
    if (this.suggestions) {
      this.suggestions.style.opacity = "0";
      setTimeout(() => (this.suggestions.style.display = "none"), 250);
    }
  }

  resetChat() {
    this.chatBody.innerHTML = `
      <section class="welcome" id="welcomeBlock">
        <div class="welcome-icon"><i class="bi bi-chat-heart-fill"></i></div>
        <h2>Bonjour !</h2>
        <p>Posez vos questions sur SUP'ONE : admissions, vie étudiante, programmes...</p>
      </section>
      <div class="suggestions" id="suggestionsBox">
        <button class="suggestion-btn" data-msg="Quelle est l'histoire de SUP'ONE ?"><i class="bi bi-book"></i> Histoire</button>
        <button class="suggestion-btn" data-msg="Comment s'inscrire à SUP'ONE ?"><i class="bi bi-pencil-square"></i> Inscription</button>
        <button class="suggestion-btn" data-msg="Quels sont les clubs disponibles ?"><i class="bi bi-people"></i> Clubs</button>
        <button class="suggestion-btn" data-msg="Quels documents pour l'admission ?"><i class="bi bi-file-earmark-text"></i> Documents</button>
      </div>`;
    this.welcome = document.getElementById("welcomeBlock");
    this.suggestions = document.getElementById("suggestionsBox");
    this.suggestions.querySelectorAll(".suggestion-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        const msg = btn.getAttribute("data-msg");
        if (msg && !this.isProcessing) {
          this.input.value = msg;
          this.onInput();
          this.sendMessage();
        }
      });
    });
    this.showToast("Nouvelle conversation");
    this.input.focus();
  }

  addMessage(html, role) {
    const wrap = document.createElement("div");
    wrap.className = `msg-wrap ${role}`;
    const bubble = document.createElement("div");
    bubble.className = role === "user" ? "msg-user" : "msg-bot";
    bubble.innerHTML = html;
    wrap.appendChild(bubble);
    this.chatBody.appendChild(wrap);
    this.scrollToEnd();
    return bubble;
  }

  scrollToEnd() {
    requestAnimationFrame(() => {
      this.chatBody.scrollTop = this.chatBody.scrollHeight;
      this.updateScrollFab();
    });
  }

  updateScrollFab() {
    if (!this.scrollFab) return;
    const atBottom = this.chatBody.scrollHeight - this.chatBody.scrollTop - this.chatBody.clientHeight < 80;
    this.scrollFab.hidden = atBottom;
  }

  createLoader() {
    return this.addMessage(
      '<div class="loader"><span></span><span></span><span></span> Réflexion...</div>',
      "bot",
    );
  }

  escape(text) {
    const d = document.createElement("div");
    d.textContent = text;
    return d.innerHTML;
  }

  async askGen3(question, loader) {
    const res = await fetch(API_V2_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, stream: true }),
    });
    if (!res.ok) throw new Error("Gen3 unavailable");

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    let answer = "";
    let bubble = null;

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";

      for (const line of lines) {
        if (!line.startsWith("data: ")) continue;
        let payload;
        try { payload = JSON.parse(line.slice(6)); } catch { continue; }

        if (payload.type === "status" && loader) {
          loader.querySelector(".loader")?.replaceChildren();
          loader.innerHTML = `<div class="loader"><span></span><span></span><span></span> ${this.escape(payload.status === "searching" ? "Recherche..." : payload.status === "generating" ? "Génération..." : "Réflexion...")}</div>`;
        } else if (payload.type === "token" && payload.content) {
          loader?.remove();
          loader = null;
          answer += payload.content;
          if (!bubble) bubble = this.addMessage("", "bot");
          bubble.innerHTML = this.escape(answer).replace(/\n/g, "<br>");
          this.scrollToEnd();
        } else if (payload.type === "error") {
          throw new Error(payload.message);
        }
      }
    }
    if (!answer) throw new Error("empty");
  }

  async askPhase1(question, loader) {
    const res = await fetch(API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, top_k: 1 }),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    loader?.remove();

    const top = data.results?.[0];
    const score = top ? Number(top.score) : 0;

    if (score < THRESH_LOW) {
      const b = this.addMessage("", "bot");
      b.textContent = "Je n'ai pas trouvé d'information précise. Essayez de reformuler ou contactez le support SUP'ONE.";
    } else if (score < THRESH_MED) {
      const q = (top.question || "").replace(/\?$/, "");
      this.addMessage(`Je ne suis pas totalement sûr — vouliez-vous dire : <strong>« ${this.escape(q)} »</strong> ?`, "bot");
    } else {
      const b = this.addMessage(
        `<div class="faq-q"><i class="bi bi-pin-angle"></i> ${this.escape(top.question)}</div><div class="faq-a">${this.escape(top.answer).replace(/\n/g, "<br>")}</div><div class="faq-meta"><i class="bi bi-tags"></i> ${this.escape(top.category || "")} · Score ${score.toFixed(2)}</div>`,
        "bot",
      );
      return b;
    }
  }

  async sendMessage() {
    const text = this.input.value.trim();
    if (!text || this.isProcessing) return;

    this.isProcessing = true;
    this.sendBtn.disabled = true;
    this.hideWelcome();
    this.addMessage(this.escape(text), "user");
    this.input.value = "";
    this.onInput();

    const loader = this.createLoader();

    try {
      if (this.gen3Available) {
        try {
          await this.askGen3(text, loader);
          return;
        } catch {
          this.gen3Available = false;
        }
      }
      await this.askPhase1(text, loader);
    } catch {
      loader?.remove();
      this.addMessage('<i class="bi bi-wifi-off"></i> Impossible de joindre le serveur. Démarrez le backend (<code>python manage.py runserver</code>) puis réessayez.', "bot");
      this.setStatus(false, "Hors ligne");
    } finally {
      this.isProcessing = false;
      this.onInput();
      this.input.focus();
    }
  }
}

document.addEventListener("DOMContentLoaded", () => new SupOneAI());
