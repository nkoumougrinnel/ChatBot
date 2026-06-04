import { IconRefresh, IconWifiOff } from './Icons'

export function OfflineBanner({ onRetry, retrying }) {
  return (
    <div className="offline-banner" role="alert">
      <IconWifiOff />
      <div className="offline-banner__text">
        <strong>Serveur inaccessible</strong>
        <span>Vérifiez votre connexion internet</span>
      </div>
      <button
        type="button"
        className="offline-banner__retry"
        onClick={onRetry}
        disabled={retrying}
        aria-label="Réessayer la connexion"
      >
        <IconRefresh />
        {retrying ? '…' : 'Réessayer'}
      </button>
    </div>
  )
}
