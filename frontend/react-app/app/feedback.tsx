import { Ionicons } from '@expo/vector-icons';
import React, { useState } from 'react';
import { ScrollView, StyleSheet, Text, TextInput, TouchableOpacity, View } from 'react-native';

export default function FeedbackScreen() {
  const [problemType, setProblemType] = useState('');
  const [comment, setComment] = useState('');

  return (
    <ScrollView style={styles.container}>
      <View style={styles.card}>
        <Text style={styles.title}>Partager le feedback</Text>

        {/* Sélecteur de problème (Simplifié pour le moment) */}
        <Text style={styles.label}>Type de problème</Text>
        <TouchableOpacity style={styles.dropdown}>
          <Text style={styles.dropdownText}>
            {problemType || "Sélectionner un problème"}
          </Text>
          <Ionicons name="chevron-down" size={20} color="#666" />
        </TouchableOpacity>

        {/* Zone de texte facultative */}
        <Text style={styles.label}>Partager des informations (facultatif)</Text>
        <TextInput
          style={styles.textArea}
          placeholder="Décris le problème ici..."
          multiline={true}
          numberOfLines={6}
          textAlignVertical="top"
          value={comment}
          onChangeText={setComment}
        />

        {/* Bouton Soumettre */}
        <TouchableOpacity style={styles.submitButton}>
          <Text style={styles.submitButtonText}>Soumettre</Text>
        </TouchableOpacity>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f5f5', padding: 20 },
  card: { backgroundColor: '#fff', borderRadius: 15, padding: 20, elevation: 3 },
  title: { fontSize: 18, fontWeight: 'bold', textAlign: 'center', marginBottom: 25 },
  label: { fontSize: 14, color: '#333', marginBottom: 10, fontWeight: '500' },
  dropdown: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    padding: 12,
    marginBottom: 20,
  },
  dropdownText: { color: '#666' },
  textArea: {
    backgroundColor: '#e0e0e0', // Gris comme sur ta maquette
    borderRadius: 8,
    padding: 15,
    height: 150,
    marginBottom: 30,
  },
  submitButton: {
    backgroundColor: '#C4B5B5', // Couleur beige/grise de ta maquette
    padding: 15,
    borderRadius: 25,
    alignItems: 'center',
  },
  submitButtonText: { color: '#555', fontWeight: 'bold', fontSize: 16 },
});