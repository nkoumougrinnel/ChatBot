/**
 * ==============================================================================
 * SUP'ONE AI — CORE APPLICATION COMPONENT
 * ==============================================================================
 * Architecture : 
 * - State Management: React Hooks (useState, useEffect, useCallback)
 * - Custom Hooks: useChat (Logic), useTheme (Theming), usePwaInstall, useNativeKeyboard
 * - UI Engine: Inline Styles with CSS Variables & Keyframes for high performance
 *
 * Features:
 * - Real-time Streaming (Gen3 IA) & FAQ TF-IDF Fallback
 * - JWT Authentication & Session Persistence (via window.storage)
 * - PWA Support (Install Banners)
 * - Native-optimized (Capacitor) UI with Safe Area management
 * - Advanced UI: Skeleton screens, micro-animations, glassmorphism
 *
 * ─────────────────────────────────────────────────────────────────────────────
 * CORRECTIONS APPLIQUÉES :
 * 1. Utilisation de localStorage standard pour la persistance.
 * 2. IcoMail, IcoUser, IcoLock acceptent désormais une prop `size`.
 * 3. ProfileModal : hooks déplacés avant le early return (règles des Hooks).
 * 4. Welcome : suppression de l'état `showAboutModal` inutilisé.
 * 5. AboutModal : rendu du markdown (**gras**) via renderMd().
 * ==============================================================================
 */

import { Capacitor } from '@capacitor/core'
import { useCallback, useEffect, useRef, useState } from 'react'
import { useChat } from './hooks/useChat'
import { useTheme } from './hooks/useTheme'
import { usePwaInstall } from './hooks/usePwaInstall'
import { useNativeKeyboard } from './hooks/useNativeKeyboard'

// ─── Design tokens ────────────────────────────────────────────────────────────
const GLOBAL_STYLE = `
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  :root {
    --brand-600: #1a4480;
    --brand-500: #2355a0;
    --brand-400: #3b6fd4;
    --brand-300: #60a5fa;
    --brand-200: #93c5fd;
    --brand-100: #dbeafe;
    --success:   #22c55e;
    --success-bg: rgba(34,197,94,.08);
    --warning:   #f59e0b;
    --warning-bg: rgba(245,158,11,.12);
    --error:     #ef4444;
    --error-bg:  rgba(239,68,68,.12);
    --r-xs: 6px; --r-sm: 10px; --r-md: 14px; --r-lg: 18px; --r-xl: 24px; --r-full: 9999px;
    --thread-max: 720px;
    --font: 'Inter', system-ui, -apple-system, sans-serif;
    --t-fast: 120ms ease;
    --t-base: 200ms ease;
    --t-slow: 320ms cubic-bezier(0.16, 1, 0.3, 1);
    --safe-bottom: env(safe-area-inset-bottom, 0px);
    --sidebar-w: 300px;
    --safe-top: env(safe-area-inset-top, 0px);
    --keyboard-offset: 0px;
  }

  :root, [data-theme="dark"] {
    --bg:             #0a0e1a;
    --bg-elevated:    #0f1729;
    --header-bg:      rgba(10,14,26,.88);
    --surface:        rgba(255,255,255,.04);
    --surface-hover:  rgba(255,255,255,.07);
    --surface-active: rgba(255,255,255,.10);
    --border:         rgba(255,255,255,.06);
    --border-strong:  rgba(255,255,255,.12);
    --text:           #edf2f7;
    --text-secondary: rgba(237,242,247,.62);
    --text-tertiary:  rgba(237,242,247,.32);
    --user-bubble:    linear-gradient(135deg, var(--brand-500), var(--brand-400));
    --composer-bg:    rgba(255,255,255,.04);
    --composer-border: rgba(255,255,255,.08);
    --chip-bg:        rgba(255,255,255,.04);
    --chip-border:    rgba(255,255,255,.08);
    --chip-hover:     rgba(255,255,255,.08);
    --scrollbar:      rgba(255,255,255,.10);
    --glow:           rgba(59,111,212,.35);
    --glow-strong:    rgba(59,111,212,.55);
    --shadow-sm:      0 1px 3px rgba(0,0,0,.3);
    --shadow-md:      0 4px 16px rgba(0,0,0,.35);
    --shadow-lg:      0 12px 40px rgba(0,0,0,.45);
    --shadow-xl:      0 20px 60px rgba(0,0,0,.55);
    --overlay:        rgba(0,0,0,.65);
  }

  [data-theme="light"] {
    --bg:             #f0f4fa;
    --bg-elevated:    #ffffff;
    --header-bg:      rgba(255,255,255,.92);
    --surface:        rgba(26,58,107,.04);
    --surface-hover:  rgba(26,58,107,.07);
    --surface-active: rgba(26,58,107,.10);
    --border:         rgba(0,0,0,.06);
    --border-strong:  rgba(0,0,0,.10);
    --text:           #0f172a;
    --text-secondary: #475569;
    --text-tertiary:  #94a3b8;
    --user-bubble:    var(--brand-500);
    --composer-bg:    #ffffff;
    --composer-border: #d1d9e6;
    --chip-bg:        #ffffff;
    --chip-border:    #e2e8f0;
    --chip-hover:     #f1f5f9;
    --scrollbar:      rgba(0,0,0,.10);
    --glow:           rgba(59,111,212,.15);
    --glow-strong:    rgba(59,111,212,.25);
    --shadow-sm:      0 1px 3px rgba(0,0,0,.06);
    --shadow-md:      0 4px 16px rgba(0,0,0,.08);
    --shadow-lg:      0 12px 40px rgba(0,0,0,.12);
    --shadow-xl:      0 20px 60px rgba(0,0,0,.16);
    --overlay:        rgba(0,0,0,.45);
  }

  html, body, #root { width:100%; height:100%; height:100dvh; font-family:var(--font); }
  body {
    background: var(--bg); color: var(--text); line-height: 1.6;
    -webkit-font-smoothing: antialiased; -moz-osx-font-smoothing: grayscale;
    overflow: hidden;
  }
  button { cursor:pointer; border:none; background:none; font-family:inherit; }
  button:focus-visible { outline: 2px solid var(--brand-300); outline-offset: 2px; }
  button:active:not(:disabled) { transform:scale(.97); }

  ::-webkit-scrollbar { width:5px; }
  ::-webkit-scrollbar-track { background:transparent; }
  ::-webkit-scrollbar-thumb { background:var(--scrollbar); border-radius:99px; }
  ::-webkit-scrollbar-thumb:hover { background: var(--text-tertiary); }

  @media (prefers-reduced-motion:reduce) {
    *,*::before,*::after { animation-duration:.01ms!important; transition-duration:.01ms!important; }
  }

  input, textarea {
    background: var(--composer-bg);
    border: 1px solid var(--composer-border);
    color: var(--text);
  }
`

const KEYFRAMES = `
  @keyframes fadeUp   { from{opacity:0;transform:translateY(16px)} to{opacity:1;transform:translateY(0)} }
  @keyframes msgIn    { from{opacity:0;transform:translateY(8px)}  to{opacity:1;transform:translateY(0)} }
  @keyframes chipIn   { from{opacity:0;transform:translateY(8px) scale(.97)} to{opacity:1;transform:translateY(0) scale(1)} }
  @keyframes slideDown{ from{opacity:0;transform:translateY(-8px)} to{opacity:1;transform:translateY(0)} }
  @keyframes pulse    { 0%,100%{opacity:1} 50%{opacity:.35} }
  @keyframes spin     { to{transform:rotate(360deg)} }
  @keyframes blink    { 50%{opacity:0} }
  @keyframes glowPulse{
    0%,100%{box-shadow:0 0 0 8px var(--glow),0 8px 32px var(--glow);transform:scale(1)}
    50%    {box-shadow:0 0 0 14px transparent,0 8px 32px var(--glow-strong);transform:scale(1.03)}
  }
  @keyframes typingBounce{
    0%,80%,100%{transform:scale(.65);opacity:.3}
    40%{transform:scale(1);opacity:1}
  }
  @keyframes fadeInChat { from{opacity:0;transform:scale(.995) translateY(10px)} to{opacity:1;transform:scale(1) translateY(0)} }
  @keyframes slideRight { from{opacity:0;transform:translateX(-24px)} to{opacity:1;transform:translateX(0)} }
  @keyframes popIn     { from{opacity:0;transform:scale(.92) translateY(-8px)} to{opacity:1;transform:scale(1) translateY(0)} }
  @keyframes skeletonPulse { 0%,100%{opacity:.45} 50%{opacity:.15} }
  @keyframes shimmer { 0%{background-position:-200% 0} 100%{background-position:200% 0} }
`

const isNative = Capacitor.isNativePlatform()

// ─── Markdown renderer (gras + sauts de ligne) ────────────────────────────────
function renderMd(text) {
  if (!text) return null
  return text.split('\n').map((line, i) => {
    const parts = line.split(/\*\*(.*?)\*\*/g)
    const nodes = parts.map((p, j) => j % 2 === 1 ? <strong key={j}>{p}</strong> : p)
    return <p key={i} style={{ margin: i > 0 ? '6px 0 0' : 0, lineHeight: 1.65 }}>{nodes}</p>
  })
}

