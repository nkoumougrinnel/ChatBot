import Constants from 'expo-constants';

// Prefer the modern expoConfig; fall back to manifest for older SDKs
const config = (Constants as any).expoConfig ?? (Constants as any).manifest ?? {};

// Config: backend base url and mock mode
export const BACKEND_BASE_URL = config?.extra?.BACKEND_BASE_URL ?? 'http://localhost:8000';
export const MOCK_API = (config?.extra?.MOCK_API === 'true') || false;

async function delay(ms: number) {
  return new Promise((r) => setTimeout(r, ms));
}

export async function request(path: string, options: RequestInit = {}) {
  const url = `${BACKEND_BASE_URL}${path}`;

  if (MOCK_API) {
    // Return canned responses for common endpoints (expand as needed)
    await delay(300);
    if (path.includes('/api/chatbot/ask')) {
      return {
        ok: true,
        json: async () => ({ question: '', results: [{ faq_id: 0, question: 'Mock', answer: 'Réponse mock', score: 1, category: 'mock' }], count: 1, status: 'confident' })
      } as any;
    }

    if (path.includes('/api/user/profile')) {
      return {
        ok: true,
        json: async () => ({ name: 'Utilisateur Mock', email: 'mock@example.com' })
      } as any;
    }

    return { ok: true, json: async () => ({}) } as any;
  }

  // Real network request
  const res = await fetch(url, options);
  return res;
}
