import { Picker } from '@react-native-picker/picker'; // N'oublie pas : npx expo install @react-native-picker/picker
import React, { useState } from 'react';
import { Alert, ScrollView, StyleSheet, Text, TextInput, TouchableOpacity, View } from 'react-native';

export default function FeedbackScreen() {
  const [problemType, setProblemType] = useState('');
  const [comment, setComment] = useState('');

  const handleSendFeedback = () => {
    if (!problemType) {
      Alert.alert("Sélection requise", "Choisis un type de problème avant d'envoyer.");
      return;
    }
    Alert.alert("Merci !", "Ton retour nous aide à améliorer Supone ai.");
    setComment('');
    setProblemType('');
  };

  return (
    <ScrollView style={styles.container}>
      <View style={styles.card}>
        <Text style={styles.title}>Partager le feedback</Text>

        <Text style={styles.label}>Type de problème</Text>
        {/* Conteneur stylisé pour le Picker */}
        <View style={styles.pickerContainer}>
          <Picker
            selectedValue={problemType}
            onValueChange={(itemValue) => setProblemType(itemValue)}
            style={styles.picker}
            dropdownIconColor="#2155CD"
          >
            <Picker.Item label="Sélectionner un problème" value="" color="#999" />
            <Picker.Item label="Mauvaise réponse" value="wrong_answer" />
            <Picker.Item label="Réponse trop courte" value="too_short" />
            <Picker.Item label="Tu n'as pas compris ma question" value="not_understood" />
            <Picker.Item label="Autre" value="other" />
          </Picker>
        </View>

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

        <TouchableOpacity 
          style={[styles.submitButton, problemType ? styles.activeButton : null]} 
          onPress={handleSendFeedback}
        >
          <Text style={styles.submitButtonText}>Soumettre</Text>
        </TouchableOpacity>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f8faff', padding: 20 },
  card: { backgroundColor: '#fff', borderRadius: 15, padding: 20, elevation: 3 },
  title: { fontSize: 20, fontWeight: 'bold', textAlign: 'center', marginBottom: 25 },
  label: { fontSize: 14, color: '#333', marginBottom: 10, fontWeight: '600' },
  pickerContainer: {
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 10,
    marginBottom: 20,
    overflow: 'hidden', // Pour garder les bords arrondis sur Android
  },
  picker: {
    height: 55,
    width: '100%',
  },
  textArea: {
    backgroundColor: '#E9E9EB', // Gris clair conforme à ta maquette
    borderRadius: 10,
    padding: 15,
    height: 150,
    marginBottom: 30,
    fontSize: 16,
  },
  submitButton: {
    backgroundColor: '#C4C4C4', // Gris par défaut (maquette 7)
    padding: 15,
    borderRadius: 25,
    alignItems: 'center',
  },
  activeButton: {
    backgroundColor: '#2155CD', // Devient bleu SUP'PTIC quand une option est choisie
  },
  submitButtonText: { color: '#fff', fontWeight: 'bold', fontSize: 16 },
});