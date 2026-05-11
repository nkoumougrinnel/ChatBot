import { Ionicons } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import * as Clipboard from 'expo-clipboard';
import { useLocalSearchParams, useRouter } from 'expo-router';
import React, { useEffect, useRef, useState } from 'react';
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
} from 'react-native';

import Animated, { FadeInDown, FadeInUp } from 'react-native-reanimated';
import { SafeAreaView, useSafeAreaInsets } from 'react-native-safe-area-context';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------
type Message = {
  id: string;
  text: string;
  sender: 'user' | 'bot';
};

const MessageActions = ({ text }: { text: string }) => {
  const router = useRouter();
  const [liked,    setLiked]    = useState(false);
  const [disliked, setDisliked] = useState(false);

  const handleCopy = async () => {
    await Clipboard.setStringAsync(text);
    Alert.alert('Copié', 'Réponse copiée !');
  };

  const handleLike = () => { setLiked(!liked); setDisliked(false); };

  const handleDislike = () => {
    setDisliked(true);
    setLiked(false);
    router.push('/feedback' as any);
  };

  return (
    <View style={styles.actionRow}>
      {/* Copier */}
      <TouchableOpacity hitSlop={10} onPress={handleCopy} style={styles.actionBtn}>
        <Ionicons name="copy-outline" size={17} color="#888" />
      </TouchableOpacity>

      {/* Pouce haut */}
      <TouchableOpacity hitSlop={10} onPress={handleLike} style={styles.actionBtn}>
        <Ionicons
          name={liked ? 'thumbs-up' : 'thumbs-up-outline'}
          size={17}
          color={liked ? '#1a4594' : '#888'}
        />
      </TouchableOpacity>

      {/* Pouce bas direction le feedback */}
      <TouchableOpacity hitSlop={10} onPress={handleDislike} style={styles.actionBtn}>
        <Ionicons
          name={disliked ? 'thumbs-down' : 'thumbs-down-outline'}
          size={17}
          color={disliked ? '#e53935' : '#888'}
        />
      </TouchableOpacity>

      {/* Régénérer */}
      <TouchableOpacity hitSlop={10} style={styles.actionBtn}>
        <Ionicons name="refresh-outline" size={17} color="#888" />
      </TouchableOpacity>
    </View>
  );
};

// ---------------------------------------------------------------------------
// Indicateur de saisi
// ---------------------------------------------------------------------------
const TypingIndicator = () => (
  <Animated.View entering={FadeInUp.duration(300)} style={styles.botMsgWrapper}>
    <View style={[styles.bubble, styles.botBubble, styles.typingBubble]}>
      <ActivityIndicator size="small" color="#1a4594" style={{ marginRight: 8 }} />
      <Text style={styles.typingText}>Sup One AI réfléchit…</Text>
    </View>
  </Animated.View>
);

