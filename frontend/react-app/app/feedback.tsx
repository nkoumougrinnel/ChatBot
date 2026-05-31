// app/feedback.tsx — SUP'ONE
// Écran de feedback — envoie au backend POST /api/feedback/
//
// Reçoit via router.push params :
//   question : la question posée dans le chat
//   score    : score FAISS du pipeline (float en string)

import { Picker } from "@react-native-picker/picker";
import { useLocalSearchParams, useRouter } from "expo-router";
import React, { useState } from "react";
import {
  ActivityIndicator,
  Alert,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from "react-native";

import { sendFeedback } from "../Service/api";
import { lireToken } from "../Service/authStorage";

const PROBLEM_TYPES = [
  { label: "Sélectionner un problème",  value: "" },
  { label: "Mauvaise réponse",          value: "wrong_answer" },
  { label: "Réponse trop courte",       value: "too_short" },
  { label: "Question mal comprise",     value: "not_understood" },
  { label: "Autre",                     value: "other" },
];

export default function FeedbackScreen() {
  const router = useRouter();
  const params = useLocalSearchParams<{ question?: string; score?: string }>();

  const questionOriginale = params.question ?? "";
  const scoreOriginal     = params.score ? parseFloat(params.score) : undefined;

  const [problemType, setProblemType] = useState("");
  const [comment,     setComment]     = useState("");
  const [envoi,       setEnvoi]       = useState(false);

  async function handleSendFeedback() {
    if (!problemType) {
      Alert.alert("Sélection requise", "Choisis un type de problème avant d'envoyer.");
      return;
    }

    setEnvoi(true);
    try {
      const token = await lireToken();

      if (!token) {
        Alert.alert(
          "Non connecté",
          "Connectez-vous pour envoyer un feedback.",
          [{ text: "OK", onPress: () => router.back() }],
        );
        return;
      }

      await sendFeedback(
        {
          feedback_type:        "negatif",
          question_utilisateur: questionOriginale || "Question non renseignée",
          comment:              comment.trim() || `Problème : ${problemType}`,
          score_similarite:     scoreOriginal ?? null,
          faq:                  null,
        },
        token,
      );

      Alert.alert(
        "Merci !",
        "Ton retour nous aide à améliorer Supone AI.",
        [{ text: "OK", onPress: () => router.back() }],
      );
      setComment("");
      setProblemType("");

    } catch (erreur: any) {
      Alert.alert("Erreur", erreur.message ?? "Impossible d'envoyer le feedback.");
    } finally {
      setEnvoi(false);
    }
  }

  return (
    <ScrollView style={styles.container} keyboardShouldPersistTaps="handled">
      <View style={styles.card}>
        <Text style={styles.title}>Signaler un problème</Text>

        {/* Question originale */}
        {questionOriginale ? (
          <View style={styles.contextBox}>
            <Text style={styles.contextLabel}>Question concernée :</Text>
            <Text style={styles.contextText} numberOfLines={3}>{questionOriginale}</Text>
          </View>
        ) : null}

        <Text style={styles.label}>Type de problème</Text>
        <View style={styles.pickerContainer}>
          <Picker
            selectedValue={problemType}
            onValueChange={(itemValue) => setProblemType(itemValue)}
            style={styles.picker}
            dropdownIconColor="#2155CD"
          >
            {PROBLEM_TYPES.map((item) => (
              <Picker.Item
                key={item.value}
                label={item.label}
                value={item.value}
                color={item.value === "" ? "#999" : "#000"}
              />
            ))}
          </Picker>
        </View>

        <Text style={styles.label}>Commentaire (facultatif)</Text>
        <TextInput
          style={styles.textArea}
          placeholder="Décris le problème ici..."
          multiline
          numberOfLines={6}
          textAlignVertical="top"
          value={comment}
          onChangeText={setComment}
        />

        <TouchableOpacity
          style={[styles.submitButton, problemType ? styles.activeButton : null]}
          onPress={handleSendFeedback}
          disabled={envoi}
          activeOpacity={0.8}
        >
          {envoi
            ? <ActivityIndicator color="#fff" />
            : <Text style={styles.submitButtonText}>Soumettre</Text>
          }
        </TouchableOpacity>

        <TouchableOpacity style={styles.cancelButton} onPress={() => router.back()}>
          <Text style={styles.cancelText}>Annuler</Text>
        </TouchableOpacity>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container:    { flex: 1, backgroundColor: "#f8faff", padding: 20 },
  card:         { backgroundColor: "#fff", borderRadius: 15, padding: 20, elevation: 3 },
  title:        { fontSize: 20, fontWeight: "bold", textAlign: "center", marginBottom: 20 },
  contextBox:   { backgroundColor: "#f0f4ff", borderRadius: 10, padding: 12, marginBottom: 20 },
  contextLabel: { fontSize: 12, color: "#666", marginBottom: 4 },
  contextText:  { fontSize: 14, color: "#333" },
  label:        { fontSize: 14, color: "#333", marginBottom: 10, fontWeight: "600" },
  pickerContainer: {
    backgroundColor: "#fff", borderWidth: 1, borderColor: "#ddd",
    borderRadius: 10, marginBottom: 20, overflow: "hidden",
  },
  picker:           { height: 55, width: "100%" },
  textArea:         {
    backgroundColor: "#E9E9EB", borderRadius: 10,
    padding: 15, height: 150, marginBottom: 20, fontSize: 16,
  },
  submitButton:     { backgroundColor: "#C4C4C4", padding: 15, borderRadius: 25, alignItems: "center", marginBottom: 10 },
  activeButton:     { backgroundColor: "#2155CD" },
  submitButtonText: { color: "#fff", fontWeight: "bold", fontSize: 16 },
  cancelButton:     { alignItems: "center", padding: 12 },
  cancelText:       { color: "#888", fontSize: 14 },
});
