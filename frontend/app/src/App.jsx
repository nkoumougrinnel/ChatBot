import { Capacitor } from '@capacitor/core'
import { useCallback, useEffect, useRef, useState } from 'react'
import { useChat } from './hooks/useChat'
import { useTheme } from './hooks/useTheme'
import { usePwaInstall } from './hooks/usePwaInstall'
import { useNativeKeyboard } from './hooks/useNativeKeyboard'

const isNative = Capacitor.isNativePlatform()

const GLOBAL_STYLE = `
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');

  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  :root {
    --font: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    --thread-max: 768px;
    --sidebar-w: 260px;
    --safe-top: env(safe-area-inset-top, 0px);
    --safe-bottom: env(safe-area-inset-bottom, 0px);
    --keyboard-offset: 0px;
    --t-fast: 150ms ease;
    --t-base: 250ms ease;
    --radius: 12px;
  }

  :root, [data-theme="dark"] {
    --bg-primary: #212121;
    --bg-secondary: #171717;
    --bg-tertiary: #303030;
    --bg-hover: #3a3a3a;
    --bg-active: #424242;
    --bg-input: #2f2f2f;
    --border: #424242;
    --border-light: #3a3a3a;
    --text-primary: #ececec;
    --text-secondary: #b4b4b4;
    --text-tertiary: #8e8e8e;
    --text-placeholder: #7a7a7a;
    --accent: #10a37f;
    --accent-hover: #1a7f64;
    --accent-bg: rgba(16,163,115,.12);
    --error: #ef4444;
    --error-bg: rgba(239,68,68,.12);
    --shadow-sm: 0 1px 2px rgba(0,0,0,.3);
    --shadow-md: 0 4px 12px rgba(0,0,0,.4);
    --overlay: rgba(0,0,0,.6);
    --scrollbar: rgba(255,255,255,.12);
    --user-bubble: #2f2f2f;
    --assistant-bubble: transparent;
    --code-bg: #1a1a1a;
  }

  [data-theme="light"] {
    --bg-primary: #ffffff;
    --bg-secondary: #f7f7f8;
    --bg-tertiary: #ececec;
    --bg-hover: #e8e8e8;
    --bg-active: #d9d9d9;
    --bg-input: #f4f4f4;
    --border: #d9d9d9;
    --border-light: #e8e8e8;
    --text-primary: #0d0d0d;
    --text-secondary: #6e6e6e;
    --text-tertiary: #9a9a9a;
    --text-placeholder: #8e8e8e;
    --accent: #10a37f;
    --accent-hover: #0e8c6b;
    --accent-bg: rgba(16,163,115,.08);
    --error: #dc2626;
    --error-bg: rgba(220,38,38,.08);
    --shadow-sm: 0 1px 2px rgba(0,0,0,.06);
    --shadow-md: 0 4px 12px rgba(0,0,0,.08);
    --overlay: rgba(0,0,0,.4);
    --scrollbar: rgba(0,0,0,.12);
    --user-bubble: #f4f4f4;
    --assistant-bubble: transparent;
    --code-bg: #f7f7f8;
  }

  html, body, #root { width: 100%; height: 100%; height: 100dvh; }
  body {
    font-family: var(--font);
    background: var(--bg-primary);
    color: var(--text-primary);
    line-height: 1.6;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
    overflow: hidden;
  }
  button { cursor: pointer; border: none; background: none; font-family: inherit; color: inherit; }
  button:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
  input, textarea { font-family: inherit; }

  ::-webkit-scrollbar { width: 6px; }
  ::-webkit-scrollbar-track { background: transparent; }
  ::-webkit-scrollbar-thumb { background: var(--scrollbar); border-radius: 99px; }
  ::-webkit-scrollbar-thumb:hover { background: var(--text-tertiary); }

  @media (prefers-reduced-motion: reduce) {
    *, *::before, *::after { animation-duration: .01ms !important; transition-duration: .01ms !important; }
  }
`

const KEYFRAMES = `
  @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
  @keyframes slideUp { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
  @keyframes slideDown { from { opacity: 0; transform: translateY(-8px); } to { opacity: 1; transform: translateY(0); } }
  @keyframes slideRight { from { opacity: 0; transform: translateX(-16px); } to { opacity: 1; transform: translateX(0); } }
  @keyframes spin { to { transform: rotate(360deg); } }
  @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: .5; } }
  @keyframes blink { 50% { opacity: 0; } }
  @keyframes bounce { 0%, 80%, 100% { transform: scale(.6); opacity: .4; } 40% { transform: scale(1); opacity: 1; } }
`

function renderMd(text) {
  if (!text) return null
  return text.split('\n').map((line, i) => {
    const parts = line.split(/\*\*(.*?)\*\*/g)
    const nodes = parts.map((p, j) => j % 2 === 1 ? <strong key={j} style={{ fontWeight: 600 }}>{p}</strong> : p)
    return <p key={i} style={{ margin: i > 0 ? '4px 0 0' : 0, lineHeight: 1.65 }}>{nodes}</p>
  })
}

const Svg = ({ size = 20, children, ...rest }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden {...rest}>{children}</svg>
)
const stroke = (d, w = 2) => <path d={d} stroke="currentColor" strokeWidth={w} strokeLinecap="round" strokeLinejoin="round" />

