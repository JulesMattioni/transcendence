import { useCallback, useEffect, useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import { UserPlus, Trash2 } from "lucide-react";
import DashboardLayout from "../../components/dashboard/DashboardLayout";
import Modal from "../../components/Modal";
import InviteMemberForm from "../../components/InviteMemberForm";
import { useOrg } from "../../context/orgContextValue";
import { ApiError } from "../../api/client";
import { me, type UserRead } from "../../api/auth";
import {
  listMembers,
  listOrgInvitations,
  updateMemberRole,
  removeMember,
  deleteOrganisation,
  roleName,
  OrgRole,
  type OrgMember,
  type Invitation,
} from "../../api/org";

function memberName(m: OrgMember): string {
  const full = [m.first_name, m.last_name].filter(Boolean).join(" ");
  return full || m.email || `User #${m.user_id}`;
}

function AdminPage() {
  const { isAdmin, loading: orgLoading, currentOrg, reloadOrgs } = useOrg();
  const navigate = useNavigate();

  const [members, setMembers] = useState<OrgMember[]>([]);
  const [invitations, setInvitations] = useState<Invitation[]>([]);
  const [isDeleteOrgOpen, setIsDeleteOrgOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isInviteOpen, setIsInviteOpen] = useState(false);
  const [currentUser, setCurrentUser] = useState<UserRead | null>(null);

  const orgId = currentOrg?.org_id ?? null;

  const load = useCallback(async () => {
    if (orgId === null) return;
    setLoading(true);
    setError(null);
    try {
      const [mem, inv] = await Promise.all([
        listMembers(orgId),
        listOrgInvitations(orgId),
      ]);
      setMembers(mem);
      setInvitations(inv.filter((i) => i.status === "pending"));
    } catch (err) {
      const message =
        err instanceof ApiError ? err.message : "Could not load members.";
      setError(message);
    } finally {
      setLoading(false);
    }
  }, [orgId]);

  useEffect(() => {
    me()
      .then(setCurrentUser)
      .catch(() => setCurrentUser(null));
  }, []);

  useEffect(() => {
    if (orgId === null) return;
    let active = true;

    const run = async () => {
      try {
        const [mem, inv] = await Promise.all([
          listMembers(orgId),
          listOrgInvitations(orgId),
        ]);
        if (!active) return;
        setMembers(mem);
        setInvitations(inv.filter((i) => i.status === "pending"));
        setError(null);
      } catch (err) {
        if (!active) return;
        const message =
          err instanceof ApiError ? err.message : "Could not load members.";
        setError(message);
      } finally {
        if (active) setLoading(false);
      }
    };

    run();
    return () => {
      active = false;
    };
  }, [orgId]);

  async function handleRoleChange(userId: number, newRole: number) {
    if (orgId === null) return;
    try {
      await updateMemberRole(orgId, userId, newRole);
      await load();
    } catch (err) {
      const message =
        err instanceof ApiError ? err.message : "Could not update role.";
      setError(message);
    }
  }

  async function handleRemove(userId: number) {
    if (orgId === null) return;
    try {
      await removeMember(orgId, userId);
      await load();
    } catch (err) {
      const message =
        err instanceof ApiError ? err.message : "Could not remove member.";
      setError(message);
    }
  }

  async function handleDeleteOrg() {
    if (orgId === null) return;
    try {
      await deleteOrganisation(orgId);
      setIsDeleteOrgOpen(false);
      await reloadOrgs();
      navigate("/dashboard");
    } catch (err) {
      const message =
        err instanceof ApiError
          ? err.message
          : "Could not delete organisation.";
      setError(message);
      setIsDeleteOrgOpen(false);
    }
  }

  if (orgLoading) {
    return (
      <DashboardLayout>
        <div className="flex h-full items-center justify-center">
          <p className="text-muted">Loading…</p>
        </div>
      </DashboardLayout>
    );
  }

  if (!isAdmin) {
    return <Navigate to="/dashboard" replace />;
  }

  return (
    <DashboardLayout>
      <div className="flex items-center justify-between">
        <h1 className="font-serif text-2xl font-bold text-black">Admin</h1>
        <div className="flex items-center gap-3">
          <button
            onClick={() => setIsInviteOpen(true)}
            className="inline-flex items-center gap-2 bg-keepr px-4 py-2 font-medium text-white transition-colors duration-200 hover:bg-blue-700"
          >
            Invite member <UserPlus size={15} strokeWidth={2} />
          </button>
          <button
            onClick={() => setIsDeleteOrgOpen(true)}
            className="inline-flex items-center gap-2 bg-red-600 px-4 py-2 font-medium text-white transition-colors duration-200 hover:bg-red-700"
          >
            Delete organisation <Trash2 size={15} strokeWidth={2} />
          </button>
        </div>
      </div>

      {error && <p className="mt-4 text-red-600">{error}</p>}
      {loading && <p className="mt-4 text-muted">Loading…</p>}

      {/* Invitations */}
      {!loading && invitations.length > 0 && (
        <div className="mt-6">
          <h2 className="font-sans text-lg font-semibold text-black">
            Pending invitations
          </h2>
          <ul className="mt-2 border border-gray-200">
            {invitations.map((inv) => (
              <li
                key={inv.id}
                className="flex items-center justify-between px-4 py-3"
              >
                <span className="text-sm text-black">{inv.email}</span>
                <span className="text-sm text-muted">
                  {roleName(inv.role_id)} · pending
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Members*/}
      {!loading && (
        <div className="mt-6">
          <h2 className="font-sans text-lg font-semibold text-black">
            Members
          </h2>
          <ul className="mt-2 bg-white divide-y divide-gray-200 border border-gray-200">
            {members.map((m) => {
              const isSelf = m.user_id === currentUser?.id;
              return (
                <li
                  key={m.user_id}
                  className="flex items-center justify-between gap-3 px-4 py-3"
                >
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-medium text-black">
                      {memberName(m)}
                    </p>
                    {m.email && (
                      <p className="truncate text-xs text-muted">{m.email}</p>
                    )}
                  </div>

                  <select
                    value={m.role_id}
                    disabled={isSelf}
                    onChange={(e) =>
                      handleRoleChange(m.user_id, Number(e.target.value))
                    }
                    className="border border-gray-300 px-2 py-1 text-sm disabled:opacity-50"
                  >
                    <option value={OrgRole.Admin}>Admin</option>
                    <option value={OrgRole.Editor}>Editor</option>
                    <option value={OrgRole.Reader}>Reader</option>
                  </select>

                  <button
                    onClick={() => handleRemove(m.user_id)}
                    disabled={isSelf}
                    className="shrink-0 p-1 text-muted transition-colors duration-200 hover:text-red-600 disabled:opacity-30 disabled:hover:text-muted"
                  >
                    <Trash2 size={18} />
                  </button>
                </li>
              );
            })}
          </ul>
        </div>
      )}

      <Modal
        isOpen={isInviteOpen}
        onClose={() => setIsInviteOpen(false)}
        title="Invite member"
      >
        {orgId !== null && (
          <InviteMemberForm
            orgId={orgId}
            onSuccess={() => {
              setIsInviteOpen(false);
              load();
            }}
          />
        )}
      </Modal>
      <Modal
        isOpen={isDeleteOrgOpen}
        onClose={() => setIsDeleteOrgOpen(false)}
        title="Delete organisation"
      >
        <p className="text-black">
          Are you sure you want to delete{" "}
          <span className="font-medium">{currentOrg?.name}</span>? This
          action cannot be undone.
        </p>
        <div className="mt-6 flex justify-end gap-3">
          <button
            onClick={() => setIsDeleteOrgOpen(false)}
            className="px-4 py-2 text-muted transition-colors duration-200 hover:text-black"
          >
            Cancel
          </button>
          <button
            onClick={handleDeleteOrg}
            className="bg-red-600 px-4 py-2 font-medium text-white transition-colors duration-200 hover:bg-red-700"
          >
            Delete
          </button>
        </div>
      </Modal>
    </DashboardLayout>
  );
}

export default AdminPage;
