import { IconDownload, IconPlus, IconRefresh } from './Icons'

export function ChatHeader({
  online,
  pipelineLabel,
  onNewChat,
  onInstall,
  canInstall,
  onRefresh,
  refreshing,
}) {
  const showRetry = online === false && onRefresh

  return (
    <header className="header">
      <button
        type="button"
        className="header-btn"
        onClick={onNewChat}
        aria-label="Nouvelle conversation"
        title="Nouvelle conversation"
      >
        <IconPlus />
      </button>

      <div className="header-brand">
        <img src="/icon.png" alt="" className="header-logo" width={44} height={44} />
        <div className="header-titles">
          <h1>SUP&apos;ONE AI</h1>
          <p className={`header-status ${online === false ? 'offline' : online ? 'online' : ''}`}>
            <span className="status-pulse" />
            {online === null
              ? 'Connexion…'
              : online
                ? `En ligne${pipelineLabel && pipelineLabel !== '…' ? ` · ${pipelineLabel}` : ''}`
                : 'Hors ligne'}
          </p>
        </div>
        {online && pipelineLabel && pipelineLabel !== '…' && (
          <span className="header-pipeline-pill">{pipelineLabel}</span>
        )}
      </div>

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
        <div className="header-spacer" aria-hidden />
      )}
    </header>
  )
}
