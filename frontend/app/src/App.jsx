import { Capacitor } from '@capacitor/core'
import { useCallback, useState } from 'react'
import { ChatHeader } from './components/ChatHeader'
import { Composer } from './components/Composer'
import { InstallBanner } from './components/InstallBanner'
import { MessageBubble } from './components/MessageBubble'
import { OfflineBanner } from './components/OfflineBanner'
import { Suggestions } from './components/Suggestions'
import { Toast } from './components/Toast'
import { Welcome } from './components/Welcome'
import { IconArrowDown } from './components/Icons'
import { useChat } from './hooks/useChat'
import { usePwaInstall } from './hooks/usePwaInstall'
import './App.css'

const isNative = Capacitor.isNativePlatform()

export default function App() {
  const chat = useChat()
  const pwa = usePwaInstall()
  const [showScrollFab, setShowScrollFab] = useState(false)
  const [refreshing, setRefreshing] = useState(false)

  const handleRefresh = useCallback(async () => {
    setRefreshing(true)
    await chat.refreshHealth()
    setRefreshing(false)
    if (chat.online) chat.showToastMsg('Connexion rétablie')
  }, [chat])

  const handleScroll = () => {
    chat.onListScroll()
    const el = chat.listRef.current
    if (!el) return
    const atBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 100
    setShowScrollFab(!atBottom && chat.messages.length > 0)
  }

  const handleInstall = async () => {
    const ok = await pwa.install()
    if (ok) chat.showToastMsg('Application installée !')
  }

  return (
    <div className={`app-shell ${isNative ? 'app-shell--native' : ''}`}>
      <div className="app-bg" aria-hidden />
      <div className="chat-shell">
        {pwa.showBanner && (
          <InstallBanner onInstall={handleInstall} onDismiss={pwa.dismiss} />
        )}

        {chat.online === false && (
          <OfflineBanner onRetry={handleRefresh} retrying={refreshing} />
        )}

        <ChatHeader
          online={chat.online}
          pipelineLabel={chat.pipelineLabel}
          onNewChat={chat.resetChat}
          onInstall={handleInstall}
          canInstall={pwa.canInstall}
          onRefresh={handleRefresh}
          refreshing={refreshing}
        />

        <main
          className="message-list"
          ref={chat.listRef}
          onScroll={handleScroll}
          aria-live="polite"
        >
          {chat.showWelcome && <Welcome />}
          {chat.showWelcome && (
            <Suggestions
              items={chat.suggestions}
              disabled={chat.isProcessing}
              onSelect={chat.sendMessage}
            />
          )}
          {chat.messages.map((msg) => (
            <MessageBubble
              key={msg.id}
              message={msg}
              onCopy={() => chat.showToastMsg('Réponse copiée')}
            />
          ))}
        </main>

        {showScrollFab && (
          <button
            type="button"
            className="scroll-fab"
            onClick={() => {
              chat.scrollToBottom()
              setShowScrollFab(false)
            }}
            aria-label="Descendre"
          >
            <IconArrowDown />
          </button>
        )}

        <Composer
          disabled={chat.isProcessing || chat.online === false}
          onSend={chat.sendMessage}
          compact={isNative}
        />
      </div>

      <Toast message={chat.toast} />
    </div>
  )
}
