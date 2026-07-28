import { useEffect, useMemo, useState, type PropsWithChildren } from 'react'
import type { Session } from '@supabase/supabase-js'
import { isTestAuthEnabled, supabase } from '../lib/supabase'
import { AuthContext, type AppSession, type AuthContextValue } from './auth'

const TEST_SESSION_KEY = 'maintenant:test-session'

function toAppSession(session: Session | null): AppSession | null {
  if (!session) return null
  return {
    user: {
      id: session.user.id,
      email: session.user.email,
    },
  }
}

function loadTestSession(): AppSession | null {
  const stored = window.localStorage.getItem(TEST_SESSION_KEY)
  if (!stored) return null
  try {
    const parsed = JSON.parse(stored) as AppSession
    return parsed.user?.id ? parsed : null
  } catch {
    window.localStorage.removeItem(TEST_SESSION_KEY)
    return null
  }
}

function createTestSession(email: string): AppSession {
  return {
    user: {
      id: 'local-test-user',
      email,
    },
  }
}

export function AuthProvider({ children }: PropsWithChildren) {
  const [session, setSession] = useState<AppSession | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!supabase) {
      setSession(isTestAuthEnabled ? loadTestSession() : null)
      setLoading(false)
      return
    }

    let active = true
    void supabase.auth.getSession().then(({ data }) => {
      if (active) {
        setSession(toAppSession(data.session))
        setLoading(false)
      }
    })

    const { data } = supabase.auth.onAuthStateChange((_event, nextSession) => {
      setSession(toAppSession(nextSession))
      setLoading(false)
    })

    return () => {
      active = false
      data.subscription.unsubscribe()
    }
  }, [])

  const value = useMemo<AuthContextValue>(
    () => ({
      session,
      loading,
      signIn: async (email, password) => {
        if (!supabase) {
          if (!isTestAuthEnabled) {
            throw new Error('Supabase is not configured. Add the required values to .env.')
          }
          const testSession = createTestSession(email)
          window.localStorage.setItem(TEST_SESSION_KEY, JSON.stringify(testSession))
          setSession(testSession)
          return
        }
        const { error } = await supabase.auth.signInWithPassword({ email, password })
        if (error) throw error
      },
      signOut: async () => {
        if (!supabase) {
          window.localStorage.removeItem(TEST_SESSION_KEY)
          setSession(null)
          return
        }
        const { error } = await supabase.auth.signOut()
        if (error) throw error
      },
    }),
    [loading, session],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