const IcoSend = () => <Svg size={18}>{stroke('M5 12h14M12 5l7 7-7 7')}</Svg>
const IcoNewChat = () => <Svg size={18}>{stroke('M12 5v14M5 12h14')}</Svg>
const IcoHistory = () => <Svg size={18}>{stroke('M12 8v4l3 3m6-3a9 9 0 1 1-9-9 8.959 8.959 0 0 1 4.5 1.2')}</Svg>
const IcoUser = ({ size = 18 }) => <Svg size={size}><circle cx="12" cy="7" r="4" stroke="currentColor" strokeWidth="1.5"/>{stroke('M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2', 1.5)}</Svg>
const IcoLogOut = () => <Svg size={18}>{stroke('M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9')}</Svg>
const IcoMail = ({ size = 18 }) => <Svg size={size}>{stroke('M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2zM22 6l-10 7L2 6', 1.5)}</Svg>
const IcoLock = ({ size = 18 }) => <Svg size={size}><rect x="3" y="11" width="18" height="11" rx="2" stroke="currentColor" strokeWidth="1.5"/>{stroke('M7 11V7a5 5 0 0 1 10 0v4', 1.5)}</Svg>
const IcoSun = () => <Svg size={18}><circle cx="12" cy="12" r="4" stroke="currentColor" strokeWidth="1.5"/>{stroke('M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41', 1.5)}</Svg>
const IcoMoon = () => <Svg size={18}>{stroke('M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z', 1.5)}</Svg>
const IcoCopy = () => <Svg size={14}><rect x="9" y="9" width="13" height="13" rx="2" stroke="currentColor" strokeWidth="1.5"/>{stroke('M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1', 1.5)}</Svg>
const IcoCheck = () => <Svg size={14}>{stroke('M20 6L9 17l-5-5', 2)}</Svg>
const IcoThumbUp = () => <Svg size={14}>{stroke('M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3H14zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3', 1.5)}</Svg>
const IcoThumbDown = () => <Svg size={14}>{stroke('M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3H10zM17 2h3a2 2 0 0 1 2 2v7a2 2 0 0 1-2 2h-3', 1.5)}</Svg>
const IcoRefresh = () => <Svg size={16}>{stroke('M21 12a9 9 0 1 1-2.64-6.36M21 3v6h-6', 1.5)}</Svg>
const IcoWifiOff = () => <Svg size={16}>{stroke('M1 1l22 22M16.72 11.06A10.94 10.94 0 0 1 19 12.55M5 12.55a10.94 10.94 0 0 1 5.17-2.39M8.53 16.11a6 6 0 0 1 6.95 0M12 20h.01', 1.5)}</Svg>
const IcoDownload = () => <Svg size={16}>{stroke('M12 3v12m0 0l4-4m-4 4l-4-4M4 21h16', 1.5)}</Svg>
const IcoChevDown = () => <Svg size={16}>{stroke('M6 9l6 6 6-6', 1.5)}</Svg>
const IcoPlus = () => <Svg size={16}>{stroke('M12 5v14M5 12h14', 1.5)}</Svg>
const IcoSidebar = () => <Svg size={18}>{stroke('M3 12h18M3 6h18M3 18h18', 1.5)}</Svg>
const IcoMenu = () => <Svg size={20}>{stroke('M4 6h16M4 12h16M4 18h16', 1.5)}</Svg>
const IcoSparkles = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" aria-hidden>
    <path d="M12 2l1.5 4.5L18 8l-4.5 1.5L12 14l-1.5-4.5L6 8l4.5-1.5L12 2zM5 16l.8 2.2L8 19l-2.2.8L5 22l-.8-2.2L2 19l2.2-.8L5 16zM19 15l.6 1.8 1.8.6-1.8.6-.6 1.8-.6-1.8L16 18l1.8-.6.6-1.4z"/>
  </svg>
)

function StatusDot({ status }) {
  const c = { online: '#10a37f', degraded: '#f59e0b', offline: '#ef4444', checking: '#8e8e8e' }
  return <span style={{ width: 7, height: 7, borderRadius: '50%', background: c[status] || '#8e8e8e', flexShrink: 0, animation: status === 'checking' ? 'pulse 1.5s ease infinite' : 'none' }} />
}

function SidebarButton({ children, onClick, label, active, danger }) {
  const [hov, setHov] = useState(false)
  return (
    <button
      type="button" onClick={onClick} aria-label={label} title={label}
      onMouseEnter={() => setHov(true)} onMouseLeave={() => setHov(false)}
      style={{
        width: 34, height: 34, borderRadius: 8,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        color: danger ? 'var(--error)' : active ? 'var(--text-primary)' : 'var(--text-secondary)',
        background: active ? 'var(--bg-tertiary)' : hov ? 'var(--bg-hover)' : 'transparent',
        transition: 'background var(--t-fast), color var(--t-fast)',
        flexShrink: 0,
      }}
    >{children}</button>
  )
}

function Header({ serverStatus, faqCount, isDark, onToggleTheme, onNewChat, onRefresh, refreshing, onInstall, canInstall, onToggleSidebar, user, onAuthClick, onProfileClick, onLogout }) {
  const labels = { online: 'En ligne', degraded: 'Service partiel', offline: 'Hors ligne', checking: 'Connexion...' }
  const subtitle = faqCount != null && serverStatus !== 'offline'
    ? `${labels[serverStatus]}  |  ${faqCount.toLocaleString('fr-FR')} FAQ`
    : labels[serverStatus] || '...'

  return (
    <header style={{
      display: 'flex', alignItems: 'center', gap: 8, height: 52,
      padding: '0 16px', paddingTop: 'var(--safe-top)',
      background: 'var(--bg-secondary)', borderBottom: '1px solid var(--border-light)',
      flexShrink: 0, zIndex: 10,
    }}>
      <SidebarButton onClick={onToggleSidebar} label="Menu">
        <IcoMenu />
      </SidebarButton>

      <div style={{ display: 'flex', alignItems: 'center', gap: 10, flex: 1, minWidth: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <div style={{
            width: 28, height: 28, borderRadius: 6,
            background: 'var(--accent)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            color: '#fff',
          }}>
            <IcoSparkles />
          </div>
          <span style={{ fontSize: 15, fontWeight: 600, color: 'var(--text-primary)', letterSpacing: '-0.01em' }}>
            SUP'ONE AI
          </span>
        </div>
        <span style={{ color: 'var(--text-tertiary)', fontSize: 13 }}>{subtitle}</span>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: 2 }}>
        <SidebarButton onClick={onToggleTheme} label={isDark ? 'Mode clair' : 'Mode sombre'}>
          {isDark ? <IcoSun /> : <IcoMoon />}
        </SidebarButton>

        {serverStatus === 'offline' ? (
          <SidebarButton onClick={onRefresh} label="Reconnecter" active>
            <IcoRefresh />
          </SidebarButton>
        ) : canInstall && !isNative ? (
          <SidebarButton onClick={onInstall} label="Installer" active>
            <IcoDownload />
          </SidebarButton>
        ) : (
          <SidebarButton onClick={onRefresh} disabled={refreshing || serverStatus === 'checking'} label="Actualiser">
            <IcoRefresh />
          </SidebarButton>
        )}

        <SidebarButton onClick={onNewChat} label="Nouveau chat">
          <IcoNewChat />
        </SidebarButton>

        {user ? (
          <button
            onClick={onProfileClick}
            style={{
              width: 30, height: 30, borderRadius: '50%',
              background: 'var(--bg-tertiary)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: 13, fontWeight: 600, color: 'var(--text-primary)',
              border: '1px solid var(--border)',
              transition: 'border-color var(--t-fast)',
            }}
          >
            {user.username.charAt(0).toUpperCase()}
          </button>
        ) : (
          <SidebarButton onClick={onAuthClick} label="Connexion">
            <IcoUser size={16} />
          </SidebarButton>
        )}
      </div>
    </header>
  )
}

