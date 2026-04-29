import { Ionicons, MaterialCommunityIcons } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import * as Clipboard from 'expo-clipboard';
import { useLocalSearchParams, useRouter } from 'expo-router';
import React, { useEffect, useRef, useState } from 'react';
import {
  Alert,
  FlatList,
  Keyboard,
  KeyboardAvoidingView,
  Platform,
  SafeAreaView,
  Share,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View
} from 'react-native';
import Animated, { FadeInDown, FadeInUp } from 'react-native-reanimated';

// Composant pour les actions sous les messages du bot
const MessageActions = ({ text }: { text: string }) => {
  const router = useRouter();
  const handleShare = async () => { try { await Share.share({ message: text }); } catch (e) {} };
  const handleCopy = async () => { await Clipboard.setStringAsync(text); Alert.alert("Copié", "Réponse copiée !"); };

  return (
    <View style={styles.actionRow}>
      <TouchableOpacity><MaterialCommunityIcons name="thumb-up-outline" size={18} color="#666" /></TouchableOpacity>
      <TouchableOpacity onPress={() => router.push('/feedback' as any)}><MaterialCommunityIcons name="thumb-down-outline" size={18} color="#666" /></TouchableOpacity>
      <TouchableOpacity><MaterialCommunityIcons name="refresh" size={18} color="#666" /></TouchableOpacity>
      <TouchableOpacity onPress={handleShare}><Ionicons name="share-social-outline" size={18} color="#666" /></TouchableOpacity>
      <TouchableOpacity onPress={handleCopy}><Ionicons name="copy-outline" size={18} color="#666" /></TouchableOpacity>
    </View>
  );
};

