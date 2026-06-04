import { Capacitor } from '@capacitor/core'
import { StatusBar, Style } from '@capacitor/status-bar'

const STATUS_COLORS = {
  dark: { bar: '#0a1628', style: Style.Dark },
  light: { bar: '#ffffff', style: Style.Light },
}

/** Barre de statut Android alignée sur le thème ChatGPT (clair / sombre). */
export async function syncNativeStatusBar(theme) {
  if (!Capacitor.isNativePlatform()) return
  const t = theme === 'light' ? 'light' : 'dark'
  const { bar, style } = STATUS_COLORS[t]
  try {
    await StatusBar.setStyle({ style })
    await StatusBar.setBackgroundColor({ color: bar })
  } catch {
    /* plugin indisponible en web */
  }
}
