import { useState } from 'react'
import { ArrowRight, ArrowLeft } from 'lucide-react'
import { Link } from 'react-router-dom'
import AuthLayout from '../components/auth/AuthLayout'
import AuthInput from '../components/auth/AuthInput'
import AuthButton from '../components/auth/AuthButton'
import GoogleIcon from '../components/icons/GoogleIcon'
import FortyTwoIcon from '../components/icons/FortyTwoIcon'

function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')

  return (
    <AuthLayout>
      <p className='text-center font-sans font-bold text-2xl'>
        Keepr.
      </p>
      <h1 className='text-center font-serif font-bold text-4xl'>
        Welcome back
      </h1>

      <form className='mt-4 space-y-4'>
        <p className='text-center font-sans font-light text-sm text-muted'>
          Log in to your Keepr account.
        </p>
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
