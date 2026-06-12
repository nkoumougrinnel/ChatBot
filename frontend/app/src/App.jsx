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
 * - JWT Authentication & Session Persistence
 * - PWA Support (Install Banners)
 * - Native-optimized (Capacitor) UI with Safe Area management
 * - Advanced UI: Skeleton screens, micro-animations, glassmorphism
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
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  :root {
    --brand-500: #2355a0;
    --brand-400: #3b6fd4;
    --brand-300: #60a5fa;
    --success:   #22c55e;
    --success-bg: rgba(34,197,94,.08);
    --warning:   #f59e0b;
    --warning-bg: rgba(245,158,11,.12);
    --error:     #ef4444;
    --error-bg:  rgba(239,68,68,.12);
    --r-sm: 8px; --r-md: 12px; --r-lg: 16px; --r-full: 9999px;
    --thread-max: 720px;
    --font: 'Inter', system-ui, -apple-system, sans-serif;
    --t-fast: 120ms ease;
    --t-base: 200ms ease;
    --safe-bottom: env(safe-area-inset-bottom, 0px);
    --sidebar-w: 280px;
    --safe-top: env(safe-area-inset-top, 0px);
    --keyboard-offset: 0px;
  }

  :root, [data-theme="dark"] {
    --bg:             #0b1220;
    --bg-elevated:    #0f1d35;
    --header-bg:      rgba(11,18,32,.92);
    --surface:        rgba(255,255,255,.05);
    --surface-hover:  rgba(255,255,255,.07);
    --border:         rgba(255,255,255,.08);
    --border-strong:  rgba(255,255,255,.14);
    --text:           #edf2f7;
    --text-secondary: rgba(237,242,247,.65);
    --text-tertiary:  rgba(237,242,247,.35);
    --user-bubble:    linear-gradient(135deg, var(--brand-500), var(--brand-400));
    --composer-bg:    rgba(255,255,255,.05);
    --composer-border: rgba(255,255,255,.1);
    --chip-bg:        rgba(255,255,255,.05);
    --chip-border:    rgba(255,255,255,.1);
    --chip-hover:     rgba(255,255,255,.09);
    --scrollbar:      rgba(255,255,255,.12);
    --glow:           rgba(59,111,212,.4);
  }

  [data-theme="light"] {
    --bg:             #f0f4fa;
    --bg-elevated:    #ffffff;
    --header-bg:      rgba(255,255,255,.95);
    --surface:        rgba(26,58,107,.04);
    --surface-hover:  rgba(26,58,107,.07);
    --border:         rgba(0,0,0,.07);
    --border-strong:  rgba(0,0,0,.12);
    --text:           #0f172a;
    --text-secondary: #475569;
    --text-tertiary:  #94a3b8;
    --user-bubble:    var(--brand-500);
    --composer-bg:    #ffffff;
    --composer-border: #d1d9e6;
    --chip-bg:        #ffffff;
    --chip-border:    #e2e8f0;
    --chip-hover:     #f1f5f9;
    --scrollbar:      rgba(0,0,0,.12);
    --glow:           rgba(59,111,212,.2);
  }

  html, body, #root { width:100%; height:100%; height:100dvh; font-family:var(--font); }
  body {
    background: var(--bg); color: var(--text); line-height: 1.6;
    -webkit-font-smoothing: antialiased; overflow: hidden;
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
  @keyframes fadeUp   { from{opacity:0;transform:translateY(12px)} to{opacity:1;transform:translateY(0)} }
  @keyframes msgIn    { from{opacity:0;transform:translateY(5px)}  to{opacity:1;transform:translateY(0)} }
  @keyframes chipIn   { from{opacity:0;transform:translateY(6px)}  to{opacity:1;transform:translateY(0)} }
  @keyframes slideDown{ from{opacity:0;transform:translateY(-5px)} to{opacity:1;transform:translateY(0)} }
  @keyframes pulse    { 0%,100%{opacity:1} 50%{opacity:.4} }
  @keyframes spin     { to{transform:rotate(360deg)} }
  @keyframes blink    { 50%{opacity:0} }
  @keyframes glowPulse{
    0%,100%{box-shadow:0 0 0 8px var(--glow),0 8px 32px var(--glow);transform:scale(1)}
    50%    {box-shadow:0 0 0 14px transparent,0 8px 32px var(--glow);transform:scale(1.02)}
  }
  @keyframes typingBounce{
    0%,80%,100%{transform:scale(.7);opacity:.4}
    40%{transform:scale(1);opacity:1}
  }
  @keyframes fadeInChat { from{opacity:0;transform:scale(0.99) translateY(8px)} to{opacity:1;transform:scale(1) translateY(0)} }
  @keyframes slideRight { from{opacity:0;transform:translateX(-20px)} to{opacity:1;transform:translateX(0)} }
  @keyframes popIn     { from{opacity:0;transform:scale(0.95) translateY(-10px)} to{opacity:1;transform:scale(1) translateY(0)} }
  @keyframes skeletonPulse { 0%,100%{opacity:.5} 50%{opacity:.2} }
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
const IcoUser      = () => <Svg size={20}><circle cx="12" cy="7" r="4" stroke="currentColor" strokeWidth="2"/>{stroke('M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2')}</Svg>
const IcoLogOut    = () => <Svg size={18}>{stroke('M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9')}</Svg>
const IcoMail      = () => <Svg size={18}>{stroke('M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2zM22 6l-10 7L2 6')}</Svg>
const IcoLock      = () => <Svg size={18}><rect x="3" y="11" width="18" height="11" rx="2" ry="2" stroke="currentColor" strokeWidth="2"/>{stroke('M7 11V7a5 5 0 0 1 10 0v4')}</Svg>
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
      display: 'inline-block', width: 7, height: 7, borderRadius: '50%', flexShrink: 0,
      background: colors[status] ?? 'var(--text-tertiary)',
      animation: status === 'checking' ? 'pulse 1.2s ease infinite' : 'none',
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
      display: 'flex', alignItems: 'center', gap: 8, height: isNative ? 48 : 56,
      padding: `0 16px`, paddingTop: `var(--safe-top)`,
      background: 'var(--header-bg)', backdropFilter: 'blur(12px)',
      borderBottom: '1px solid var(--border)', flexShrink: 0, zIndex: 10,
    }}>
      {user && (
        <HdrBtn onClick={onToggleSidebar} label="Historique">
          <IcoHistory />
        </HdrBtn>
      )}

      {/* Brand */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, flex: 1, minWidth: 0 }}>
        <div style={{ position: 'relative', flexShrink: 0, display: isNative ? 'none' : 'block' }}>
          <div style={{
            width: 34, height: 34, borderRadius: 10,
            background: 'linear-gradient(135deg, var(--brand-500), var(--brand-300))',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            color: '#fff', boxShadow: '0 2px 8px var(--glow)',
          }}>
            <IcoSparkles />
          </div>
          <span style={{
            position: 'absolute', bottom: -1, right: -1,
            width: 10, height: 10, borderRadius: '50%',
            border: '2px solid var(--bg)',
            background: { online: 'var(--success)', degraded: 'var(--warning)', offline: 'var(--error)', checking: 'var(--text-tertiary)' }[serverStatus],
            animation: serverStatus === 'checking' ? 'pulse 1.2s ease infinite' : 'none',
          }} />
        </div>
        <div style={{ minWidth: 0 }}>
          <p style={{ fontSize: 14, fontWeight: 600, letterSpacing: '-0.01em', color: 'var(--text)', lineHeight: 1.2 }}>
            SUP'ONE AI
          </p>
          <p style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: 11.5, color: 'var(--text-secondary)', marginTop: 1 }}>
            {serverStatus !== 'online' && <StatusDot status={serverStatus} />}
            {subtitle}
          </p>
        </div>
      </div>

      {/* Actions */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 2 }}>
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
  const [showDropdown, setShowDropdown] = useState(false);
  const buttonRef = useRef(null);

  const handleToggleDropdown = (e) => {
    e.stopPropagation(); // Empêche le clic de se propager au document immédiatement
    setShowDropdown(prev => !prev);
  };

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (buttonRef.current && !buttonRef.current.contains(event.target)) {
        setShowDropdown(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  return (
    <div style={{ position: 'relative', display: 'inline-block' }} ref={buttonRef}>
      <button
        type="button" onClick={handleToggleDropdown}
        aria-label={user.username} title={user.username}
        style={{
          width: isNative ? 44 : 34, height: isNative ? 44 : 34,
          borderRadius: '50%',
          minWidth: isNative ? 44 : 'auto',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          color: '#fff',
          background: 'var(--brand-500)',
          transition: 'all var(--t-base)',
        }}
        onMouseEnter={e => { e.currentTarget.style.background = 'var(--brand-400)'; }}
        onMouseLeave={e => { e.currentTarget.style.background = 'var(--brand-500)'; }}
      >
        <span style={{ fontSize: 14, fontWeight: 600, lineHeight: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', width: '100%', height: '100%' }}>
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
  );
}

function UserDropdown({ onClose, onProfileClick, onLogout }) {
  return (
    <div style={{
      position: 'absolute',
      top: 'calc(100% + 8px)', // Positionne le menu déroulant sous le bouton
      right: 0,
      background: 'var(--bg-elevated)',
      border: '1px solid var(--border-strong)',
      borderRadius: 'var(--r-md)',
      boxShadow: '0 4px 12px rgba(0,0,0,.2)',
      minWidth: 160,
      zIndex: 60, // Assure que le menu est au-dessus des autres éléments
      animation: 'popIn .25s cubic-bezier(0.16, 1, 0.3, 1)',
      padding: '8px 0',
    }}>
      <button onClick={() => { onProfileClick(); onClose(); }} style={{
        width: '100%', textAlign: 'left', padding: '10px 16px',
        fontSize: 14, color: 'var(--text)',
        background: 'transparent', border: 'none',
      }} onMouseEnter={e => e.currentTarget.style.background = 'var(--surface-hover)'} onMouseLeave={e => e.currentTarget.style.background = 'transparent'}>
        Mon profil
      </button>
      <button onClick={() => { onLogout(); onClose(); }} style={{
        width: '100%', textAlign: 'left', padding: '10px 16px',
        fontSize: 14, color: 'var(--text)',
        background: 'transparent', border: 'none',
      }} onMouseEnter={e => e.currentTarget.style.background = 'var(--surface-hover)'} onMouseLeave={e => e.currentTarget.style.background = 'transparent'}>
        Déconnexion
      </button>
    </div>
  );
}

// ─── Skeletons ────────────────────────────────────────────────────────────────
function SidebarSkeleton() {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12, padding: '10px 14px' }}>
      {[1, 2, 3, 4, 5].map(i => (
        <div key={i} style={{
          height: 38, width: '100%', borderRadius: 10,
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
      gap: 20, animation: 'fadeUp .4s ease'
    }}>
      <div style={{
        width: 42, height: 42, border: '3.5px solid var(--border-strong)',
        borderTopColor: 'var(--brand-500)', borderRadius: '50%',
        animation: 'spin .8s linear infinite'
      }} />
      <p style={{ fontSize: 14, color: 'var(--text-secondary)', fontWeight: 500, letterSpacing: '0.02em', textTransform: 'uppercase' }}>
        Sécurisation de la connexion…
      </p>
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
  const [isAuthenticating, setIsAuthenticating] = useState(false)

  // Persistance : Charger l'utilisateur au démarrage
  useEffect(() => {
    const savedUser  = localStorage.getItem('supone-user')
    const savedToken = localStorage.getItem('supone-token')

    if (savedUser && savedToken) {
      setIsAuthenticating(true)
      // Simulation d'une vérification de validité du Token (Refresh Token)
      setTimeout(() => {
        try {
          setUser(JSON.parse(savedUser))
          chat.showToastMsg("Session restaurée avec succès")
        } catch (e) {
          handleLogout()
        } finally {
          setIsAuthenticating(false)
        }
      }, 1000)
    }
  }, [chat])

  useNativeKeyboard()

  const handleLogin = (userData) => {
    setIsAuthenticating(true)
    // Simulation d'une latence réseau pour un effet pro
    setTimeout(() => {
      setUser(userData)
      localStorage.setItem('supone-token', 'sk_live_' + Math.random().toString(36).substr(2))
      localStorage.setItem('supone-user', JSON.stringify(userData))
      setAuthView(null)
      setIsAuthenticating(false)
      chat.showToastMsg(`Bonjour ${userData.username} !`)
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
    chat.showToastMsg("Fonctionnalité 'Mon profil' à venir !");
  };

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
            ? 'radial-gradient(ellipse 60% 40% at 50% 0%, rgba(35,85,160,.18) 0%, transparent 70%)'
            : 'radial-gradient(ellipse 60% 40% at 50% 0%, rgba(59,111,212,.07) 0%, transparent 70%)',
        }} />

        {/* Shell principal */}
        <div style={{ position: 'relative', zIndex: 1, flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column' }}>

          <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} history={chat.history} onSelect={chat.loadThread} />

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
        width: isNative ? 44 : 34, height: isNative ? 44 : 34, borderRadius: 8, minWidth: isNative ? 44 : 'auto',
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
      margin: '8px auto 0', padding: '12px 14px',
      maxWidth: 'var(--thread-max)', width: 'calc(100% - 32px)',
      background: 'var(--bg-elevated)', border: '1px solid var(--border-strong)',
      borderRadius: 'var(--r-lg)', position: 'relative', animation: 'slideDown .3s ease',
    }}>
      <button
        type="button" onClick={onDismiss} aria-label="Fermer"
        style={{ position: 'absolute', top: 6, right: 8, width: 24, height: 24, fontSize: '1.1rem', color: 'var(--text-secondary)' }}
      >×</button>
      <div style={{
        width: 44, height: 44, borderRadius: 10, flexShrink: 0,
        background: 'linear-gradient(135deg, var(--brand-500), var(--brand-300))',
        display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff',
      }}>
        <IcoSparkles />
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <p style={{ fontSize: 13.5, fontWeight: 600 }}>Installer SUP'ONE AI</p>
        <p style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 2 }}>Accès rapide depuis votre écran d'accueil</p>
      </div>
      <button
        type="button" onClick={onInstall}
        style={{ padding: '7px 13px', background: 'var(--brand-500)', color: '#fff', borderRadius: 'var(--r-full)', fontSize: 12.5, fontWeight: 600, display: 'flex', alignItems: 'center', gap: 5, flexShrink: 0 }}
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
      margin: '8px auto 0', padding: '10px 14px',
      maxWidth: 'var(--thread-max)', width: 'calc(100% - 32px)',
      background: 'var(--error-bg)', border: '1px solid rgba(239,68,68,.25)',
      borderRadius: 'var(--r-lg)', animation: 'slideDown .3s ease',
    }}>
      <IcoWifiOff />
      <div style={{ flex: 1 }}>
        <p style={{ fontSize: 13, fontWeight: 600 }}>Serveur inaccessible</p>
        <p style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 2 }}>Vérifiez votre connexion internet</p>
      </div>
      <button
        type="button" onClick={onRetry} disabled={retrying}
        style={{ padding: '6px 12px', borderRadius: 'var(--r-sm)', background: 'var(--error)', color: '#fff', fontSize: 12, fontWeight: 600, display: 'flex', alignItems: 'center', gap: 5, opacity: retrying ? 0.6 : 1 }}
      >
        <IcoRefresh /> {retrying ? '…' : 'Réessayer'}
      </button>
    </div>
  )
}

