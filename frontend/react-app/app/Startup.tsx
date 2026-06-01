// app/Startup.tsx — SUP'ONE
// Splash + vérification du token backend au démarrage.
// Vérifie que le token local est encore valide via GET /api/auth/me/.

import { router } from "expo-router";
import React, { useState } from "react";
import { View } from "react-native";

import { fetchMe } from "../Service/api";
import { lireToken, seDeconnecter } from "../Service/authStorage";
import SplashScrenUI from "./SplashScrenUI";

export default function Startup() {
  const [splashActif, setSplashActif] = useState(true);

  async function quandSplashEstTermine() {
    setSplashActif(false);

    const token = await lireToken();

    if (!token) {
      router.replace("/login");
      return;
    }

    // Ping le backend pour vérifier que le token est toujours valide
    const user = await fetchMe(token);

    if (user) {
      router.replace("/");
    } else {
      // Token expiré ou révoqué → nettoyage + renvoi vers login
      await seDeconnecter();
      router.replace("/login");
    }
  }

  if (splashActif) {
    return <SplashScrenUI onFinish={quandSplashEstTermine} />;
  }

  return <View style={{ flex: 1, backgroundColor: "#0f172a" }} />;
}
