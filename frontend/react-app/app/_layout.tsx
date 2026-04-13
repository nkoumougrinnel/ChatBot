import { Ionicons } from '@expo/vector-icons';
import { Drawer } from 'expo-router/drawer';
import { GestureHandlerRootView } from 'react-native-gesture-handler';

export default function Layout() {
  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <Drawer
        screenOptions={{
          // Header bleu SUP'PTIC
          headerStyle: {
            backgroundColor: '#2155CD',
          },
          headerTintColor: '#fff',
          headerTitleStyle: {
            fontWeight: 'bold',
          },
          // Icône profil à droite
          headerRight: () => (
            <Ionicons 
              name="person-circle-outline" 
              size={28} 
              color="white" 
              style={{ marginRight: 15 }} 
            />
          ),
          // Correction : On utilise drawerContentStyle ou on gère le fond dans les pages directement
          drawerStyle: {
            backgroundColor: '#fff',
            width: 250,
          },
        }}
      >
        <Drawer.Screen
          name="index"
          options={{
            drawerLabel: 'Nouvelle discussion',
            title: 'Supone ai',
            drawerIcon: ({ color }: { color: string }) => (
              <Ionicons name="chatbubble-outline" size={20} color={color} />
            ),
          }}
        />

        <Drawer.Screen
          name="feedback"
          options={{
            drawerLabel: 'Partager le feedback',
            title: 'Feedback',
            drawerIcon: ({ color }: { color: string }) => (
              <Ionicons name="alert-circle-outline" size={20} color={color} />
            ),
          }}
        />
      </Drawer>
    </GestureHandlerRootView>
  );
}