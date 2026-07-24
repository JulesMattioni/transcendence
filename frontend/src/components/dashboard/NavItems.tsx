import { Home, FileText, Shield, MessageCircle } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'

export interface NavItem {
  to: string
  label: string
  icon: LucideIcon
  adminOnly?: boolean
}


/**
 * Dashboard navigation entries shared by the sidebar and bottom nav.
 * Items flagged adminOnly are shown only to organisation admins.
 */
export const navItems: NavItem[] = [
  { to: '/dashboard', label: 'Home', icon: Home },
  { to: '/dashboard/files', label: 'Files', icon: FileText },
  { to: '/dashboard/chat', label: 'Chat', icon: MessageCircle },
  { to: '/dashboard/admin', label: 'Admin', icon: Shield, adminOnly: true },
]
