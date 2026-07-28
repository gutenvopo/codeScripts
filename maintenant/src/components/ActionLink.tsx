import { ArrowRight, type LucideIcon } from 'lucide-react'
import { Link } from 'react-router-dom'

interface ActionLinkProps {
  to: string
  title: string
  description: string
  icon: LucideIcon
}

export function ActionLink({ to, title, description, icon: Icon }: ActionLinkProps) {
  return (
    <Link
      to={to}
      className="glass-panel group grid min-h-24 grid-cols-[3rem_1fr_1.5rem] items-center gap-4 rounded-3xl px-5 py-4 transition-all hover:-translate-y-0.5 hover:border-white/45 hover:bg-white/18 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 focus-visible:ring-offset-canvas"
    >
      <span className="flex h-12 w-12 items-center justify-center rounded-2xl border border-white/35 bg-gradient-to-br from-white/22 via-brand-soft to-accent/24 text-accent shadow-glow">
        <Icon aria-hidden="true" size={24} />
      </span>
      <span className="min-w-0">
        <span className="block text-base font-semibold text-ink">{title}</span>
        <span className="mt-1 block text-sm leading-5 text-muted">{description}</span>
      </span>
      <ArrowRight
        aria-hidden="true"
        className="text-muted transition-transform group-hover:translate-x-1 group-hover:text-accent"
        size={20}
      />
    </Link>
  )
}
