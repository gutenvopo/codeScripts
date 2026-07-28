import type { ButtonHTMLAttributes, PropsWithChildren } from 'react'

type ButtonVariant = 'primary' | 'secondary' | 'quiet' | 'danger'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant
}

const variants: Record<ButtonVariant, string> = {
  primary: 'border-white/30 bg-gradient-to-r from-brand via-brand-hover to-accent text-white shadow-glow hover:from-brand-hover hover:via-brand hover:to-accent-hover',
  secondary: 'border-white/35 bg-white/16 text-ink hover:bg-white/24',
  quiet: 'border-transparent bg-transparent text-white/78 hover:bg-white/14 hover:text-white',
  danger: 'border-danger-line bg-danger-soft/50 text-danger hover:bg-danger-soft',
}

export function Button({
  children,
  className = '',
  type = 'button',
  variant = 'primary',
  ...props
}: PropsWithChildren<ButtonProps>) {
  return (
    <button
      type={type}
      className={`inline-flex min-h-12 items-center justify-center gap-3 rounded-full border px-5 py-3 text-sm font-semibold transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 focus-visible:ring-offset-canvas disabled:cursor-not-allowed disabled:opacity-50 ${variants[variant]} ${className}`}
      {...props}
    >
      {children}
    </button>
  )
}