function Sidebar({ open, onClose, history, onSelect, onShowAbout, onNewChat }) {
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    if (open) {
      if (Array.isArray(history)) {
        const t = setTimeout(() => setIsLoading(false), 300)
        return () => clearTimeout(t)
      }
    } else {
      setIsLoading(true)
    }
  }, [open, history])

  if (!open) return null

  return (
    <aside style={{ position: 'fixed', inset: 0, zIndex: 100, display: 'flex' }}>
      <div style={{
        width: 'var(--sidebar-w)', background: 'var(--bg-secondary)',
        borderRight: '1px solid var(--border-light)',
        display: 'flex', flexDirection: 'column',
        animation: 'slideRight .25s cubic-bezier(0.16, 1, 0.3, 1)',
        zIndex: 102,
      }}>
        <div style={{ padding: '14px 14px 14px 16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)' }}>Discussions</span>
          <button onClick={onClose} style={{
            width: 32, height: 32, borderRadius: 8,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            color: 'var(--text-secondary)', background: 'transparent',
            transition: 'background var(--t-fast)',
          }}
          onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-hover)'}
          onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
          >
            <Svg size={16}>{stroke('M18 6L6 18M6 6l12 12', 1.5)}</Svg>
          </button>
        </div>

        <div style={{ padding: '0 14px 14px' }}>
          <button
            onClick={() => { onNewChat(); onClose(); }}
            style={{
              display: 'flex', alignItems: 'center', gap: 8, width: '100%',
              padding: '10px 12px', borderRadius: 8,
              border: '1px solid var(--border)',
              color: 'var(--text-primary)', fontSize: 13.5,
              background: 'transparent', transition: 'background var(--t-fast)',
            }}
            onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-hover)'}
            onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
          >
            <IcoPlus /> Nouvelle discussion
          </button>
        </div>

        <div style={{ flex: 1, overflowY: 'auto', padding: '0 8px' }}>
          {isLoading ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4, padding: '8px 6px' }}>
              {[1,2,3,4,5].map(i => (
                <div key={i} style={{ height: 36, borderRadius: 6, background: 'var(--bg-tertiary)', animation: 'pulse 1.5s ease infinite', animationDelay: `${i*100}ms` }} />
              ))}
            </div>
          ) : history && history.length > 0 ? (
            history.map(item => (
              <button key={item.id} onClick={() => { onSelect(item.id); onClose(); }} style={{
                width: '100%', margin: '2px 0', padding: '8px 10px', borderRadius: 6,
                textAlign: 'left', fontSize: 13, color: 'var(--text-secondary)',
                background: 'transparent', transition: 'background var(--t-fast)',
                display: 'flex', alignItems: 'center', gap: 8,
              }}
              onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-hover)'}
              onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
              >
                <Svg size={14}>{stroke('M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z', 1.5)}</Svg>
                <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{item.title || 'Sans titre'}</span>
              </button>
            ))
          ) : (
            <p style={{ padding: '32px 12px', textAlign: 'center', color: 'var(--text-tertiary)', fontSize: 13 }}>Aucune conversation</p>
          )}
        </div>

        <div style={{ padding: '12px 14px', borderTop: '1px solid var(--border-light)' }}>
          <button onClick={() => { onShowAbout(); onClose(); }} style={{
            display: 'flex', alignItems: 'center', gap: 8, width: '100%',
            padding: '8px 10px', borderRadius: 6, fontSize: 13, color: 'var(--text-secondary)',
            background: 'transparent', transition: 'background var(--t-fast)',
          }}
          onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-hover)'}
          onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
          >
            <Svg size={14}>{stroke('M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10zM12 16v-4M12 8h.01', 1.5)}</Svg>
            Aide
          </button>
        </div>
      </div>
      <div onClick={onClose} style={{ flex: 1, background: 'var(--overlay)', animation: 'fadeIn .2s ease', zIndex: 101 }} />
    </aside>
  )
}

