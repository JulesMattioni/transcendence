import { useState } from 'react'
import { ArrowRight, ArrowLeft } from 'lucide-react'
import { Link, useNavigate } from 'react-router-dom'
import { login, loginVerify2fa } from '../api/auth'
import { ApiError } from '../api/client'
import { validateEmail, validateRequired } from '../utils/validation'
import AuthLayout from '../components/auth/AuthLayout'
import AuthInput from '../components/auth/AuthInput'
import AuthButton from '../components/auth/AuthButton'
import GoogleIcon from '../components/icons/GoogleIcon'
import FortyTwoIcon from '../components/icons/FortyTwoIcon'

function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()
  const [pendingToken, setPendingToken] = useState<string | null>(null)
  const [code, setCode] = useState('')

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')

    const emailError = validateEmail(email)
    if (emailError) return setError(emailError)

    const passwordError = validateRequired(password, 'Password')
    if (passwordError) return setError(passwordError)

    setLoading(true)
    try {
      const result = await login({ email, password })
      if (result.kind === '2fa_required') {
        setPendingToken(result.pendingToken)
      } else {
        navigate('/dashboard')
      }
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message)
      } else {
        setError('Something went wrong. Please try again.')
      }
    } finally {
      setLoading(false)
    }
  }

  async function handleVerify2fa(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    if (!pendingToken) return
    if (!/^\d{6}$/.test(code.trim())) {
      return setError('Enter the 6-digit code from your authenticator app.')
    }

    setLoading(true)
    try {
      await loginVerify2fa(pendingToken, code.trim())
      navigate('/dashboard')
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message)
      } else {
        setError('Something went wrong. Please try again.')
      }
    } finally {
      setLoading(false)
    }
  }

  function backToCredentials() {
    setPendingToken(null)
    setCode('')
    setError('')
  }

  {/* 2fa */}
  if (pendingToken) {
    return (
      <AuthLayout>
        <p className='text-center font-sans font-bold text-2xl'>Keepr.</p>
        <h1 className='text-center font-serif font-bold text-4xl'>
          Two-factor authentication
        </h1>

        <form className='mt-4 space-y-4' onSubmit={handleVerify2fa}>
          <p className='text-center font-sans font-light text-sm text-muted'>
            Enter the 6-digit code from your authenticator app.
          </p>
          {error && (
            <p className='text-center text-sm text-red-500'>{error}</p>
          )}
          <AuthInput
            type="text"
            name="code"
            placeholder='123456'
            value={code}
            onChange={(v) => setCode(v.replace(/\D/g, ''))}
          />
          <AuthButton
            children="Verify"
            loading={loading}
            icon=<ArrowRight size={15} strokeWidth={2}/>
          />
          <button
            type='button'
            onClick={backToCredentials}
            className='flex items-center text-sans text-sm text-muted hover:text-black'
          >
            <ArrowLeft size={14} className='text-keepr'/>Back
          </button>
        </form>
      </AuthLayout>
    )
  }

  return (
    <AuthLayout>
      <p className='text-center font-sans font-bold text-2xl'>
        Keepr.
      </p>
      <h1 className='text-center font-serif font-bold text-4xl'>
        Welcome back
      </h1>

      <form className='mt-4 space-y-4' onSubmit={handleSubmit}>
        <p className='text-center font-sans font-light text-sm text-muted'>
          Log in to your Keepr account.
        </p>
        {error && (
          <p className='text-center text-sm text-red-500'>
            {error}
          </p>
        )}
        <AuthInput
          type="email"
          name="email"
          placeholder='email@example.com'
          value={email}
          onChange={setEmail}
        />
        <AuthInput
          type="password"
          name="password"
          placeholder='Password'
          value={password}
          onChange={setPassword}
          autoComplete='new-password'
        />
        <div className='-mt-2 flex justify-end'>
          <Link to={'/'} className='text-sm text-keepr opacity-60 hover:opacity-100'>
            Forgot password ?
          </Link>
        </div>
        <AuthButton
          children="Sign In"
          loading={loading}
          icon=<ArrowRight size={15} strokeWidth={2}/>
        />
        <div className='grid grid-cols-2 gap-3'>
          <AuthButton
            children="Connect with "
            variant='outline'
            type='button'
            icon=<GoogleIcon/>
          />
          <AuthButton
            children="Connect with "
            variant='outline'
            type='button'
            icon=<FortyTwoIcon/>
          />
        </div>
        <p className='text-center font-sans font-light text-sm text-muted'>
          Don't have an account ? <Link to={'/register'} className='hover:text-black underline'> Sign Up</Link>
        </p>
        <Link to={'/'} className='flex items-center text-sans text-sm text-muted hover:text-black'>
          <ArrowLeft size={14} className='text-keepr'/>Back
        </Link>
      </form>
    </AuthLayout>
  )
}

export default LoginPage
