import { useState } from 'react'
import AuthLayout from '../components/auth/AuthLayout'
import AuthInput from '../components/auth/AuthInput'


function RegisterPage() {
  const [first_name, setFirstName] = useState('')
  const [last_name, setLastName] = useState('')
  const [email, setEmail] = useState('')
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
        <p className='text-center font-sans font-light text-sm'>
          Get started with Keepr.
        </p>
        <div className='grid grid-cols-2 gap-3'>
          <AuthInput
            type="text"
            name="FirstName"
            placeholder='First name'
            value={first_name}
            onChange={setFirstName}
          />
          <AuthInput
            type="text"
            name="LastName"
            placeholder='Last name'
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
      </form>
    </AuthLayout>
  )
}

export default RegisterPage
