import { createClient, type Session, type SupabaseClient } from '@supabase/supabase-js'
import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'

/** Supabase is used ONLY for sign-in (DEC-001): never call .from(), .storage or .rpc here.
 * All data goes through the backend API. */
export function createAuthClient(url: string, publishableKey: string): SupabaseClient {
  return createClient(url, publishableKey, {
    auth: { persistSession: true, autoRefreshToken: true, detectSessionInUrl: true },
  })
}

interface AuthState {
  client: SupabaseClient
  session: Session | null
  /** true until the stored session has been read */
  loading: boolean
}

const AuthContext = createContext<AuthState | null>(null)

export function AuthProvider({
  client,
  children,
}: {
  client: SupabaseClient
  children: ReactNode
}) {
  const [session, setSession] = useState<Session | null>(null)
  const [loading, setLoading] = useState(true)
  useEffect(() => {
    let active = true
    void client.auth.getSession().then(({ data }) => {
      if (active) {
        setSession(data.session)
        setLoading(false)
      }
    })
    const { data } = client.auth.onAuthStateChange((_event, next) => {
      setSession(next)
      setLoading(false)
    })
    return () => {
      active = false
      data.subscription.unsubscribe()
    }
  }, [client])
  return (
    <AuthContext.Provider value={{ client, session, loading }}>{children}</AuthContext.Provider>
  )
}

export function useAuth(): AuthState {
  const state = useContext(AuthContext)
  if (!state) throw new Error('useAuth must be used inside <AuthProvider>')
  return state
}
