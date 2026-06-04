import heroImg from '../assets/hero.png'
import { IconSparkles } from './Icons'

const FEATURES = [
  { icon: '🎓', label: 'Admissions & filières' },
  { icon: '🏫', label: 'Vie sur le campus' },
  { icon: '🤖', label: 'IA Gemini + base FAQ' },
]

export function Welcome() {
  return (
    <section className="welcome">
      <div className="welcome-hero">
        <img src={heroImg} alt="" className="welcome-hero__img" />
        <div className="welcome-badge">
          <IconSparkles />
        </div>
      </div>
      <h2>Bienvenue sur SUP&apos;ONE AI</h2>
      <p>
        Posez vos questions sur SUP&apos;PTIC : inscriptions, campus, clubs,
        examens et vie étudiante. Réponses instantanées, 24h/24.
      </p>
      <div className="welcome-features">
        {FEATURES.map((f) => (
          <span key={f.label} className="welcome-feature">
            <span aria-hidden>{f.icon}</span>
            {f.label}
          </span>
        ))}
      </div>
    </section>
  )
}
