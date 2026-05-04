// ============================================================
// SplashScreen.tsx
// Écran d'animation de démarrage de l'application
// ============================================================

import React, { useEffect, useRef } from 'react';
import {
  Animated,
  Dimensions,
  Image,
  StatusBar,
  StyleSheet,
  Text,
  View,
} from 'react-native';

// Récupère les dimensions de l'écran
const { width, height } = Dimensions.get('window');

// ============================================================
// PROPS : onFinish est appelé quand l'animation est terminée
// ============================================================

interface SplashScreenProps {
  onFinish: () => void;
}

export default function SplashScreen({ onFinish }: SplashScreenProps) {

  // --- Valeurs animées ---
  const logoScale   = useRef(new Animated.Value(0)).current; // échelle du logo
  const logoOpacity = useRef(new Animated.Value(0)).current; // transparence logo
  const textOpacity = useRef(new Animated.Value(0)).current; // transparence texte
  const textY       = useRef(new Animated.Value(30)).current; // position texte (montée)
  const dotsOpacity = useRef(new Animated.Value(0)).current; // transparence des points

  useEffect(() => {
    // ============================================================
    // SÉQUENCE D'ANIMATION PRINCIPALE
    // ============================================================
    Animated.sequence([

      Animated.parallel([
        Animated.spring(logoScale, {
          toValue: 1,
          tension: 60,        
          friction: 6,        
          useNativeDriver: true,
        }),
        Animated.timing(logoOpacity, {
          toValue: 1,
          duration: 400,
          useNativeDriver: true,
        }),
      ]),

  
      Animated.delay(200),

      
      Animated.parallel([
        Animated.timing(textOpacity, {
          toValue: 1,
          duration: 500,
          useNativeDriver: true,
        }),
        Animated.timing(textY, {
          toValue: 0,        
          duration: 500,
          useNativeDriver: true,
        }),
      ]),

      
      Animated.timing(dotsOpacity, {
        toValue: 1,
        duration: 400,
        useNativeDriver: true,
      }),

      Animated.delay(1200),

    ]).start(() => {
      onFinish();
    });
  }, []);

  return (
    <View style={styles.container}>
      <StatusBar hidden />

      {/* ---- LOGO ---- */}
      <Animated.View
        style={[
          styles.logoWrapper,
          {
            opacity: logoOpacity,
            transform: [{ scale: logoScale }],
          },
        ]}
      >
        <Image
          source={require('../assets/images/logoAI.png')}
          style={styles.logo}
          resizeMode="contain"
        />
      </Animated.View>

      {/* ---- NOM DE L'APPLICATION  ---- */}
      <Animated.View
        style={{
          opacity: textOpacity,
          transform: [{ translateY: textY }],
          alignItems: 'center',
        }}
      >
        <Text style={styles.appName}>Supone</Text>

        {/* Devise de supone au cas ou */}
        <Text style={styles.tagline}>Votre assistant IA </Text>
      </Animated.View>

      {/* ---- POINTS DE CHARGEMENT ---- */}
      <Animated.View style={[styles.dotsContainer, { opacity: dotsOpacity }]}>
        <View style={styles.dot} />
        <View style={styles.dot} />
        <View style={styles.dot} />
      </Animated.View>

      {/* ---- VERSION au cas ou ---- */}
      <Text style={styles.version}>v1.0.0</Text>
    </View>
  );
}

// ============================================================
// STYLES
// ============================================================
const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#1a1a2e',   
    alignItems: 'center',
    justifyContent: 'center',
  },
  logoWrapper: {
    marginBottom: -35,
    
    shadowColor: '#6366f1',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.4,
    shadowRadius: 20,
    elevation: 12,               
  },
  logo: {
    width: 500,                  
    height: 500,
    borderRadius: 24,
  },
  appName: {
    fontSize: 26,
    fontWeight: '700',
    color: '#f1f5f9',
    letterSpacing: 1,
    marginBottom: 6,
  },
  tagline: {
    fontSize: 13,
    color: '#94a3b8',
    marginBottom: 40,
  },
  dotsContainer: {
    flexDirection: 'row',
    gap: 8,
  },
  dot: {
    width: 7,
    height: 7,
    borderRadius: 4,
    backgroundColor: '#818cf8',  
  },
  version: {
    position: 'absolute',
    bottom: 24,
    fontSize: 11,
    color: '#475569',
  },
});