function Welcome({ suggestions, disabled, onSelect, user }) {
  const [greeting, setGreeting] = useState('')

  useEffect(() => {
    const hour = new Date().getHours()
    let t = 'Bonjour'
    if (hour >= 18) t = 'Bonsoir'
    if (hour >= 21 || hour < 5) t = 'Bonne nuit'
    const opts = [
      `${t}${user ? ', ' + user.username : ''}`,
      `Bienvenue${user ? ', ' + user.username : ''}`,
    ]
    setGreeting(opts[Math.floor(Math.random() * opts.length)])
  }, [user])

  if (!greeting) return null

  return (
    <div style={{
      flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center',
      justifyContent: 'center', padding: '60px 20px 32px', textAlign: 'center',
      animation: 'fadeIn .4s ease',
    }}>
      <div style={{
        width: 48, height: 48, borderRadius: 10, marginBottom: 24,
        background: 'var(--accent)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        color: '#fff',
      }}>
        <IcoSparkles />
      </div>

      <h1 style={{
        fontSize: 'clamp(22px, 3.5vw, 28px)', fontWeight: 600,
        color: 'var(--text-primary)', lineHeight: 1.3, marginBottom: 8,
      }}>
        {greeting}
      </h1>
      <p style={{ fontSize: 14, color: 'var(--text-secondary)', maxWidth: 400, lineHeight: 1.5 }}>
        Assistant IA pour SUP'PTIC. Posez vos questions sur l'ecole, les inscriptions, les examens et les services.
      </p>

      {suggestions?.length > 0 && (
        <div style={{
          display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: 8, marginTop: 32, width: '100%', maxWidth: 560,
        }}>
          {suggestions.map((text, i) => (
            <button
              key={text} type="button" disabled={disabled} onClick={() => onSelect(text)}
              style={{
                padding: '12px 14px', textAlign: 'left',
                background: 'var(--bg-secondary)', border: '1px solid var(--border-light)',
                borderRadius: 8, color: 'var(--text-primary)',
                fontSize: 13, lineHeight: 1.4,
                opacity: disabled ? 0.5 : 1, cursor: disabled ? 'not-allowed' : 'pointer',
                transition: 'background var(--t-fast), border-color var(--t-fast)',
                animation: `slideUp .3s ease ${i * 50}ms backwards`,
              }}
              onMouseEnter={e => { if (!disabled) { e.currentTarget.style.background = 'var(--bg-tertiary)'; e.currentTarget.style.borderColor = 'var(--border)'; }}}
              onMouseLeave={e => { e.currentTarget.style.background = 'var(--bg-secondary)'; e.currentTarget.style.borderColor = 'var(--border-light)'; }}
            >
              {text}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

function TypingDots({ label }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'var(--text-secondary)', fontSize: 14 }}>
      <span style={{ display: 'flex', gap: 4 }}>
        {[0, 1, 2].map(i => (
          <span key={i} style={{
            width: 6, height: 6, borderRadius: '50%', display: 'inline-block',
            background: 'var(--text-tertiary)',
            animation: `bounce 1.2s ${i * 0.15}s ease-in-out infinite`,
          }} />
        ))}
      </span>
      <span>{label || 'Reflexion...'}</span>
    </div>
  )
}

function FeedbackBar({ faqId, userQuestion, score, onSubmitFeedback, onToast }) {
  const [vote, setVote] = useState(null)
  const [submitting, setSubmitting] = useState(false)
  const [showForm, setShowForm] = useState(false)
  const [comment, setComment] = useState('')

  if (!userQuestion) return null

  const send = async (type, extra = '') => {
    if (submitting || vote) return
    setSubmitting(true)
    try {
      await onSubmitFeedback({ faqId, feedbackType: type, question: userQuestion, score, comment: extra })
      setVote(type)
      onToast?.(type === 'positif' ? 'Merci !' : 'Merci, votre retour nous aide a ameliorer.')
      setShowForm(false)
    } catch {
      onToast?.("Impossible d'envoyer le feedback")
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div style={{ marginTop: 10, display: 'flex', alignItems: 'center', gap: 4, flexWrap: 'wrap' }}>
      {[
        { type: 'positif', Icon: IcoThumbUp, label: 'Utile' },
        { type: 'negatif', Icon: IcoThumbDown, label: 'Pas utile' },
      ].map(({ type, Icon, label }) => (
        <FbBtn key={type} active={vote === type} onClick={() => {
          if (type === 'negatif' && !vote) { setShowForm(true); return }
          send(type)
        }} disabled={submitting || !!vote} label={label}>
          <Icon /> {label}
        </FbBtn>
      ))}
      {showForm && !vote && (
        <div style={{
          width: '100%', marginTop: 8, padding: '12px',
          background: 'var(--bg-secondary)', border: '1px solid var(--border-light)',
          borderRadius: 8, animation: 'slideUp .2s ease',
        }}>
          <textarea
            value={comment} onChange={e => setComment(e.target.value)}
            placeholder="Dites-nous ce qui pourrait etre ameliore..." rows={2} maxLength={500}
            style={{
              width: '100%', padding: '8px 10px', borderRadius: 6,
              border: '1px solid var(--border)', background: 'var(--bg-input)',
              color: 'var(--text-primary)', fontSize: 13, resize: 'none',
              outline: 'none', fontFamily: 'inherit',
            }}
          />
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 6, marginTop: 8 }}>
            <button onClick={() => setShowForm(false)} style={{ fontSize: 12.5, color: 'var(--text-secondary)', padding: '5px 10px', borderRadius: 6 }}>Annuler</button>
            <button onClick={() => send('negatif', comment.trim())} disabled={submitting} style={{ fontSize: 12.5, fontWeight: 500, color: '#fff', background: 'var(--accent)', padding: '5px 12px', borderRadius: 6 }}>Envoyer</button>
          </div>
        </div>
      )}
    </div>
  )
}

function FbBtn({ children, onClick, active, disabled }) {
  const [hov, setHov] = useState(false)
  return (
    <button onClick={onClick} disabled={disabled}
      onMouseEnter={() => setHov(true)} onMouseLeave={() => setHov(false)}
      style={{
        display: 'inline-flex', alignItems: 'center', gap: 5, padding: '4px 8px', borderRadius: 6,
        fontSize: 12, color: active ? 'var(--accent)' : 'var(--text-tertiary)',
        background: active ? 'var(--accent-bg)' : hov ? 'var(--bg-tertiary)' : 'transparent',
        transition: 'background var(--t-fast), color var(--t-fast)',
        opacity: disabled && !active ? 0.4 : 1,
      }}
    >{children}</button>
  )
}

function MessageBubble({ message, onCopy, onSubmitFeedback, onToast }) {
  const [copied, setCopied] = useState(false)

  const handleCopy = async () => {
    if (!message.content) return
    try {
      await navigator.clipboard.writeText(message.content)
      setCopied(true)
      onCopy?.()
      setTimeout(() => setCopied(false), 2000)
    } catch {}
  }

  if (message.role === 'user') {
    return (
      <div style={{
        display: 'flex', justifyContent: 'flex-end', width: '100%',
        paddingLeft: isNative ? '6%' : '16%',
        animation: 'slideUp .2s ease',
      }}>
        <div style={{
          background: 'var(--user-bubble)', color: 'var(--text-primary)',
          padding: '10px 16px', borderRadius: '16px 16px 4px 16px',
          fontSize: 14.5, lineHeight: 1.6, maxWidth: '85%',
          border: '1px solid var(--border-light)',
        }}>
          {renderMd(message.content)}
        </div>
      </div>
    )
  }

  if (message.status === 'error') {
    return (
      <div style={{
        display: 'flex', gap: 12, animation: 'slideUp .2s ease',
        padding: '12px 0',
      }}>
        <div style={{
          width: 28, height: 28, borderRadius: 6, flexShrink: 0,
          background: 'var(--error-bg)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          color: 'var(--error)',
        }}>
          <Svg size={14}>{stroke('M12 9v4M12 17h.01', 1.5)}</Svg>
        </div>
        <div style={{
          background: 'var(--error-bg)', border: '1px solid rgba(239,68,68,.15)',
          borderRadius: '4px 16px 16px 16px', padding: '12px 16px', flex: 1,
        }}>
          <p style={{ fontSize: 12, fontWeight: 600, color: 'var(--error)', marginBottom: 4, textTransform: 'uppercase', letterSpacing: '0.03em' }}>Erreur</p>
          <p style={{ fontSize: 13.5, color: 'var(--text-secondary)', lineHeight: 1.5 }}>{message.content}</p>
        </div>
      </div>
    )
  }

  const loading = message.status === 'loading'
  const streaming = message.status === 'streaming'
  const done = message.status === 'done'

  return (
    <div style={{
      display: 'flex', gap: 12, alignItems: 'flex-start',
      animation: 'slideUp .2s ease', padding: '8px 0',
    }}>
      <div style={{
        width: 28, height: 28, borderRadius: 6, flexShrink: 0,
        background: 'var(--accent)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        color: '#fff', marginTop: 2,
      }}>
        <IcoSparkles />
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontSize: 14.5, color: 'var(--text-primary)', lineHeight: 1.7 }}>
          {loading && <TypingDots label={message.statusLabel} />}
          {(streaming || done) && message.content && (
            <>
              {renderMd(message.content)}
              {streaming && (
                <span style={{
                  display: 'inline-block', width: 2, height: '1em', marginLeft: 2,
                  background: 'var(--accent)', verticalAlign: 'text-bottom',
                  animation: 'blink .8s step-end infinite',
                }} />
              )}
            </>
          )}

          {message.mode === 'low' && (
            <div style={{
              marginTop: 14, padding: '14px',
              background: 'var(--bg-secondary)', borderRadius: 8,
              border: '1px solid var(--border-light)',
              fontSize: 13, color: 'var(--text-secondary)',
              animation: 'slideUp .25s ease',
            }}>
              <p style={{ fontWeight: 600, color: 'var(--text-primary)', marginBottom: 8, fontSize: 12.5, textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                Suggestions
              </p>
              <ul style={{ paddingLeft: 18, lineHeight: 1.8, listStyleType: 'disc' }}>
                <li>Precisez votre demande (ex: "frais de scolarite ITT")</li>
                <li>Reformulez avec d'autres mots</li>
                <li>Contactez le secretariat : <a href="mailto:support@e-supptic.cm" style={{ color: 'var(--accent)', textDecoration: 'none' }}>support@e-supptic.cm</a></li>
              </ul>
            </div>
          )}
        </div>

        {done && message.content && message.mode !== 'low' && (
          <FeedbackBar
            faqId={message.faqId}
            userQuestion={message.userQuestion}
            score={message.score}
            onSubmitFeedback={onSubmitFeedback}
            onToast={onToast}
          />
        )}

        {done && message.content && (
          <div style={{ display: 'flex', alignItems: 'center', marginTop: 6 }}>
            <button
              type="button" onClick={handleCopy} aria-label="Copier"
              style={{
                display: 'inline-flex', alignItems: 'center', gap: 4, padding: '4px 8px',
                borderRadius: 6, fontSize: 12,
                color: copied ? 'var(--accent)' : 'var(--text-tertiary)',
                background: copied ? 'var(--accent-bg)' : 'transparent',
                transition: 'background var(--t-fast), color var(--t-fast)',
              }}
              onMouseEnter={e => { if (!copied) e.currentTarget.style.background = 'var(--bg-tertiary)'; }}
              onMouseLeave={e => { if (!copied) e.currentTarget.style.background = 'transparent'; }}
            >
              {copied ? <><IcoCheck /> Copie</> : <><IcoCopy /> Copier</>}
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

function Composer({ disabled, onSend, compact }) {
  const [value, setValue] = useState('')
  const ref = useRef(null)
  const MAX = 500

  const autoResize = useCallback(() => {
    const el = ref.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = `${Math.min(el.scrollHeight, 160)}px`
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

  const canSend = value.length > 0 && !disabled

  return (
    <div style={{
      flexShrink: 0, background: 'var(--bg-primary)',
      borderTop: compact ? 'none' : '1px solid var(--border-light)',
      paddingBottom: `calc(var(--safe-bottom) + var(--keyboard-offset))`,
    }}>
      <div style={{ maxWidth: 'var(--thread-max)', margin: '0 auto', padding: compact ? '8px 12px' : '12px 16px 16px' }}>
        <div style={{
          display: 'flex', alignItems: 'flex-end', gap: 8,
          background: 'var(--bg-input)', border: '1px solid var(--border)',
          borderRadius: 24, padding: '6px 6px 6px 16px',
          transition: 'border-color var(--t-fast)',
        }}
        onFocusCapture={e => e.currentTarget.style.borderColor = 'var(--border)'}
        onBlurCapture={e => e.currentTarget.style.borderColor = 'var(--border)'}
        >
          <textarea
            ref={ref} value={value}
            onChange={e => { setValue(e.target.value.slice(0, MAX)); autoResize() }}
            onKeyDown={onKey}
            placeholder="Envoyez un message..."
            disabled={disabled} rows={1} aria-label="Message" autoComplete="off"
            style={{
              flex: 1, border: 'none', background: 'transparent', color: 'var(--text-primary)',
              fontSize: 14.5, outline: 'none', resize: 'none', lineHeight: 1.5,
              maxHeight: 160, padding: '6px 0', fontFamily: 'inherit',
              opacity: disabled ? 0.5 : 1,
            }}
          />
          <button
            type="button" onClick={submit} disabled={!canSend} aria-label="Envoyer"
            style={{
              width: 32, height: 32, borderRadius: 16, flexShrink: 0, marginBottom: 1,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              background: canSend ? 'var(--accent)' : 'var(--bg-tertiary)',
              color: canSend ? '#fff' : 'var(--text-tertiary)',
              transition: 'background var(--t-fast), color var(--t-fast)',
            }}
          >
            <IcoSend />
          </button>
        </div>
        <p style={{ fontSize: 11.5, color: 'var(--text-tertiary)', textAlign: 'center', marginTop: 8 }}>
          SUP'ONE peut faire des erreurs. Verifiez les informations importantes.
        </p>
      </div>
    </div>
  )
}

function Toast({ message }) {
  return (
    <div role="status" style={{
      position: 'fixed', bottom: 80, left: '50%',
      transform: `translateX(-50%) translateY(${message ? 0 : 60}px)`,
      background: 'var(--text-primary)', color: 'var(--bg-primary)',
      padding: '8px 18px', borderRadius: 8,
      fontSize: 13, fontWeight: 500, zIndex: 100,
      boxShadow: 'var(--shadow-md)',
      opacity: message ? 1 : 0,
      transition: 'transform .3s cubic-bezier(0.16, 1, 0.3, 1), opacity .3s ease',
      pointerEvents: 'none', whiteSpace: 'nowrap',
    }}>
      {message || '\u00A0'}
    </div>
  )
}

function ScrollFab({ visible, onClick }) {
  return (
    <button
      type="button" onClick={onClick} aria-label="Descendre"
      style={{
        position: 'absolute',
        bottom: `calc(72px + var(--safe-bottom) + var(--keyboard-offset))`,
        right: isNative ? 'max(12px, env(safe-area-inset-right))' : 16,
        width: 34, height: 34, borderRadius: '50%',
        background: 'var(--bg-secondary)', border: '1px solid var(--border)',
        color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', justifyContent: 'center',
        boxShadow: 'var(--shadow-sm)', zIndex: 10,
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

function LoadingScreen() {
  return (
    <div style={{
      flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
      gap: 16, animation: 'fadeIn .4s ease',
    }}>
      <div style={{
        width: 32, height: 32, borderRadius: 8,
        background: 'var(--accent)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        color: '#fff',
      }}>
        <IcoSparkles />
      </div>
      <div style={{ textAlign: 'center' }}>
        <p style={{ fontSize: 13, color: 'var(--text-secondary)', fontWeight: 500 }}>Chargement...</p>
      </div>
    </div>
  )
}

function AuthPage({ mode, onSwitch, onLogin }) {
  const [email, setEmail] = useState('')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [errors, setErrors] = useState({})

  const validate = () => {
    const e = {}
    if (!email) e.email = "L'email est requis"
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) e.email = "Format invalide"
    if (mode === 'signup' && !username.trim()) e.username = "Le nom est requis"
    if (!password) e.password = "Le mot de passe est requis"
    else if (password.length <= 6) e.password = "Plus de 6 caracteres requis"
    setErrors(e)
    return Object.keys(e).length === 0
  }

  const handleSubmit = () => {
    if (validate()) {
      onLogin({ username: mode === 'signup' ? username : email.split('@')[0], email })
    }
  }

  const inputStyle = (hasErr) => ({
    width: '100%', padding: '10px 12px 10px 36px', borderRadius: 8,
    border: `1px solid ${hasErr ? 'var(--error)' : 'var(--border)'}`,
    background: 'var(--bg-input)', color: 'var(--text-primary)',
    fontSize: 14, outline: 'none', transition: 'border-color var(--t-fast)',
  })

  return (
    <div style={{
      flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20,
      animation: 'fadeIn .4s ease',
    }}>
      <div style={{ width: '100%', maxWidth: 360, padding: 28, borderRadius: 12, background: 'var(--bg-secondary)', border: '1px solid var(--border-light)' }}>
        <div style={{ textAlign: 'center', marginBottom: 28 }}>
          <div style={{
            width: 40, height: 40, borderRadius: 8,
            background: 'var(--accent)', margin: '0 auto 14px',
            display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff',
          }}>
            <IcoSparkles />
          </div>
          <h2 style={{ fontSize: 20, fontWeight: 600 }}>{mode === 'login' ? 'Bienvenue' : 'Creer un compte'}</h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: 13.5, marginTop: 6 }}>Entrez vos informations</p>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <div>
            <div style={{ position: 'relative' }}>
              <span style={{ position: 'absolute', left: 12, top: 11, color: 'var(--text-tertiary)' }}><IcoMail size={14}/></span>
              <input placeholder="Email" value={email} onChange={e => setEmail(e.target.value)} style={inputStyle(errors.email)} />
            </div>
            {errors.email && <p style={{ color: 'var(--error)', fontSize: 12, marginTop: 4, marginLeft: 2 }}>{errors.email}</p>}
          </div>
          {mode === 'signup' && (
            <div>
              <div style={{ position: 'relative' }}>
                <span style={{ position: 'absolute', left: 12, top: 11, color: 'var(--text-tertiary)' }}><IcoUser size={14}/></span>
                <input placeholder="Nom d'utilisateur" value={username} onChange={e => setUsername(e.target.value)} style={inputStyle(errors.username)} />
              </div>
              {errors.username && <p style={{ color: 'var(--error)', fontSize: 12, marginTop: 4, marginLeft: 2 }}>{errors.username}</p>}
            </div>
          )}
          <div>
            <div style={{ position: 'relative' }}>
              <span style={{ position: 'absolute', left: 12, top: 11, color: 'var(--text-tertiary)' }}><IcoLock size={14}/></span>
              <input type="password" placeholder="Mot de passe" value={password} onChange={e => setPassword(e.target.value)} style={inputStyle(errors.password)} />
            </div>
            {errors.password && <p style={{ color: 'var(--error)', fontSize: 12, marginTop: 4, marginLeft: 2 }}>{errors.password}</p>}
          </div>
          <button onClick={handleSubmit} style={{
            marginTop: 6, padding: '11px', borderRadius: 8,
            background: 'var(--accent)', color: '#fff', fontWeight: 600, fontSize: 14,
            transition: 'background var(--t-fast)',
          }}
          onMouseEnter={e => e.currentTarget.style.background = 'var(--accent-hover)'}
          onMouseLeave={e => e.currentTarget.style.background = 'var(--accent)'}
          >
            {mode === 'login' ? 'Se connecter' : "Creer un compte"}
          </button>
        </div>

        <p style={{ textAlign: 'center', marginTop: 20, fontSize: 13, color: 'var(--text-secondary)' }}>
          {mode === 'login' ? "Pas encore de compte ?" : "Deja un compte ?"}
          <button onClick={() => { setErrors({}); onSwitch(); }} style={{ color: 'var(--accent)', fontWeight: 600, marginLeft: 4 }}>
            {mode === 'login' ? "S'inscrire" : 'Se connecter'}
          </button>
        </p>
      </div>
    </div>
  )
}

function InstallBanner({ onInstall, onDismiss }) {
  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 12,
      margin: '8px auto 0', padding: '12px 16px',
      maxWidth: 'var(--thread-max)', width: 'calc(100% - 32px)',
      background: 'var(--bg-secondary)', border: '1px solid var(--border-light)',
      borderRadius: 8, animation: 'slideDown .25s ease',
    }}>
      <div style={{ width: 36, height: 36, borderRadius: 8, background: 'var(--accent)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', flexShrink: 0 }}>
        <IcoSparkles />
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <p style={{ fontSize: 13, fontWeight: 600 }}>Installer SUP'ONE AI</p>
        <p style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 2 }}>Acces rapide depuis l'ecran d'accueil</p>
      </div>
      <button onClick={onInstall} style={{ padding: '6px 12px', background: 'var(--accent)', color: '#fff', borderRadius: 6, fontSize: 12.5, fontWeight: 500, flexShrink: 0 }}>Installer</button>
      <button onClick={onDismiss} style={{ color: 'var(--text-tertiary)', padding: 4, fontSize: 16, lineHeight: 1 }}>&times;</button>
    </div>
  )
}

function OfflineBanner({ onRetry, retrying }) {
  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 10,
      margin: '8px auto 0', padding: '12px 16px',
      maxWidth: 'var(--thread-max)', width: 'calc(100% - 32px)',
      background: 'var(--error-bg)', border: '1px solid rgba(239,68,68,.15)',
      borderRadius: 8, animation: 'slideDown .25s ease',
    }}>
      <IcoWifiOff />
      <div style={{ flex: 1 }}>
        <p style={{ fontSize: 13, fontWeight: 600 }}>Serveur inaccessible</p>
        <p style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 1 }}>Verifiez votre connexion</p>
      </div>
      <button onClick={onRetry} disabled={retrying} style={{ padding: '6px 12px', borderRadius: 6, background: 'var(--error)', color: '#fff', fontSize: 12.5, fontWeight: 500, opacity: retrying ? 0.6 : 1 }}>
        {retrying ? '...' : 'Reessayer'}
      </button>
    </div>
  )
}

