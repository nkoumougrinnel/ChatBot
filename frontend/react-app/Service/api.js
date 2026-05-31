import axios from 'axios';
// Utilise la variable d'env Vite — jamais d'URL hardcodée
const BASE_URL = import.meta.env.VITE_API_BASE_URL
|| 'http://localhost:8000/api';
export const askQuestion = async (text, history = []) => {
const response = await axios.post(`${BASE_URL}/chatbot/ask/`, {
question: text,
history: history,
});
return response.data;
};
export const sendFeedback = async (messageId, type) => {
return axios.post(`${BASE_URL}/feedback/`, {
message_id: messageId,
type: type,
});
};