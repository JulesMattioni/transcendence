import { useState } from 'react'
import { ArrowRight, ArrowLeft } from 'lucide-react'
import { Link } from 'react-router-dom'
import AuthLayout from '../components/auth/AuthLayout'
import AuthInput from '../components/auth/AuthInput'
import AuthButton from '../components/auth/AuthButton'
import GoogleIcon from '../components/icons/GoogleIcon'
import FortyTwoIcon from '../components/icons/FortyTwoIcon'


function RegisterPage() {
  const [first_name, setFirstName] = useState('')
  const [last_name, setLastName] = useState('')
  const [email, setEmail] = useState('')
  // const [phone, setPhone] = useState('')
  const [password, setPassword] = useState('')
  const [confirm_password, setConfirmPassword] = useState('')

  return (
    <AuthLayout>
      <p className='text-center font-sans font-bold text-2xl'>
        Keepr.
      </p>
      <h1 className='text-center font-serif font-bold text-4xl'>
        Create your account
      </h1>

      <form className='mt-4 space-y-4'>
        <p className='text-center font-sans font-light text-sm text-muted'>
          Get started with Keepr.
        </p>
        <div className='grid grid-cols-2 gap-3'>
          <AuthInput
            type="text"
            name="FirstName"
            placeholder='First Name'
            value={first_name}
            onChange={setFirstName}
          />
          <AuthInput
            type="text"
            name="LastName"
            placeholder='Last Name'
            value={last_name}
            onChange={setLastName}
          />
        </div>
        <AuthInput
          type="email"
          name="email"
          placeholder='email@example.com'
          value={email}
          onChange={setEmail}
        />
        {/* <AuthInput
          type="tel"
          name="phone"
          placeholder='Phone Number'
          value={phone}
          onChange={setPhone}
          autoComplete='tel'
        /> */}
        <AuthInput
          type="password"
          name="password"
          placeholder='Password'
          value={password}
          onChange={setPassword}
          autoComplete='new-password'
        />
        <AuthInput
          type="password"
          name="ConfirmPassword"
          placeholder='Confirm Password'
          value={confirm_password}
          onChange={setConfirmPassword}
          autoComplete='new-password'
        />
        <AuthButton
          children="Create Account"
          icon=<ArrowRight size={15} strokeWidth={2}/>
        />
        <div className='grid grid-cols-2 gap-3'>
          <AuthButton
            children="Create with "
            variant='outline'
            type='button'
            icon=<GoogleIcon/>
          />
          <AuthButton
            children="Create with "
            variant='outline'
            type='button'
            icon=<FortyTwoIcon/>
          />
        </div>
        <p className='text-center font-sans font-light text-sm text-muted'>
          Already have an account ? <Link to={'/login'} className='hover:text-black underline'> Sign In</Link>
        </p>
        <Link to={'/'} className='flex items-center text-sans text-sm text-muted hover:text-black'>
          <ArrowLeft size={14} className='text-keepr'/>Back
        </Link>
      </form>
    </AuthLayout>
  )
}

export default RegisterPage
