import { Ionicons } from "@expo/vector-icons";
import AsyncStorage from "@react-native-async-storage/async-storage";
import { DrawerActions } from "@react-navigation/native";
import * as Clipboard from "expo-clipboard";
import { useLocalSearchParams, useRouter, useNavigation } from "expo-router";
import React, { useEffect, useRef, useState } from "react";
import { askChatbot } from "../Service/api";
import {
  ActivityIndicator,
  Alert,
  Animated,
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

import AnimatedRN, { FadeInDown, FadeInUp } from "react-native-reanimated";
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
    router.push("/feedback" as any);
  };

  return (
    <View style={styles.actionRow}>
      <TouchableOpacity hitSlop={10} onPress={handleCopy} style={styles.actionBtn}>
        <Ionicons name="copy-outline" size={17} color="#888" />
      </TouchableOpacity>
      <TouchableOpacity hitSlop={10} onPress={handleLike} style={styles.actionBtn}>
        <Ionicons name={liked ? "thumbs-up" : "thumbs-up-outline"} size={17} color={liked ? VS_CODE_BLUE : "#888"} />
      </TouchableOpacity>
      <TouchableOpacity hitSlop={10} onPress={handleDislike} style={styles.actionBtn}>
        <Ionicons name={disliked ? "thumbs-down" : "thumbs-down-outline"} size={17} color={disliked ? "#e53935" : "#888"} />
      </TouchableOpacity>
      <TouchableOpacity hitSlop={10} style={styles.actionBtn}>
        <Ionicons name="refresh-outline" size={17} color="#888" />
      </TouchableOpacity>
    </View>
  );
};

// ============================================================
// ANIMATION "Supone réfléchit" — 3 points qui rebondissent
// en vague l'un après l'autre
// ============================================================
const TypingIndicator = () => {
  // Une valeur animée par point
  const dot1 = useRef(new Animated.Value(0)).current;
  const dot2 = useRef(new Animated.Value(0)).current;
  const dot3 = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    // Anime un point en boucle avec un délai de départ
    const animer = (dot: Animated.Value, delai: number) => {
      Animated.loop(
        Animated.sequence([
          // Pause initiale pour décaler chaque point
          Animated.delay(delai),
          // Monte le point vers le haut
          Animated.timing(dot, {
            toValue: -7,
            duration: 280,
            useNativeDriver: true,
          }),
          // Redescend le point à sa position initiale
          Animated.timing(dot, {
            toValue: 0,
            duration: 280,
            useNativeDriver: true,
          }),
          // Pause avant de recommencer la boucle
          Animated.delay(500),
        ])
      ).start();
    };

    // Chaque point démarre avec 180ms de décalage
    animer(dot1, 0);
    animer(dot2, 180);
    animer(dot3, 360);
  }, []);

  return (
    <AnimatedRN.View entering={FadeInUp.duration(300)} style={styles.botMsgWrapper}>
      <View style={[styles.bubble, styles.botBubble, styles.typingBubble]}>
        {/* Texte */}
        <Text style={styles.typingText}>Supone réfléchit</Text>

        {/* Point 1 */}
        <Animated.View style={{ transform: [{ translateY: dot1 }] }}>
          <View style={styles.typingDot} />
        </Animated.View>

        {/* Point 2 */}
        <Animated.View style={{ transform: [{ translateY: dot2 }] }}>
          <View style={styles.typingDot} />
        </Animated.View>

        {/* Point 3 */}
        <Animated.View style={{ transform: [{ translateY: dot3 }] }}>
          <View style={styles.typingDot} />
        </Animated.View>
      </View>
    </AnimatedRN.View>
  );
};

