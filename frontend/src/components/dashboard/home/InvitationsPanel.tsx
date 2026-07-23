import { useCallback, useEffect, useState } from "react";
import {
  listMyInvitations,
  acceptInvitation,
  declineInvitation,
  getOrganisation,
  roleName,
  type Invitation,
} from "../../../api/org";
import { ApiError } from "../../../api/client";

function InvitationsPanel({ onAccepted }: { onAccepted: () => void }) {
  const [invitations, setInvitations] = useState<Invitation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<number | null>(null);
  const [orgNames, setOrgNames] = useState<Record<number, string>>({});

  const loadOrgNames = useCallback((invs: Invitation[]) => {
    const ids = [...new Set(invs.map((i) => i.org_id))];
    Promise.all(
      ids.map((id) =>
        getOrganisation(id)
          .then((org) => [id, org.name] as const)
          .catch(() => null),
      ),
    ).then((entries) => {
      const names: Record<number, string> = {};
      for (const e of entries) if (e) names[e[0]] = e[1];
      setOrgNames(names);
    });
  }, []);

  const load = useCallback(() => {
    return listMyInvitations()
      .then((data) => {
        setInvitations(data);
        loadOrgNames(data);
      })
      .catch((err) => {
        const message =
          err instanceof ApiError ? err.message : "Could not load invitations.";
        setError(message);
      })
      .finally(() => setLoading(false));
  }, [loadOrgNames]);

  useEffect(() => {
    let active = true;
    listMyInvitations()
      .then((data) => {
        if (!active) return;
        setInvitations(data);
        loadOrgNames(data);
      })
      .catch(() => active && setError("Could not load invitations."))
      .finally(() => active && setLoading(false));
    return () => {
      active = false;
    };
  }, [loadOrgNames]);

  async function handleAccept(id: number) {
    setBusyId(id);
    try {
      await acceptInvitation(id);
      await load();
      onAccepted();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not accept.");
    } finally {
      setBusyId(null);
    }
  }

  async function handleDecline(id: number) {
    setBusyId(id);
    try {
      await declineInvitation(id);
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not decline.");
    } finally {
      setBusyId(null);
    }
  }

  return (
    <div className="flex min-h-0 flex-1 flex-col border border-gray-200 bg-white">
      <div className="shrink-0 border-b border-gray-200 px-4 py-3">
        <h2 className="font-sans text-lg font-semibold text-black">
          Invitations
        </h2>
      </div>
      <div className="min-h-0 flex-1 overflow-y-auto">
        {error && <p className="px-4 py-2 text-sm text-red-600">{error}</p>}
        {loading ? (
          <p className="px-4 py-3 text-sm text-muted">Loading…</p>
        ) : invitations.length === 0 ? (
          <p className="px-4 py-3 text-sm text-muted">
            No pending invitations.
          </p>
        ) : (
          <ul className="divide-y divide-gray-200">
            {invitations.map((inv) => (
              <li key={inv.id} className="px-4 py-3">
                <p className="text-sm text-black">
                  Invitation to join{" "}
                  <span className="font-medium">
                    {orgNames[inv.org_id] ?? "an organisation"}
                  </span>
                </p>
                <p className="text-xs text-muted">
                  Role: {roleName(inv.role_id)}
                </p>
                <div className="mt-2 flex gap-2">
                  <button
                    onClick={() => handleAccept(inv.id)}
                    disabled={busyId === inv.id}
                    className="bg-keepr px-3 py-1 text-sm font-medium text-white transition-colors duration-200 hover:bg-blue-700 disabled:opacity-50"
                  >
                    Accept
                  </button>
                  <button
                    onClick={() => handleDecline(inv.id)}
                    disabled={busyId === inv.id}
                    className="px-3 py-1 text-sm text-muted transition-colors duration-200 hover:text-red-600 disabled:opacity-50"
                  >
                    Decline
                  </button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}

export default InvitationsPanel;
