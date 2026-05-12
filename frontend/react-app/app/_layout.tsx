// ============================================================
// Configuration de la navigation Expo Router.
// ============================================================

import { Stack } from 'expo-router';

export default function RootLayout() {
  return (
    <Stack
      initialRouteName="Startup"  
    >
      {/* Écran de démarrage — splash + routage */}
      <Stack.Screen
        name="Startup"
        options={{ headerShown: false }}
      />

      {/* Page de connexion — sans header, plein écran */}
      <Stack.Screen
        name="login"
        options={{ headerShown: false }}
      />

      {/* Ta page principale — index.tsx reste libre */}
      <Stack.Screen
        name="index"
        options={{ headerShown: false }}
      />

      {/* Tes autres écrans existants */}
      <Stack.Screen
        name="feedback"
        options={{ headerShown: false }}
      />
    </Stack>
  );
}