import { useEffect, useState } from 'react'
import { Navigate } from 'react-router-dom'
import { Loader2 } from 'lucide-react'
import { me } from '../../api/auth'

type AuthState = 'checking' | 'authenticated' | 'unauthenticated'

function RequireAuth({ children }: { children: React.ReactNode }) {
  const [status, setStatus] = useState<AuthState>('checking')

  useEffect(() => {
    me()
      .then(() => setStatus('authenticated'))
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