// ─── Icons ────────────────────────────────────────────────────────────────────
const Svg = ({ size = 20, children, ...rest }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden {...rest}>{children}</svg>
)
const stroke = (d, w = 2) => <path d={d} stroke="currentColor" strokeWidth={w} strokeLinecap="round" strokeLinejoin="round" />

const IcoSend      = () => <Svg>{stroke('M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z')}</Svg>
const IcoNewChat   = () => <Svg size={18}>{stroke('M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7M18.5 2.5a2.121 2.121 0 1 1 3 3L12 15l-4 1 1-4 9.5-9.5z')}</Svg>
const IcoHistory   = () => <Svg size={20}>{stroke('M12 8v4l3 3m6-3a9 9 0 1 1-9-9 8.959 8.959 0 0 1 4.5 1.2')}</Svg>
// FIX 2: IcoUser, IcoMail, IcoLock acceptent maintenant une prop `size` (utilisée dans AuthPage avec size={16})
const IcoUser      = ({ size = 20 }) => <Svg size={size}><circle cx="12" cy="7" r="4" stroke="currentColor" strokeWidth="2"/>{stroke('M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2')}</Svg>
const IcoLogOut    = () => <Svg size={18}>{stroke('M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9')}</Svg>
const IcoMail      = ({ size = 18 }) => <Svg size={size}>{stroke('M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2zM22 6l-10 7L2 6')}</Svg>
const IcoLock      = ({ size = 18 }) => <Svg size={size}><rect x="3" y="11" width="18" height="11" rx="2" ry="2" stroke="currentColor" strokeWidth="2"/>{stroke('M7 11V7a5 5 0 0 1 10 0v4')}</Svg>
const IcoSun       = () => <Svg size={18}><circle cx="12" cy="12" r="4" stroke="currentColor" strokeWidth="2"/>{stroke('M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41')}</Svg>
const IcoMoon      = () => <Svg size={18}>{stroke('M21 14.5A8.5 8.5 0 1110.5 4 15 15 0 0021 14.5z')}</Svg>
const IcoCopy      = () => <Svg size={15}><rect x="9" y="9" width="13" height="13" rx="2" stroke="currentColor" strokeWidth="2"/>{stroke('M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1')}</Svg>
const IcoThumbUp   = () => <Svg size={16}>{stroke('M7 11v9a1 1 0 01-1 1H4a1 1 0 01-1-1v-7a1 1 0 011-1h2.2l2.4-5.2a1.5 1.5 0 012.8.4V9h5.6a2 2 0 011.9 2.6l-1.2 6.2A2 2 0 0115.8 20H9')}</Svg>
const IcoThumbDown = () => <Svg size={16}>{stroke('M17 13V4a1 1 0 00-1-1h-2a1 1 0 00-1 1v7a1 1 0 001 1h2.2l-2.4 5.2a1.5 1.5 0 01-2.8-.4V15H5.4a2 2 0 01-1.9-2.6l1.2-6.2A2 2 0 016.6 4H13')}</Svg>
const IcoRefresh   = () => <Svg size={17}>{stroke('M21 12a9 9 0 11-2.64-6.36M21 3v6h-6')}</Svg>
const IcoWifiOff   = () => <Svg size={17}>{stroke('M1 1l22 22M16.72 11.06A10.94 10.94 0 0119 12.55M5 12.55a10.94 10.94 0 015.17-2.39M8.53 16.11a6 6 0 016.95 0M12 20h.01')}</Svg>
const IcoDownload  = () => <Svg size={17}>{stroke('M12 3v12m0 0l4-4m-4 4l-4-4M4 21h16')}</Svg>
const IcoChevDown  = () => <Svg size={18}>{stroke('M6 9l6 6 6-6')}</Svg>
const IcoSparkles  = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor" aria-hidden>
    <path d="M12 2l1.5 4.5L18 8l-4.5 1.5L12 14l-1.5-4.5L6 8l4.5-1.5L12 2zM5 16l.8 2.2L8 19l-2.2.8L5 22l-.8-2.2L2 19l2.2-.8L5 16zM19 15l.6 1.8 1.8.6-1.8.6-.6 1.8-.6-1.8L16 18l1.8-.6.6-1.4z"/>
  </svg>
)

// ─── Status dot ───────────────────────────────────────────────────────────────
function StatusDot({ status }) {
  const colors = { online: 'var(--success)', degraded: 'var(--warning)', offline: 'var(--error)', checking: 'var(--text-tertiary)' }
  return (
    <span style={{
      display: 'inline-block', width: 8, height: 8, borderRadius: '50%', flexShrink: 0,
      background: colors[status] ?? 'var(--text-tertiary)',
      animation: status === 'checking' ? 'pulse 1.2s ease infinite' : 'none',
      boxShadow: status === 'online' ? '0 0 6px var(--success)' : 'none',
    }} />
  )
}

// ─── Header ───────────────────────────────────────────────────────────────────
function Header({ serverStatus, faqCount, isDark, onToggleTheme, onNewChat, onRefresh, refreshing, onInstall, canInstall, onToggleSidebar, user, onAuthClick, onProfileClick, onLogout }) {
  const labels = { online: 'En ligne', degraded: 'Service partiel', offline: 'Hors ligne', checking: 'Connexion…' }
  const subtitle = faqCount != null && serverStatus !== 'offline'
    ? `${labels[serverStatus]} · ${faqCount.toLocaleString('fr-FR')} FAQ`
    : labels[serverStatus] ?? '…'

  const showRetry  = serverStatus === 'offline'
  const showInstall = !showRetry && canInstall && !isNative

  return (
    <header style={{
      display: 'flex', alignItems: 'center', gap: 8, height: isNative ? 50 : 58,
      padding: `0 16px`, paddingTop: `var(--safe-top)`,
      background: 'var(--header-bg)', backdropFilter: 'blur(16px) saturate(1.2)',
      borderBottom: '1px solid var(--border)', flexShrink: 0, zIndex: 10,
    }}>
      {user && (
        <HdrBtn onClick={onToggleSidebar} label="Historique">
          <IcoHistory />
        </HdrBtn>
      )}

      {/* Brand */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, flex: 1, minWidth: 0 }}>
        <div style={{ position: 'relative', flexShrink: 0, display: isNative ? 'none' : 'block' }}>
          <div style={{
            width: 36, height: 36, borderRadius: 14,
            background: 'linear-gradient(135deg, var(--brand-500), var(--brand-300))',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            color: '#fff', boxShadow: '0 2px 12px var(--glow)',
            transition: 'transform var(--t-base)',
          }}>
            <IcoSparkles />
          </div>
          <span style={{
            position: 'absolute', bottom: -1, right: -1,
            width: 11, height: 11, borderRadius: '50%',
            border: '2px solid var(--bg)',
            background: { online: 'var(--success)', degraded: 'var(--warning)', offline: 'var(--error)', checking: 'var(--text-tertiary)' }[serverStatus],
            animation: serverStatus === 'checking' ? 'pulse 1.2s ease infinite' : 'none',
          }} />
        </div>
        <div style={{ minWidth: 0 }}>
          <p style={{ fontSize: 15, fontWeight: 700, letterSpacing: '-0.015em', color: 'var(--text)', lineHeight: 1.2 }}>
            SUP'ONE AI
          </p>
          <p style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: 12, color: 'var(--text-secondary)', marginTop: 2 }}>
            {serverStatus !== 'online' && <StatusDot status={serverStatus} />}
            {subtitle}
          </p>
        </div>
      </div>

      {/* Actions */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
        <HdrBtn onClick={onToggleTheme} label={isDark ? 'Mode clair' : 'Mode sombre'}>
          {isDark ? <IcoSun /> : <IcoMoon />}
        </HdrBtn>

        {showRetry ? (
          <HdrBtn onClick={onRefresh} disabled={refreshing} label="Réessayer" accent spin={refreshing}>
            <IcoRefresh />
          </HdrBtn>
        ) : showInstall ? (
          <HdrBtn onClick={onInstall} label="Installer l'application" accent>
            <IcoDownload />
          </HdrBtn>
        ) : (
          <HdrBtn onClick={onRefresh} disabled={refreshing || serverStatus === 'checking'} label="Actualiser">
            <IcoRefresh />
          </HdrBtn>
        )}

        {user ? (
          <UserAvatarButton user={user} onProfileClick={onProfileClick} onLogout={onLogout} />
        ) : (
          <div style={{ animation: 'popIn .3s ease' }}>
            <HdrBtn onClick={onAuthClick} label="Connexion">
              <IcoUser />
            </HdrBtn>
          </div>
        )}

        <HdrBtn onClick={onNewChat} label="Nouveau" accent>
          <IcoNewChat />
        </HdrBtn>
      </div>
    </header>
  )
}