function DegradedBanner() {
  return (
    <div style={{
      padding: '8px 16px', textAlign: 'center', fontSize: 12, fontWeight: 500,
      color: '#f59e0b', background: 'rgba(245,158,11,.08)',
      borderBottom: '1px solid rgba(245,158,11,.15)',
    }}>
      Base FAQ en cours d'indexation
    </div>
  )
}

function AboutModal({ open, onClose }) {
  if (!open) return null
  return (
    <div style={{
      position: 'fixed', inset: 0, zIndex: 200, display: 'flex', alignItems: 'center', justifyContent: 'center',
      background: 'var(--overlay)', animation: 'fadeIn .2s ease',
    }}>
      <div style={{
        width: '100%', maxWidth: 440, padding: 28, borderRadius: 12,
        background: 'var(--bg-secondary)', border: '1px solid var(--border-light)',
        boxShadow: 'var(--shadow-md)', position: 'relative',
        animation: 'slideUp .25s cubic-bezier(0.16, 1, 0.3, 1)',
      }}>
        <button onClick={onClose} style={{
          position: 'absolute', top: 12, right: 12,
          width: 28, height: 28, borderRadius: 6,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          color: 'var(--text-tertiary)', background: 'transparent',
        }}
        onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-hover)'}
        onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
        >
          <Svg size={14}>{stroke('M18 6L6 18M6 6l12 12', 1.5)}</Svg>
        </button>
        <div style={{ textAlign: 'center', marginBottom: 20 }}>
          <div style={{
            width: 40, height: 40, borderRadius: 8, marginBottom: 14,
            background: 'var(--accent)', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', color: '#fff',
          }}>
            <IcoSparkles />
          </div>
          <h2 style={{ fontSize: 18, fontWeight: 600 }}>SUP'ONE AI</h2>
        </div>
        <p style={{ fontSize: 13.5, color: 'var(--text-secondary)', lineHeight: 1.6, marginBottom: 12 }}>
          Assistant virtuel intelligent pour SUP'PTIC. Developpe par l'equipe SUP'ONE.
        </p>
        <p style={{ fontSize: 13.5, color: 'var(--text-secondary)', lineHeight: 1.6, marginBottom: 12 }}>
          {renderMd("**Version :** 2.0")}
        </p>
        <p style={{ fontSize: 13.5, color: 'var(--text-secondary)', lineHeight: 1.6 }}>
          Plus d'infos : <a href="https://e-supptic.cm/" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--accent)', textDecoration: 'none' }}>e-supptic.cm</a>
        </p>
      </div>
    </div>
  )
}

