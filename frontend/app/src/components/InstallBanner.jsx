import { IconDownload } from './Icons'

export function InstallBanner({ onInstall, onDismiss }) {
  return (
    <div className="install-banner" role="dialog" aria-label="Installer l'application">
      <button type="button" className="install-banner__close" onClick={onDismiss} aria-label="Fermer">
        ×
      </button>
      <img src="/icon.png" alt="" width={48} height={48} className="install-banner__icon" />
      <div className="install-banner__body">
        <strong>Installer SUP&apos;ONE AI</strong>
        <p>Accès rapide depuis votre écran d&apos;accueil — mobile et bureau.</p>
      </div>
      <button type="button" className="install-banner__cta" onClick={onInstall}>
        <IconDownload />
        Installer
      </button>
    </div>
  )
}
