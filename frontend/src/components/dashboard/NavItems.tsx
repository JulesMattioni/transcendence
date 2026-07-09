import { Home, FileText, Shield } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'

export interface NavItem {
  to: string
  label: string
  icon: LucideIcon
}

export const navItems: NavItem[] = [
  { to: '/dashboard', label: 'Home', icon: Home },
  { to: '/dashboard/files', label: 'Files', icon: FileText },
  { to: '/dashboard/admin', label: 'Admin', icon: Shield },
]
