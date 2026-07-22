import { useState } from "react";
import { Plus } from "lucide-react";
import DashboardLayout from "../../components/dashboard/DashboardLayout";
import Modal from "../../components/Modal";
import CreateOrgForm from "../../components/CreateOrgForm";
import { useOrg } from "../../context/orgContextValue";

function HomePage() {
  const { orgs, currentOrg, loading, reloadOrgs, setCurrentOrg } = useOrg();
  const [isCreateOpen, setIsCreateOpen] = useState(false);

  return (
    <DashboardLayout>
      <div className="flex items-center justify-between">
        <h1 className="font-serif text-2xl font-bold text-black">Home</h1>
        <button
          onClick={() => setIsCreateOpen(true)}
          className="inline-flex items-center gap-2 bg-keepr px-4 py-2 font-medium text-white transition-colors duration-200 hover:bg-blue-700"
        >
          Create organisation <Plus size={15} strokeWidth={2} />
        </button>
      </div>

      {loading && <p className="mt-4 text-muted">Loading…</p>}

      {!loading && orgs.length === 0 && (
        <p className="mt-4 text-muted">
          You don't belong to any organisation yet. Create one to get started.
        </p>
      )}

      {!loading && orgs.length > 0 && (
        <p className="mt-4 text-muted">
          Current organisation:{" "}
          <span className="font-medium text-black">
            {currentOrg?.name ?? "—"}
          </span>
        </p>
      )}

      <Modal
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        title="Create organisation"
      >
        <CreateOrgForm
          onSuccess={async (org) => {
            setIsCreateOpen(false);
            await reloadOrgs();
            setCurrentOrg(org.id);
          }}
        />
      </Modal>
    </DashboardLayout>
  );
}

export default HomePage;
