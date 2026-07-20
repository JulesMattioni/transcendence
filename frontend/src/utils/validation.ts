const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

export function validateEmail(email: string): string | null {
  if (!email.trim()) return 'Email is required.'
  if (!EMAIL_RE.test(email)) return 'Please enter a valid email address.'
  return null
}

export function validateRequired(value: string, label: string): string | null {
  if (!value.trim()) return `${label} is required.`
  return null
}

export function validatePasswordMatch(
  password: string,
  confirm: string,
): string | null {
  if (password !== confirm) return 'Passwords do not match.'
  return null
}

export interface PasswordRule {
  label: string
  met: boolean
}

export function checkPasswordRules(password: string): PasswordRule[] {
  return [
    { label: 'At least 8 characters', met: password.length >= 8 },
    { label: 'One uppercase letter', met: /[A-Z]/.test(password) },
    { label: 'One lowercase letter', met: /[a-z]/.test(password) },
    { label: 'One number', met: /[0-9]/.test(password) },
    { label: 'One special character', met: /[^A-Za-z0-9]/.test(password) },
  ]
}

export function isPasswordValid(password: string): boolean {
  return checkPasswordRules(password).every((rule) => rule.met)
}
