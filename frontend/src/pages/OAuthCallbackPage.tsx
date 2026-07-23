import { useEffect, useRef } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { exchangeOAuthCode } from '../api/auth'
import { ApiError } from '../api/client'

function OAuthCallbackPage() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const handled = useRef(false)

  useEffect(() => {
    if (handled.current) return
    handled.current = true

    const exchangeCode = searchParams.get('exchange_code')
    const pendingToken = searchParams.get('pending_token')

    if (pendingToken) {
      navigate('/login', { state: { pendingToken } })
      return
    }

    if (!exchangeCode) {
      navigate('/login', { state: { oauthError: 'Missing authorization code. Please try again.' } })
      return
    }

    exchangeOAuthCode(exchangeCode)
      .then(() => navigate('/dashboard'))
      .catch((err) => {
        const message =
          err instanceof ApiError ? err.message : 'Something went wrong. Please try again.'
        navigate('/login', { state: { oauthError: message } })
      })
  }, [searchParams, navigate])

  return (
    <div className='flex min-h-screen items-center justify-center'>
      <p className='font-sans text-sm text-muted'>Signing you in…</p>
    </div>
  )
}

export default OAuthCallbackPage
