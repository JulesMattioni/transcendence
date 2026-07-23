import { Routes, Route } from "react-router-dom";
import LandingPage from "../pages/LandingPage";
import LoginPage from "../pages/LoginPage";
import RegisterPage from "../pages/RegisterPage";
import HomePage from "../pages/dashboard/HomePage";
import FilesPage from "../pages/dashboard/FilesPage";
import AdminPage from "../pages/dashboard/AdminPage";
import ChatPage from "../pages/dashboard/ChatPage";
import UserPage from "../pages/dashboard/UserPage";
import ProtectedLayout from "../components/auth/ProtectedLayout";
import PrivacyPolicyPage from "../pages/PrivacyPolicyPage";
import TermsOfServicePage from "../pages/TermsOfServicePage";
import OAuthCallbackPage from "../pages/OAuthCallbackPage";

function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/oauth/callback" element={<OAuthCallbackPage />} />

      <Route path="/dashboard" element={<ProtectedLayout />}>
        <Route index element={<HomePage />} />
        <Route path="files" element={<FilesPage />} />
        <Route path="admin" element={<AdminPage />} />
        <Route path="chat" element={<ChatPage />} />
        <Route path="user" element={<UserPage />} />
      </Route>

      <Route path="/privacy" element={<PrivacyPolicyPage />} />
      <Route path="/terms" element={<TermsOfServicePage />} />
    </Routes>
  );
}

export default AppRoutes;
