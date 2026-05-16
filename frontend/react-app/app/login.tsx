import { router } from 'expo-router';
import React, { useState } from 'react';
import {
  ActivityIndicator, Alert,
  KeyboardAvoidingView, Platform,
  StyleSheet,
  Text, TextInput, TouchableOpacity,
  View
} from 'react-native';
import { marquerCommeConnecte, sauvegarderToken } from '../Service/authStorage';
import { saveUserProfile } from '../Service/user';


export default function LoginScreen() {
  const [email,             setEmail]             = useState('');
  const [nom,               setNom]               = useState('');
  const [motDePasse,        setMotDePasse]         = useState('');
  const [chargement,        setChargement]         = useState(false);
  const [mdpVisible,        setMdpVisible]         = useState(false);

  // ============================================================
  // Connexion : connexion et redirection vers l'ecran principal 
  // ============================================================
  async function seConnecter() {
    if (!nom.trim() || !email.trim() || !motDePasse.trim()) {
      Alert.alert('Champs requis', 'Veuillez remplir tous les champs.');
      return;
    }

    setChargement(true);

    try {
      // 🔄 SIMULATION : Pour tester sans backend
      console.log('Tentative de connexion avec:', { email, password: motDePasse });

      // Simuler un délai réseau
      await new Promise(resolve => setTimeout(resolve, 1000));

      // Simuler une réponse réussie
      const donnees = {
        token: 'fake-jwt-token-' + Date.now(),
        user: { id: 1, email }
      };

      console.log('Connexion simulée réussie:', donnees);

      // ✅ Succès → on sauvegarde le token et les infos utilisateur
      await sauvegarderToken(donnees.token);
      await marquerCommeConnecte();
      // Sauvegarde du nom et de l'email pour affichage dans le profil
      await saveUserProfile({ name: nom, email });

      // Redirection vers la page principale (index.tsx)
      router.replace('/');

    } catch (erreur: any) {
      Alert.alert('Erreur', erreur.message);
    } finally {
      setChargement(false);
    }
  }

  return (
    <KeyboardAvoidingView
      style={styles.conteneur}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      {/* EN-TÊTE */}
      <View style={styles.entete}>
        <Text style={styles.titre}>Bienvenue</Text>
        <Text style={styles.sousTitre}>Inscrivez-vous pour continuer</Text>
      </View>

      {/* FORMULAIRE */}
      <View style={styles.formulaire}>

        <Text style={styles.etiquette}>Nom</Text>
        <TextInput
          style={styles.champ}
          placeholder="Nom"
          placeholderTextColor="#475569"
          value={nom}
          onChangeText={setNom}
          autoCapitalize="words"
        />

        <Text style={styles.etiquette}>Adresse e-mail</Text>
        <TextInput
          style={styles.champ}
          placeholder="vous@email.com"
          placeholderTextColor="#475569"
          value={email}
          onChangeText={setEmail}
          keyboardType="email-address"
          autoCapitalize="none"
          autoCorrect={false}
          returnKeyType="next"
        />

        <Text style={styles.etiquette}>Mot de passe</Text>
        <View style={styles.rangeeMotDePasse}>
          <TextInput
            style={[styles.champ, { flex: 1, marginBottom: 0 }]}
            placeholder="••••••••"
            placeholderTextColor="#475569"
            value={motDePasse}
            onChangeText={setMotDePasse}
            secureTextEntry={!mdpVisible}
            returnKeyType="done"
            onSubmitEditing={seConnecter}
          />
          <TouchableOpacity
            style={styles.boutonOeil}
            onPress={() => setMdpVisible(!mdpVisible)}
          >
            <Text style={{ fontSize: 16 }}>{mdpVisible ? '🙈' : '👁️'}</Text>
          </TouchableOpacity>
        </View>

        <TouchableOpacity
          onPress={() => Alert.alert('Info', 'Fonctionnalité à venir.')}
          style={{ alignItems: 'flex-end', marginTop: 8 }}
        >
          <Text style={styles.lienOublie}>Mot de passe oublié ?</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.bouton, chargement && { opacity: 0.6 }]}
          onPress={seConnecter}
          disabled={chargement}
          activeOpacity={0.8}
        >
          {chargement
            ? <ActivityIndicator color="#fff" />
            : <Text style={styles.boutonTexte}>Se connecter</Text>
          }
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  conteneur: {
    flex: 1,
    backgroundColor: '#0f172a',
    justifyContent: 'center',
    paddingHorizontal: 28,
  },
  entete: {
    alignItems: 'center',
    marginBottom: 20,
  },
  logoBoite: {
    width: 80, height: 80,
    backgroundColor: '#6366f1',
    borderRadius: 22,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 20,
    shadowColor: '#6366f1',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.45,
    shadowRadius: 16,
    elevation: 10,
  },
  logoTexte: { fontSize: 32, fontWeight: '700', color: '#fff' },
  titre: { fontSize: 26, fontWeight: '700', color: '#f1f5f9', marginBottom: 6 },
  sousTitre: { fontSize: 14, color: '#64748b' },
  formulaire: { gap: 2 },
  etiquette: { fontSize: 13, color: '#94a3b8', marginBottom: 8, marginTop: 14 },
  champ: {
    backgroundColor: '#1e293b',
    borderWidth: 0.5,
    borderColor: '#334155',
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 14,
    fontSize: 15,
    color: '#f1f5f9',
    marginBottom: 4,
  },
  rangeeMotDePasse: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#1e293b',
    borderWidth: 0.5,
    borderColor: '#334155',
    borderRadius: 12,
    paddingRight: 14,
  },
  boutonOeil: { padding: 4 },
  lienOublie: { color: '#6366f1', fontSize: 13 },
  bouton: {
    backgroundColor: '#6366f1',
    borderRadius: 12,
    paddingVertical: 16,
    alignItems: 'center',
    marginTop: 20,
    shadowColor: '#6366f1',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 6,
  },
  boutonTexte: { color: '#fff', fontSize: 16, fontWeight: '600' },

});