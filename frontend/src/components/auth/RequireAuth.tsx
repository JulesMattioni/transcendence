import { useEffect, useState } from 'react'
import { Navigate } from 'react-router-dom'
import { Loader2 } from 'lucide-react'
import { me } from '../../api/auth'
import { connectRealtime } from '../../api/realtime'

type AuthState = 'checking' | 'authenticated' | 'unauthenticated'

/**
 * Guard that verifies the session via /me before rendering its children:
 * shows a spinner while checking, opens the realtime connection once
 * authenticated, and redirects to /login otherwise.
 */
function RequireAuth({ children }: { children: React.ReactNode }) {
  const [status, setStatus] = useState<AuthState>('checking')

  useEffect(() => {
    me()
      .then(() => {
        connectRealtime()
        setStatus('authenticated')
      })
      .catch(() => setStatus('unauthenticated'))
  }, [])

  if (status === 'checking') {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <Loader2 size={28} className="animate-spin text-keepr" />
      </div>
    )
  }

  if (status === 'unauthenticated') {
    return <Navigate to="/login" replace />
  }

  return <>{children}</>
}

export default RequireAuth