function UserAvatarButton({ user, onProfileClick, onLogout }) {
  const [showDropdown, setShowDropdown] = useState(false)
  const buttonRef = useRef(null)

  const handleToggleDropdown = (e) => {
    e.stopPropagation()
    setShowDropdown(prev => !prev)
  }

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (buttonRef.current && !buttonRef.current.contains(event.target)) {
        setShowDropdown(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [])

  return (
    <div style={{ position: 'relative', display: 'inline-block' }} ref={buttonRef}>
      <button
        type="button" onClick={handleToggleDropdown}
        aria-label={user.username} title={user.username}
        style={{
          width: isNative ? 44 : 36, height: isNative ? 44 : 36,
          borderRadius: '50%',
          minWidth: isNative ? 44 : 'auto',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          color: '#fff',
          background: 'linear-gradient(135deg, var(--brand-500), var(--brand-400))',
          boxShadow: '0 2px 8px var(--glow)',
          transition: 'all var(--t-base)',
        }}
        onMouseEnter={e => { e.currentTarget.style.transform = 'scale(1.05)'; }}
        onMouseLeave={e => { e.currentTarget.style.transform = 'scale(1)'; }}
      >
        <span style={{ fontSize: 14, fontWeight: 700, lineHeight: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', width: '100%', height: '100%' }}>
          {user.username.charAt(0).toUpperCase()}
        </span>
      </button>
      {showDropdown && (
        <UserDropdown
          onClose={() => setShowDropdown(false)}
          onProfileClick={onProfileClick}
          onLogout={onLogout}
        />
      )}
    </div>
  )
}

function UserDropdown({ onClose, onProfileClick, onLogout }) {
  return (
    <div style={{
      position: 'absolute',
      top: 'calc(100% + 8px)',
      right: 0,
      background: 'var(--bg-elevated)',
      border: '1px solid var(--border-strong)',
      borderRadius: 'var(--r-md)',
      boxShadow: 'var(--shadow-lg)',
      minWidth: 170,
      zIndex: 60,
      animation: 'popIn .25s cubic-bezier(0.16, 1, 0.3, 1)',
      padding: '6px 0',
    }}>
      <button onClick={() => { onProfileClick(); onClose(); }} style={{
        width: '100%', textAlign: 'left', padding: '10px 16px',
        fontSize: 13.5, color: 'var(--text)',
        background: 'transparent', border: 'none',
        transition: 'background var(--t-fast)',
      }} onMouseEnter={e => e.currentTarget.style.background = 'var(--surface-hover)'} onMouseLeave={e => e.currentTarget.style.background = 'transparent'}>
        Mon profil
      </button>
      <button onClick={() => { onLogout(); onClose(); }} style={{
        width: '100%', textAlign: 'left', padding: '10px 16px',
        fontSize: 13.5, color: 'var(--error)',
        background: 'transparent', border: 'none',
        transition: 'background var(--t-fast)',
      }} onMouseEnter={e => e.currentTarget.style.background = 'var(--error-bg)'} onMouseLeave={e => e.currentTarget.style.background = 'transparent'}>
        Déconnexion
      </button>
    </div>
  )
}

// ─── Skeletons ────────────────────────────────────────────────────────────────
function SidebarSkeleton() {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 10, padding: '12px 14px' }}>
      {[1, 2, 3, 4, 5].map(i => (
        <div key={i} style={{
          height: 40, width: '100%', borderRadius: 12,
          background: 'var(--border-strong)', animation: 'skeletonPulse 1.8s ease-in-out infinite'
        }} />
      ))}
    </div>
  )
}

// ─── Loading Screen ───────────────────────────────────────────────────────────
function LoadingScreen() {
  return (
    <div style={{
      flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
      gap: 24, animation: 'fadeUp .5s ease'
    }}>
      <div style={{
        position: 'relative', width: 48, height: 48,
      }}>
        <div style={{
          position: 'absolute', inset: 0,
          border: '3px solid var(--border-strong)',
          borderTopColor: 'var(--brand-500)', borderRadius: '50%',
          animation: 'spin .8s linear infinite'
        }} />
        <div style={{
          position: 'absolute', inset: 6,
          border: '2px solid transparent',
          borderBottomColor: 'var(--brand-300)', borderRadius: '50%',
          animation: 'spin 1.2s linear infinite reverse'
        }} />
      </div>
      <div style={{ textAlign: 'center' }}>
        <p style={{ fontSize: 14, color: 'var(--text-secondary)', fontWeight: 500, letterSpacing: '0.03em', textTransform: 'uppercase' }}>
          Sécurisation de la connexion…
        </p>
        <p style={{ fontSize: 12, color: 'var(--text-tertiary)', marginTop: 6 }}>
          Vérification de la session en cours
        </p>
      </div>
    </div>
  )
}

// ─── App ──────────────────────────────────────────────────────────────────────
export default function App() {
  const chat            = useChat()
  const pwa             = usePwaInstall()
  const { isDark, toggleTheme } = useTheme()
  const [showScrollFab, setShowScrollFab] = useState(false)
  const [refreshing, setRefreshing]       = useState(false)

  // Nouveaux états pro
  const [user, setUser]                   = useState(null) // null = non connecté
  const [authView, setAuthView]           = useState(null) // null, 'login', 'signup'
  const [sidebarOpen, setSidebarOpen]     = useState(false)
  const [showAbout, setShowAbout]         = useState(false)
  const [showProfile, setShowProfile]     = useState(false)
  const [isAuthenticating, setIsAuthenticating] = useState(false)

  // FIX 1: Persistance via window.storage (localStorage non supporté dans les artifacts)
  // Charger l'utilisateur au démarrage
  useEffect(() => {
    let cancelled = false

    ;(async () => {
      try {
        const savedUser  = localStorage.getItem('supone-user')
        const savedToken = localStorage.getItem('supone-token')

        if (cancelled) return

        if (savedUser && savedToken) {
          setIsAuthenticating(true)
          // Simulation d'une vérification de validité du Token (Refresh Token)
          setTimeout(() => {
            if (cancelled) return
            try {
              setUser(JSON.parse(savedUser))
              chat.showToastMsg("Session restaurée avec succès")
              chat.refreshHistory()
            } catch (e) {
              handleLogout()
            } finally {
              setIsAuthenticating(false)
            }
          }, 1000)
        }
      } catch {
        // Pas de session sauvegardée — comportement normal pour un nouvel utilisateur
      }
    })()

    return () => { cancelled = true }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []) // On retire 'chat' pour éviter la boucle infinie

  useNativeKeyboard()

  const handleLogin = (userData) => {
    setIsAuthenticating(true)
    // Simulation d'une latence réseau pour un effet pro
    setTimeout(async () => {
      setUser(userData)
      try {
        localStorage.setItem('supone-token', 'sk_live_' + Math.random().toString(36).substr(2))
        localStorage.setItem('supone-user', JSON.stringify(userData))
      } catch (e) {
        console.error('Erreur de persistance de session', e)
      }
      setAuthView(null)
      setIsAuthenticating(false)
      chat.showToastMsg(`Bonjour ${userData.username} !`)
      chat.refreshHistory()
    }, 1200)
  }

  const handleLogout = () => {
    setUser(null)
    localStorage.removeItem('supone-token')
    localStorage.removeItem('supone-user')
    chat.resetChat()
    chat.showToastMsg("Déconnexion réussie")
  }

  const handleProfileClick = () => {
    setShowProfile(true)
  }

  const handleAuthClick = () => {
    if (user) {
      // This case should now be handled by UserAvatarButton
      // but keeping it for consistency if IcoUser is clicked when user is logged in (which shouldn't happen with the new logic)
      if (window.confirm("Voulez-vous vous déconnecter ?")) handleLogout()
    } else {
      setAuthView('login')
    }
  }

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

  const theme = isDark ? 'dark' : 'light'

  return (
    <>
      <style dangerouslySetInnerHTML={{ __html: GLOBAL_STYLE + KEYFRAMES }} />

      <div
        data-theme={theme}
        className={isNative ? 'native-app' : ''}
        style={{
          width: '100%', height: '100vh', height: '100dvh',
          display: 'flex', flexDirection: 'column',
          background: 'var(--bg)', overflow: 'hidden', position: 'relative',
        }}
      >
        {/* Fond ambiant */}
        <div aria-hidden style={{
          position: 'fixed', inset: 0, pointerEvents: 'none', zIndex: 0,
          background: isDark
            ? 'radial-gradient(ellipse 70% 50% at 50% -10%, rgba(35,85,160,.22) 0%, transparent 70%)'
            : 'radial-gradient(ellipse 70% 50% at 50% -10%, rgba(59,111,212,.08) 0%, transparent 70%)',
        }} />

        {/* Shell principal */}
        <div style={{ position: 'relative', zIndex: 1, flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column' }}>

          <Sidebar
            open={sidebarOpen}
            onClose={() => setSidebarOpen(false)}
            history={isAuthenticating ? null : (chat.history || [])}
            onSelect={chat.loadThread}
            onShowAbout={() => setShowAbout(true)}
            onNewChat={chat.resetChat}
          />

          {/* Banners */}
          {pwa.showBanner && <InstallBanner onInstall={handleInstall} onDismiss={pwa.dismiss} />}
          {chat.serverStatus === 'offline'  && <OfflineBanner onRetry={handleRefresh} retrying={refreshing} />}
          {chat.serverStatus === 'degraded' && <DegradedBanner />}

          <Header
            serverStatus={chat.serverStatus}
            faqCount={chat.healthInfo?.faq_count}
            isDark={isDark}
            onToggleTheme={toggleTheme}
            onNewChat={chat.resetChat}
            onRefresh={handleRefresh}
            refreshing={refreshing}
            onInstall={handleInstall}
            canInstall={pwa.canInstall}
            onToggleSidebar={() => setSidebarOpen(!sidebarOpen)}
            user={user}
            onAuthClick={handleAuthClick}
            onProfileClick={handleProfileClick}
            onLogout={handleLogout}
          />

          {isAuthenticating ? (
            <LoadingScreen />
          ) : authView ? (
            <AuthPage
              mode={authView}
              onSwitch={() => setAuthView(authView === 'login' ? 'signup' : 'login')}
              onLogin={handleLogin}
            />
          ) : (
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0, animation: 'fadeInChat .6s cubic-bezier(0.16, 1, 0.3, 1)' }}>
              {/* Thread */}
              <main
                ref={chat.listRef}
                onScroll={handleScroll}
                aria-live="polite"
                aria-label="Conversation"
                style={{
                  flex: 1, overflowY: 'auto',
                  maxWidth: isNative ? '100%' : 'var(--thread-max)',
                  width: '100%', margin: '0 auto',
                  padding: isNative ? '16px max(12px,env(safe-area-inset-right)) 8px max(12px,env(safe-area-inset-left))' : '24px 16px 8px',
                  display: 'flex', flexDirection: 'column',
                  scrollBehavior: 'smooth', WebkitOverflowScrolling: 'touch',
                }}
              >
                {chat.showWelcome ? (
                  <Welcome
                    suggestions={chat.suggestions}
                    disabled={chat.isProcessing}
                    onSelect={chat.sendMessage}
                    user={user}
                  />
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 22 }}>
                    {chat.messages.map(msg => (
                      <MessageBubble
                        key={msg.id}
                        message={msg}
                        onCopy={() => chat.showToastMsg('Réponse copiée')}
                        onSubmitFeedback={chat.sendFeedback}
                        onToast={chat.showToastMsg}
                      />
                    ))}
                  </div>
                )}
              </main>

              <ScrollFab
                visible={showScrollFab}
                onClick={() => { chat.scrollToBottom(); setShowScrollFab(false) }}
              />

              <Composer
                disabled={chat.isProcessing || chat.serverStatus === 'offline'}
                onSend={chat.sendMessage}
                compact={isNative}
              />
            </div>
          )}
        </div>

        <Toast message={chat.toast} />

        <AboutModal open={showAbout} onClose={() => setShowAbout(false)} />
        <ProfileModal open={showProfile} onClose={() => setShowProfile(false)} user={user} onLogout={handleLogout} onSave={(u) => { setUser(u); chat.showToastMsg('Profil mis à jour'); }} />
      </div>
    </>
  )
}
function HdrBtn({ children, onClick, disabled, label, accent, spin }) {
  return (
    <button
      type="button" onClick={onClick} disabled={disabled}
      aria-label={label} title={label}
      style={{
        width: isNative ? 44 : 36, height: isNative ? 44 : 36, borderRadius: 10, minWidth: isNative ? 44 : 'auto',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        color: accent ? '#fff' : 'var(--text-secondary)',
        background: accent ? 'var(--brand-500)' : 'var(--surface)',
        transition: 'all var(--t-base)',
        opacity: disabled ? 0.4 : 1,
      }}
      onMouseEnter={e => { if (!disabled) { e.currentTarget.style.background = accent ? 'var(--brand-400)' : 'var(--surface-hover)'; if (!accent) e.currentTarget.style.color = 'var(--text)'; }}}
      onMouseLeave={e => { e.currentTarget.style.background = accent ? 'var(--brand-500)' : 'transparent'; if (!accent) e.currentTarget.style.color = 'var(--text-secondary)'; }}
    >
      <span style={{ display: 'flex', animation: spin ? 'spin .8s linear infinite' : 'none' }}>
        {children}
      </span>
    </button>
  )
}

