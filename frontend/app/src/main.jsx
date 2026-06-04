import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { Capacitor } from '@capacitor/core'
import { SplashScreen } from '@capacitor/splash-screen'
import './index.css'
import App from './App.jsx'
import { syncNativeStatusBar } from './utils/nativeChrome.js'

;(function initTheme() {
  try {
    const stored = localStorage.getItem('supone-theme')
    const theme =
      stored === 'light' || stored === 'dark'
        ? stored
        : window.matchMedia('(prefers-color-scheme: light)').matches
          ? 'light'
          : 'dark'
    document.documentElement.setAttribute('data-theme', theme)
  } catch {
    document.documentElement.setAttribute('data-theme', 'dark')
  }
})()

if (Capacitor.isNativePlatform()) {
  document.documentElement.classList.add('native-app')
  const stored = localStorage.getItem('supone-theme')
  const bootTheme =
    stored === 'light' || stored === 'dark'
      ? stored
      : window.matchMedia('(prefers-color-scheme: light)').matches
        ? 'light'
        : 'dark'
  syncNativeStatusBar(bootTheme)
  SplashScreen.hide().catch(() => {})
}

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
