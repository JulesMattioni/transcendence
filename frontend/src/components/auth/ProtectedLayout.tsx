import { Outlet } from 'react-router-dom'
import RequireAuth from './RequireAuth'
import { OrgProvider } from '../../context/OrgContext'

/**
 * Layout for the authenticated area: gates access behind RequireAuth,
 * provides the organisation context, and renders the matched child route.
 */
function ProtectedLayout() {
  return (
    <RequireAuth>
      <OrgProvider>
        <Outlet />
      </OrgProvider>
    </RequireAuth>
  )
}

export default ProtectedLayout
