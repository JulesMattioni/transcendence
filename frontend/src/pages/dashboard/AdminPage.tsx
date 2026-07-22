import { Navigate } from "react-router-dom";
import DashboardLayout from "../../components/dashboard/DashboardLayout";
import { useOrg } from "../../context/orgContextValue";

function AdminPage() {
  const { isAdmin, loading } = useOrg();

  if (loading) {
    return (
      <DashboardLayout>
        <p className="text-muted">Loading…</p>
      </DashboardLayout>
    );
  }

  if (!isAdmin) {
    return <Navigate to="/dashboard" replace />;
  }

  return (
    <DashboardLayout>
      <h1 className="font-serif text-2xl font-bold text-black">Admin</h1>
      <p className="mt-2 text-muted">Admin content will go here.</p>
    </DashboardLayout>
  );
}

export default AdminPage;