function ProfileModal({ open, onClose, user, onLogout, onSave }) {
  const [editing, setEditing] = useState(false)
  const [username, setUsername] = useState(user?.username ?? '')
  const [email, setEmail] = useState(user?.email ?? '')

  useEffect(() => {
    if (user) { setUsername(user.username); setEmail(user.email); setEditing(false) }
  }, [user, open])

  if (!open || !user) return null

  const save = () => {
    const updated = { ...user, username: username.trim() || user.username, email: email.trim() || user.email }
    try { localStorage.setItem('supone-user', JSON.stringify(updated)) } catch {}
    onSave?.(updated)
    onClose()
  }

  return (
    <div style={{
      position: 'fixed', inset: 0, zIndex: 200, display: 'flex', alignItems: 'center', justifyContent: 'center',
      background: 'var(--overlay)', animation: 'fadeIn .2s ease',
    }}>
      <div style={{
        width: '100%', maxWidth: 360, padding: 28, borderRadius: 12,
        background: 'var(--bg-secondary)', border: '1px solid var(--border-light)',
        position: 'relative', animation: 'slideUp .25s cubic-bezier(0.16, 1, 0.3, 1)', textAlign: 'center',
      }}>
        <button onClick={onClose} style={{
          position: 'absolute', top: 12, right: 12,
          width: 28, height: 28, borderRadius: 6,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          color: 'var(--text-tertiary)',
        }}
        onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-hover)'}
        onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
        >
          <Svg size={14}>{stroke('M18 6L6 18M6 6l12 12', 1.5)}</Svg>
        </button>
        <div style={{
          width: 64, height: 64, borderRadius: '50%',
          background: 'var(--bg-tertiary)', border: '1px solid var(--border)',
          color: 'var(--text-primary)', display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 24, fontWeight: 600, margin: '0 auto 16px',
        }}>
          {username.charAt(0).toUpperCase()}
        </div>
        {!editing ? (
          <>
            <h2 style={{ fontSize: 17, fontWeight: 600 }}>{user.username}</h2>
            <p style={{ color: 'var(--text-secondary)', fontSize: 13, marginTop: 4, marginBottom: 20 }}>{user.email}</p>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              <button onClick={() => setEditing(true)} style={{ padding: '10px', borderRadius: 8, background: 'var(--bg-tertiary)', border: '1px solid var(--border-light)', fontWeight: 500, fontSize: 13 }}>Modifier le profil</button>
              <button onClick={() => { onLogout(); onClose(); }} style={{ padding: '10px', borderRadius: 8, background: 'var(--error-bg)', color: 'var(--error)', fontWeight: 500, fontSize: 13 }}>Deconnexion</button>
            </div>
          </>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            <input value={username} onChange={e => setUsername(e.target.value)} placeholder="Nom" style={{ padding: '9px 12px', borderRadius: 8, border: '1px solid var(--border)', background: 'var(--bg-input)', color: 'var(--text-primary)', fontSize: 13.5 }} />
            <input value={email} onChange={e => setEmail(e.target.value)} placeholder="Email" style={{ padding: '9px 12px', borderRadius: 8, border: '1px solid var(--border)', background: 'var(--bg-input)', color: 'var(--text-primary)', fontSize: 13.5 }} />
            <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end', marginTop: 4 }}>
              <button onClick={() => setEditing(false)} style={{ padding: '8px 14px', borderRadius: 6, fontSize: 13, color: 'var(--text-secondary)' }}>Annuler</button>
              <button onClick={save} style={{ padding: '8px 14px', borderRadius: 6, background: 'var(--accent)', color: '#fff', fontSize: 13, fontWeight: 500 }}>Enregistrer</button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

function UserAvatarButton({ user, onProfileClick, onLogout }) {
  const [show, setShow] = useState(false)
  const ref = useRef(null)

  useEffect(() => {
    const h = e => { if (ref.current && !ref.current.contains(e.target)) setShow(false) }
    document.addEventListener('mousedown', h)
    return () => document.removeEventListener('mousedown', h)
  }, [])

  return (
    <div ref={ref} style={{ position: 'relative' }}>
      <button onClick={() => setShow(!show)} style={{
        width: 30, height: 30, borderRadius: '50%',
        background: 'var(--bg-tertiary)', border: '1px solid var(--border)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontSize: 13, fontWeight: 600, color: 'var(--text-primary)',
      }}>
        {user.username.charAt(0).toUpperCase()}
      </button>
      {show && (
        <div style={{
          position: 'absolute', top: 'calc(100% + 6px)', right: 0,
          background: 'var(--bg-secondary)', border: '1px solid var(--border-light)',
          borderRadius: 8, minWidth: 150, zIndex: 60,
          animation: 'slideUp .2s ease', padding: '4px 0',
          boxShadow: 'var(--shadow-md)',
        }}>
          <button onClick={() => { onProfileClick(); setShow(false) }} style={{ width: '100%', textAlign: 'left', padding: '8px 12px', fontSize: 13, background: 'transparent' }}
            onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-hover)'}
            onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
          >Mon profil</button>
          <button onClick={() => { onLogout(); setShow(false) }} style={{ width: '100%', textAlign: 'left', padding: '8px 12px', fontSize: 13, color: 'var(--error)', background: 'transparent' }}
            onMouseEnter={e => e.currentTarget.style.background = 'var(--error-bg)'}
            onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
          >Deconnexion</button>
        </div>
      )}
    </div>
  )
}

export default function App() {
  const chat = useChat()
  const pwa = usePwaInstall()
  const { isDark, toggleTheme } = useTheme()
  const [showScrollFab, setShowScrollFab] = useState(false)
  const [refreshing, setRefreshing] = useState(false)
  const [user, setUser] = useState(null)
  const [authView, setAuthView] = useState(null)
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [showAbout, setShowAbout] = useState(false)
  const [showProfile, setShowProfile] = useState(false)
  const [isAuthenticating, setIsAuthenticating] = useState(false)

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      try {
        const savedUser = localStorage.getItem('supone-user')
        const savedToken = localStorage.getItem('supone-token')
        if (cancelled) return
        if (savedUser && savedToken) {
          setIsAuthenticating(true)
          setTimeout(() => {
            if (cancelled) return
            try { setUser(JSON.parse(savedUser)); chat.refreshHistory() } catch { handleLogout() } finally { setIsAuthenticating(false) }
          }, 800)
        }
      } catch {}
    })()
    return () => { cancelled = true }
  }, [])

  useNativeKeyboard()

  const handleLogin = (userData) => {
    setIsAuthenticating(true)
    setTimeout(async () => {
      setUser(userData)
      try {
        localStorage.setItem('supone-token', 'sk_live_' + Math.random().toString(36).substr(2))
        localStorage.setItem('supone-user', JSON.stringify(userData))
      } catch {}
      setAuthView(null)
      setIsAuthenticating(false)
      chat.showToastMsg(`Bienvenue ${userData.username} !`)
      chat.refreshHistory()
    }, 800)
  }

  const handleLogout = () => {
    setUser(null)
    localStorage.removeItem('supone-token')
    localStorage.removeItem('supone-user')
    chat.resetChat()
  }

  const handleRefresh = useCallback(async () => {
    setRefreshing(true)
    await chat.refreshHealth()
    setRefreshing(false)
    if (chat.online) chat.showToastMsg('Connexion restauree')
  }, [chat])

  const handleScroll = () => {
    chat.onListScroll()
    const el = chat.listRef.current
    if (!el) return
    setShowScrollFab(el.scrollHeight - el.scrollTop - el.clientHeight < 100)
  }

  const handleInstall = async () => {
    const ok = await pwa.install()
    if (ok) chat.showToastMsg('Installe !')
  }

  const theme = isDark ? 'dark' : 'light'

  return (
    <>
      <style dangerouslySetInnerHTML={{ __html: GLOBAL_STYLE + KEYFRAMES }} />
      <div data-theme={theme} style={{
        width: '100%', height: '100vh', height: '100dvh',
        display: 'flex', flexDirection: 'column',
        background: 'var(--bg-primary)', overflow: 'hidden',
      }}>
        <Sidebar
          open={sidebarOpen} onClose={() => setSidebarOpen(false)}
          history={isAuthenticating ? null : (chat.history || [])}
          onSelect={chat.loadThread}
          onShowAbout={() => setShowAbout(true)}
          onNewChat={chat.resetChat}
        />

        {pwa.showBanner && <InstallBanner onInstall={handleInstall} onDismiss={pwa.dismiss} />}
        {chat.serverStatus === 'offline' && <OfflineBanner onRetry={handleRefresh} retrying={refreshing} />}
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
          onAuthClick={() => setAuthView('login')}
          onProfileClick={() => setShowProfile(true)}
          onLogout={handleLogout}
        />

        {isAuthenticating ? (
          <LoadingScreen />
        ) : authView ? (
          <AuthPage mode={authView} onSwitch={() => setAuthView(authView === 'login' ? 'signup' : 'login')} onLogin={handleLogin} />
        ) : (
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0, animation: 'fadeIn .3s ease' }}>
            <main
              ref={chat.listRef}
              onScroll={handleScroll}
              aria-live="polite"
              aria-label="Conversation"
              style={{
                flex: 1, overflowY: 'auto',
                maxWidth: isNative ? '100%' : 'var(--thread-max)',
                width: '100%', margin: '0 auto',
                padding: isNative ? '12px max(10px,env(safe-area-inset-right)) 6px max(10px,env(safe-area-inset-left))' : '16px 16px 8px',
                display: 'flex', flexDirection: 'column',
                scrollBehavior: 'smooth',
              }}
            >
              {chat.showWelcome ? (
                <Welcome suggestions={chat.suggestions} disabled={chat.isProcessing} onSelect={chat.sendMessage} user={user} />
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                  {chat.messages.map(msg => (
                    <MessageBubble
                      key={msg.id} message={msg}
                      onCopy={() => chat.showToastMsg('Copie')}
                      onSubmitFeedback={chat.sendFeedback}
                      onToast={chat.showToastMsg}
                    />
                  ))}
                </div>
              )}
            </main>

            <ScrollFab visible={showScrollFab} onClick={() => { chat.scrollToBottom(); setShowScrollFab(false) }} />

            <Composer
              disabled={chat.isProcessing || chat.serverStatus === 'offline'}
              onSend={chat.sendMessage}
              compact={isNative}
            />
          </div>
        )}

        <Toast message={chat.toast} />
        <AboutModal open={showAbout} onClose={() => setShowAbout(false)} />
        <ProfileModal open={showProfile} onClose={() => setShowProfile(false)} user={user} onLogout={handleLogout} onSave={(u) => { setUser(u); chat.showToastMsg('Profil mis a jour'); }} />
      </div>
    </>
  )
}
