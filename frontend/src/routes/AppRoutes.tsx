import { Routes, Route } from 'react-router-dom'
import LandingPage from '../pages/LandingPage'
import LoginPage from '../pages/LoginPage'
import RegisterPage from '../pages/RegisterPage'
import HomePage from '../pages/dashboard/HomePage'
import FilesPage from '../pages/dashboard/FilesPage'
import AdminPage from '../pages/dashboard/AdminPage'


function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/dashboard" element={<HomePage />} />
      <Route path="/dashboard/files" element={<FilesPage />} />
      <Route path="/dashboard/admin" element={<AdminPage />} />
    </Routes>
  )
}

export default AppRoutes