export default function Index() {
  const { reset, sessionId } = useLocalSearchParams();
  const navigation = useNavigation();
  const router = useRouter();
  const [userName, setUserName] = useState("Étudiant");
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [inputText, setInputText] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [chatHistory, setChatHistory] = useState<Message[]>([
    { id: "1", text: "Bonjour ! Je suis Supone. Pose-moi une question sur le SUP'PTIC.", sender: "bot" },
  ]);

  const insets = useSafeAreaInsets();
  const flatListRef = useRef<FlatList>(null);

  const scrollToBottom = () => {
    setTimeout(() => flatListRef.current?.scrollToEnd({ animated: true }), 100);
  };

  const openMenu = () => {
    const parent = navigation.getParent();
    if (parent) {
      parent.dispatch(DrawerActions.openDrawer());
    } else {
      navigation.dispatch(DrawerActions.openDrawer());
    }
  };

  useEffect(() => {
  if (reset === "true") {
    // Nouvelle discussion voulue explicitement
    setChatHistory([{ id: "1", text: "Bonjour ! Je suis Supone. Pose-moi une question sur le SUP'PTIC.", sender: "bot" }]);
    setCurrentSessionId(null);
    setInputText("");
    setIsTyping(false);
  } else if (!sessionId && !reset) {
    // Retour depuis feedback ou autre page — restaure la dernière session
    const restoreLast = async () => {
      try {
        const saved = await AsyncStorage.getItem("chat_history");
        if (saved) {
          const sessions = JSON.parse(saved);
          if (sessions.length > 0) {
            const last = sessions[0]; // la plus récente
            setChatHistory(last.messages);
            setCurrentSessionId(last.id);
          }
        }
      } catch (e) {
        console.error(e);
      }
    };
    restoreLast();
  }
}, [reset]);

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
      const userFirstMsg = messages.find((m) => m.sender === "user")?.text || "Nouvelle discussion";
      const title = userFirstMsg.length > 25 ? userFirstMsg.substring(0, 25) + "…" : userFirstMsg;
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

  const handleSend = async (text?: string) => {
    const messageToSend = (text ?? inputText).trim();
    if (!messageToSend || isTyping) return;

    const newUserMsg: Message = { id: Date.now().toString(), text: messageToSend, sender: "user" };
    const withUser = [...chatHistory, newUserMsg];
    setChatHistory(withUser);
    setInputText("");
    saveChatSession(withUser);
    scrollToBottom();
    setIsTyping(true);

    try {
      const apiResponse = await askChatbot(messageToSend, 3);
      const answer = apiResponse.results.length > 0 ? apiResponse.results[0].answer : "Désolé, je n'ai pas compris.";
      const botMsg: Message = { id: (Date.now() + 1).toString(), text: answer, sender: "bot" };
      const finalHistory = [...withUser, botMsg];
      setChatHistory(finalHistory);
      saveChatSession(finalHistory);
    } catch (error) {
      setChatHistory([...withUser, { id: Date.now().toString(), text: "Erreur serveur.", sender: "bot" }]);
    } finally {
      setIsTyping(false);
      scrollToBottom();
    }
  };

  return (
    <SafeAreaView style={styles.container} edges={["top", "left", "right"]}>
      <StatusBar barStyle="light-content" backgroundColor={VS_CODE_BLUE} translucent />

      <View style={styles.customHeader}>
        <TouchableOpacity onPress={openMenu} style={styles.headerIcon}>
          <Ionicons name="menu" size={28} color="#fff" />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Supone ai</Text>
        <TouchableOpacity onPress={() => router.push('/profile')} style={styles.headerIcon}>
          <Ionicons name="person-circle-outline" size={30} color="#fff" />
        </TouchableOpacity>
      </View>

      <KeyboardAvoidingView style={styles.screen} behavior={Platform.OS === "ios" ? "padding" : "height"}>
        <FlatList
          ref={flatListRef}
          data={chatHistory}
          keyExtractor={(item) => item.id}
          onContentSizeChange={scrollToBottom}
          ListFooterComponent={isTyping ? <TypingIndicator /> : null}
          ListHeaderComponent={
            chatHistory.length <= 1 ? (
              <AnimatedRN.View entering={FadeInDown.duration(800)} style={styles.welcomeSection}>
                <Text style={styles.greetingText}>Bonjour {userName} !</Text>
                <Text style={styles.subGreetingText}>Besoin d'aide ?</Text>
                <View style={styles.suggestionsWrapper}>
                  {["📚 Histoire du SUP'PTIC", "🏠 Logement étudiant", "🎯 Clubs"].map((item, idx) => (
                    <TouchableOpacity key={idx} style={styles.suggestionChip} onPress={() => handleSend(item)}>
                      <Text style={styles.suggestionText}>{item}</Text>
                    </TouchableOpacity>
                  ))}
                </View>
              </AnimatedRN.View>
            ) : null
          }
          renderItem={({ item }) => (
            <AnimatedRN.View entering={FadeInUp.duration(350)} style={item.sender === "user" ? styles.userMsgWrapper : styles.botMsgWrapper}>
              <View style={[styles.bubble, item.sender === "user" ? styles.userBubble : styles.botBubble]}>
                <Text style={item.sender === "user" ? styles.userText : styles.botText}>{item.text}</Text>
              </View>
              {item.sender === "bot" && item.id !== "1" && <MessageActions text={item.text} />}
            </AnimatedRN.View>
          )}
          contentContainerStyle={styles.listContent}
        />

        <View style={[styles.inputContainer, { paddingBottom: Math.max(insets.bottom, 12) }]}>
          <View style={styles.inputArea}>
            <TextInput
              style={styles.input}
              placeholder="Pose une question..."
              value={inputText}
              onChangeText={setInputText}
              multiline
            />
            <TouchableOpacity onPress={() => handleSend()} disabled={!inputText.trim() || isTyping} style={styles.sendButton}>
              <Ionicons name="send" size={18} color="#fff" />
            </TouchableOpacity>
          </View>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: BACKGROUND_COLOR },
  screen: { flex: 1 },
  customHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    height: 64,
    backgroundColor: VS_CODE_BLUE,
    elevation: 4,
  },
  headerTitle: { fontSize: 20, fontWeight: 'bold', color: '#fff' },
  headerIcon: { padding: 6 },
  listContent: { padding: 20, flexGrow: 1 },
  welcomeSection: { marginTop: 45, marginBottom: 40, paddingHorizontal: 10 },
  greetingText: { fontSize: 24, color: "#64748b", marginBottom: 6 },
  subGreetingText: { fontSize: 34, fontWeight: "600", color: "#1e293b", marginBottom: 35 },
  suggestionsWrapper: { gap: 12 },
  suggestionChip: {
    backgroundColor: "#fff",
    paddingVertical: 15,
    paddingHorizontal: 20,
    borderRadius: 25,
    alignSelf: "flex-start",
    borderWidth: 1,
    borderColor: "#e2e8f0"
  },
  suggestionText: { color: "#334155", fontSize: 16, fontWeight: "500" },
  userMsgWrapper: { alignSelf: "flex-end", marginBottom: 20, maxWidth: "80%" },
  botMsgWrapper: { alignSelf: "flex-start", marginBottom: 20, maxWidth: "85%" },
  bubble: { padding: 16, borderRadius: 20 },
  userBubble: { backgroundColor: VS_CODE_BLUE, borderBottomRightRadius: 4 },
  botBubble: { backgroundColor: BOT_BUBBLE, borderBottomLeftRadius: 4 },
  userText: { color: "#fff", fontSize: 16 },
  botText: { color: "#1e293b", fontSize: 16 },
  actionRow: { flexDirection: "row", gap: 6, marginTop: 8 },
  actionBtn: { padding: 8, borderRadius: 20, backgroundColor: "rgba(0,0,0,0.03)" },
  inputContainer: { backgroundColor: BACKGROUND_COLOR, paddingHorizontal: 16, paddingTop: 10 },
  inputArea: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "#fff",
    borderRadius: 30,
    paddingHorizontal: 18,
    minHeight: 58,
    borderWidth: 1,
    borderColor: "#e2e8f0"
  },
  input: { flex: 1, fontSize: 16, paddingVertical: 10 },
  sendButton: {
    backgroundColor: VS_CODE_BLUE,
    width: 40, height: 40,
    borderRadius: 20,
    alignItems: "center",
    justifyContent: "center",
    marginLeft: 10
  },
  // Styles de l'animation TypingIndicator
  typingBubble: { flexDirection: "row", alignItems: "center", gap: 4 },
  typingText: { color: "#94a3b8", fontSize: 14, fontStyle: "italic", marginRight: 4 },
  typingDot: {
    width: 7,
    height: 7,
    borderRadius: 4,
    backgroundColor: VS_CODE_BLUE,
  },
});