import { AlertCircle, LockKeyhole, Mail } from 'lucide-react'
import { useState, type FormEvent } from 'react'
import { Navigate, useLocation, useNavigate } from 'react-router-dom'
import { BrandLogo } from '../components/BrandLogo'
import { Button } from '../components/Button'
import { useAuth } from '../context/useAuth'
import { isSupabaseConfigured, isTestAuthEnabled } from '../lib/supabase'

interface LoginLocationState {
  from?: string
}

export function LoginPage() {
  const { session, loading, signIn } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  if (!loading && session) return <Navigate to="/maintenance" replace />

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setError('')
    setSubmitting(true)
    try {
      await signIn(email.trim(), password)
      const state = location.state as LoginLocationState | null
      navigate(state?.from ?? '/maintenance', { replace: true })
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Sign in failed. Please try again.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <main className="app-shell flex min-h-screen items-center justify-center px-4 py-10 text-ink">
      <section className="glass-panel w-full max-w-5xl rounded-[2rem] p-6 sm:p-9">
        <div className="mb-8 flex justify-center">
          <BrandLogo />
        </div>

        {isTestAuthEnabled ? (
          <div className="mb-5 flex gap-3 rounded-2xl border border-warning-line bg-warning-soft/80 p-3 text-sm text-warning" role="alert">
            <AlertCircle className="mt-0.5 shrink-0" aria-hidden="true" size={18} />
            Test login is enabled. Enter any email and password to continue.
          </div>
        ) : null}

        {!isSupabaseConfigured && !isTestAuthEnabled ? (
          <div className="mb-5 flex gap-3 rounded-2xl border border-warning-line bg-warning-soft/80 p-3 text-sm text-warning" role="alert">
            <AlertCircle className="mt-0.5 shrink-0" aria-hidden="true" size={18} />
            Add your Supabase URL and anon key to <code>.env</code> before signing in.
          </div>
        ) : null}

        <form className="space-y-5" onSubmit={handleSubmit}>
          <label className="block">
            <span className="mb-2 block text-sm font-medium text-ink">Email address</span>
            <span className="relative block">
              <Mail className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-muted" aria-hidden="true" size={18} />
              <input
                type={isTestAuthEnabled ? 'text' : 'email'}
                autoComplete={isTestAuthEnabled ? 'username' : 'email'}
                required
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                className="field-control min-h-12 w-full rounded-2xl py-3 pl-11 pr-4 text-base text-ink outline-none transition-colors placeholder:text-muted/60 focus:border-accent focus:ring-1 focus:ring-accent"
                placeholder={isTestAuthEnabled ? 'tester' : 'operator@facility.com'}
              />
            </span>
          </label>

          <label className="block">
            <span className="mb-2 block text-sm font-medium text-ink">Password</span>
            <span className="relative block">
              <LockKeyhole className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-muted" aria-hidden="true" size={18} />
              <input
                type="password"
                autoComplete="current-password"
                required
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                className="field-control min-h-12 w-full rounded-2xl py-3 pl-11 pr-4 text-base text-ink outline-none transition-colors placeholder:text-muted/60 focus:border-accent focus:ring-1 focus:ring-accent"
                placeholder="Enter your password"
              />
            </span>
          </label>

          {error ? (
            <p className="flex gap-2 text-sm text-danger" role="alert">
              <AlertCircle className="mt-0.5 shrink-0" aria-hidden="true" size={17} />
              {error}
            </p>
          ) : null}

          <Button type="submit" className="w-full" disabled={submitting || (!isSupabaseConfigured && !isTestAuthEnabled)}>
            {submitting ? 'Signing in...' : 'Sign In'}
          </Button>
        </form>
      </section>
    </main>
  )
}