// ---------------------------------------------------------------------------
// Composant principal
// ---------------------------------------------------------------------------
export default function Index() {
  const { reset, sessionId } = useLocalSearchParams();
  const [userName, setUserName]               = useState('Étudiant');
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [inputText, setInputText]             = useState('');
  const [isTyping, setIsTyping]               = useState(false);
  const [chatHistory, setChatHistory]         = useState<Message[]>([
    { id: '1', text: "Bonjour ! Je suis Supone. Pose-moi une question sur le SUP'PTIC.", sender: 'bot' },
  ]);

  const insets = useSafeAreaInsets();
  const flatListRef = useRef<FlatList>(null);

  const scrollToBottom = () => {
    setTimeout(() => flatListRef.current?.scrollToEnd({ animated: true }), 80);
  };

  // 1. Réinitialisation
  useEffect(() => {
    if (reset) {
      setChatHistory([{ id: '1', text: "Bonjour ! Je suis Supone. Pose-moi une question sur le SUP'PTIC.", sender: 'bot' }]);
      setCurrentSessionId(null);
      setInputText('');
      setIsTyping(false);
      Keyboard.dismiss();
    }
  }, [reset]);

  // composante a implementer avec la base de donnees
  // 2. Charger une session depuis l'historique 
  useEffect(() => {
    if (sessionId) {
      const loadSession = async () => {
        const saved = await AsyncStorage.getItem('chat_history');
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

  // 3. Charger le nom de l'utilisateur
  useEffect(() => {
    const fetchUser = async () => {
      const savedName = await AsyncStorage.getItem('user_name');
      if (savedName) setUserName(savedName);
    };
    fetchUser();
  }, []);

  // 4. Sauvegarder la session
  const saveChatSession = async (messages: Message[]) => {
    try {
      const saved = await AsyncStorage.getItem('chat_history');
      let sessions = saved ? JSON.parse(saved) : [];
      const id = currentSessionId || Date.now().toString();
      const userFirstMsg = messages.find((m) => m.sender === 'user')?.text || 'Nouvelle discussion';
      const title = userFirstMsg.length > 25 ? userFirstMsg.substring(0, 25) + '…' : userFirstMsg;
      const newSession = { id, title, messages };
      const index = sessions.findIndex((s: any) => s.id === id);
      if (index > -1) { sessions[index] = newSession; } else { sessions.unshift(newSession); }
      await AsyncStorage.setItem('chat_history', JSON.stringify(sessions));
      if (!currentSessionId) setCurrentSessionId(id);
    } catch (e) {
      console.error('Erreur de sauvegarde :', e);
    }
  };

  // Version statique (active par défaut)
  const generateBotResponse = (input: string): string => {
    const low = input.toLowerCase();
    if (low.includes('histoire')) return "L'École Nationale Supérieure des Postes, des Télécommunications et des TIC (SUP'PTIC) forme les cadres de l'économie numérique depuis des décennies.";
    if (low.includes('chambre'))  return 'Pour les logements, veuillez consulter le service de la scolarité pour connaître les disponibilités des cités universitaires.';
    if (low.includes('club'))     return "Vous pouvez rejoindre le club de Robotique, de Musique ou d'Entrepreneuriat dès la rentrée !";
    if (low.includes('question')) return 'Je suis votre assistant dédié à répondre à vos questions !';
    return "Je suis votre assistant SUP'PTIC. Je n'ai pas la réponse précise, mais je peux vous rediriger vers l'administration.";
  };

  const handleSend = async (text?: string) => {
    const messageToSend = (text ?? inputText).trim();
    if (!messageToSend || isTyping) return;

    const newUserMsg: Message = { id: Date.now().toString(), text: messageToSend, sender: 'user' };
    const withUser = [...chatHistory, newUserMsg];
    setChatHistory(withUser);
    setInputText('');
    saveChatSession(withUser);
    scrollToBottom();
    setIsTyping(true);
    scrollToBottom();

    // Simulation de la réponse du bot (délai de 1,5 s)
    setTimeout(() => {
      setIsTyping(false);
      const responseText = generateBotResponse(messageToSend);
      const botMsg: Message = { id: (Date.now() + 1).toString(), text: responseText, sender: 'bot' };
      const finalHistory = [...withUser, botMsg];
      setChatHistory(finalHistory);
      saveChatSession(finalHistory);
      scrollToBottom();
    }, 1500);

  };

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------
  return (
    <SafeAreaView style={styles.container} edges={['top', 'left', 'right']}>
      <StatusBar barStyle="dark-content" backgroundColor="transparent" translucent />

      {/* Conteneur principal  */}
      <KeyboardAvoidingView
        style={styles.screen}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      >

        {/* ── Liste des messages ── */}
        <FlatList
          ref={flatListRef}
          data={chatHistory}
          keyExtractor={(item) => item.id}
          onContentSizeChange={scrollToBottom}
          showsVerticalScrollIndicator={true}
          indicatorStyle="black"
          ListFooterComponent={isTyping ? <TypingIndicator /> : null}
          ListHeaderComponent={
            chatHistory.length <= 1 ? (
              <Animated.View entering={FadeInDown.duration(800)} style={styles.welcomeSection}>
                <Text style={styles.greetingText}>Bonjour {userName} !</Text>
                <Text style={styles.subGreetingText}>Par où commencer ?</Text>
                <View style={styles.suggestionsWrapper}>
                  {[
                    "📚 Histoire du SUP'PTIC",
                    '🏠 Louer une chambre',
                    "🎯 S'inscrire à un club",
                    '❓ Poser une question',
                  ].map((item, idx) => {
                    const dataMsg = [
                      "Parler de l'histoire de SUP'PTIC",
                      'Comment louer une chambre ?',
                      'Quels sont les clubs disponibles ?',
                      "j'ai une question ?",
                    ][idx];
                    return (
                      <TouchableOpacity key={idx} style={styles.suggestionChip} onPress={() => handleSend(dataMsg)} activeOpacity={0.75}>
                        <Text style={styles.suggestionText}>{item}</Text>
                      </TouchableOpacity>
                    );
                  })}
                </View>
              </Animated.View>
            ) : null
          }
          renderItem={({ item }) => (
            <Animated.View entering={FadeInUp.duration(350)} style={item.sender === 'user' ? styles.userMsgWrapper : styles.botMsgWrapper}>
              <View style={[styles.bubble, item.sender === 'user' ? styles.userBubble : styles.botBubble]}>
                <Text style={item.sender === 'user' ? styles.userText : styles.botText}>{item.text}</Text>
                <View style={item.sender === 'user' ? styles.userArrow : styles.botArrow} />
              </View>
              {item.sender === 'bot' && item.id !== '1' && (
                <Animated.View entering={FadeInUp.delay(200)}>
                  <MessageActions text={item.text} />
                </Animated.View>
              )}
            </Animated.View>
          )}
          contentContainerStyle={styles.listContent}
        />

        {/* ── Zone de saisie ─ */}
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

// ---------------------------------------------------------------------------
// Styles
// ---------------------------------------------------------------------------
const PRIMARY    = '#1a4594';
const BOT_BUBBLE = '#f1f3f5';

const styles = StyleSheet.create({

  container: {
    flex: 1,
    backgroundColor: '#f8faff',
    paddingTop: Platform.OS === 'android' ? StatusBar.currentHeight ?? 0 : 0,
  },

  screen: {
    flex: 1,
  },

  listContent: {
    padding: 16,
    paddingBottom: 8,
    flexGrow: 1,
  },

  // Section d'accueil
  welcomeSection:     { marginTop: 10, marginBottom: 28 },
  greetingText:       { fontSize: 16, color: '#666' },
  subGreetingText:    { fontSize: 24, fontWeight: 'bold', color: '#000', marginBottom: 18 },
  suggestionsWrapper: { marginTop: 8, gap: 8 },
  suggestionChip: {
    backgroundColor: '#fff',
    paddingVertical: 12,
    paddingHorizontal: 18,
    borderRadius: 20,
    alignSelf: 'flex-start',
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.06,
    shadowRadius: 4,
    borderWidth: 1,
    borderColor: 'rgba(0,0,0,0.08)',
    marginBottom: 2,
  },
  suggestionText: { color: '#333', fontWeight: '500', fontSize: 14 },

  // Wrappers messages
  userMsgWrapper: { alignSelf: 'flex-end',   marginBottom: 18, maxWidth: '80%' },
  botMsgWrapper:  { alignSelf: 'flex-start', marginBottom: 18, maxWidth: '85%' },

  // Bulles
  bubble: { padding: 14, borderRadius: 18, position: 'relative' },
  userBubble: {
    backgroundColor: PRIMARY,
    borderBottomRightRadius: 5,
    shadowColor: PRIMARY,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.2,
    shadowRadius: 10,
    elevation: 4,
  },
  botBubble: {
    backgroundColor: BOT_BUBBLE,
    borderBottomLeftRadius: 5,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 5,
    elevation: 2,
  },

  // Flèches
  userArrow: {
    position: 'absolute', bottom: 0, right: -6,
    width: 0, height: 0,
    borderTopWidth: 10, borderTopColor: 'transparent',
    borderLeftWidth: 12, borderLeftColor: PRIMARY,
  },
  botArrow: {
    position: 'absolute', bottom: 0, left: -6,
    width: 0, height: 0,
    borderTopWidth: 10, borderTopColor: 'transparent',
    borderRightWidth: 12, borderRightColor: BOT_BUBBLE,
  },

  // Textes
  userText: { color: '#fff', fontSize: 15, lineHeight: 22 },
  botText:  { color: '#111', fontSize: 15, lineHeight: 22 },

  // Indicateur de frappe
  typingBubble: { flexDirection: 'row', alignItems: 'center', paddingVertical: 10 },
  typingText:   { color: '#777', fontSize: 13, fontStyle: 'italic' },

  // Actions bot
  actionRow: { flexDirection: 'row', gap: 4, marginTop: 8, paddingLeft: 2 },
  actionBtn: { padding: 7, borderRadius: 20, backgroundColor: 'rgba(0,0,0,0.04)' },

  // ── Zone de saisie ──────────────────────────────────────────────────────
  inputContainer: {
    backgroundColor: '#fff',
    paddingHorizontal: 14,
    paddingTop: 10,
    borderTopWidth: 1,
    borderTopColor: '#eee',
  },
  inputArea: {
    flexDirection: 'row',
    alignItems: 'center',  
    backgroundColor: '#f0f2f5',
    borderRadius: 24,
    paddingHorizontal: 12,
    paddingVertical: 6,
    minHeight: 44,
  },
  inputIcon: { marginRight: 6 },
  input: {
    flex: 1,
    color: '#000',
    fontSize: 15,
    lineHeight: 20,
    maxHeight: 100,
    paddingVertical: 4,
  },
  sendButton: {
    marginLeft: 8,
    backgroundColor: PRIMARY,
    width: 36,
    height: 36,
    borderRadius: 18,
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0,
  },
  disclaimer: { textAlign: 'center', fontSize: 10, color: '#bbb', marginTop: 6, marginBottom: 2 },
});
