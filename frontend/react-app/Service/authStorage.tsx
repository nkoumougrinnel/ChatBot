// ============================================================
// Gestion du token de connexion (AsyncStorage).
// ============================================================

import AsyncStorage from '@react-native-async-storage/async-storage';

const CLE_TOKEN = '@mon_app:token_utilisateur';
const CLE_CONNEXION = '@mon_app:deja_connecte';

// Sauvegarde le token après connexion réussie
export async function sauvegarderToken(token: string): Promise<void> {
  await AsyncStorage.setItem(CLE_TOKEN, token);
}

// Lit le token → null si jamais connecté
export async function lireToken(): Promise<string | null> {
  return await AsyncStorage.getItem(CLE_TOKEN);
}

// Supprime le token → déconnexion
export async function supprimerToken(): Promise<void> {
  await AsyncStorage.removeItem(CLE_TOKEN);
}

// Appelé après une connexion réussie → marque comme connecté
export async function marquerCommeConnecte(): Promise<void> {
  await AsyncStorage.setItem(CLE_CONNEXION, 'oui');
}

// Vérifie si l'utilisateur s'est déjà connecté
// Retourne true → déjà connecté / false → première fois
export async function estDejaConnecte(): Promise<boolean> {
  const valeur = await AsyncStorage.getItem(CLE_CONNEXION);
  return valeur === 'oui';
}

// Réinitialise → l'utilisateur devra se reconnecter
export async function seDeconnecter(): Promise<void> {
  await AsyncStorage.removeItem(CLE_CONNEXION);
}