export default function Index() {
  const { reset, sessionId } = useLocalSearchParams();
  const [userName, setUserName] = useState("Étudiant");
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [inputText, setInputText] = useState('');
  const [chatHistory, setChatHistory] = useState([
    { id: '1', text: "Bonjour ! Je suis Supone. Pose-moi une question sur le SUP'PTIC.", sender: 'bot' }
  ]);
  
  const flatListRef = useRef<FlatList>(null);

  // 1. Gérer la réinitialisation (Nouvelle discussion)
  useEffect(() => {
    if (reset) {
      setChatHistory([{ id: '1', text: "Bonjour ! Je suis Supone. Pose-moi une question sur le SUP'PTIC.", sender: 'bot' }]);
      setCurrentSessionId(null);
      setInputText('');
      Keyboard.dismiss();
    }
  }, [reset]);

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

  // 4. Sauvegarder la session dans AsyncStorage
  const saveChatSession = async (messages: any[]) => {
    try {
      const saved = await AsyncStorage.getItem('chat_history');
      let sessions = saved ? JSON.parse(saved) : [];
      
      const id = currentSessionId || Date.now().toString();
      // On prend le premier message de l'utilisateur pour le titre
      const userFirstMsg = messages.find(m => m.sender === 'user')?.text || "Nouvelle discussion";
      const title = userFirstMsg.length > 25 ? userFirstMsg.substring(0, 25) + "..." : userFirstMsg;

      const newSession = { id, title, messages };
      
      const index = sessions.findIndex((s: any) => s.id === id);
      if (index > -1) {
        sessions[index] = newSession;
      } else {
        sessions.unshift(newSession);
      }

      await AsyncStorage.setItem('chat_history', JSON.stringify(sessions));
      if (!currentSessionId) setCurrentSessionId(id);
    } catch (e) {
      console.error("Erreur de sauvegarde :", e);
    }
  };

  const handleSend = (text: string) => {
    const messageToSend = text || inputText;
    if (!messageToSend.trim()) return;
    
    const newUserMsg = { id: Date.now().toString(), text: messageToSend, sender: 'user' };
    const updatedHistory = [...chatHistory, newUserMsg];
    
    setChatHistory(updatedHistory);
    setInputText('');
    saveChatSession(updatedHistory);
    
    setTimeout(() => flatListRef.current?.scrollToEnd({ animated: true }), 100);

    // Simulation réponse bot
    setTimeout(() => {
      const botMsg = { id: (Date.now() + 1).toString(), text: "Je recherche les informations pour vous...", sender: 'bot' };
      const finalHistory = [...updatedHistory, botMsg];
      setChatHistory(finalHistory);
      saveChatSession(finalHistory);
      setTimeout(() => flatListRef.current?.scrollToEnd({ animated: true }), 100);
    }, 1000);
  };

  return (
    <SafeAreaView style={styles.container}>
      <KeyboardAvoidingView 
        style={{ flex: 1 }}
        behavior={Platform.OS === 'ios' ? 'padding' : 'padding'}
        keyboardVerticalOffset={Platform.OS === 'ios' ? 90 : 80}
      >
        <FlatList
          ref={flatListRef}
          data={chatHistory}
          keyExtractor={(item) => item.id}
          automaticallyAdjustKeyboardInsets={true}
          onContentSizeChange={() => flatListRef.current?.scrollToEnd({ animated: true })}
          ListHeaderComponent={
            chatHistory.length <= 1 ? (
              <Animated.View entering={FadeInDown.duration(800)} style={styles.welcomeSection}>
                <Text style={styles.greetingText}>Bonjour {userName} !</Text>
                <Text style={styles.subGreetingText}>Par où commencer ?</Text>
                <View style={styles.suggestionsWrapper}>
                  {['Histoire du SUP\'PTIC', 'S\'inscrire à un club', 'Louer une chambre'].map((item, idx) => (
                    <TouchableOpacity key={idx} style={styles.suggestionChip} onPress={() => handleSend(item)}>
                      <Text style={styles.suggestionText}>{item}</Text>
                    </TouchableOpacity>
                  ))}
                </View>
              </Animated.View>
            ) : null
          }
          renderItem={({ item }) => (
            <View style={item.sender === 'user' ? styles.userMsgWrapper : styles.botMsgWrapper}>
              <View style={[styles.bubble, item.sender === 'user' ? styles.userBubble : styles.botBubble]}>
                <Text style={item.sender === 'user' ? styles.userText : styles.botText}>{item.text}</Text>
                <View style={item.sender === 'user' ? styles.userArrow : styles.botArrow} />
              </View>
              {item.sender === 'bot' && item.id !== '1' && (
                 <Animated.View entering={FadeInUp}>
                    <MessageActions text={item.text} />
                 </Animated.View>
              )}
            </View>
          )}
          contentContainerStyle={styles.listContent}
        />

        <View style={styles.inputContainer}>
          <View style={styles.inputArea}>
            <TextInput 
              style={styles.input} 
              placeholder="Demander à Supone..." 
              value={inputText} 
              onChangeText={setInputText}
              multiline={true} 
              textAlignVertical="center"
            />
            <TouchableOpacity onPress={() => handleSend('')} disabled={!inputText.trim()} style={styles.sendButton}>
              <Ionicons name="send" size={24} color={inputText.trim() ? "#2155CD" : "#ccc"} />
            </TouchableOpacity>
          </View>
          <Text style={styles.disclaimer}>Supone est une IA et peut se tromper.</Text>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f8faff' },
  listContent: { padding: 20, paddingBottom: 10 },
  welcomeSection: { marginTop: 10, marginBottom: 30 }, 
  greetingText: { fontSize: 18, color: '#555' },
  subGreetingText: { fontSize: 26, fontWeight: 'bold', color: '#000', marginBottom: 20 },
  suggestionsWrapper: { marginTop: 10 },
  suggestionChip: { backgroundColor: '#fff', padding: 12, borderRadius: 20, marginBottom: 10, alignSelf: 'flex-start', elevation: 2, borderWidth: 1, borderColor: '#eee' },
  suggestionText: { color: '#333', fontWeight: '500' },
  userMsgWrapper: { alignSelf: 'flex-end', marginBottom: 20, maxWidth: '80%' },
  botMsgWrapper: { alignSelf: 'flex-start', marginBottom: 20, maxWidth: '85%' },
  bubble: { padding: 14, borderRadius: 18, position: 'relative' },
  userBubble: { backgroundColor: '#2155CD', borderBottomRightRadius: 4 },
  botBubble: { backgroundColor: '#E9E9EB', borderBottomLeftRadius: 4 },
  userArrow: { position: 'absolute', bottom: 0, right: -6, width: 0, height: 0, borderTopWidth: 10, borderTopColor: 'transparent', borderLeftWidth: 12, borderLeftColor: '#2155CD' },
  botArrow: { position: 'absolute', bottom: 0, left: -6, width: 0, height: 0, borderTopWidth: 10, borderTopColor: 'transparent', borderRightWidth: 12, borderRightColor: '#E9E9EB' },
  userText: { color: '#fff', fontSize: 15 },
  botText: { color: '#000', fontSize: 15 },
  actionRow: { flexDirection: 'row', gap: 18, marginTop: 8, paddingLeft: 5 },
  inputContainer: { backgroundColor: '#fff', paddingHorizontal: 15, paddingTop: 10, paddingBottom: Platform.OS === 'ios' ? 20 : 10, borderTopWidth: 1, borderTopColor: '#eee' },
  inputArea: { flexDirection: 'row', alignItems: 'flex-end', backgroundColor: '#f0f2f5', borderRadius: 22, paddingHorizontal: 15, paddingVertical: 8, minHeight: 45 },
  input: { flex: 1, color: '#000', fontSize: 16, maxHeight: 120, paddingTop: 8, paddingBottom: 8 },
  sendButton: { marginLeft: 10, marginBottom: 5 },
  disclaimer: { textAlign: 'center', fontSize: 10, color: '#aaa', marginTop: 8 }
});