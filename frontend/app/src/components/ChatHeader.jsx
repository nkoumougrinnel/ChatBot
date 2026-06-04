import { IconDownload, IconMoon, IconNewChat, IconRefresh, IconSun } from './Icons'

const STATUS_LABELS = {
  checking: 'Vérification…',
  online: 'En ligne',
  degraded: 'Service partiel',
  offline: 'Hors ligne',
}

export function ChatHeader({
  serverStatus = 'checking',
  faqCount,
  onNewChat,
  onInstall,
  canInstall,
  onRefresh,
  refreshing,
  isDark,
  onToggleTheme,
}) {
  const showRetry = serverStatus === 'offline' && onRefresh
  const statusText = STATUS_LABELS[serverStatus] || '…'
  const subtitle =
    faqCount != null && serverStatus !== 'offline'
      ? `${statusText} · ${faqCount.toLocaleString('fr-FR')} FAQ`
      : statusText

  return (
    <header className="header">
      <button
        type="button"
        className="header-btn header-btn--new-chat"
        onClick={onNewChat}
        aria-label="Nouvelle conversation"
        title="Nouvelle conversation"
      >
        <IconNewChat />
      </button>

      <div className="header-brand">
        <div className="header-logo-wrap">
          <img src="/icon.png" alt="" className="header-logo" width={32} height={32} />
          <span className={`header-live-dot header-live-dot--${serverStatus}`} aria-hidden />
        </div>
        <div className="header-titles">
          <h1>
            <span>SUP&apos;ONE AI</span>
          </h1>
          <p className={`header-status header-status--${serverStatus}`}>
            <span className={`status-pulse status-pulse--${serverStatus}`} />
            {subtitle}
          </p>
        </div>
      </div>

      <div className="header-actions">
        <button
          type="button"
          className="header-btn"
          onClick={onToggleTheme}
          aria-label={isDark ? 'Activer le mode clair' : 'Activer le mode sombre'}
          title={isDark ? 'Mode clair' : 'Mode sombre'}
        >
          {isDark ? <IconSun /> : <IconMoon />}
        </button>

        {showRetry ? (
          <button
            type="button"
            className={`header-btn header-btn--accent ${refreshing ? 'header-btn--spin' : ''}`}
            onClick={onRefresh}
            disabled={refreshing}
            aria-label="Réessayer la connexion"
            title="Réessayer"
          >
            <IconRefresh />
          </button>
        ) : canInstall ? (
          <button
            type="button"
            className="header-btn header-btn--accent"
            onClick={onInstall}
            aria-label="Installer l'application"
            title="Installer"
          >
            <IconDownload />
          </button>
        ) : (
          <button
            type="button"
            className="header-btn"
            onClick={onRefresh}
            disabled={refreshing || serverStatus === 'checking'}
            aria-label="Actualiser le statut serveur"
            title="Actualiser"
          >
            <IconRefresh />
          </button>
        )}
      </div>
    </header>
  )
}
