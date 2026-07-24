import {
  useEffect,
  useState,
  useCallback,
  type ReactNode,
} from 'react'
import { me } from '../api/auth'
import { listMyOrgs, isAdminRole, type OrgMembership, canWriteFiles } from '../api/org'
import { setCurrentOrgId } from '../api/currentOrg'
import { OrgContext, type OrgContextValue } from './orgContextValue'

const STORAGE_KEY = 'current_org_id'

/**
 * Provides the current organisation state to the app: loads the user's
 * organisations, restores the last selected one from local storage,
 * derives the current role and permissions, and mirrors the selection
 * into the API layer so org-scoped calls default to it.
 */
export function OrgProvider({ children }: { children: ReactNode }) {
  const [orgs, setOrgs] = useState<OrgMembership[]>([])
  const [currentOrgId, setCurrentOrgIdState] = useState<number | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const pickCurrent = useCallback((list: OrgMembership[]): number | null => {
    const stored = Number(localStorage.getItem(STORAGE_KEY))
    if (stored && list.some((o) => o.org_id === stored)) return stored
    return list.length > 0 ? list[0].org_id : null
  }, [])

  const reloadOrgs = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const user = await me()
      const list = await listMyOrgs(user.id)
      setOrgs(list)
      setCurrentOrgIdState(pickCurrent(list))
    } catch {
      setError('Could not load organisations.')
      setOrgs([])
      setCurrentOrgIdState(null)
    } finally {
      setLoading(false)
    }
  }, [pickCurrent])

  useEffect(() => {
    let active = true

    const load = async () => {
      try {
        const user = await me()
        const list = await listMyOrgs(user.id)
        if (!active) return
        setOrgs(list)
        setCurrentOrgIdState(pickCurrent(list))
      } catch {
        if (!active) return
        setError('Could not load organisations.')
        setOrgs([])
        setCurrentOrgIdState(null)
      } finally {
        if (active) setLoading(false)
      }
    }

    load()
    return () => {
      active = false
    }
  }, [pickCurrent])

  useEffect(() => {
    setCurrentOrgId(currentOrgId)
    if (currentOrgId !== null) {
      localStorage.setItem(STORAGE_KEY, String(currentOrgId))
    }
  }, [currentOrgId])

  const setCurrentOrg = useCallback((orgId: number) => {
    setCurrentOrgIdState(orgId)
  }, [])

  const currentOrg = orgs.find((o) => o.org_id === currentOrgId) ?? null
  const role = currentOrg?.role ?? null

  const value: OrgContextValue = {
    orgs,
    currentOrg,
    role,
    isAdmin: isAdminRole(role),
    canWrite: canWriteFiles(role),
    loading,
    error,
    setCurrentOrg,
    reloadOrgs,
  }

  return <OrgContext.Provider value={value}>{children}</OrgContext.Provider>
}
