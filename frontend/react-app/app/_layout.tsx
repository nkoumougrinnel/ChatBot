import { Ionicons } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { DrawerContentScrollView, DrawerItem } from '@react-navigation/drawer';
import { useRouter } from 'expo-router';
import { Drawer } from 'expo-router/drawer';
import React, { useEffect, useState } from 'react';
import { StyleSheet, Text } from 'react-native';
import { GestureHandlerRootView } from 'react-native-gesture-handler';

function CustomDrawerContent(props: any) {
  const router = useRouter();
  const [history, setHistory] = useState<any[]>([]);

  // Charger l'historique au démarrage et à chaque ouverture du menu
  useEffect(() => {
    const loadHistory = async () => {
      const saved = await AsyncStorage.getItem('chat_history');
      if (saved) setHistory(JSON.parse(saved));
    };
    loadHistory();
  }, [props.navigation.getState()]); 

  return (
    <DrawerContentScrollView {...props}>
      <Text style={styles.drawerSectionTitle}>Actions</Text>
      <DrawerItem
        label="Nouvelle discussion"
        icon={({ color, size }) => <Ionicons name="add-circle-outline" color={color} size={size} />}
        onPress={() => router.push({ pathname: '/', params: { reset: Date.now().toString() } })}
      />

      <Text style={styles.drawerSectionTitle}>Historique récent</Text>
      {history.map((chat) => (
        <DrawerItem
          key={chat.id}
          label={chat.title}
          labelStyle={{ fontSize: 14 }}
          icon={({ color }) => <Ionicons name="chatbox-outline" color={color} size={18} />}
          onPress={() => router.push({ pathname: '/', params: { sessionId: chat.id } })}
        />
      ))}
    </DrawerContentScrollView>
  );
}

export default function Layout() {
  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <Drawer
        drawerContent={(props) => <CustomDrawerContent {...props} />}
        screenOptions={{
          headerStyle: { backgroundColor: '#2155CD' },
          headerTintColor: '#fff',
          headerTitleStyle: { fontWeight: 'bold' },
        }}
      >
        <Drawer.Screen name="index" options={{ title: 'Supone ai' }} />
      </Drawer>
    </GestureHandlerRootView>
  );
}

const styles = StyleSheet.create({
  drawerSectionTitle: { fontSize: 12, fontWeight: 'bold', color: '#888', marginLeft: 18, marginVertical: 10, textTransform: 'uppercase' },
});