function DegradedBanner() {
  return (
    <div role="status" style={{
      padding: '7px 16px', textAlign: 'center', fontSize: 12,
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
  const [showAboutModal, setShowAboutModal] = useState(false)

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
      justifyContent: 'center', padding: '40px 16px 24px', textAlign: 'center',
      animation: 'fadeUp .6s cubic-bezier(0.16, 1, 0.3, 1)',
    }}>
      <div style={{
        width: 64, height: 64, borderRadius: 18, marginBottom: 24,
        background: 'linear-gradient(135deg, var(--brand-500) 0%, var(--brand-300) 100%)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        color: '#fff',
        boxShadow: '0 0 0 8px var(--glow), 0 8px 32px var(--glow)',
        animation: 'glowPulse 3s ease-in-out infinite',
      }}>
        <IcoSparkles />
      </div>

      <h1 style={{
        fontSize: 'clamp(22px, 4vw, 28px)', fontWeight: 700,
        letterSpacing: '-0.03em', color: 'var(--text)', lineHeight: 1.2,
      }}>
        {greeting}
      </h1>
      <p style={{ fontSize: 14.5, color: 'var(--text-secondary)', lineHeight: 1.6, marginTop: 10, maxWidth: 420 }}>
        Assistant officiel SUP'PTIC — posez vos questions sur l'école,
        les inscriptions, les examens et les services étudiants.
      </p>

      {/* Suggestion cards en grille */}
      {suggestions?.length > 0 && (
        <div style={{
          display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(175px, 1fr))',
          gap: 8, marginTop: 32, width: '100%', maxWidth: 560,
        }}>
          {suggestions.map((text, i) => (
            <button
              key={text} type="button" disabled={disabled} onClick={() => onSelect(text)}
              style={{
                padding: '12px 14px', textAlign: 'left',
                background: 'var(--chip-bg)', border: '1px solid var(--chip-border)',
                borderRadius: 'var(--r-lg)', color: 'var(--text)',
                fontSize: 13, lineHeight: 1.4,
                opacity: disabled ? 0.5 : 1, cursor: disabled ? 'not-allowed' : 'pointer',
                transition: 'background var(--t-base), border-color var(--t-base)',
                animation: `chipIn .35s ease ${i * 55}ms backwards`,
              }}
              onMouseEnter={e => { if (!disabled) { e.currentTarget.style.background = 'var(--chip-hover)'; e.currentTarget.style.borderColor = 'var(--brand-300)'; }}}
              onMouseLeave={e => { e.currentTarget.style.background = 'var(--chip-bg)'; e.currentTarget.style.borderColor = 'var(--chip-border)'; }}
            >
              <span style={{ fontSize: 15, display: 'block', marginBottom: 4 }}>💬</span>
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
      <span style={{ display: 'flex', gap: 4 }}>
        {[0, 1, 2].map(i => (
          <span key={i} style={{
            width: 6, height: 6, borderRadius: '50%', display: 'inline-block',
            background: 'var(--brand-300)',
            animation: `typingBounce 1.1s ${i * 0.15}s ease-in-out infinite`,
          }} />
        ))}
      </span>
      <span>{label || 'Réflexion…'}</span>
    </div>
  )
}

// ─── Avatar bot ───────────────────────────────────────────────────────────────
function BotAvatar({ error }) {
  return (
    <div style={{
      width: 30, height: 30, borderRadius: 9, flexShrink: 0, marginTop: 2,
      background: error ? 'var(--error-bg)' : 'linear-gradient(135deg, var(--brand-500), var(--brand-300))',
      border: `1px solid ${error ? 'rgba(239,68,68,.25)' : 'transparent'}`,
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      color: error ? 'var(--error)' : '#fff',
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
    <div style={{ marginTop: 10 }}>
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
          marginTop: 8, padding: '12px 14px',
          background: 'var(--surface)', border: '1px solid var(--border)',
          borderRadius: 'var(--r-lg)', animation: 'fadeUp .2s ease',
        }}>
          <p style={{ fontSize: 12.5, color: 'var(--text-secondary)', marginBottom: 8 }}>
            Qu'est-ce qui pourrait être amélioré ? <em style={{ opacity: .7 }}>(optionnel)</em>
          </p>
          <textarea
            value={comment} onChange={e => setComment(e.target.value)}
            placeholder="Décrivez le problème…" rows={2} maxLength={500}
            style={{
              width: '100%', padding: '8px 10px', borderRadius: 'var(--r-md)',
              border: '1px solid var(--composer-border)', background: 'var(--composer-bg)',
              color: 'var(--text)', fontSize: 13, resize: 'vertical', fontFamily: 'inherit', outline: 'none',
            }}
          />
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 6, marginTop: 8 }}>
            <button type="button" onClick={() => setShowForm(false)}
              style={{ fontSize: 13, color: 'var(--text-secondary)', padding: '5px 10px', borderRadius: 'var(--r-sm)' }}>
              Annuler
            </button>
            <button type="button" onClick={() => send('negatif', comment.trim())} disabled={submitting}
              style={{ fontSize: 13, fontWeight: 600, color: '#fff', background: 'var(--brand-500)', padding: '5px 14px', borderRadius: 'var(--r-sm)' }}>
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
        display: 'inline-flex', alignItems: 'center', gap: 6, padding: '6px 12px', borderRadius: 8,
        fontSize: 12.5, fontWeight: 500,
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
        animation: 'msgIn .2s ease',
      }}>
        <div style={{
          background: 'var(--user-bubble)', color: '#fff',
          padding: '10px 16px', borderRadius: '18px 18px 4px 18px',
          fontSize: 15, lineHeight: 1.6, maxWidth: '100%',
          boxShadow: '0 4px 12px rgba(35,85,160,.2)',
        }}>
          {renderMd(message.content)}
        </div>
      </div>
    )
  }

  // Erreur
  if (message.status === 'error') {
    return (
      <div style={{ display: 'flex', gap: 10, animation: 'msgIn .2s ease' }}>
        <BotAvatar error />
        <div style={{
          background: 'var(--error-bg)', border: '1px solid rgba(239,68,68,.2)',
          borderRadius: '4px 18px 18px 18px', padding: '12px 16px', flex: 1,
        }}>
          <p style={{ fontSize: 12, fontWeight: 600, color: 'var(--error)', marginBottom: 4 }}>Connexion impossible</p>
          <p style={{ fontSize: 14, color: 'var(--text-secondary)', lineHeight: 1.55 }}>{message.content}</p>
        </div>
      </div>
    )
  }

  const loading   = message.status === 'loading'
  const streaming = message.status === 'streaming'
  const done      = message.status === 'done'

  return (
    <div style={{ display: 'flex', gap: 10, alignItems: 'flex-start', animation: 'msgIn .2s ease' }}>
      <BotAvatar />
      <div style={{ flex: 1, minWidth: 0, paddingTop: 4 }}>
        <div style={{ fontSize: 14.5, color: 'var(--text)', lineHeight: 1.65 }}>
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
              marginTop: 14, padding: '16px',
              background: 'var(--warning-bg)', borderRadius: 'var(--r-md)', 
              border: '1px solid rgba(245,158,11,.2)',
              fontSize: 13.5, color: 'var(--text-secondary)',
              animation: 'popIn .3s ease'
            }}>
              <p style={{ fontWeight: 700, color: 'var(--warning)', marginBottom: 8, fontSize: 12, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                <span style={{ marginRight: 6 }}>💡</span> Pistes de solution
              </p>
              <ul style={{ paddingLeft: 18, lineHeight: 1.8, listStyleType: 'circle' }}>
                <li>Précisez votre demande (ex: "frais d'inscription ITT")</li>
                <li>Reformulez votre question avec d'autres mots</li>
                <li>Contactez l'assistance : <a href="mailto:support@e-supptic.cm" style={{ color: 'var(--brand-300)', textDecoration: 'none' }}>support@e-supptic.cm</a></li>
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
          <div style={{ display: 'flex', alignItems: 'center', marginTop: 6 }}>
            <button
              type="button" onClick={handleCopy} aria-label="Copier la réponse"
              style={{
                display: 'inline-flex', alignItems: 'center', gap: 4, padding: '4px 8px',
                borderRadius: 7, fontSize: 12.5, fontWeight: 500,
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
      <div style={{ maxWidth: 'var(--thread-max)', margin: '0 auto', padding: compact ? '8px 12px' : '10px 16px 14px' }}>
        <div
          style={{
            display: 'flex', alignItems: 'flex-end', gap: 6,
            background: 'var(--composer-bg)', border: `1px solid ${len > 0 ? 'var(--brand-400)' : 'var(--composer-border)'}`,
            borderRadius: 24, padding: '6px 6px 6px 16px',
            boxShadow: len > 0 ? '0 4px 20px rgba(0,0,0,.2)' : '0 2px 8px rgba(0,0,0,.1)',
            backdropFilter: 'blur(8px)',
            transition: 'border-color var(--t-base), box-shadow var(--t-base)',
          }}
          onFocusCapture={e => { e.currentTarget.style.borderColor = 'var(--brand-300)'; e.currentTarget.style.boxShadow = '0 2px 16px rgba(0,0,0,.15), 0 0 0 3px var(--glow)'; }}
          onBlurCapture={e => { e.currentTarget.style.borderColor = 'var(--composer-border)'; e.currentTarget.style.boxShadow = '0 2px 16px rgba(0,0,0,.15), 0 0 0 1px var(--border)'; }}
        >
          <textarea
            ref={ref} value={value}
            onChange={e => { setValue(e.target.value.slice(0, MAX)); autoResize() }}
            onKeyDown={onKey}
            placeholder="Posez votre question…"
            disabled={disabled} rows={1} aria-label="Votre message" autoComplete="off"
            style={{
              flex: 1, border: 'none', background: 'transparent', color: 'var(--text)',
              fontSize: 15, outline: 'none', resize: 'none', lineHeight: 1.5,
              maxHeight: 180, padding: '8px 0', fontFamily: 'inherit',
              opacity: disabled ? 0.5 : 1,
            }}
          />
          <button
            type="button" onClick={submit} disabled={!canSend} aria-label="Envoyer"
            style={{
              width: 36, height: 36, borderRadius: 14, flexShrink: 0, marginBottom: 1,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              background: canSend ? 'var(--brand-500)' : 'var(--surface)',
              color: canSend ? '#fff' : 'var(--text-tertiary)',
              transition: 'background var(--t-base), color var(--t-fast)',
            }}
            onMouseEnter={e => { if (canSend) e.currentTarget.style.background = 'var(--brand-400)'; }}
            onMouseLeave={e => { if (canSend) e.currentTarget.style.background = 'var(--brand-500)'; }}
          >
            <IcoSend />
          </button>
        </div>

        <div style={{
          display: 'flex', justifyContent: 'space-between',
          marginTop: 6, padding: '0 4px', fontSize: 11.5, color: 'var(--text-tertiary)',
        }}>
          {!compact && <span>SUP'ONE peut faire des erreurs. Vérifiez les informations importantes.</span>}
          <span style={{ marginLeft: compact ? 'auto' : 0, color: len > 450 ? 'var(--warning)' : 'inherit' }}>
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
      transform: `translateX(-50%) translateY(${message ? 0 : 70}px)`,
      background: 'var(--text)', color: 'var(--bg)',
      padding: '9px 18px', borderRadius: 'var(--r-md)',
      fontSize: 13.5, fontWeight: 500, zIndex: 100,
      boxShadow: '0 4px 24px rgba(0,0,0,.3)',
      opacity: message ? 1 : 0,
      transition: 'transform .3s ease, opacity .3s ease',
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
        right: isNative ? 'max(12px, env(safe-area-inset-right))' : 16,
        width: 36, height: 36, borderRadius: '50%',
        background: 'var(--bg-elevated)', border: '1px solid var(--border-strong)',
        color: 'var(--text)', display: 'flex', alignItems: 'center', justifyContent: 'center',
        boxShadow: '0 2px 12px rgba(0,0,0,.2)', zIndex: 10,
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
function Sidebar({ open, onClose, history, onSelect, onShowAbout }) {
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    if (open) {
      const timer = setTimeout(() => setIsLoading(false), 800)
      return () => clearTimeout(timer)
    } else {
      setIsLoading(true)
    }
  }, [open])

  if (!open) return null

  return (
    <aside style={{
      position: 'fixed', inset: 0, zIndex: 100, display: 'flex'
    }}>
      <div 
        onClick={onClose} 
        style={{ flex: 1, background: 'rgba(0,0,0,0.6)', backdropFilter: 'blur(4px)', animation: 'fadeInChat .3s ease' }} 
      />
      <div style={{
        width: 'var(--sidebar-w)', background: 'var(--bg-elevated)', 
        borderRight: '1px solid var(--border-strong)',
        display: 'flex', flexDirection: 'column', 
        boxShadow: '20px 0 60px rgba(0,0,0,0.5)',
        animation: 'slideRight .4s cubic-bezier(0.16, 1, 0.3, 1)'
      }}>
        <div style={{ padding: '24px 20px', borderBottom: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <p style={{ fontWeight: 700, fontSize: 15, letterSpacing: '0.02em', color: 'var(--text)' }}>RÉCENT</p>
          <button onClick={onClose} style={{ color: 'var(--text-tertiary)', fontSize: 24, lineHeight: 0 }}>×</button>
        </div>
        
        <div style={{ flex: 1, overflowY: 'auto' }}>
          {isLoading ? (
            <SidebarSkeleton />
          ) : history?.length > 0 ? (
            history.map(item => (
              <button key={item.id} onClick={() => { onSelect(item.id); onClose(); }} style={{
                width: 'calc(100% - 20px)', margin: '4px 10px', padding: '12px', borderRadius: 10, textAlign: 'left',
                fontSize: 13.5, color: 'var(--text-secondary)', transition: 'all .2s'
              }} onMouseEnter={e => e.currentTarget.style.background = 'var(--surface)'} onMouseLeave={e => e.currentTarget.style.background = 'transparent'}>
                {item.title}
              </button>
            ))
          ) : <p style={{ padding: 20, textAlign: 'center', color: 'var(--text-tertiary)', fontSize: 13 }}>Aucune conversation</p>}
        </div>

        <div style={{ padding: 16, borderTop: '1px solid var(--border)', background: 'var(--surface)' }}>
          <button onClick={() => { onShowAbout(); onClose(); }} style={{
            display: 'flex', alignItems: 'center', gap: 10, width: '100%', 
            padding: '10px 12px', borderRadius: 10, fontSize: 13, color: 'var(--brand-300)',
            fontWeight: 500
          }}>
            <span style={{ fontSize: 16 }}>📖</span> Aide & Documentation
          </button>
        </div>
      </div>
    </aside>
  )
}

// ─── About Modal ──────────────────────────────────────────────────────────────
function AboutModal({ open, onClose }) {
  if (!open) return null;

  return (
    <div style={{
      position: 'fixed', inset: 0, zIndex: 200, display: 'flex', alignItems: 'center', justifyContent: 'center',
      background: 'rgba(0,0,0,0.7)', backdropFilter: 'blur(8px)', animation: 'fadeInChat .3s ease'
    }}>
      <div style={{
        width: '100%', maxWidth: 500, padding: 32, borderRadius: 24,
        background: 'var(--bg-elevated)', border: '1px solid var(--border-strong)',
        boxShadow: '0 20px 40px rgba(0,0,0,0.4)', position: 'relative',
        animation: 'popIn .3s cubic-bezier(0.16, 1, 0.3, 1)'
      }}>
        <button onClick={onClose} style={{
          position: 'absolute', top: 16, right: 16, fontSize: '1.2rem', color: 'var(--text-secondary)'
        }}>×</button>
        <h2 style={{ fontSize: 24, fontWeight: 700, marginBottom: 16, color: 'var(--text)' }}>À propos de SUP'ONE AI</h2>
        <p style={{ fontSize: 14.5, color: 'var(--text-secondary)', lineHeight: 1.6 }}>
          SUP'ONE AI est votre assistant virtuel intelligent, conçu pour vous aider et discuter avec vous de façon naturelle.
          Il a été développé par des experts passionnés des technologies et de la formation, motivés par le souhait d'améliorer l'excellence académique dans le domaine des TIC au Cameroun.
        </p>
        <p style={{ fontSize: 14.5, color: 'var(--text-secondary)', lineHeight: 1.6, marginTop: 12 }}>
          **Architecture :** React Hooks, Custom Hooks (useChat, useTheme, usePwaInstall, useNativeKeyboard).
        </p>
        <p style={{ fontSize: 14.5, color: 'var(--text-secondary)', lineHeight: 1.6, marginTop: 12 }}>
          **Fonctionnalités :** Streaming en temps réel (Gen3 IA) & Fallback FAQ TF-IDF, Authentification JWT & Persistance de session, Support PWA, Interface optimisée pour le natif (Capacitor), Interface utilisateur avancée.
        </p>
        <p style={{ fontSize: 14.5, color: 'var(--text-secondary)', lineHeight: 1.6, marginTop: 12 }}>
          **Version :** 2.0
        </p>
        <p style={{ fontSize: 14.5, color: 'var(--text-secondary)', lineHeight: 1.6, marginTop: 12 }}>
          Pour plus d'informations, visitez <a href="https://e-supptic.cm/" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--brand-300)', textDecoration: 'none' }}>e-supptic.cm</a>.
        </p>
      </div>
    </div>
  );
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

  const errorStyle = { color: 'var(--error)', fontSize: 11, marginTop: 4, marginLeft: 4, animation: 'msgIn .2s ease' }

  return (
    <div style={{
      flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20,
      animation: 'fadeUp .4s ease'
    }}>
      <div style={{
        width: '100%', maxWidth: 380, padding: 32, borderRadius: 24,
        background: 'var(--bg-elevated)', border: '1px solid var(--border-strong)',
        boxShadow: '0 20px 40px rgba(0,0,0,0.4)'
      }}>
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <div style={{ width: 50, height: 50, background: 'var(--brand-500)', borderRadius: 14, margin: '0 auto 16px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff' }}>
            <IcoSparkles />
          </div>
          <h2 style={{ fontSize: 24, fontWeight: 700 }}>{mode === 'login' ? 'Bon retour !' : 'Rejoindre SUP\'ONE'}</h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: 14, marginTop: 8 }}>Veuillez entrer vos informations</p>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <div style={{ position: 'relative' }}>
            <div style={{ position: 'relative' }}>
              <span style={{ position: 'absolute', left: 12, top: 12, color: 'var(--text-tertiary)' }}><IcoMail size={16}/></span>
              <input 
                placeholder="Email" 
                value={email}
                onChange={e => setEmail(e.target.value)}
                style={{ width: '100%', padding: '12px 12px 12px 40px', borderRadius: 12, outline: 'none', border: `1px solid ${errors.email ? 'var(--error)' : 'var(--composer-border)'}` }} 
              />
            </div>
            {errors.email && <p style={errorStyle}>{errors.email}</p>}
          </div>
          {mode === 'signup' && (
             <div style={{ position: 'relative' }}>
              <div style={{ position: 'relative' }}>
                <span style={{ position: 'absolute', left: 12, top: 12, color: 'var(--text-tertiary)' }}><IcoUser size={16}/></span>
                <input 
                  placeholder="Nom d'utilisateur" 
                  value={username}
                  onChange={e => setUsername(e.target.value)}
                  style={{ width: '100%', padding: '12px 12px 12px 40px', borderRadius: 12, outline: 'none', border: `1px solid ${errors.username ? 'var(--error)' : 'var(--composer-border)'}` }} 
                />
              </div>
              {errors.username && <p style={errorStyle}>{errors.username}</p>}
            </div>
          )}
          <div style={{ position: 'relative' }}>
            <div style={{ position: 'relative' }}>
              <span style={{ position: 'absolute', left: 12, top: 12, color: 'var(--text-tertiary)' }}><IcoLock size={16}/></span>
              <input 
                type="password" 
                placeholder="Mot de passe" 
                value={password}
                onChange={e => setPassword(e.target.value)}
                style={{ width: '100%', padding: '12px 12px 12px 40px', borderRadius: 12, outline: 'none', border: `1px solid ${errors.password ? 'var(--error)' : 'var(--composer-border)'}` }} 
              />
            </div>
            {errors.password && <p style={errorStyle}>{errors.password}</p>}
          </div>
          <button onClick={handleSubmit} style={{
            marginTop: 8, padding: 14, borderRadius: 12, background: 'var(--brand-500)', color: '#fff', fontWeight: 600, fontSize: 15
          }}>
            {mode === 'login' ? 'Se connecter' : 'Créer un compte'}
          </button>
        </div>

        <p style={{ textAlign: 'center', marginTop: 24, fontSize: 13.5, color: 'var(--text-secondary)' }}>
          {mode === 'login' ? "Pas encore de compte ?" : "Déjà un compte ?"}
          <button onClick={() => { setErrors({}); onSwitch(); }} style={{ color: 'var(--brand-300)', fontWeight: 600, marginLeft: 6 }}>
            {mode === 'login' ? 'S\'inscrire' : 'Se connecter'}
          </button>
        </p>
      </div>
    </div>
  )
}
