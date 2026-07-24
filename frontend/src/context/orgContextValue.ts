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

/** React context holding the current organisation state and actions. */
export const OrgContext = createContext<OrgContextValue | undefined>(undefined)

/**
 * Access the organisation context, throwing if used outside an
 * OrgProvider.
 */
export function useOrg(): OrgContextValue {
  const ctx = useContext(OrgContext)
  if (!ctx) {
    throw new Error('useOrg must be used within an OrgProvider')
  }
  return ctx
}
