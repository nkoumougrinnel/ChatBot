import AsyncStorage from '@react-native-async-storage/async-storage';
import { request } from './client';

const KEY_NAME = 'user_name';
const KEY_EMAIL = 'user_email';

export type UserProfile = {
  name?: string;
  email?: string;
};

export async function saveUserProfile(profile: UserProfile) {
  // locally persist
  if (profile.name) await AsyncStorage.setItem(KEY_NAME, profile.name);
  if (profile.email) await AsyncStorage.setItem(KEY_EMAIL, profile.email);

  // placeholder for backend sync when available
  try {
    await request('/api/user/profile', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(profile) });
  } catch (e) {
    console.warn('Failed to sync profile to backend (mock/local only).', e);
  }
}

export async function getUserProfile(): Promise<UserProfile> {
  // try local
  const name = await AsyncStorage.getItem(KEY_NAME);
  const email = await AsyncStorage.getItem(KEY_EMAIL);

  // attempt fetch from backend (graceful fallback)
  try {
    const res = await request('/api/user/profile');
    if (res.ok) {
      const json = await res.json();
      return { name: json.name ?? name ?? undefined, email: json.email ?? email ?? undefined };
    }
  } catch (e) {
    // ignore
  }

  return { name: name ?? undefined, email: email ?? undefined };
}
