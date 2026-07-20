import { Check, X } from 'lucide-react'
import { checkPasswordRules } from '../../utils/validation'

function PasswordChecklist({ password }: { password: string }) {
  if (password.length === 0) return null

  const rules = checkPasswordRules(password)

  return (
    <ul className="space-y-1">
      {rules.map((rule) => (
        <li
          key={rule.label}
          className={`flex items-center gap-2 text-xs ${
            rule.met ? 'text-green-600' : 'text-red-500'
          }`}
        >
          {rule.met ? <Check size={14} /> : <X size={14} />}
          {rule.label}
        </li>
      ))}
    </ul>
  )
}

export default PasswordChecklist
