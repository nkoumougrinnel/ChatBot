// app/login.tsx — SUP'ONE
// Écran de connexion — appel réel au backend POST /api/auth/login/

import { router } from "expo-router";
import React, { useState } from "react";
import {
  ActivityIndicator,
  Alert,
  KeyboardAvoidingView,
  Platform,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from "react-native";

import { loginUser } from "../Service/api";
import { marquerCommeConnecte } from "../Service/authStorage";

export default function LoginScreen() {
  const [username,   setUsername]   = useState("");
  const [motDePasse, setMotDePasse] = useState("");
  const [chargement, setChargement] = useState(false);
  const [mdpVisible, setMdpVisible] = useState(false);

  async function seConnecter() {
    if (!username.trim() || !motDePasse.trim()) {
      Alert.alert("Champs requis", "Veuillez remplir tous les champs.");
      return;
    }

    setChargement(true);
    try {
      const { token, user } = await loginUser(username.trim(), motDePasse);

      // Persister token + données utilisateur localement
      await marquerCommeConnecte(token, user);

      router.replace("/");
    } catch (erreur: any) {
      // Le message vient directement du backend :
      // "Identifiants incorrects.", "Ce compte est désactivé.", etc.
      Alert.alert("Connexion échouée", erreur.message ?? "Une erreur est survenue.");
    } finally {
      setChargement(false);
    }
  }

  return (
    <KeyboardAvoidingView
      style={styles.conteneur}
      behavior={Platform.OS === "ios" ? "padding" : "height"}
    >
      <View style={styles.entete}>
        <Text style={styles.titre}>Bienvenue</Text>
        <Text style={styles.sousTitre}>Connectez-vous pour continuer</Text>
      </View>

      <View style={styles.formulaire}>
        <Text style={styles.etiquette}>Nom d'utilisateur</Text>
        <TextInput
          style={styles.champ}
          placeholder="votre_identifiant"
          placeholderTextColor="#475569"
          value={username}
          onChangeText={setUsername}
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
            <Text style={{ fontSize: 16 }}>{mdpVisible ? "🙈" : "👁️"}</Text>
          </TouchableOpacity>
        </View>

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
    backgroundColor: "#0f172a",
    justifyContent: "center",
    paddingHorizontal: 28,
  },
  entete:    { alignItems: "center", marginBottom: 20 },
  titre:     { fontSize: 26, fontWeight: "700", color: "#f1f5f9", marginBottom: 6 },
  sousTitre: { fontSize: 14, color: "#64748b" },
  formulaire: { gap: 2 },
  etiquette:  { fontSize: 13, color: "#94a3b8", marginBottom: 8, marginTop: 14 },
  champ: {
    backgroundColor: "#1e293b",
    borderWidth: 0.5,
    borderColor: "#334155",
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 14,
    fontSize: 15,
    color: "#f1f5f9",
    marginBottom: 4,
  },
  rangeeMotDePasse: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "#1e293b",
    borderWidth: 0.5,
    borderColor: "#334155",
    borderRadius: 12,
    paddingRight: 14,
  },
  boutonOeil: { padding: 4 },
  bouton: {
    backgroundColor: "#6366f1",
    borderRadius: 12,
    paddingVertical: 16,
    alignItems: "center",
    marginTop: 20,
    shadowColor: "#6366f1",
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 6,
  },
  boutonTexte: { color: "#fff", fontSize: 16, fontWeight: "600" },
});
