import React from 'react';
import { ActivityIndicator, View, StyleSheet } from 'react-native';
import { Redirect } from 'expo-router';

export default function Index() {
  // Declarative redirect to drawer/chat — avoids navigating before Root Layout mounts
  return (
    <View style={styles.container}>
      <ActivityIndicator size="large" color="#007ACC" />
      <Redirect href="/drawer/chat" />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, alignItems: 'center', justifyContent: 'center', backgroundColor: '#fff' },
});