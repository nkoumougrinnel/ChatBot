import { Capacitor } from '@capacitor/core'
import { useCallback, useEffect, useState } from 'react'

const isNativeApp = Capacitor.isNativePlatform()

export function usePwaInstall() {
  const [deferredPrompt, setDeferredPrompt] = useState(null)
  const [canInstall, setCanInstall] = useState(false)
  const [dismissed, setDismissed] = useState(() => {
    try {
      return sessionStorage.getItem('pwa-dismiss') === '1'
    } catch {
      return false
    }
  })

  useEffect(() => {
    const onBeforeInstall = (e) => {
      e.preventDefault()
      setDeferredPrompt(e)
      setCanInstall(true)
    }
    const onInstalled = () => {
      setDeferredPrompt(null)
      setCanInstall(false)
    }
    window.addEventListener('beforeinstallprompt', onBeforeInstall)
    window.addEventListener('appinstalled', onInstalled)
    return () => {
      window.removeEventListener('beforeinstallprompt', onBeforeInstall)
      window.removeEventListener('appinstalled', onInstalled)
    }
  }, [])

  const install = useCallback(async () => {
    if (!deferredPrompt) return false
    deferredPrompt.prompt()
    const { outcome } = await deferredPrompt.userChoice
    setDeferredPrompt(null)
    setCanInstall(false)
    return outcome === 'accepted'
  }, [deferredPrompt])

  const dismiss = useCallback(() => {
    setDismissed(true)
    try {
      sessionStorage.setItem('pwa-dismiss', '1')
    } catch {
      /* ignore */
    }
  }, [])

  const showBanner = !isNativeApp && canInstall && !dismissed

  return { canInstall: !isNativeApp && canInstall, showBanner, install, dismiss, isNativeApp }
}
