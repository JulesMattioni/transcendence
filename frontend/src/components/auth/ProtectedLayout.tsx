import { Outlet } from 'react-router-dom'
import RequireAuth from './RequireAuth'
import { OrgProvider } from '../../context/OrgContext'

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
