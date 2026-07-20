import { Check, X } from 'lucide-react'

interface PasswordMatchProps {
  password: string
  confirm: string
}

function PasswordMatch({ password, confirm }: PasswordMatchProps) {
  if (confirm.length <= 1) return null

  const match = password === confirm

  return (
    <p
      className={`flex items-center gap-2 text-xs ${
        match ? 'text-green-600' : 'text-red-500'
      }`}
    >
      {match ? <Check size={14} /> : <X size={14} />}
      {match ? 'Passwords match' : 'Passwords do not match'}
    </p>
  )
}

export default PasswordMatch
