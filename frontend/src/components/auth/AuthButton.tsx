import type { ReactNode } from 'react'
import { Loader2 } from 'lucide-react'

interface AuthButtonProps {
  children: ReactNode
  type?: 'submit' | 'button'
  variant?: 'primary' | 'outline'
  loading?: boolean
  icon?: ReactNode
  onClick?: () => void
}

const variantClasses = {
  primary:
    'bg-keepr text-white hover:bg-blue-700',
  outline:
    'border border-gray-200 bg-white text-ink hover:bg-gray-50',
}

function AuthButton({
  children,
  type = 'submit',
  variant = 'primary',
  loading = false,
  icon,
  onClick,
}: AuthButtonProps) {
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={loading}
      className={`flex w-full items-center justify-center gap-2 px-6 py-3 text-sm font-regular transition-colors disabled:cursor-not-allowed disabled:opacity-60 ${variantClasses[variant]}`}
    >
      {children}
      {loading ? (
        <Loader2 size={18} className="animate-spin" />
      ) : (
        icon
      )}
    </button>
  )
}

export default AuthButton
