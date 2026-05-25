import { Ionicons } from "@expo/vector-icons";
import AsyncStorage from "@react-native-async-storage/async-storage";
import { DrawerActions } from "@react-navigation/native";
import * as Clipboard from "expo-clipboard";
import { useLocalSearchParams, useRouter, useNavigation } from "expo-router";
import React, { useEffect, useRef, useState } from "react";
import { askChatbotStream } from "../../Service/chatbotApi";
import {
  Alert,
  FlatList,
  KeyboardAvoidingView,
  Platform,
  StatusBar,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from "react-native";
import Animated, {
  Easing,
  FadeInDown,
  FadeInUp,
  useAnimatedStyle,
  useSharedValue,
  withRepeat,
  withTiming,
} from "react-native-reanimated";
import {
  SafeAreaView,
  useSafeAreaInsets,
} from "react-native-safe-area-context";

const VS_CODE_BLUE = "#007ACC";
const BOT_BUBBLE = "#f1f3f5";
const BACKGROUND_COLOR = "#f8faff";

type Message = {
  id: string;
  text: string;
  sender: "user" | "bot";
};

// --- Composant d'actions (copier, likes, etc.) ---
const MessageActions = ({ text }: { text: string }) => {
  const router = useRouter();
  const [liked, setLiked] = useState(false);
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
    router.push("/feedback");
  };

  return (
    <View style={styles.actionRow}>
      <TouchableOpacity onPress={handleCopy} style={styles.actionBtn}>
        <Ionicons name="copy-outline" size={17} color="#888" />
      </TouchableOpacity>
      <TouchableOpacity onPress={handleLike} style={styles.actionBtn}>
        <Ionicons
          name={liked ? "thumbs-up" : "thumbs-up-outline"}
          size={17}
          color={liked ? VS_CODE_BLUE : "#888"}
        />
      </TouchableOpacity>
      <TouchableOpacity onPress={handleDislike} style={styles.actionBtn}>
        <Ionicons
          name={disliked ? "thumbs-down" : "thumbs-down-outline"}
          size={17}
          color={disliked ? "#e53935" : "#888"}
        />
      </TouchableOpacity>
      <TouchableOpacity style={styles.actionBtn}>
        <Ionicons name="refresh-outline" size={17} color="#888" />
      </TouchableOpacity>
    </View>
  );
};

// --- Spinner circulaire (animation de chargement) ---
const CircularSpinner = () => {
  const DOT_COUNT = 7;
  const RADIUS = 13;
  const rotation = useSharedValue(0);

  useEffect(() => {
    rotation.value = withRepeat(
      withTiming(360, { duration: 1100, easing: Easing.linear }),
      -1,
      false,
    );
  }, []);

  const animStyle = useAnimatedStyle(() => ({
    transform: [{ rotate: `${rotation.value}deg` }],
  }));

  return (
    <View style={spinnerStyles.shell}>
      <Animated.View style={[spinnerStyles.wheel, animStyle]}>
        {Array.from({ length: DOT_COUNT }).map((_, i) => {
          const angle = (i / DOT_COUNT) * 2 * Math.PI;
          const x = RADIUS * Math.cos(angle);
          const y = RADIUS * Math.sin(angle);
          const opacity = 0.2 + (i / DOT_COUNT) * 0.8;
          return (
            <View
              key={i}
              style={[
                spinnerStyles.dot,
                { opacity, transform: [{ translateX: x }, { translateY: y }] },
              ]}
            />
          );
        })}
      </Animated.View>
    </View>
  );
};

const spinnerStyles = StyleSheet.create({
  shell: {
    width: 46,
    height: 46,
    justifyContent: "center",
    alignItems: "center",
    marginBottom: 6,
  },
  wheel: {
    width: 7,
    height: 7,
    justifyContent: "center",
    alignItems: "center",
  },
  dot: {
    position: "absolute",
    width: 7,
    height: 7,
    borderRadius: 3.5,
    backgroundColor: VS_CODE_BLUE,
  },
});

// --- Indicateur de frappe : soit spinner, soit texte en cours de streaming ---
const TypingIndicator = ({ text }: { text: string }) => (
  <Animated.View entering={FadeInUp.duration(300)} style={styles.botMsgWrapper}>
    <View style={[styles.bubble, styles.botBubble]}>
      {text ? <Text style={styles.botText}>{text}</Text> : <CircularSpinner />}
    </View>
  </Animated.View>
);

