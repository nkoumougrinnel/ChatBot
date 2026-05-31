import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Alert, TextInput, KeyboardAvoidingView, Platform } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { router } from 'expo-router';
import { supprimerToken, seDeconnecter } from '../Service/authStorage';
import { saveUserProfile } from '../Service/user';

export default function ProfileScreen() {
  const [name, setName] = useState<string>('');
  const [email, setEmail] = useState<string>('');
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    (async () => {
      const n = await AsyncStorage.getItem('user_name');
      const e = await AsyncStorage.getItem('user_email');
      setName(n ?? '');
      setEmail(e ?? '');
    })();
  }, []);

  const handleLogout = async () => {
    Alert.alert('Déconnexion', 'Voulez-vous vous déconnecter ?', [
      { text: 'Annuler', style: 'cancel' },
      { text: 'Déconnecter', style: 'destructive', onPress: async () => {
        await supprimerToken();
        await seDeconnecter();
        // clear stored user info
        await AsyncStorage.removeItem('user_name');
        await AsyncStorage.removeItem('user_email');
        router.replace('/login');
      }}
    ]);
  };

  return (
    <KeyboardAvoidingView style={styles.container} behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
      <View style={styles.card}>
        <Text style={styles.label}>Nom</Text>
        <TextInput
          style={styles.input}
          placeholder="Ton nom"
          placeholderTextColor="#9CA3AF"
          value={name}
          onChangeText={setName}
        />

        <Text style={[styles.label, { marginTop: 18 }]}>E-mail</Text>
        <TextInput
          style={styles.input}
          placeholder="email@exemple.com"
          placeholderTextColor="#9CA3AF"
          value={email}
          onChangeText={setEmail}
          keyboardType="email-address"
          autoCapitalize="none"
        />

        <TouchableOpacity
          style={[styles.saveBtn, saving ? { opacity: 0.7 } : null]}
          onPress={async () => {
            setSaving(true);
            try {
              await saveUserProfile({ name: name || undefined, email: email || undefined });
              Alert.alert('Enregistré', 'Tes informations ont été sauvegardées.');
            } catch (e) {
              Alert.alert('Erreur', 'Impossible de sauvegarder.');
            } finally {
              setSaving(false);
            }
          }}
        >
          <Text style={styles.saveText}>Enregistrer</Text>
        </TouchableOpacity>

        <TouchableOpacity style={styles.logoutBtn} onPress={handleLogout}>
          <Text style={styles.logoutText}>Se déconnecter</Text>
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f8faff', padding: 20 },
  card: { backgroundColor: '#fff', borderRadius: 12, padding: 20, elevation: 3 },
  label: { color: '#94a3b8', fontSize: 12, fontWeight: '600' },
  value: { fontSize: 18, color: '#1f2937', marginTop: 6 },
  logoutBtn: { marginTop: 30, backgroundColor: '#ef4444', padding: 12, borderRadius: 10, alignItems: 'center' },
  logoutText: { color: '#fff', fontWeight: '700' },
  input: {
    marginTop: 8,
    backgroundColor: '#f3f4f6',
    paddingHorizontal: 12,
    paddingVertical: 10,
    borderRadius: 8,
    color: '#111827',
  },
  saveBtn: { marginTop: 20, backgroundColor: '#2155CD', padding: 12, borderRadius: 10, alignItems: 'center' },
  saveText: { color: '#fff', fontWeight: '700' },
});
