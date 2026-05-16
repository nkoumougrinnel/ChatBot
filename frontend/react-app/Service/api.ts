import { request } from './client';

export type ChatbotResult = {
  faq_id: number;
  question: string;
  answer: string;
  score: number;
  category: string;
};

export type ChatbotResponse = {
  question: string;
  results: ChatbotResult[];
  count: number;
  status: "not found" | "uncertain" | "confident";
};

export async function askChatbot(
  question: string,
  topK = 1,
): Promise<ChatbotResponse> {
  const res = await request('/api/chatbot/ask/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, top_k: topK }),
  });

  if (!res.ok) {
    const text = await res.text?.();
    throw new Error(`Erreur API chatbot: ${text ?? 'unknown'}`);
  }

  return await res.json();
}
