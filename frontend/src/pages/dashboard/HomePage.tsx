import { useEffect, useState } from "react";
import { Plus } from "lucide-react";
import DashboardLayout from "../../components/dashboard/DashboardLayout";
import Modal from "../../components/Modal";
import CreateOrgForm from "../../components/CreateOrgForm";
import ConnectionsPanel from "../../components/dashboard/home/ConnectionsPanel";
import AuditPanel from "../../components/dashboard/home/AuditPanel";
import InvitationsPanel from "../../components/dashboard/home/InvitationsPanel";
import AnalyticsPanel from "../../components/dashboard/home/AnalyticsPanel";
import { useOrg } from "../../context/orgContextValue";
import { me } from "../../api/auth";

function HomePage() {
  const { reloadOrgs, setCurrentOrg, currentOrg } = useOrg();
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [myUserId, setMyUserId] = useState<number | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    let active = true;
    me()
      .then((u) => active && setMyUserId(u.id))
      .catch(() => active && setMyUserId(null));
    return () => {
      active = false;
    };
  }, []);

  return (
    <DashboardLayout>
      <div className="flex items-center justify-between">
        <h1 className="font-serif text-2xl font-bold text-black">Home</h1>
        <button
          onClick={() => setIsCreateOpen(true)}
          className="inline-flex items-center gap-2 rounded bg-keepr px-4 py-2 font-medium text-white transition-colors duration-200 hover:bg-blue-700"
        >
          Create organisation <Plus size={15} strokeWidth={2} />
        </button>
      </div>

      <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Connections */}
        <div>
          {myUserId !== null && (
            <ConnectionsPanel key={refreshKey} myUserId={myUserId} />
          )}
        </div>

        {/* Audit + Invit */}
        <div className="flex flex-col gap-6 lg:h-96">
          <AuditPanel />
          <InvitationsPanel
            key={refreshKey}
            onAccepted={async () => {
              await reloadOrgs();
              setRefreshKey((k) => k + 1);
            }}
          />
        </div>
      </div>

      {/* Analytics dashboard for the selected organisation */}
      {currentOrg && (
        <AnalyticsPanel key={currentOrg.org_id} orgId={currentOrg.org_id} />
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
            setRefreshKey((k) => k + 1);
          }}
        />
      </Modal>
    </DashboardLayout>
  );
}

export default HomePage;