// --- Simule l'affichage progressif d'un texte (pour les réponses non-LLM) ---
const simulateStreaming = async (
  fullText: string,
  onToken: (token: string) => void,
  onDone: () => void,
  delayMs = 30,
) => {
  let accumulated = "";
  const words = fullText.split(/(\s+)/); // garde les espaces
  for (const chunk of words) {
    accumulated += chunk;
    onToken(accumulated);
    await new Promise((resolve) => setTimeout(resolve, delayMs));
  }
  onDone();
};

// --- COMPOSANT PRINCIPAL ---
export default function ChatScreen() {
  const { reset, sessionId } = useLocalSearchParams();
  const navigation = useNavigation();
  const router = useRouter();
  const [userName, setUserName] = useState("Étudiant");
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [inputText, setInputText] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [currentBotId, setCurrentBotId] = useState<string | null>(null);
  const [chatHistory, setChatHistory] = useState<Message[]>([
    {
      id: "1",
      text: "Bonjour ! Je suis Supone. Pose-moi une question sur le SUP'PTIC.",
      sender: "bot",
    },
  ]);

  const insets = useSafeAreaInsets();
  const flatListRef = useRef<FlatList>(null);

  const scrollToBottom = () => {
    setTimeout(() => flatListRef.current?.scrollToEnd({ animated: true }), 100);
  };

  const openMenu = () => {
    const parent = navigation.getParent();
    if (parent) parent.dispatch(DrawerActions.openDrawer());
    else navigation.dispatch(DrawerActions.openDrawer());
  };

  // --- Gestion de la session (reset, chargement, sauvegarde) ---
  useEffect(() => {
    if (reset === "true") {
      setChatHistory([
        {
          id: "1",
          text: "Bonjour ! Je suis Supone. Pose-moi une question sur le SUP'PTIC.",
          sender: "bot",
        },
      ]);
      setCurrentSessionId(null);
      setInputText("");
      setIsTyping(false);
    } else if (!sessionId && !reset) {
      const restoreLast = async () => {
        try {
          const saved = await AsyncStorage.getItem("chat_history");
          if (saved) {
            const sessions = JSON.parse(saved);
            if (sessions.length > 0) {
              setChatHistory(sessions[0].messages);
              setCurrentSessionId(sessions[0].id);
            }
          }
        } catch (e) {
          console.error(e);
        }
      };
      restoreLast();
    }
  }, [reset, sessionId]);

  useEffect(() => {
    if (!currentSessionId && chatHistory.length === 1) {
      const saveWelcome = async () => {
        try {
          const id = Date.now().toString();
          const newSession = {
            id,
            title: "Nouvelle discussion",
            messages: chatHistory,
          };
          const saved = await AsyncStorage.getItem("chat_history");
          let sessions = saved ? JSON.parse(saved) : [];
          sessions.unshift(newSession);
          await AsyncStorage.setItem("chat_history", JSON.stringify(sessions));
          setCurrentSessionId(id);
        } catch (e) {
          console.error(e);
        }
      };
      saveWelcome();
    }
  }, [chatHistory, currentSessionId]);

  useEffect(() => {
    if (sessionId) {
      const loadSession = async () => {
        const saved = await AsyncStorage.getItem("chat_history");
        if (saved) {
          const sessions = JSON.parse(saved);
          const active = sessions.find((s: any) => s.id === sessionId);
          if (active) {
            setChatHistory(active.messages);
            setCurrentSessionId(active.id);
          }
        }
      };
      loadSession();
    }
  }, [sessionId]);

  useEffect(() => {
    const fetchUser = async () => {
      const savedName = await AsyncStorage.getItem("user_name");
      if (savedName) setUserName(savedName);
    };
    fetchUser();
  }, []);

  const saveChatSession = async (messages: Message[]) => {
    try {
      const saved = await AsyncStorage.getItem("chat_history");
      let sessions = saved ? JSON.parse(saved) : [];
      const id = currentSessionId || Date.now().toString();
      const userFirstMsg =
        messages.find((m) => m.sender === "user")?.text ||
        "Nouvelle discussion";
      const title =
        userFirstMsg.length > 25
          ? userFirstMsg.substring(0, 25) + "…"
          : userFirstMsg;
      const newSession = { id, title, messages };
      const index = sessions.findIndex((s: any) => s.id === id);
      if (index > -1) sessions[index] = newSession;
      else sessions.unshift(newSession);
      await AsyncStorage.setItem("chat_history", JSON.stringify(sessions));
      if (!currentSessionId) setCurrentSessionId(id);
    } catch (e) {
      console.error(e);
    }
  };

  // --- Envoi du message ---
  const handleSend = async (text?: string) => {
    const messageToSend = (text ?? inputText).trim();
    if (!messageToSend || isTyping) return;

    // Ajouter le message utilisateur
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

    const botMsgId = (Date.now() + 1).toString();
    setCurrentBotId(botMsgId);
    setIsTyping(true);

    let accumulated = "";
    let isLlamaStream = false;

    const updateBotMessage = (newText: string) => {
      setChatHistory((prev) => {
        if (!prev.some((m) => m.id === botMsgId)) {
          const newBot: Message = {
            id: botMsgId,
            text: newText,
            sender: "bot",
          };
          const updated = [...prev, newBot];
          saveChatSession(updated);
          return updated;
        }
        const updated = prev.map((m) =>
          m.id === botMsgId ? { ...m, text: newText } : m,
        );
        saveChatSession(updated);
        return updated;
      });
      scrollToBottom();
    };

    try {
      await askChatbotStream(
        messageToSend,
        (status) => {},
        async (meta) => {
          console.log("[SSE] meta", meta);
          if (meta.method !== "LLM" && meta.answer) {
            updateBotMessage(""); // ← message vide avec spinner
            await new Promise((resolve) => setTimeout(resolve, 300));
            simulateStreaming(
              meta.answer,
              updateBotMessage,
              () => {
                setIsTyping(false);
                setCurrentBotId(null);
              },
              25,
            );
          }
        },
        (token) => {
          isLlamaStream = true;
          accumulated += token;
          updateBotMessage(accumulated);
        },
        (elapsed_ms) => {
          if (isLlamaStream) {
            setIsTyping(false);
            setCurrentBotId(null);
          }
        },
        (error) => {
          console.error("Erreur API :", error);
          updateBotMessage("Erreur serveur. Veuillez réessayer plus tard.");
          setIsTyping(false);
          setCurrentBotId(null);
          Alert.alert("Erreur", "Le backend est indisponible.");
        },
      );
    } catch (error) {
      updateBotMessage("Erreur serveur.");
      setIsTyping(false);
      setCurrentBotId(null);
    }
  };

  return (
    <SafeAreaView style={styles.container} edges={["top", "left", "right"]}>
      <StatusBar
        barStyle="light-content"
        backgroundColor={VS_CODE_BLUE}
        translucent
      />

      <View style={styles.customHeader}>
        <TouchableOpacity onPress={openMenu} style={styles.headerIcon}>
          <Ionicons name="menu" size={28} color="#fff" />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Supone ai</Text>
        <TouchableOpacity
          onPress={() => Alert.alert("Profil", `Connecté : ${userName}`)}
          style={styles.headerIcon}
        >
          <Ionicons name="person-circle-outline" size={30} color="#fff" />
        </TouchableOpacity>
      </View>

      <KeyboardAvoidingView
        style={styles.screen}
        behavior={Platform.OS === "ios" ? "padding" : "height"}
      >
        <FlatList
          ref={flatListRef}
          data={chatHistory}
          keyExtractor={(item) => item.id}
          onContentSizeChange={scrollToBottom}
          ListFooterComponent={
            isTyping &&
            currentBotId &&
            !chatHistory.some((m) => m.id === currentBotId && m.text) ? (
              <TypingIndicator text="" />
            ) : null
          }
          ListHeaderComponent={
            chatHistory.length <= 1 ? (
              <Animated.View
                entering={FadeInDown.duration(800)}
                style={styles.welcomeSection}
              >
                <Text style={styles.greetingText}>Bonjour {userName} !</Text>
                <Text style={styles.subGreetingText}>Besoin d'aide ?</Text>
                <View style={styles.suggestionsWrapper}>
                  {[
                    "📚 Histoire du SUP'PTIC",
                    "🏠 Logement étudiant",
                    "🎯 Clubs",
                  ].map((item, idx) => (
                    <TouchableOpacity
                      key={idx}
                      style={styles.suggestionChip}
                      onPress={() => handleSend(item)}
                    >
                      <Text style={styles.suggestionText}>{item}</Text>
                    </TouchableOpacity>
                  ))}
                </View>
              </Animated.View>
            ) : null
          }
          renderItem={({ item }) => (
            <Animated.View
              entering={
                item.sender === "bot"
                  ? FadeInDown.springify().damping(15)
                  : FadeInUp.duration(350)
              }
              style={
                item.sender === "user"
                  ? styles.userMsgWrapper
                  : styles.botMsgWrapper
              }
            >
              <View
                style={[
                  styles.bubble,
                  item.sender === "user" ? styles.userBubble : styles.botBubble,
                ]}
              >
                <Text
                  style={
                    item.sender === "user" ? styles.userText : styles.botText
                  }
                >
                  {item.text}
                </Text>
              </View>
              {item.sender === "bot" && item.id !== "1" && (
                <MessageActions text={item.text} />
              )}
            </Animated.View>
          )}
          contentContainerStyle={styles.listContent}
        />

        <View
          style={[
            styles.inputContainer,
            { paddingBottom: Math.max(insets.bottom, 12) },
          ]}
        >
          <View style={styles.inputArea}>
            <TextInput
              style={styles.input}
              placeholder="Pose une question..."
              value={inputText}
              onChangeText={setInputText}
              multiline
            />
            <TouchableOpacity
              onPress={() => handleSend()}
              disabled={!inputText.trim() || isTyping}
              style={styles.sendButton}
            >
              <Ionicons name="send" size={18} color="#fff" />
            </TouchableOpacity>
          </View>
          <Text style={styles.footerDisclaimer}>Supone peut se tromper.</Text>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: BACKGROUND_COLOR },
  screen: { flex: 1 },
  customHeader: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: 16,
    height: 64,
    backgroundColor: VS_CODE_BLUE,
    elevation: 4,
  },
  headerTitle: { fontSize: 20, fontWeight: "bold", color: "#fff" },
  headerIcon: { padding: 6 },
  listContent: { padding: 20, flexGrow: 1 },
  welcomeSection: { marginTop: 45, marginBottom: 40, paddingHorizontal: 10 },
  greetingText: { fontSize: 24, color: "#64748b", marginBottom: 6 },
  subGreetingText: {
    fontSize: 34,
    fontWeight: "600",
    color: "#1e293b",
    marginBottom: 35,
  },
  suggestionsWrapper: { gap: 12 },
  suggestionChip: {
    backgroundColor: "#fff",
    paddingVertical: 15,
    paddingHorizontal: 20,
    borderRadius: 25,
    alignSelf: "flex-start",
    borderWidth: 1,
    borderColor: "#e2e8f0",
  },
  suggestionText: { color: "#334155", fontSize: 16, fontWeight: "500" },
  userMsgWrapper: { alignSelf: "flex-end", marginBottom: 20, maxWidth: "80%" },
  botMsgWrapper: { alignSelf: "flex-start", marginBottom: 20, maxWidth: "85%" },
  bubble: { padding: 16, borderRadius: 20 },
  userBubble: { backgroundColor: VS_CODE_BLUE, borderBottomRightRadius: 4 },
  botBubble: { backgroundColor: BOT_BUBBLE, borderBottomLeftRadius: 4 },
  userText: { color: "#fff", fontSize: 16 },
  botText: { color: "#1e293b", fontSize: 16 },
  footerDisclaimer: {
    marginTop: 8,
    color: "#94a3b8",
    fontSize: 12,
    textAlign: "center",
    fontStyle: "italic",
  },
  actionRow: { flexDirection: "row", gap: 6, marginTop: 8 },
  actionBtn: {
    padding: 8,
    borderRadius: 20,
    backgroundColor: "rgba(0,0,0,0.03)",
  },
  inputContainer: {
    backgroundColor: BACKGROUND_COLOR,
    paddingHorizontal: 16,
    paddingTop: 10,
  },
  inputArea: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "#fff",
    borderRadius: 30,
    paddingHorizontal: 18,
    minHeight: 58,
    borderWidth: 1,
    borderColor: "#e2e8f0",
  },
  input: { flex: 1, fontSize: 16, paddingVertical: 10 },
  sendButton: {
    backgroundColor: VS_CODE_BLUE,
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: "center",
    justifyContent: "center",
    marginLeft: 10,
  },
});