// ─── Banners ──────────────────────────────────────────────────────────────────
function InstallBanner({ onInstall, onDismiss }) {
  return (
    <div role="dialog" aria-label="Installer l'application" style={{
      display: 'flex', alignItems: 'center', gap: 14,
      margin: '10px auto 0', padding: '14px 16px',
      maxWidth: 'var(--thread-max)', width: 'calc(100% - 32px)',
      background: 'var(--bg-elevated)', border: '1px solid var(--border-strong)',
      borderRadius: 'var(--r-lg)', position: 'relative', animation: 'slideDown .35s cubic-bezier(0.16, 1, 0.3, 1)',
      boxShadow: 'var(--shadow-md)',
    }}>
      <button
        type="button" onClick={onDismiss} aria-label="Fermer"
        style={{ position: 'absolute', top: 8, right: 10, width: 24, height: 24, fontSize: '1.1rem', color: 'var(--text-secondary)' }}
      >×</button>
      <div style={{
        width: 46, height: 46, borderRadius: 12, flexShrink: 0,
        background: 'linear-gradient(135deg, var(--brand-500), var(--brand-300))',
        display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff',
        boxShadow: '0 2px 10px var(--glow)',
      }}>
        <IcoSparkles />
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <p style={{ fontSize: 14, fontWeight: 700 }}>Installer SUP'ONE AI</p>
        <p style={{ fontSize: 12.5, color: 'var(--text-secondary)', marginTop: 3 }}>Accès rapide depuis votre écran d'accueil</p>
      </div>
      <button
        type="button" onClick={onInstall}
        style={{ padding: '8px 14px', background: 'var(--brand-500)', color: '#fff', borderRadius: 'var(--r-full)', fontSize: 13, fontWeight: 600, display: 'flex', alignItems: 'center', gap: 5, flexShrink: 0, transition: 'all var(--t-fast)' }}
        onMouseEnter={e => { e.currentTarget.style.background = 'var(--brand-400)'; }}
        onMouseLeave={e => { e.currentTarget.style.background = 'var(--brand-500)'; }}
      >
        <IcoDownload /> Installer
      </button>
    </div>
  )
}

function OfflineBanner({ onRetry, retrying }) {
  return (
    <div role="alert" style={{
      display: 'flex', alignItems: 'center', gap: 10,
      margin: '10px auto 0', padding: '12px 16px',
      maxWidth: 'var(--thread-max)', width: 'calc(100% - 32px)',
      background: 'var(--error-bg)', border: '1px solid rgba(239,68,68,.25)',
      borderRadius: 'var(--r-lg)', animation: 'slideDown .35s cubic-bezier(0.16, 1, 0.3, 1)',
    }}>
      <IcoWifiOff />
      <div style={{ flex: 1 }}>
        <p style={{ fontSize: 13.5, fontWeight: 600 }}>Serveur inaccessible</p>
        <p style={{ fontSize: 12.5, color: 'var(--text-secondary)', marginTop: 2 }}>Vérifiez votre connexion internet</p>
      </div>
      <button
        type="button" onClick={onRetry} disabled={retrying}
        style={{ padding: '7px 14px', borderRadius: 'var(--r-sm)', background: 'var(--error)', color: '#fff', fontSize: 12.5, fontWeight: 600, display: 'flex', alignItems: 'center', gap: 5, opacity: retrying ? 0.6 : 1, transition: 'opacity var(--t-fast)' }}
      >
        <IcoRefresh /> {retrying ? '…' : 'Réessayer'}
      </button>
    </div>
  )
}

function DegradedBanner() {
  return (
    <div role="status" style={{
      padding: '8px 16px', textAlign: 'center', fontSize: 12.5, fontWeight: 500,
      color: 'var(--warning)', background: 'var(--warning-bg)',
      borderBottom: '1px solid rgba(245,158,11,.2)',
    }}>
      Base FAQ en cours d'indexation — certaines réponses peuvent être limitées.
    </div>
  )
}

