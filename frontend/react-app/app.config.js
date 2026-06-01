// frontend/react-app/app.config.js
export default {
  name: "Supone AI",
  slug: "supone-ai",
  version: "1.0.0",
  platforms: ["ios", "android", "web"],
  extra: {
    BACKEND_BASE_URL: process.env.BACKEND_BASE_URL ?? "http://localhost:8000",
    MOCK_API: process.env.MOCK_API ?? "false",
  },
};