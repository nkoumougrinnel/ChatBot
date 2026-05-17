import { router } from 'expo-router';
import React, { useState } from 'react';
import { View } from 'react-native';
import { lireToken } from '../Service/authStorage';
import SplashScrenUI from './SplashScrenUI';

export default function Startup() {
  const [splashActif, setSplashActif] = useState(true);

  async function quandSplashEstTermine() {
    setSplashActif(false);
    const token = await lireToken();
    // Vérification de l'existence du token
    if (token) {
      // Token trouvé = utilisateur déjà connecté
      // On va directement sur l'interface principale du chat
      router.replace('/drawer/chat');
    } else {
      // Pas de token = première utilisation
      // On affiche le formulaire de connexion
      router.replace('/login');
    }
  }

  if (splashActif) {
    return <SplashScrenUI onFinish={quandSplashEstTermine} />;
  }

  return <View style={{ flex: 1, backgroundColor: '#0f172a' }} />;
}