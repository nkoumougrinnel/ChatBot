// Service/authStorage.tsx — SUP'ONE
// Persistance locale du token et des données utilisateur via AsyncStorage.

import AsyncStorage from "@react-native-async-storage/async-storage";
import type { User } from "./api";

const KEY_TOKEN = "@supone:auth_token";
const KEY_USER  = "@supone:user";

// ─── Token ────────────────────────────────────────────────────────

export async function sauvegarderToken(token: string): Promise<void> {
  await AsyncStorage.setItem(KEY_TOKEN, token);
}

export async function lireToken(): Promise<string | null> {
  return AsyncStorage.getItem(KEY_TOKEN);
}

export async function supprimerToken(): Promise<void> {
  await AsyncStorage.removeItem(KEY_TOKEN);
}

// ─── Utilisateur ──────────────────────────────────────────────────

export async function sauvegarderUser(user: User): Promise<void> {
  await AsyncStorage.setItem(KEY_USER, JSON.stringify(user));
}

export async function lireUser(): Promise<User | null> {
  const raw = await AsyncStorage.getItem(KEY_USER);
  if (!raw) return null;
  try { return JSON.parse(raw) as User; } catch { return null; }
}

export async function supprimerUser(): Promise<void> {
  await AsyncStorage.removeItem(KEY_USER);
}

// ─── Connexion / Déconnexion complète ────────────────────────────

/** Sauvegarde token + user après un login réussi. */
export async function marquerCommeConnecte(token: string, user: User): Promise<void> {
  await Promise.all([sauvegarderToken(token), sauvegarderUser(user)]);
}

/** Supprime token + user → déconnexion complète. */
export async function seDeconnecter(): Promise<void> {
  await Promise.all([supprimerToken(), supprimerUser()]);
}

/** Retourne le prénom ou username pour l'affichage dans le chat. */
export async function lireNomAffichage(): Promise<string> {
  const user = await lireUser();
  return user?.first_name || user?.username || "Étudiant";
}
