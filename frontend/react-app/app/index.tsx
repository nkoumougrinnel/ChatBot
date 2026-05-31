// app/index.tsx — SUP'ONE
// Écran principal de chat — pipeline Gen3 avec token utilisateur.

import { Ionicons } from "@expo/vector-icons";
import AsyncStorage from "@react-native-async-storage/async-storage";
import * as Clipboard from "expo-clipboard";
import { useLocalSearchParams, useRouter } from "expo-router";
import React, { useEffect, useRef, useState } from "react";
import {
  ActivityIndicator,
  Alert,
  FlatList,
  Keyboard,
  KeyboardAvoidingView,
  Platform,
  StatusBar,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from "react-native";
import Animated, { FadeInDown, FadeInUp } from "react-native-reanimated";
import { SafeAreaView, useSafeAreaInsets } from "react-native-safe-area-context";

import { askChatbot } from "../Service/api";
import { lireNomAffichage, lireToken } from "../Service/authStorage";

// ─────────────────────────────────────────────────────────────────
// Types
// ─────────────────────────────────────────────────────────────────

type Message = {
  id: string;
  text: string;
  sender: "user" | "bot";
  method?: string;
  level?: string;
  score?: number;
  question?: string; // question originale, pour passer au feedback
};

// ─────────────────────────────────────────────────────────────────
// Badge méthode pipeline
// ─────────────────────────────────────────────────────────────────

const METHOD_CONFIG: Record<
  string,
  { label: string; color: string; bg: string; icon: keyof typeof Ionicons.glyphMap }
> = {
  CONV:    { label: "Conversation", color: "#5c6bc0", bg: "#eef0fb", icon: "chatbubble-ellipses-outline" },
  DIRECT:  { label: "Direct",       color: "#1a4594", bg: "#e8eef8", icon: "flash-outline" },
  "TF-IDF":{ label: "TF-IDF",       color: "#e65100", bg: "#fff3e0", icon: "search-outline" },
  LLM:     { label: "LLM",          color: "#6a1b9a", bg: "#f3e5f5", icon: "sparkles-outline" },
  OFFBASE: { label: "Hors sujet",   color: "#c62828", bg: "#ffebee", icon: "alert-circle-outline" },
};

const MethodBadge = ({ method, level }: { method?: string; level?: string }) => {
  if (!method) return null;
  const config = METHOD_CONFIG[method] ?? {
    label: method, color: "#666", bg: "#f0f0f0",
    icon: "hardware-chip-outline" as keyof typeof Ionicons.glyphMap,
  };
  return (
    <View style={[styles.methodBadge, { backgroundColor: config.bg }]}>
      <Ionicons name={config.icon} size={12} color={config.color} />
      <Text style={[styles.methodBadgeText, { color: config.color }]}>{config.label}</Text>
      {level ? (
        <Text style={[styles.methodLevel, { color: config.color }]}>{level.toUpperCase()}</Text>
      ) : null}
    </View>
  );
};

// ─────────────────────────────────────────────────────────────────
// Actions sur un message bot (like, dislike, copier, régénérer)
// ─────────────────────────────────────────────────────────────────

const MessageActions = ({
  text,
  question,
  score,
}: {
  text: string;
  question?: string;
  score?: number;
}) => {
  const router = useRouter();
  const [liked,    setLiked]    = useState(false);
  const [disliked, setDisliked] = useState(false);

  const handleCopy = async () => {
    await Clipboard.setStringAsync(text);
    Alert.alert("Copié", "Réponse copiée !");
  };

  const handleLike = () => {
    setLiked(!liked);
    setDisliked(false);
  };

  const handleDislike = () => {
    setDisliked(true);
    setLiked(false);
    // Passe la question et le score au feedback pour les envoyer au backend
    router.push({
      pathname: "/feedback",
      params: {
        question: question ?? "",
        score:    score != null ? String(score) : "",
      },
    } as any);
  };

  return (
    <View style={styles.actionRow}>
      <TouchableOpacity hitSlop={10} onPress={handleCopy} style={styles.actionBtn}>
        <Ionicons name="copy-outline" size={17} color="#888" />
      </TouchableOpacity>
      <TouchableOpacity hitSlop={10} onPress={handleLike} style={styles.actionBtn}>
        <Ionicons
          name={liked ? "thumbs-up" : "thumbs-up-outline"}
          size={17}
          color={liked ? "#1a4594" : "#888"}
        />
      </TouchableOpacity>
      <TouchableOpacity hitSlop={10} onPress={handleDislike} style={styles.actionBtn}>
        <Ionicons
          name={disliked ? "thumbs-down" : "thumbs-down-outline"}
          size={17}
          color={disliked ? "#e53935" : "#888"}
        />
      </TouchableOpacity>
      <TouchableOpacity hitSlop={10} style={styles.actionBtn}>
        <Ionicons name="refresh-outline" size={17} color="#888" />
      </TouchableOpacity>
    </View>
  );
};

// ─────────────────────────────────────────────────────────────────
// Indicateur "bot réfléchit"
// ─────────────────────────────────────────────────────────────────

const TypingIndicator = ({ status }: { status: string }) => {
  const label =
    status === "generating" ? "Supone AI génère une réponse…"
    : status === "searching" ? "Supone AI recherche…"
    : "Supone AI réfléchit…";

  return (
    <Animated.View entering={FadeInUp.duration(300)} style={styles.botMsgWrapper}>
      <View style={[styles.bubble, styles.botBubble, styles.typingBubble]}>
        <ActivityIndicator size="small" color="#1a4594" style={{ marginRight: 8 }} />
        <Text style={styles.typingText}>{label}</Text>
      </View>
    </Animated.View>
  );
};

// ─────────────────────────────────────────────────────────────────
// Composant principal
// ─────────────────────────────────────────────────────────────────

export default function Index() {
  const { reset, sessionId } = useLocalSearchParams();
  const insets = useSafeAreaInsets();
  const flatListRef = useRef<FlatList>(null);

  const [userName,         setUserName]         = useState("Étudiant");
  const [authToken,        setAuthToken]        = useState<string | null>(null);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [inputText,        setInputText]        = useState("");
  const [isTyping,         setIsTyping]         = useState(false);
  const [typingStatus,     setTypingStatus]     = useState("thinking");
  const [chatHistory,      setChatHistory]      = useState<Message[]>([
    { id: "1", text: "Bonjour ! Je suis Supone. Pose-moi une question sur le SUP'PTIC.", sender: "bot" },
  ]);

  const scrollToBottom = () =>
    setTimeout(() => flatListRef.current?.scrollToEnd({ animated: true }), 80);

  // Charger token + nom utilisateur au montage
  useEffect(() => {
    (async () => {
      const token = await lireToken();
      setAuthToken(token);
      const nom = await lireNomAffichage();
      setUserName(nom);
    })();
  }, []);

  // Réinitialisation (nouvelle discussion depuis le drawer)
  useEffect(() => {
    if (reset) {
      setChatHistory([
        { id: "1", text: "Bonjour ! Je suis Supone. Pose-moi une question sur le SUP'PTIC.", sender: "bot" },
      ]);
      setCurrentSessionId(null);
      setInputText("");
      setIsTyping(false);
      Keyboard.dismiss();
    }
  }, [reset]);

  // Charger une session depuis l'historique AsyncStorage
  useEffect(() => {
    if (!sessionId) return;
    (async () => {
      const saved = await AsyncStorage.getItem("chat_history");
      if (!saved) return;
      const sessions = JSON.parse(saved);
      const active = sessions.find((s: any) => s.id === sessionId);
      if (active) {
        setChatHistory(active.messages);
        setCurrentSessionId(active.id);
      }
    })();
  }, [sessionId]);

  // Sauvegarde session AsyncStorage
  const saveChatSession = async (messages: Message[]) => {
    try {
      const saved = await AsyncStorage.getItem("chat_history");
      let sessions = saved ? JSON.parse(saved) : [];
      const id = currentSessionId || Date.now().toString();
      const userFirstMsg = messages.find((m) => m.sender === "user")?.text || "Nouvelle discussion";
      const title = userFirstMsg.length > 25 ? userFirstMsg.slice(0, 25) + "…" : userFirstMsg;
      const newSession = { id, title, messages };
      const index = sessions.findIndex((s: any) => s.id === id);
      if (index > -1) sessions[index] = newSession;
      else sessions.unshift(newSession);
      await AsyncStorage.setItem("chat_history", JSON.stringify(sessions));
      if (!currentSessionId) setCurrentSessionId(id);
    } catch (e) {
      console.error("Erreur sauvegarde session :", e);
    }
  };

  // Envoi d'un message
  const handleSend = async (text?: string) => {
    const messageToSend = (text ?? inputText).trim();
    if (!messageToSend || isTyping) return;

    const newUserMsg: Message = {
      id: Date.now().toString(),
      text: messageToSend,
      sender: "user",
    };
    const withUser = [...chatHistory, newUserMsg];
    setChatHistory(withUser);
    setInputText("");
    saveChatSession(withUser);
    scrollToBottom();

    setIsTyping(true);
    setTypingStatus("thinking");
    scrollToBottom();

    try {
      const apiResponse = await askChatbot(
        messageToSend,
        authToken,   // token utilisateur — null pour les anonymes
      );

      // Mettre à jour le statut d'affichage pendant le chargement
      if (apiResponse.level === "llm") setTypingStatus("generating");

      const answer =
        apiResponse.error && !apiResponse.answer
          ? apiResponse.error
          : apiResponse.answer || "Je n'ai pas trouvé de réponse. Peux-tu reformuler ?";

      const botMsg: Message = {
        id:       (Date.now() + 1).toString(),
        text:     answer,
        sender:   "bot",
        method:   apiResponse.method  || undefined,
        level:    apiResponse.level   || undefined,
        score:    apiResponse.score,
        question: messageToSend,  // conservé pour le feedback
      };

      const finalHistory = [...withUser, botMsg];
      setChatHistory(finalHistory);
      saveChatSession(finalHistory);
      scrollToBottom();

    } catch (error: any) {
      console.error("Erreur API chatbot :", error);
      const botMsg: Message = {
        id:     (Date.now() + 1).toString(),
        text:   "Le service est temporairement indisponible. Veuillez réessayer.",
        sender: "bot",
      };
      const finalHistory = [...withUser, botMsg];
      setChatHistory(finalHistory);
      saveChatSession(finalHistory);
      scrollToBottom();
    } finally {
      setIsTyping(false);
      setTypingStatus("thinking");
    }
  };

  // ─────────────────────────────────────────────────────────────────
  // Render
  // ─────────────────────────────────────────────────────────────────
  return (
    <SafeAreaView style={styles.container} edges={["top", "left", "right"]}>
      <StatusBar barStyle="dark-content" backgroundColor="transparent" translucent />

      <KeyboardAvoidingView
        style={styles.screen}
        behavior={Platform.OS === "ios" ? "padding" : "height"}
      >
        <FlatList
          ref={flatListRef}
          data={chatHistory}
          keyExtractor={(item) => item.id}
          onContentSizeChange={scrollToBottom}
          showsVerticalScrollIndicator
          indicatorStyle="black"
          ListFooterComponent={isTyping ? <TypingIndicator status={typingStatus} /> : null}
          ListHeaderComponent={
            chatHistory.length <= 1 ? (
              <Animated.View entering={FadeInDown.duration(800)} style={styles.welcomeSection}>
                <Text style={styles.greetingText}>Bonjour {userName} !</Text>
                <Text style={styles.subGreetingText}>Par où commencer ?</Text>
                <View style={styles.suggestionsWrapper}>
                  {[
                    { label: "📚 Histoire du SUP'PTIC",  msg: "Parle-moi de l'histoire de SUP'PTIC" },
                    { label: "🏠 Louer une chambre",     msg: "Comment louer une chambre ?" },
                    { label: "🎯 S'inscrire à un club",  msg: "Quels sont les clubs disponibles ?" },
                    { label: "❓ Poser une question",    msg: "J'ai une question" },
                  ].map((item, idx) => (
                    <TouchableOpacity
                      key={idx}
                      style={styles.suggestionChip}
                      onPress={() => handleSend(item.msg)}
                      activeOpacity={0.75}
                    >
                      <Text style={styles.suggestionText}>{item.label}</Text>
                    </TouchableOpacity>
                  ))}
                </View>
              </Animated.View>
            ) : null
          }
          renderItem={({ item }) => (
            <Animated.View
              entering={FadeInUp.duration(350)}
              style={item.sender === "user" ? styles.userMsgWrapper : styles.botMsgWrapper}
            >
              <View style={[styles.bubble, item.sender === "user" ? styles.userBubble : styles.botBubble]}>
                <Text style={item.sender === "user" ? styles.userText : styles.botText}>
                  {item.text}
                </Text>
                <View style={item.sender === "user" ? styles.userArrow : styles.botArrow} />
              </View>
              {item.sender === "bot" && item.method && (
                <MethodBadge method={item.method} level={item.level} />
              )}
              {item.sender === "bot" && item.id !== "1" && (
                <Animated.View entering={FadeInUp.delay(200)}>
                  <MessageActions
                    text={item.text}
                    question={item.question}
                    score={item.score}
                  />
                </Animated.View>
              )}
            </Animated.View>
          )}
          contentContainerStyle={styles.listContent}
        />

        {/* Zone de saisie */}
        <View style={[styles.inputContainer, { paddingBottom: Math.max(insets.bottom, 8) }]}>
          <View style={styles.inputArea}>
            <Ionicons name="add-circle-outline" size={22} color="#aaa" style={styles.inputIcon} />
            <TextInput
              style={styles.input}
              placeholder="Écrivez votre message..."
              placeholderTextColor="#aaa"
              value={inputText}
              onChangeText={setInputText}
              multiline
              returnKeyType="send"
              blurOnSubmit={false}
              onSubmitEditing={() => handleSend()}
            />
            <TouchableOpacity
              onPress={() => handleSend()}
              disabled={!inputText.trim() || isTyping}
              style={[styles.sendButton, { opacity: inputText.trim() && !isTyping ? 1 : 0.35 }]}
              activeOpacity={0.8}
            >
              <Ionicons name="send" size={17} color="#fff" />
            </TouchableOpacity>
          </View>
          <Text style={styles.disclaimer}>Supone est une IA et peut se tromper.</Text>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

// ─────────────────────────────────────────────────────────────────
// Styles (identiques à l'original)
// ─────────────────────────────────────────────────────────────────

const PRIMARY    = "#1a4594";
const BOT_BUBBLE = "#f1f3f5";

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#f8faff",
    paddingTop: Platform.OS === "android" ? (StatusBar.currentHeight ?? 0) : 0,
  },
  screen:      { flex: 1 },
  listContent: { padding: 16, paddingBottom: 8, flexGrow: 1 },

  welcomeSection:   { marginTop: 10, marginBottom: 28 },
  greetingText:     { fontSize: 16, color: "#666" },
  subGreetingText:  { fontSize: 24, fontWeight: "bold", color: "#000", marginBottom: 18 },
  suggestionsWrapper: { marginTop: 8, gap: 8 },
  suggestionChip: {
    backgroundColor: "#fff", paddingVertical: 12, paddingHorizontal: 18,
    borderRadius: 20, alignSelf: "flex-start", elevation: 2,
    shadowColor: "#000", shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.06, shadowRadius: 4,
    borderWidth: 1, borderColor: "rgba(0,0,0,0.08)", marginBottom: 2,
  },
  suggestionText: { color: "#333", fontWeight: "500", fontSize: 14 },

  userMsgWrapper: { alignSelf: "flex-end",  marginBottom: 18, maxWidth: "80%" },
  botMsgWrapper:  { alignSelf: "flex-start", marginBottom: 18, maxWidth: "85%" },

  bubble:     { padding: 14, borderRadius: 18, position: "relative" },
  userBubble: {
    backgroundColor: PRIMARY, borderBottomRightRadius: 5,
    shadowColor: PRIMARY, shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.2, shadowRadius: 10, elevation: 4,
  },
  botBubble: {
    backgroundColor: BOT_BUBBLE, borderBottomLeftRadius: 5,
    shadowColor: "#000", shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05, shadowRadius: 5, elevation: 2,
  },
  userArrow: {
    position: "absolute", bottom: 0, right: -6,
    width: 0, height: 0,
    borderTopWidth: 10, borderTopColor: "transparent",
    borderLeftWidth: 12, borderLeftColor: PRIMARY,
  },
  botArrow: {
    position: "absolute", bottom: 0, left: -6,
    width: 0, height: 0,
    borderTopWidth: 10, borderTopColor: "transparent",
    borderRightWidth: 12, borderRightColor: BOT_BUBBLE,
  },

  userText:    { color: "#fff", fontSize: 15, lineHeight: 22 },
  botText:     { color: "#111", fontSize: 15, lineHeight: 22 },
  typingBubble: { flexDirection: "row", alignItems: "center", paddingVertical: 10 },
  typingText:   { color: "#777", fontSize: 13, fontStyle: "italic" },

  actionRow: { flexDirection: "row", gap: 4, marginTop: 8, paddingLeft: 2 },
  actionBtn:  { padding: 7, borderRadius: 20, backgroundColor: "rgba(0,0,0,0.04)" },

  methodBadge: {
    flexDirection: "row", alignItems: "center", alignSelf: "flex-start",
    gap: 4, marginTop: 6, paddingHorizontal: 10, paddingVertical: 4, borderRadius: 12,
  },
  methodBadgeText: { fontSize: 11, fontWeight: "600" },
  methodLevel:     { fontSize: 10, fontWeight: "500", opacity: 0.75, marginLeft: 2 },

  inputContainer: {
    backgroundColor: "#fff", paddingHorizontal: 14, paddingTop: 10,
    borderTopWidth: 1, borderTopColor: "#eee",
  },
  inputArea: {
    flexDirection: "row", alignItems: "center",
    backgroundColor: "#f0f2f5", borderRadius: 24,
    paddingHorizontal: 12, paddingVertical: 6, minHeight: 44,
  },
  inputIcon:   { marginRight: 6 },
  input: {
    flex: 1, color: "#000", fontSize: 15, lineHeight: 20,
    maxHeight: 100, paddingVertical: 4,
  },
  sendButton: {
    marginLeft: 8, backgroundColor: PRIMARY,
    width: 36, height: 36, borderRadius: 18,
    alignItems: "center", justifyContent: "center", flexShrink: 0,
  },
  disclaimer: { textAlign: "center", fontSize: 10, color: "#bbb", marginTop: 6, marginBottom: 2 },
});
