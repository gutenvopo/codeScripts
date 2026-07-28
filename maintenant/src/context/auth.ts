import { createContext } from 'react'

export interface AppSession {
  user: {
    id: string
    email?: string
  }
}

export interface AuthContextValue {
  session: AppSession | null
  loading: boolean
  signIn: (email: string, password: string) => Promise<void>
  signOut: () => Promise<void>
}

export const AuthContext = createContext<AuthContextValue | null>(null)
