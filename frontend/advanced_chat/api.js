// Detect API endpoint based on current location
const API_BASE = (() => {
  const host = window.location.hostname;

  if (host.includes("ngrok-free.dev")) {
    return "https://patternable-felicitously-shaunta.ngrok-free.dev";
  }

  if (host.includes("netlify.app")) {
    return "https://chatbot-production-5202.up.railway.app";
  }

  if (host.includes("192.168") || host.includes("10.")) {
    return `http://${host}:8001`;
  }

  return "http://localhost:8001";
})();

const ENDPOINTS = {
  ASK_V1: `${API_BASE}/api/chatbot/ask/`,
  ASK_V2: `${API_BASE}/api/v2/chatbot/ask/`,
  HEALTH: `${API_BASE}/api/health/`,
  FEEDBACK: `${API_BASE}/api/feedback/`,
  HISTORY: `${API_BASE}/api/history/`,
  STATS: `${API_BASE}/api/stats/`,
  LOGIN: `${API_BASE}/api/users/login/`,
  SIGNUP: `${API_BASE}/api/users/signup/`,
};

// Export API_BASE and ENDPOINTS
export { API_BASE, ENDPOINTS };

function getAuthHeaders(extra = {}) {
  const token = localStorage.getItem('access_token');
  const headers = { ...extra };
  if (token) headers['Authorization'] = `Token ${token}`;
  return headers;
}

// Export API functions
export async function fetchHealth() {
  const res = await fetch(ENDPOINTS.HEALTH, { 
    signal: AbortSignal.timeout(5000),
    credentials: 'include' 
  });
  if (!res.ok) throw new Error("health failed");
  return res.json();
}

export async function fetchStats() {
  const response = await fetch(ENDPOINTS.STATS, { credentials: 'include' });
  if (!response.ok) {
    throw new Error("Failed to load dynamic suggestions");
  }
  return response.json();
}

export async function fetchAskV1(question) {
  const response = await fetch(ENDPOINTS.ASK_V1, {
    method: "POST",
    headers: { 
      ...getAuthHeaders(),
      "Content-Type": "application/json", 
      "Accept": "application/json" 
    },
    credentials: 'include',
    body: JSON.stringify({ question, top_k: 1 }),
  });
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json();
}

export async function fetchAskV2Stream(question, onStatusUpdate, onToken, onMeta) {
  const response = await fetch(ENDPOINTS.ASK_V2, {
    method: "POST",
    headers: { 
      ...getAuthHeaders(),
      "Content-Type": "application/json", 
      "Accept": "text/event-stream" 
    },
    credentials: 'include',
    body: JSON.stringify({ question, stream: true }),
  });

  if (!response.ok) throw new Error(`Gen3 HTTP ${response.status}`);
  if (!response.body) throw new Error("ReadableStream non supporté");

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

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
        onStatusUpdate(payload.status);
      } else if (payload.type === "meta") {
        onMeta(payload.method);
      } else if (payload.type === "token" && payload.content) {
        onToken(payload.content);
      } else if (payload.type === "error") {
        throw new Error(payload.message || "Erreur pipeline");
      }
    }
  }
}

export async function sendFeedbackApi(payload) {
  const response = await fetch(ENDPOINTS.FEEDBACK, {
    method: "POST",
    headers: {
      ...getAuthHeaders(),
      "Content-Type": "application/json",
      "Accept": "application/json",
    },
    credentials: 'include',
    body: JSON.stringify(payload),
  });
  if (!response.ok) throw new Error(`Feedback API HTTP ${response.status}`);
  return response.json();
}

export async function deleteHistoryApi() {
  const response = await fetch(ENDPOINTS.HISTORY, {
    method: "DELETE",
    headers: getAuthHeaders(),
    credentials: 'include',
  });
  if (!response.ok) throw new Error(`Delete history failed: ${response.status}`);
  return true;
}

export async function loginUser(email, password) {
  const response = await fetch(ENDPOINTS.LOGIN, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: 'include',
    body: JSON.stringify({ email, password }),
  });
  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || "Login failed");
  }
  return response.json();
}

export async function signupUser(fullName, email, password) {
  const response = await fetch(ENDPOINTS.SIGNUP, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: 'include',
    body: JSON.stringify({ full_name: fullName, email, password }), // Assuming backend expects 'full_name'
  });
  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || "Signup failed");
  }
  return response.json();
}