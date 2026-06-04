import { Capacitor } from '@capacitor/core'
import { Keyboard } from '@capacitor/keyboard'
import { useEffect } from 'react'

/** Ajuste le composer quand le clavier virtuel Android s’ouvre. */
export function useNativeKeyboard() {
  useEffect(() => {
    if (!Capacitor.isNativePlatform()) return undefined

    const root = document.documentElement

    const onShow = (info) => {
      const h = info?.keyboardHeight ?? 0
      root.style.setProperty('--keyboard-offset', `${h}px`)
      root.classList.add('keyboard-open')
    }

    const onHide = () => {
      root.style.setProperty('--keyboard-offset', '0px')
      root.classList.remove('keyboard-open')
    }

    const showSub = Keyboard.addListener('keyboardWillShow', onShow)
    const hideSub = Keyboard.addListener('keyboardWillHide', onHide)

    return () => {
      showSub.then((h) => h.remove())
      hideSub.then((h) => h.remove())
      onHide()
    }
  }, [])
}
