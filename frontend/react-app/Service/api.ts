export const BACKEND_BASE_URL = "http://10.227.132.171:8000";

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
  const response = await fetch(`${BACKEND_BASE_URL}/api/chatbot/ask/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ question, top_k: topK }),
  });

  if (!response.ok) {
    const errorBody = await response.text();
    throw new Error(`Erreur API chatbot (${response.status}): ${errorBody}`);
  }

  return await response.json();
}