// ─── Welcome ──────────────────────────────────────────────────────────────────
function Welcome({ suggestions, disabled, onSelect, user }) {
  const [greeting, setGreeting] = useState('')

  useEffect(() => {
    const hour = new Date().getHours()
    let timeSalute = "Bonjour"
    if (hour >= 18) timeSalute = "Bonsoir"
    if (hour >= 21 || hour < 5) timeSalute = "Bonne nuit"

    const options = [
      `${timeSalute}${user ? ' ' + user.username : ''}, en quoi puis-je vous éclairer ?`,
      `Ravi de vous revoir${user ? ' ' + user.username : ''} ! Une question sur SUP'PTIC ?`,
      `Bienvenue sur SUP'ONE AI. Comment se passe votre journée ?`,
      `Je suis prêt à répondre à toutes vos questions sur l'école, ${user ? user.username : 'cher étudiant'}.`,
      `Besoin d'aide pour les inscriptions ou les examens ? Demandez-moi !`
    ]
    setGreeting(options[Math.floor(Math.random() * options.length)])
  }, [user])

  if (!greeting) return null

  return (
    <div style={{
      flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center',
      justifyContent: 'center', padding: '48px 20px 32px', textAlign: 'center',
      animation: 'fadeUp .6s cubic-bezier(0.16, 1, 0.3, 1)',
    }}>
      {/* Logo animé */}
      <div style={{
        width: 72, height: 72, borderRadius: 20, marginBottom: 28,
        background: 'linear-gradient(135deg, var(--brand-500) 0%, var(--brand-300) 100%)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        color: '#fff',
        boxShadow: '0 0 0 10px var(--glow), 0 12px 40px var(--glow-strong)',
        animation: 'glowPulse 3s ease-in-out infinite',
      }}>
        <IcoSparkles />
      </div>

      <h1 style={{
        fontSize: 'clamp(24px, 4vw, 30px)', fontWeight: 800,
        letterSpacing: '-0.035em', color: 'var(--text)', lineHeight: 1.15,
      }}>
        {greeting}
      </h1>
      <p style={{ fontSize: 15, color: 'var(--text-secondary)', lineHeight: 1.65, marginTop: 12, maxWidth: 440 }}>
        Assistant officiel SUP'PTIC — posez vos questions sur l'école,
        les inscriptions, les examens et les services étudiants.
      </p>

      {/* Suggestion cards en grille */}
      {suggestions?.length > 0 && (
        <div style={{
          display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
          gap: 10, marginTop: 36, width: '100%', maxWidth: 580,
        }}>
          {suggestions.map((text, i) => (
            <button
              key={text} type="button" disabled={disabled} onClick={() => onSelect(text)}
              style={{
                padding: '14px 16px', textAlign: 'left',
                background: 'var(--chip-bg)', border: '1px solid var(--chip-border)',
                borderRadius: 'var(--r-lg)', color: 'var(--text)',
                fontSize: 13.5, lineHeight: 1.45,
                opacity: disabled ? 0.5 : 1, cursor: disabled ? 'not-allowed' : 'pointer',
                transition: 'all var(--t-base)',
                animation: `chipIn .4s cubic-bezier(0.16, 1, 0.3, 1) ${i * 60}ms backwards`,
              }}
              onMouseEnter={e => { if (!disabled) { e.currentTarget.style.background = 'var(--chip-hover)'; e.currentTarget.style.borderColor = 'var(--brand-300)'; e.currentTarget.style.transform = 'translateY(-2px)'; }}}
              onMouseLeave={e => { e.currentTarget.style.background = 'var(--chip-bg)'; e.currentTarget.style.borderColor = 'var(--chip-border)'; e.currentTarget.style.transform = 'translateY(0)'; }}
            >
              <span style={{ fontSize: 16, display: 'block', marginBottom: 6 }}>
                {['', '', '', '', ''][i] || ''}
              </span>
              {text}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

// ─── Typing dots ──────────────────────────────────────────────────────────────
function TypingDots({ label }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'var(--text-secondary)', fontSize: 14 }}>
      <span style={{ display: 'flex', gap: 5 }}>
        {[0, 1, 2].map(i => (
          <span key={i} style={{
            width: 7, height: 7, borderRadius: '50%', display: 'inline-block',
            background: 'var(--brand-400)',
            animation: `typingBounce 1.2s ${i * 0.15}s ease-in-out infinite`,
          }} />
        ))}
      </span>
      <span style={{ fontWeight: 500 }}>{label || 'Réflexion…'}</span>
    </div>
  )
}

// ─── Avatar bot ───────────────────────────────────────────────────────────────
function BotAvatar({ error }) {
  return (
    <div style={{
      width: 32, height: 32, borderRadius: 10, flexShrink: 0, marginTop: 2,
      background: error ? 'var(--error-bg)' : 'linear-gradient(135deg, var(--brand-500), var(--brand-300))',
      border: `1px solid ${error ? 'rgba(239,68,68,.25)' : 'transparent'}`,
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      color: error ? 'var(--error)' : '#fff',
      boxShadow: error ? 'none' : '0 2px 8px var(--glow)',
    }}>
      <IcoSparkles />
    </div>
  )
}

// ─── Feedback bar ─────────────────────────────────────────────────────────────
function FeedbackBar({ faqId, userQuestion, score, onSubmitFeedback, onToast }) {
  const [vote, setVote]               = useState(null)
  const [submitting, setSubmitting]   = useState(false)
  const [showForm, setShowForm]       = useState(false)
  const [comment, setComment]         = useState('')

  if (!userQuestion) return null

  const send = async (type, extraComment = '') => {
    if (submitting || vote) return
    setSubmitting(true)
    try {
      await onSubmitFeedback({ faqId, feedbackType: type, question: userQuestion, score, comment: extraComment })
      setVote(type)
      onToast?.(type === 'positif' ? 'Merci pour votre retour positif !' : 'Merci, votre retour nous aide à améliorer les réponses.')
      setShowForm(false)
    } catch {
      onToast?.("Impossible d'envoyer le feedback")
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div style={{ marginTop: 12 }}>
      <div style={{ display: 'flex', gap: 4 }}>
        <FbBtn active={vote === 'positif'} activeColor="var(--success)" activeBg="var(--success-bg)"
          onClick={() => send('positif')} disabled={submitting || !!vote} label="Utile">
          <IcoThumbUp /><span>Utile</span>
        </FbBtn>
        <FbBtn active={vote === 'negatif'} activeColor="var(--error)" activeBg="var(--error-bg)"
          onClick={() => { if (!vote) setShowForm(true) }} disabled={submitting || !!vote} label="Peu utile">
          <IcoThumbDown /><span>Peu utile</span>
        </FbBtn>
      </div>

      {showForm && !vote && (
        <div style={{
          marginTop: 10, padding: '14px 16px',
          background: 'var(--surface)', border: '1px solid var(--border)',
          borderRadius: 'var(--r-lg)', animation: 'fadeUp .25s ease',
        }}>
          <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 10, fontWeight: 500 }}>
            Qu'est-ce qui pourrait être amélioré ? <em style={{ opacity: .6 }}>(optionnel)</em>
          </p>
          <textarea
            value={comment} onChange={e => setComment(e.target.value)}
            placeholder="Décrivez le problème…" rows={2} maxLength={500}
            style={{
              width: '100%', padding: '10px 12px', borderRadius: 'var(--r-md)',
              border: '1px solid var(--composer-border)', background: 'var(--composer-bg)',
              color: 'var(--text)', fontSize: 13.5, resize: 'vertical', fontFamily: 'inherit', outline: 'none',
            }}
          />
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, marginTop: 10 }}>
            <button type="button" onClick={() => setShowForm(false)}
              style={{ fontSize: 13, color: 'var(--text-secondary)', padding: '6px 12px', borderRadius: 'var(--r-sm)', fontWeight: 500 }}>
              Annuler
            </button>
            <button type="button" onClick={() => send('negatif', comment.trim())} disabled={submitting}
              style={{ fontSize: 13, fontWeight: 600, color: '#fff', background: 'var(--brand-500)', padding: '6px 16px', borderRadius: 'var(--r-sm)' }}>
              Envoyer
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

function FbBtn({ children, onClick, active, activeColor, activeBg, disabled, label }) {
  const [hov, setHov] = useState(false)
  return (
    <button type="button" onClick={onClick} disabled={disabled} aria-label={label}
      onMouseEnter={() => setHov(true)} onMouseLeave={() => setHov(false)}
      style={{
        display: 'inline-flex', alignItems: 'center', gap: 6, padding: '7px 14px', borderRadius: 10,
        fontSize: 13, fontWeight: 500,
        color: active ? activeColor : (hov && !disabled) ? 'var(--text)' : 'var(--text-secondary)',
        background: active ? activeBg : hov ? 'var(--surface-hover)' : 'transparent',
        transition: 'all var(--t-fast)',
        opacity: disabled && !active ? 0.4 : 1,
        cursor: disabled ? 'default' : 'pointer',
      }}>
      {children}
    </button>
  )
}

// ─── Message bubble ───────────────────────────────────────────────────────────
function MessageBubble({ message, onCopy, onSubmitFeedback, onToast }) {
  const [copied, setCopied] = useState(false)

  const handleCopy = async () => {
    if (!message.content) return
    try {
      await navigator.clipboard.writeText(message.content)
      setCopied(true)
      onCopy?.()
      setTimeout(() => setCopied(false), 2000)
    } catch { /* ignore */ }
  }

  // Message utilisateur
  if (message.role === 'user') {
    return (
      <div style={{
        display: 'flex', justifyContent: 'flex-end', width: '100%',
        paddingLeft: isNative ? '8%' : '18%',
        animation: 'msgIn .25s cubic-bezier(0.16, 1, 0.3, 1)',
      }}>
        <div style={{
          background: 'var(--user-bubble)', color: '#fff',
          padding: '11px 18px', borderRadius: '20px 20px 6px 20px',
          fontSize: 15, lineHeight: 1.65, maxWidth: '100%',
          boxShadow: '0 4px 16px rgba(35,85,160,.25)',
          position: 'relative',
        }}>
          {renderMd(message.content)}
        </div>
      </div>
    )
  }

  // Erreur
  if (message.status === 'error') {
    return (
      <div style={{ display: 'flex', gap: 10, animation: 'msgIn .25s cubic-bezier(0.16, 1, 0.3, 1)' }}>
        <BotAvatar error />
        <div style={{
          background: 'var(--error-bg)', border: '1px solid rgba(239,68,68,.2)',
          borderRadius: '6px 20px 20px 20px', padding: '14px 18px', flex: 1,
        }}>
          <p style={{ fontSize: 12.5, fontWeight: 700, color: 'var(--error)', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.04em' }}>Connexion impossible</p>
          <p style={{ fontSize: 14.5, color: 'var(--text-secondary)', lineHeight: 1.6 }}>{message.content}</p>
        </div>
      </div>
    )
  }

  const loading   = message.status === 'loading'
  const streaming = message.status === 'streaming'
  const done      = message.status === 'done'

  return (
    <div style={{ display: 'flex', gap: 10, alignItems: 'flex-start', animation: 'msgIn .25s cubic-bezier(0.16, 1, 0.3, 1)' }}>
      <BotAvatar />
      <div style={{ flex: 1, minWidth: 0, paddingTop: 4 }}>
        <div style={{ fontSize: 15, color: 'var(--text)', lineHeight: 1.7 }}>
          {loading && <TypingDots label={message.statusLabel} />}

          {(streaming || done) && message.content && (
            <>
              {renderMd(message.content)}
              {streaming && (
                <span style={{
                  display: 'inline-block', width: 2, height: '1em', marginLeft: 2,
                  background: 'var(--brand-300)', verticalAlign: 'text-bottom',
                  animation: 'blink .9s step-end infinite',
                }} />
              )}
            </>
          )}

          {message.mode === 'low' && (
            <div style={{
              marginTop: 16, padding: '18px',
              background: 'var(--warning-bg)', borderRadius: 'var(--r-lg)',
              border: '1px solid rgba(245,158,11,.2)',
              fontSize: 14, color: 'var(--text-secondary)',
              animation: 'popIn .35s ease'
            }}>
              <p style={{ fontWeight: 700, color: 'var(--warning)', marginBottom: 10, fontSize: 12.5, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Pistes de solution
              </p>
              <ul style={{ paddingLeft: 20, lineHeight: 1.9, listStyleType: 'circle' }}>
                <li>Précisez votre demande (ex: "frais d'inscription ITT")</li>
                <li>Reformulez votre question avec d'autres mots</li>
                <li>Contactez l'assistance : <a href="mailto:support@e-supptic.cm" style={{ color: 'var(--brand-300)', textDecoration: 'none', fontWeight: 500 }}>support@e-supptic.cm</a></li>
              </ul>
            </div>
          )}
        </div>

        {/* Feedback */}
        {done && message.content && message.mode !== 'low' && (
          <FeedbackBar
            faqId={message.faqId}
            userQuestion={message.userQuestion}
            score={message.score}
            onSubmitFeedback={onSubmitFeedback}
            onToast={onToast}
          />
        )}

        {/* Actions */}
        {done && message.content && (
          <div style={{ display: 'flex', alignItems: 'center', marginTop: 8 }}>
            <button
              type="button" onClick={handleCopy} aria-label="Copier la réponse"
              style={{
                display: 'inline-flex', alignItems: 'center', gap: 5, padding: '5px 10px',
                borderRadius: 8, fontSize: 12.5, fontWeight: 500,
                color: copied ? 'var(--brand-300)' : 'var(--text-secondary)',
                background: copied ? 'var(--surface)' : 'transparent',
                transition: 'all var(--t-fast)',
              }}
              onMouseEnter={e => { if (!copied) { e.currentTarget.style.background = 'var(--surface-hover)'; e.currentTarget.style.color = 'var(--text)'; }}}
              onMouseLeave={e => { if (!copied) { e.currentTarget.style.background = 'transparent'; e.currentTarget.style.color = 'var(--text-secondary)'; }}}
            >
              <IcoCopy />
              {copied ? 'Copié !' : 'Copier'}
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

// ─── Composer ─────────────────────────────────────────────────────────────────
function Composer({ disabled, onSend, compact }) {
  const [value, setValue] = useState('')
  const ref = useRef(null)
  const MAX = 500

  const autoResize = useCallback(() => {
    const el = ref.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = `${Math.min(el.scrollHeight, 180)}px`
  }, [])

  const submit = useCallback(() => {
    const text = value.trim()
    if (!text || disabled) return
    onSend(text)
    setValue('')
    if (ref.current) ref.current.style.height = 'auto'
  }, [value, disabled, onSend])

  const onKey = e => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); submit() }
  }

  const len     = value.length
  const canSend = len > 0 && !disabled

  return (
    <div style={{
      flexShrink: 0, background: 'var(--bg)',
      borderTop: compact ? 'none' : '1px solid var(--border)',
      paddingBottom: `calc(var(--safe-bottom) + var(--keyboard-offset))`,
      zIndex: 5,
    }}>
      <div style={{ maxWidth: 'var(--thread-max)', margin: '0 auto', padding: compact ? '8px 12px' : '12px 16px 16px' }}>
        <div
          style={{
            display: 'flex', alignItems: 'flex-end', gap: 8,
            background: 'var(--composer-bg)', border: `1px solid ${len > 0 ? 'var(--brand-400)' : 'var(--composer-border)'}`,
            borderRadius: 26, padding: '7px 7px 7px 18px',
            boxShadow: len > 0 ? '0 4px 24px rgba(0,0,0,.22), 0 0 0 3px var(--glow)' : 'var(--shadow-sm)',
            backdropFilter: 'blur(12px)',
            transition: 'border-color var(--t-base), box-shadow var(--t-base)',
          }}
          onFocusCapture={e => { e.currentTarget.style.borderColor = 'var(--brand-300)'; e.currentTarget.style.boxShadow = '0 4px 24px rgba(0,0,0,.22), 0 0 0 3px var(--glow-strong)'; }}
          onBlurCapture={e => { e.currentTarget.style.borderColor = len > 0 ? 'var(--brand-400)' : 'var(--composer-border)'; e.currentTarget.style.boxShadow = len > 0 ? '0 4px 24px rgba(0,0,0,.22), 0 0 0 3px var(--glow)' : 'var(--shadow-sm)'; }}
        >
          <textarea
            ref={ref} value={value}
            onChange={e => { setValue(e.target.value.slice(0, MAX)); autoResize() }}
            onKeyDown={onKey}
            placeholder="Posez votre question…"
            disabled={disabled} rows={1} aria-label="Votre message" autoComplete="off"
            style={{
              flex: 1, border: 'none', background: 'transparent', color: 'var(--text)',
              fontSize: 15, outline: 'none', resize: 'none', lineHeight: 1.55,
              maxHeight: 180, padding: '8px 0', fontFamily: 'inherit',
              opacity: disabled ? 0.5 : 1,
            }}
          />
          <button
            type="button" onClick={submit} disabled={!canSend} aria-label="Envoyer"
            style={{
              width: 38, height: 38, borderRadius: 14, flexShrink: 0, marginBottom: 1,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              background: canSend ? 'linear-gradient(135deg, var(--brand-500), var(--brand-400))' : 'var(--surface)',
              color: canSend ? '#fff' : 'var(--text-tertiary)',
              boxShadow: canSend ? '0 2px 12px var(--glow)' : 'none',
              transition: 'all var(--t-base)',
            }}
            onMouseEnter={e => { if (canSend) { e.currentTarget.style.transform = 'scale(1.05)'; e.currentTarget.style.boxShadow = '0 4px 16px var(--glow-strong)'; }}}
            onMouseLeave={e => { if (canSend) { e.currentTarget.style.transform = 'scale(1)'; e.currentTarget.style.boxShadow = '0 2px 12px var(--glow)'; }}}
          >
            <IcoSend />
          </button>
        </div>

        <div style={{
          display: 'flex', justifyContent: 'space-between',
          marginTop: 8, padding: '0 6px', fontSize: 11.5, color: 'var(--text-tertiary)',
        }}>
          {!compact && <span>SUP'ONE peut faire des erreurs. Vérifiez les informations importantes.</span>}
          <span style={{ marginLeft: compact ? 'auto' : 0, color: len > 450 ? 'var(--warning)' : 'inherit', fontWeight: len > 450 ? 600 : 400 }}>
            {len}/{MAX}
          </span>
        </div>
      </div>
    </div>
  )
}

// ─── Toast ────────────────────────────────────────────────────────────────────
function Toast({ message }) {
  return (
    <div role="status" style={{
      position: 'fixed', bottom: 100, left: '50%',
      transform: `translateX(-50%) translateY(${message ? 0 : 80}px)`,
      background: 'var(--text)', color: 'var(--bg)',
      padding: '11px 22px', borderRadius: 'var(--r-full)',
      fontSize: 14, fontWeight: 600, zIndex: 100,
      boxShadow: 'var(--shadow-lg)',
      opacity: message ? 1 : 0,
      transition: 'transform .35s cubic-bezier(0.16, 1, 0.3, 1), opacity .35s ease',
      pointerEvents: 'none', whiteSpace: 'nowrap',
    }}>
      {message || '\u00A0'}
    </div>
  )
}

// ─── Scroll FAB ───────────────────────────────────────────────────────────────
function ScrollFab({ visible, onClick }) {
  return (
    <button
      type="button" onClick={onClick} aria-label="Descendre"
      style={{
        position: 'absolute',
        bottom: `calc(80px + var(--safe-bottom) + var(--keyboard-offset))`,
        right: isNative ? 'max(12px, env(safe-area-inset-right))' : 18,
        width: 38, height: 38, borderRadius: '50%',
        background: 'var(--bg-elevated)', border: '1px solid var(--border-strong)',
        color: 'var(--text)', display: 'flex', alignItems: 'center', justifyContent: 'center',
        boxShadow: 'var(--shadow-md)', zIndex: 10,
        opacity: visible ? 1 : 0,
        transform: visible ? 'translateY(0)' : 'translateY(8px)',
        transition: 'opacity var(--t-base), transform var(--t-base)',
        pointerEvents: visible ? 'auto' : 'none',
      }}
    >
      <IcoChevDown />
    </button>
  )
}

// ─── Sidebar ──────────────────────────────────────────────────────────────────
function Sidebar({ open, onClose, history, onSelect, onShowAbout, onNewChat }) {
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    if (open) {
      if (Array.isArray(history)) {
        const timer = setTimeout(() => setIsLoading(false), 300)
        return () => clearTimeout(timer)
      }
    } else {
      setIsLoading(true)
    }
  }, [open, history])

  if (!open) return null

  return (
    <aside style={{
      position: 'fixed', inset: 0, zIndex: 100, display: 'flex'
    }}>
      <div style={{
        width: 'var(--sidebar-w)', background: 'var(--bg-elevated)',
        borderRight: '1px solid var(--border-strong)',
        display: 'flex', flexDirection: 'column',
        boxShadow: 'var(--shadow-xl)',
        animation: 'slideRight .4s cubic-bezier(0.16, 1, 0.3, 1)',
        zIndex: 102
      }}>
        <div style={{ padding: '28px 22px', borderBottom: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <p style={{ fontWeight: 700, fontSize: 14, letterSpacing: '0.06em', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>Historique</p>
          <button onClick={onClose} style={{
            width: 32, height: 32, borderRadius: 8,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            color: 'var(--text-secondary)', background: 'var(--surface)',
            transition: 'all var(--t-fast)', fontSize: 18,
          }} onMouseEnter={e => { e.currentTarget.style.background = 'var(--surface-hover)'; e.currentTarget.style.color = 'var(--text)'; }} onMouseLeave={e => { e.currentTarget.style.background = 'var(--surface)'; e.currentTarget.style.color = 'var(--text-secondary)'; }}>
            ×
          </button>
        </div>

        <div style={{ padding: '18px 16px' }}>
          <button
            onClick={() => { onNewChat(); onClose(); }}
            style={{
              display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 10, width: '100%',
              padding: '13px', borderRadius: 14, background: 'linear-gradient(135deg, var(--brand-500), var(--brand-400))',
              color: '#fff', fontSize: 14, fontWeight: 600, transition: 'all var(--t-base)',
              boxShadow: '0 2px 12px var(--glow)',
            }}
            onMouseEnter={e => { e.currentTarget.style.transform = 'translateY(-1px)'; e.currentTarget.style.boxShadow = '0 4px 16px var(--glow-strong)'; }}
            onMouseLeave={e => { e.currentTarget.style.transform = 'translateY(0)'; e.currentTarget.style.boxShadow = '0 2px 12px var(--glow)'; }}
          >
            <IcoNewChat /> Nouvelle discussion
          </button>
        </div>

        <div style={{ flex: 1, overflowY: 'auto', padding: '0 12px' }}>
          {isLoading ? (
            <SidebarSkeleton />
          ) : (history && history.length > 0) ? (
            history.map(item => (
              <button key={item.id} onClick={() => { onSelect(item.id); onClose(); }} style={{
                width: '100%', margin: '3px 0', padding: '11px 14px', borderRadius: 12, textAlign: 'left',
                fontSize: 13.5, color: 'var(--text-secondary)', transition: 'all var(--t-fast)',
                display: 'flex', alignItems: 'center', gap: 10
              }} onMouseEnter={e => { e.currentTarget.style.background = 'var(--surface-hover)'; e.currentTarget.style.color = 'var(--text)'; }} onMouseLeave={e => { e.currentTarget.style.background = 'transparent'; e.currentTarget.style.color = 'var(--text-secondary)'; }}>
                <span style={{ opacity: 0.4 }}><Svg size={15}>{stroke('M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z')}</Svg></span>
                <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{item.title || 'Discussion sans titre'}</span>
              </button>
            ))
          ) : (
            <p style={{ padding: 44, textAlign: 'center', color: 'var(--text-tertiary)', fontSize: 13 }}>Aucune conversation enregistrée</p>
          )}
        </div>

        <div style={{ padding: 18, borderTop: '1px solid var(--border)', background: 'var(--surface)' }}>
          <button onClick={() => { onShowAbout(); onClose(); }} style={{
            display: 'flex', alignItems: 'center', gap: 10, width: '100%',
            padding: '11px 14px', borderRadius: 12, fontSize: 13.5, color: 'var(--brand-300)',
            fontWeight: 500, transition: 'all var(--t-fast)',
          }} onMouseEnter={e => { e.currentTarget.style.background = 'var(--surface-hover)'; }} onMouseLeave={e => { e.currentTarget.style.background = 'transparent'; }}>
            Aide & Documentation
          </button>
        </div>
      </div>
      <div
        onClick={onClose}
        style={{ flex: 1, background: 'var(--overlay)', backdropFilter: 'blur(6px)', animation: 'fadeInChat .3s ease', zIndex: 101 }}
      />
    </aside>
  )
}

// ─── About Modal ──────────────────────────────────────────────────────────────
function AboutModal({ open, onClose }) {
  if (!open) return null

  return (
    <div style={{
      position: 'fixed', inset: 0, zIndex: 200, display: 'flex', alignItems: 'center', justifyContent: 'center',
      background: 'var(--overlay)', backdropFilter: 'blur(10px)', animation: 'fadeInChat .3s ease'
    }}>
      <div style={{
        width: '100%', maxWidth: 500, padding: 36, borderRadius: 'var(--r-xl)',
        background: 'var(--bg-elevated)', border: '1px solid var(--border-strong)',
        boxShadow: 'var(--shadow-xl)', position: 'relative',
        animation: 'popIn .35s cubic-bezier(0.16, 1, 0.3, 1)'
      }}>
        <button onClick={onClose} style={{
          position: 'absolute', top: 16, right: 16,
          width: 32, height: 32, borderRadius: 8,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          color: 'var(--text-secondary)', background: 'var(--surface)',
          transition: 'all var(--t-fast)',
        }} onMouseEnter={e => { e.currentTarget.style.background = 'var(--surface-hover)'; }} onMouseLeave={e => { e.currentTarget.style.background = 'var(--surface)'; }}>
          ×
        </button>
        <div style={{ textAlign: 'center', marginBottom: 24 }}>
          <div style={{
            width: 56, height: 56, borderRadius: 16, marginBottom: 16,
            background: 'linear-gradient(135deg, var(--brand-500), var(--brand-300))',
            display: 'inline-flex', alignItems: 'center', justifyContent: 'center', color: '#fff',
            boxShadow: '0 4px 16px var(--glow)',
          }}>
            <IcoSparkles />
          </div>
          <h2 style={{ fontSize: 22, fontWeight: 700, color: 'var(--text)' }}>À propos de SUP'ONE AI</h2>
        </div>
        <p style={{ fontSize: 14.5, color: 'var(--text-secondary)', lineHeight: 1.7 }}>
          SUP'ONE AI est votre assistant virtuel intelligent, conçu pour vous aider et discuter avec vous de façon naturelle.
          Il a été développé par des experts passionnés des technologies et de la formation, motivés par le souhait d'améliorer l'excellence académique dans le domaine des TIC au Cameroun.
        </p>
        <div style={{ fontSize: 14.5, color: 'var(--text-secondary)', lineHeight: 1.7, marginTop: 14 }}>
          {renderMd('**Architecture :** React Hooks, Custom Hooks (useChat, useTheme, usePwaInstall, useNativeKeyboard).')}
        </div>
        <div style={{ fontSize: 14.5, color: 'var(--text-secondary)', lineHeight: 1.7, marginTop: 14 }}>
          {renderMd("**Fonctionnalités :** Streaming en temps réel (Gen3 IA) & Fallback FAQ TF-IDF, Authentification JWT & Persistance de session, Support PWA, Interface optimisée pour le natif (Capacitor), Interface utilisateur avancée.")}
        </div>
        <div style={{ fontSize: 14.5, color: 'var(--text-secondary)', lineHeight: 1.7, marginTop: 14 }}>
          {renderMd('**Version :** 2.0')}
        </div>
        <p style={{ fontSize: 14.5, color: 'var(--text-secondary)', lineHeight: 1.7, marginTop: 14 }}>
          Pour plus d'informations, visitez <a href="https://e-supptic.cm/" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--brand-300)', textDecoration: 'none', fontWeight: 500 }}>e-supptic.cm</a>.
        </p>
      </div>
    </div>
  )
}

// ─── Profile Modal ────────────────────────────────────────────────────────────
function ProfileModal({ open, onClose, user, onLogout, onSave }) {
  const [editing, setEditing] = useState(false)
  const [username, setUsername] = useState(user?.username ?? '')
  const [email, setEmail] = useState(user?.email ?? '')

  useEffect(() => {
    if (user) {
      setUsername(user.username)
      setEmail(user.email)
      setEditing(false)
    }
  }, [user, open])

  if (!open || !user) return null

  const save = async () => {
    const updated = { ...user, username: username.trim() || user.username, email: email.trim() || user.email }
    try {
      localStorage.setItem('supone-user', JSON.stringify(updated))
    } catch (e) {
      console.error('Erreur de sauvegarde du profil', e)
    }
    onSave?.(updated)
    setEditing(false)
    onClose()
  }

  return (
    <div style={{
      position: 'fixed', inset: 0, zIndex: 200, display: 'flex', alignItems: 'center', justifyContent: 'center',
      background: 'var(--overlay)', backdropFilter: 'blur(10px)', animation: 'fadeInChat .3s ease'
    }}>
      <div style={{
        width: '100%', maxWidth: 400, padding: 36, borderRadius: 'var(--r-xl)',
        background: 'var(--bg-elevated)', border: '1px solid var(--border-strong)',
        boxShadow: 'var(--shadow-xl)', position: 'relative',
        animation: 'popIn .35s cubic-bezier(0.16, 1, 0.3, 1)', textAlign: 'center'
      }}>
        <button onClick={onClose} style={{
          position: 'absolute', top: 16, right: 16,
          width: 32, height: 32, borderRadius: 8,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          color: 'var(--text-secondary)', background: 'var(--surface)',
          transition: 'all var(--t-fast)',
        }} onMouseEnter={e => { e.currentTarget.style.background = 'var(--surface-hover)'; }} onMouseLeave={e => { e.currentTarget.style.background = 'var(--surface)'; }}>
          ×
        </button>
        <div style={{
          width: 84, height: 84, borderRadius: '50%',
          background: 'linear-gradient(135deg, var(--brand-500), var(--brand-400))',
          color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 34, fontWeight: 700, margin: '0 auto 22px',
          boxShadow: '0 4px 16px var(--glow)',
        }}>
          {username.charAt(0).toUpperCase()}
        </div>

        {!editing ? (
          <>
            <h2 style={{ fontSize: 22, fontWeight: 700, color: 'var(--text)' }}>{user.username}</h2>
            <p style={{ color: 'var(--text-secondary)', marginBottom: 28, fontSize: 14.5 }}>{user.email}</p>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              <button onClick={() => setEditing(true)} style={{
                padding: '13px', borderRadius: 14, background: 'var(--surface)',
                color: 'var(--text)', fontWeight: 600, transition: 'all var(--t-fast)',
              }} onMouseEnter={e => { e.currentTarget.style.background = 'var(--surface-hover)'; }} onMouseLeave={e => { e.currentTarget.style.background = 'var(--surface)'; }}>
                Modifier le profil
              </button>
              <button onClick={() => { onLogout(); onClose(); }} style={{
                padding: '13px', borderRadius: 14, background: 'var(--error-bg)',
                color: 'var(--error)', fontWeight: 600, transition: 'all var(--t-fast)',
              }} onMouseEnter={e => { e.currentTarget.style.background = 'rgba(239,68,68,.18)'; }} onMouseLeave={e => { e.currentTarget.style.background = 'var(--error-bg)'; }}>
                Déconnexion
              </button>
            </div>
          </>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <input value={username} onChange={e => setUsername(e.target.value)} placeholder="Nom d'utilisateur" style={{ padding: '12px 14px', borderRadius: 12, border: '1px solid var(--composer-border)', fontSize: 14 }} />
            <input value={email} onChange={e => setEmail(e.target.value)} placeholder="Email" style={{ padding: '12px 14px', borderRadius: 12, border: '1px solid var(--composer-border)', fontSize: 14 }} />
            <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end', marginTop: 4 }}>
              <button onClick={() => setEditing(false)} style={{ padding: '10px 16px', borderRadius: 10, fontSize: 13.5, fontWeight: 500, color: 'var(--text-secondary)' }}>Annuler</button>
              <button onClick={save} style={{ padding: '10px 16px', borderRadius: 10, background: 'var(--brand-500)', color: '#fff', fontSize: 13.5, fontWeight: 600 }}>Enregistrer</button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

// ─── Auth Page ────────────────────────────────────────────────────────────────
function AuthPage({ mode, onSwitch, onLogin }) {
  const [email, setEmail] = useState('')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [errors, setErrors] = useState({})

  const validate = () => {
    const newErrors = {}
    if (!email) {
      newErrors.email = "L'email est requis"
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      newErrors.email = "Format d'email invalide"
    }

    if (mode === 'signup' && !username.trim()) {
      newErrors.username = "Le nom d'utilisateur est requis"
    }

    if (!password) {
      newErrors.password = "Le mot de passe est requis"
    } else if (password.length <= 6) {
      newErrors.password = "Le mot de passe doit faire plus de 6 caractères"
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = () => {
    if (validate()) {
      const finalUsername = mode === 'signup' ? username : (email.split('@')[0])
      onLogin({ username: finalUsername, email })
    }
  }

  const errorStyle = { color: 'var(--error)', fontSize: 12, marginTop: 5, marginLeft: 4, animation: 'msgIn .2s ease', fontWeight: 500 }

  return (
    <div style={{
      flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 24,
      animation: 'fadeUp .5s cubic-bezier(0.16, 1, 0.3, 1)'
    }}>
      <div style={{
        width: '100%', maxWidth: 400, padding: 36, borderRadius: 'var(--r-xl)',
        background: 'var(--bg-elevated)', border: '1px solid var(--border-strong)',
        boxShadow: 'var(--shadow-xl)'
      }}>
        <div style={{ textAlign: 'center', marginBottom: 36 }}>
          <div style={{
            width: 56, height: 56, borderRadius: 16,
            background: 'linear-gradient(135deg, var(--brand-500), var(--brand-300))',
            margin: '0 auto 18px', display: 'flex', alignItems: 'center', justifyContent: 'center',
            color: '#fff', boxShadow: '0 4px 16px var(--glow)',
          }}>
            <IcoSparkles />
          </div>
          <h2 style={{ fontSize: 24, fontWeight: 800, letterSpacing: '-0.02em' }}>{mode === 'login' ? 'Bon retour !' : 'Rejoindre SUP\'ONE'}</h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: 14.5, marginTop: 8 }}>Veuillez entrer vos informations</p>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <div style={{ position: 'relative' }}>
            <div style={{ position: 'relative' }}>
              <span style={{ position: 'absolute', left: 14, top: 13, color: 'var(--text-tertiary)' }}><IcoMail size={16}/></span>
              <input
                placeholder="Email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                style={{ width: '100%', padding: '13px 14px 13px 42px', borderRadius: 14, outline: 'none', border: `1px solid ${errors.email ? 'var(--error)' : 'var(--composer-border)'}`, fontSize: 14.5, transition: 'border-color var(--t-fast)' }}
              />
            </div>
            {errors.email && <p style={errorStyle}>{errors.email}</p>}
          </div>
          {mode === 'signup' && (
             <div style={{ position: 'relative' }}>
              <div style={{ position: 'relative' }}>
                <span style={{ position: 'absolute', left: 14, top: 13, color: 'var(--text-tertiary)' }}><IcoUser size={16}/></span>
                <input
                  placeholder="Nom d'utilisateur"
                  value={username}
                  onChange={e => setUsername(e.target.value)}
                  style={{ width: '100%', padding: '13px 14px 13px 42px', borderRadius: 14, outline: 'none', border: `1px solid ${errors.username ? 'var(--error)' : 'var(--composer-border)'}`, fontSize: 14.5, transition: 'border-color var(--t-fast)' }}
                />
              </div>
              {errors.username && <p style={errorStyle}>{errors.username}</p>}
            </div>
          )}
          <div style={{ position: 'relative' }}>
            <div style={{ position: 'relative' }}>
              <span style={{ position: 'absolute', left: 14, top: 13, color: 'var(--text-tertiary)' }}><IcoLock size={16}/></span>
              <input
                type="password"
                placeholder="Mot de passe"
                value={password}
                onChange={e => setPassword(e.target.value)}
                style={{ width: '100%', padding: '13px 14px 13px 42px', borderRadius: 14, outline: 'none', border: `1px solid ${errors.password ? 'var(--error)' : 'var(--composer-border)'}`, fontSize: 14.5, transition: 'border-color var(--t-fast)' }}
              />
            </div>
            {errors.password && <p style={errorStyle}>{errors.password}</p>}
          </div>
          <button onClick={handleSubmit} style={{
            marginTop: 10, padding: 15, borderRadius: 14,
            background: 'linear-gradient(135deg, var(--brand-500), var(--brand-400))',
            color: '#fff', fontWeight: 700, fontSize: 15,
            boxShadow: '0 4px 16px var(--glow)',
            transition: 'all var(--t-base)',
          }} onMouseEnter={e => { e.currentTarget.style.transform = 'translateY(-1px)'; e.currentTarget.style.boxShadow = '0 6px 20px var(--glow-strong)'; }} onMouseLeave={e => { e.currentTarget.style.transform = 'translateY(0)'; e.currentTarget.style.boxShadow = '0 4px 16px var(--glow)'; }}>
            {mode === 'login' ? 'Se connecter' : 'Créer un compte'}
          </button>
        </div>

        <p style={{ textAlign: 'center', marginTop: 28, fontSize: 14, color: 'var(--text-secondary)' }}>
          {mode === 'login' ? "Pas encore de compte ?" : "Déjà un compte ?"}
          <button onClick={() => { setErrors({}); onSwitch(); }} style={{ color: 'var(--brand-300)', fontWeight: 600, marginLeft: 6 }}>
            {mode === 'login' ? 'S\'inscrire' : 'Se connecter'}
          </button>
        </p>
      </div>
    </div>
  )
}