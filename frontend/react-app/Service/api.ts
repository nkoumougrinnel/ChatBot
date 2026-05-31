export { BACKEND_BASE_URL } from "./client";

export type ChatbotGen3Response = {
  answer: string;
  method: string;
  level: string;
  score: number;
  elapsed_ms?: number;
  error?: string;
};

type SSEEvent =
  | { type: "status"; status: string }
  | { type: "meta"; method: string; level: string; score: number }
  | { type: "token"; content: string }
  | { type: "done"; elapsed_ms: number }
  | { type: "error"; message: string };

async function consumeSSEStream(
  response: Response,
  onEvent: (event: SSEEvent) => void,
): Promise<void> {
  const reader = response.body?.getReader();
  if (!reader) {
    throw new Error("Flux SSE indisponible (body absent).");
  }

  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const blocks = buffer.split("\n\n");
    buffer = blocks.pop() ?? "";

    for (const block of blocks) {
      for (const line of block.split("\n")) {
        if (!line.startsWith("data: ")) continue;
        try {
          onEvent(JSON.parse(line.slice(6)) as SSEEvent);
        } catch {
          // Ignorer les lignes SSE mal formées
        }
      }
    }
  }
}

export async function askChatbot(
  question: string,
  history?: Array<{ role: string; content: string }>,
): Promise<ChatbotGen3Response> {
  const response = await fetch(`${BACKEND_BASE_URL}/api/chatbot/ask/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "text/event-stream",
    },
    body: JSON.stringify({ question, history: history ?? null }),
  });

  if (!response.ok) {
    const errorBody = await response.text();
    throw new Error(`Erreur API chatbot (${response.status}): ${errorBody}`);
  }

  let answer = "";
  let method = "";
  let level = "";
  let score = 0;
  let elapsed_ms: number | undefined;
  let error: string | undefined;

  await consumeSSEStream(response, (event) => {
    switch (event.type) {
      case "meta":
        method = event.method;
        level = event.level;
        score = event.score;
        break;
      case "token":
        answer += event.content;
        break;
      case "done":
        elapsed_ms = event.elapsed_ms;
        break;
      case "error":
        error = event.message;
        break;
    }
  });

  return { answer, method, level, score, elapsed_ms, error };
}