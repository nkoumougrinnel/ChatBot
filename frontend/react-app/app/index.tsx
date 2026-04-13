import { Ionicons, MaterialCommunityIcons } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import * as Clipboard from 'expo-clipboard';
import { useRouter } from 'expo-router';
import React, { useEffect, useRef, useState } from 'react';
import {
  Alert,
  FlatList,
  Keyboard,
  Share,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View
} from 'react-native';
import Animated, { FadeInDown, FadeInUp } from 'react-native-reanimated';

// --- ACTIONS SOUS LES RÉPONSES ---
const MessageActions = ({ text }: { text: string }) => {
  const router = useRouter();
  const handleShare = async () => { try { await Share.share({ message: text }); } catch (e) { } };
  const handleCopy = async () => { await Clipboard.setStringAsync(text); Alert.alert("Copié", "Réponse copiée !"); };

  return (
    <View style={styles.actionRow}>
      <TouchableOpacity onPress={() => Alert.alert("Merci", "Heureux de vous aider !")}>
        <MaterialCommunityIcons name="thumb-up-outline" size={18} color="#666" />
      </TouchableOpacity>
      <TouchableOpacity onPress={() => router.push('/feedback' as any)}>
        <MaterialCommunityIcons name="thumb-down-outline" size={18} color="#666" />
      </TouchableOpacity>
      <TouchableOpacity><MaterialCommunityIcons name="refresh" size={18} color="#666" /></TouchableOpacity>
      <TouchableOpacity onPress={handleShare}><Ionicons name="share-social-outline" size={18} color="#666" /></TouchableOpacity>
      <TouchableOpacity onPress={handleCopy}><Ionicons name="copy-outline" size={18} color="#666" /></TouchableOpacity>
    </View>
  );
};

export default function Index() {
  const [userName, setUserName] = useState("Étudiant");
  const [inputText, setInputText] = useState('');
  const [isKeyboardVisible, setKeyboardVisible] = useState(false);
  const [keyboardHeight, setKeyboardHeight] = useState(0); // État pour la hauteur du clavier
  const [chatHistory, setChatHistory] = useState([
    { id: '1', text: "Bonjour ! Je suis Supone. Pose-moi une question sur le SUP'PTIC.", sender: 'bot' }
  ]);
  
  const flatListRef = useRef<FlatList>(null);

  useEffect(() => {
    // Gestion précise du clavier pour Android Pixel 5
    const showSub = Keyboard.addListener('keyboardDidShow', (e) => {
        setKeyboardVisible(true);
        setKeyboardHeight(e.endCoordinates.height); // Capture de la hauteur réelle en pixels
        setTimeout(() => flatListRef.current?.scrollToEnd({ animated: true }), 100);
    });
    
    const hideSub = Keyboard.addListener('keyboardDidHide', () => {
        setKeyboardVisible(false);
        setKeyboardHeight(0);
    });
    
    const fetchUser = async () => {
      const savedName = await AsyncStorage.getItem('user_name');
      if (savedName) setUserName(savedName);
    };
    
    fetchUser();
    return () => { showSub.remove(); hideSub.remove(); };
  }, []);

  const handleSend = (text: string) => {
    const messageToSend = text || inputText;
    if (!messageToSend.trim()) return;
    
    setChatHistory(prev => [...prev, { id: Date.now().toString(), text: messageToSend, sender: 'user' }]);
    setInputText('');
    
    // On ne ferme plus forcément le clavier ici pour permettre une discussion fluide
    setTimeout(() => {
      setChatHistory(prev => [...prev, { 
        id: (Date.now() + 1).toString(), 
        text: "Je recherche les informations pour vous...", 
        sender: 'bot' 
      }]);
    }, 1000);
  };

  return (
    <View style={styles.container}>
      <FlatList
        ref={flatListRef}
        data={chatHistory}
        keyExtractor={(item) => item.id}
        onContentSizeChange={() => flatListRef.current?.scrollToEnd({ animated: true })}
        ListHeaderComponent={
          chatHistory.length <= 1 && !isKeyboardVisible ? (
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
        contentContainerStyle={{ padding: 20, paddingBottom: 20 }}
      />

      {/* ZONE DE SAISIE AVEC MARGE DYNAMIQUE */}
      <View style={[styles.inputContainer, { marginBottom: keyboardHeight }]}>
        <View style={styles.inputArea}>
          <TextInput 
            style={styles.input} 
            placeholder="Demander à Supone..." 
            value={inputText} 
            onChangeText={setInputText}
            placeholderTextColor="#999"
          />
          <TouchableOpacity onPress={() => handleSend('')}>
            <Ionicons name="send" size={24} color="#2155CD" />
          </TouchableOpacity>
        </View>
        <Text style={styles.disclaimer}>Supone est une IA et peut se tromper.</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f8faff' },
  welcomeSection: { marginTop: 60, marginBottom: 30 }, 
  greetingText: { fontSize: 24, color: '#555' },
  subGreetingText: { fontSize: 38, fontWeight: 'bold', color: '#000', marginBottom: 20 },
  suggestionsWrapper: { marginTop: 10 },
  suggestionChip: { backgroundColor: '#fff', padding: 12, borderRadius: 20, marginBottom: 10, alignSelf: 'flex-start', elevation: 2, borderWidth: 1, borderColor: '#eee' },
  suggestionText: { color: '#333' },
  userMsgWrapper: { alignSelf: 'flex-end', marginBottom: 25, maxWidth: '80%' },
  botMsgWrapper: { alignSelf: 'flex-start', marginBottom: 25, maxWidth: '85%' },
  bubble: { padding: 15, borderRadius: 15, position: 'relative' },
  userBubble: { backgroundColor: '#2155CD', borderBottomRightRadius: 2 },
  botBubble: { backgroundColor: '#E9E9EB', borderBottomLeftRadius: 2 },
  userArrow: {
    position: 'absolute', bottom: 0, right: -8,
    width: 0, height: 0, borderTopWidth: 10, borderTopColor: 'transparent',
    borderLeftWidth: 10, borderLeftColor: '#2155CD',
  },
  botArrow: {
    position: 'absolute', bottom: 0, left: -8,
    width: 0, height: 0, borderTopWidth: 10, borderTopColor: 'transparent',
    borderRightWidth: 10, borderRightColor: '#E9E9EB',
  },
  userText: { color: '#fff' },
  botText: { color: '#000' },
  actionRow: { flexDirection: 'row', gap: 20, marginTop: 8, paddingLeft: 10 },
  inputContainer: { 
    backgroundColor: '#fff', 
    padding: 10, 
    borderTopWidth: 1, 
    borderTopColor: '#eee' 
  },
  inputArea: { flexDirection: 'row', alignItems: 'center', backgroundColor: '#f0f2f5', borderRadius: 25, paddingHorizontal: 15, height: 50 },
  input: { flex: 1, color: '#000' },
  disclaimer: { textAlign: 'center', fontSize: 11, color: '#888', marginTop: 8 }
});