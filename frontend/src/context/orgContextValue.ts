import { createContext, useContext } from 'react'
import type { OrgMembership } from '../api/org'

export interface OrgContextValue {
  orgs: OrgMembership[]
  currentOrg: OrgMembership | null
  role: number | null
  isAdmin: boolean
  canWrite: boolean
  loading: boolean
  error: string | null
  setCurrentOrg: (orgId: number) => void
  reloadOrgs: () => Promise<void>
}

export const OrgContext = createContext<OrgContextValue | undefined>(undefined)

export function useOrg(): OrgContextValue {
  const ctx = useContext(OrgContext)
  if (!ctx) {
    throw new Error('useOrg must be used within an OrgProvider')
  }
  return ctx
}
