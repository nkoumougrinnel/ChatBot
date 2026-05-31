import { Ionicons } from '@expo/vector-icons';
import { DrawerContentScrollView, DrawerItem } from '@react-navigation/drawer';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Drawer } from 'expo-router/drawer';
import { useRouter } from 'expo-router';
import React, { useEffect, useState } from 'react';
import { StyleSheet, Text, View, TouchableOpacity, TextInput, Alert } from 'react-native';

// Type pour l'historique
type Session = {
  id: string;
  title: string;
  messages: any[];
};

function CustomDrawerContent(props: any) {
  const router = useRouter();
  const [sessions, setSessions] = useState<Session[]>([]);
  const [query, setQuery] = useState('');

  const filtered = query
    ? sessions.filter((s) => s.title.toLowerCase().includes(query.toLowerCase()))
    : sessions;

  // Charge l'historique depuis AsyncStorage (extrait pour rafraîchir)
  const loadSessions = async () => {
    try {
      const saved = await AsyncStorage.getItem('chat_history');
      if (saved) {
        const list: Session[] = JSON.parse(saved);
        // Trier par id (timestamp) décroissant -> récent d'abord
        list.sort((a, b) => Number(b.id) - Number(a.id));
        setSessions(list);
      } else {
        setSessions([]);
      }
    } catch (e) {
      console.error('Failed to load sessions', e);
    }
  };

  useEffect(() => {
    loadSessions();
  }, []);

  const refresh = () => {
    loadSessions();
  };

  const deleteSession = async (id: string) => {
    Alert.alert('Supprimer', 'Supprimer cette discussion ?', [
      { text: 'Annuler', style: 'cancel' },
      { text: 'Supprimer', style: 'destructive', onPress: async () => {
        try {
          const saved = await AsyncStorage.getItem('chat_history');
          let list: Session[] = saved ? JSON.parse(saved) : [];
          list = list.filter((s) => s.id !== id);
          await AsyncStorage.setItem('chat_history', JSON.stringify(list));
          setSessions(list);
        } catch (e) { console.error(e); }
      }}
    ]);
  };

  const clearAll = async () => {
    Alert.alert("Effacer l'historique", "Supprimer tout l'historique ?", [
      { text: 'Annuler', style: 'cancel' },
      { text: 'Effacer', style: 'destructive', onPress: async () => {
        await AsyncStorage.removeItem('chat_history');
        setSessions([]);
      }}
    ]);
  };

  return (
    <DrawerContentScrollView {...props}>

      {/* BOUTON NOUVELLE DISCUSSION + RECHERCHE */}
      <Text style={styles.sectionTitle}>Actions</Text>
      <DrawerItem
        label="Nouvelle discussion"
        labelStyle={{ color: '#1e293b', fontWeight: '500' }}
        icon={() => <Ionicons name="add-circle-outline" size={22} color="#007ACC" />}
        onPress={() => {
          router.push(`/drawer/chat?reset=${Date.now().toString()}` as any);
          props.navigation.closeDrawer();
        }}
      />

      {/* Recherche + actions */}
      <View style={styles.searchWrapper}>
        <TextInput
          placeholder="Rechercher une discussion"
          placeholderTextColor="#9CA3AF"
          value={query}
          onChangeText={setQuery}
          style={styles.searchInput}
        />
        <View style={styles.searchActions}>
          {query.length > 0 ? (
            <TouchableOpacity onPress={() => setQuery('')} style={styles.iconBtn}>
              <Ionicons name="close-circle" size={18} color="#6B7280" />
            </TouchableOpacity>
          ) : null}
          <TouchableOpacity onPress={refresh} style={styles.iconBtn}>
            <Ionicons name="refresh" size={18} color="#2563EB" />
          </TouchableOpacity>
        </View>
      </View>

      {/* Discussions (historique) */}
      <Text style={styles.sectionTitle}>Discussions</Text>
      {filtered.length === 0 ? (
        <Text style={styles.emptyText}>Aucune discussion trouvée</Text>
      ) : (
        filtered.map((session) => (
          <View key={session.id} style={styles.sessionRow}>
            <TouchableOpacity
              style={styles.sessionBtn}
              onPress={() => {
                router.push(`/drawer/chat?sessionId=${session.id}` as any);
                props.navigation.closeDrawer();
              }}
            >
              <Ionicons name="chatbubble-outline" size={18} color="#94a3b8" style={{ marginRight: 8 }} />
              <Text style={styles.sessionLabel}>{session.title}</Text>
            </TouchableOpacity>
            <TouchableOpacity onPress={() => deleteSession(session.id)} style={styles.deleteBtn}>
              <Ionicons name="trash-outline" size={18} color="#ef4444" />
            </TouchableOpacity>
          </View>
        ))
      )}

      {/* Actions: effacer tout */}
      {sessions.length > 0 && (
        <DrawerItem
          label="Effacer l'historique"
          labelStyle={{ color: '#ef4444' }}
          icon={() => <Ionicons name="trash" size={20} color="#ef4444" />}
          onPress={clearAll}
        />
      )}

    </DrawerContentScrollView>
  );
}

export default function DrawerLayout() {
  return (
    <Drawer
      drawerContent={(props) => <CustomDrawerContent {...props} />}
      screenOptions={{
        headerShown: false,
        drawerType: 'front',
        overlayColor: 'rgba(0,0,0,0.5)',
        drawerStyle: { width: '80%' },
      }}
    >
      <Drawer.Screen name="chat" options={{ title: 'Supone ai' }} />
    </Drawer>
  );
}

const styles = StyleSheet.create({
  sectionTitle: {
    fontSize: 11,
    fontWeight: 'bold',
    color: '#94a3b8',
    marginLeft: 18,
    marginTop: 20,
    marginBottom: 4,
    textTransform: 'uppercase',
    letterSpacing: 1,
  },
  searchWrapper: {
    marginHorizontal: 12,
    marginTop: 8,
    marginBottom: 6,
    position: 'relative',
  },
  searchInput: {
    height: 42,
    backgroundColor: '#fff',
    borderRadius: 10,
    paddingHorizontal: 12,
    borderWidth: 1,
    borderColor: '#E5E7EB',
    color: '#111827',
  },
  clearBtn: {
    position: 'absolute',
    right: 8,
    top: 10,
  },
  emptyText: {
    color: '#9CA3AF',
    marginLeft: 18,
    marginTop: 8,
    fontSize: 13,
  },
  searchActions: { position: 'absolute', right: 8, top: 8, flexDirection: 'row' },
  iconBtn: { marginLeft: 8, padding: 4 },
  sessionRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingHorizontal: 12 },
  sessionBtn: { flexDirection: 'row', alignItems: 'center', paddingVertical: 10, flex: 1 },
  sessionLabel: { color: '#475569', fontSize: 14 },
  deleteBtn: { padding: 8 },
});