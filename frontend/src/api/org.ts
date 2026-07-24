import { apiFetch } from "./client";

/** Organisation role ids, mirrored from the backend's role table. */
export const OrgRole = {
  Admin: 1,
  Editor: 2,
  Reader: 3,
} as const;

export type OrgRole = (typeof OrgRole)[keyof typeof OrgRole];

export interface OrgMembership {
  org_id: number;
  name: string;
  role: number;
}

interface UserOrganisationsResponse {
  user_id: number;
  organisation: OrgMembership[];
}

export interface OrganisationRead {
  id: number;
  name: string;
}

/** List the organisations a user belongs to, with their role in each. */
export async function listMyOrgs(userId: number): Promise<OrgMembership[]> {
  const data = await apiFetch<UserOrganisationsResponse>(
    `/org/organisations/users/${userId}/organisations`,
  );
  return data.organisation ?? [];
}

/** Create a new organisation; the creator becomes its admin. */
export async function createOrg(name: string): Promise<OrganisationRead> {
  return apiFetch<OrganisationRead>("/org/organisations/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name }),
  });
}

/** Fetch a single organisation's details. */
export async function getOrganisation(orgId: number): Promise<OrganisationRead> {
  return apiFetch<OrganisationRead>(`/org/organisations/${orgId}`);
}

/** Whether the role is admin. */
export function isAdminRole(role: number | null | undefined): boolean {
  return role === OrgRole.Admin;
}

/** Whether the role may manage members (invite, change roles, remove). */
export function canManageMembers(role: number | null | undefined): boolean {
  return role === OrgRole.Admin;
}

/** Whether the role may create, edit or delete files. */
export function canWriteFiles(role: number | null | undefined): boolean {
  return role === OrgRole.Admin || role === OrgRole.Editor;
}

export interface OrgMember {
  user_id: number;
  role_id: number;
  email: string | null;
  first_name: string | null;
  last_name: string | null;
}

/** List an organisation's members with their roles and profile info. */
export async function listMembers(orgId: number): Promise<OrgMember[]> {
  return apiFetch<OrgMember[]>(`/org/organisations/${orgId}/users`);
}

/** Change a member's role within an organisation. */
export async function updateMemberRole(
  orgId: number,
  userId: number,
  newRole: number,
): Promise<void> {
  await apiFetch<unknown>(
    `/org/organisations/${orgId}/users/${userId}?new_role=${newRole}`,
    { method: "PATCH" },
  );
}

/** Remove a member from an organisation. */
export async function removeMember(
  orgId: number,
  userId: number,
): Promise<void> {
  await apiFetch<void>(`/org/organisations/${orgId}/users/${userId}`, {
    method: "DELETE",
  });
}

export interface Invitation {
  id: number;
  org_id: number;
  invited_user_id: number;
  email: string;
  first_name: string | null;
  last_name: string | null;
  role_id: number;
  status: string;
}

/** Invite an existing user to an organisation by email, with a role. */
export async function inviteMember(
  orgId: number,
  email: string,
  roleId: number,
): Promise<Invitation> {
  return apiFetch<Invitation>(`/org/organisations/${orgId}/invitations`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, role_id: roleId }),
  });
}

/** List the invitations sent for an organisation. */
export async function listOrgInvitations(orgId: number): Promise<Invitation[]> {
  return apiFetch<Invitation[]>(`/org/organisations/${orgId}/invitations`);
}

/** Map a role id to its display name, or "Unknown". */
export function roleName(roleId: number): string {
  if (roleId === OrgRole.Admin) return "Admin";
  if (roleId === OrgRole.Editor) return "Editor";
  if (roleId === OrgRole.Reader) return "Reader";
  return "Unknown";
}

/** List invitations addressed to the current user. */
export async function listMyInvitations(): Promise<Invitation[]> {
  return apiFetch<Invitation[]>(`/org/invitations/me`);
}

/** Accept an invitation, joining the organisation. */
export async function acceptInvitation(
  invitationId: number,
): Promise<Invitation> {
  return apiFetch<Invitation>(`/org/invitations/${invitationId}/accept`, {
    method: "POST",
  });
}

/** Decline an invitation. */
export async function declineInvitation(
  invitationId: number,
): Promise<Invitation> {
  return apiFetch<Invitation>(`/org/invitations/${invitationId}/decline`, {
    method: "POST",
  });
}

export interface Connection {
  user_id: number;
  email: string | null;
  first_name: string | null;
  last_name: string | null;
  org_ids: number[];
}

/**
 * Build the current user's connections: everyone who shares at least one
 * organisation with them, deduplicated across orgs and annotated with the
 * shared org ids. Member lookups that fail are skipped, not fatal.
 */
export async function listMyConnections(
  myUserId: number,
): Promise<Connection[]> {
  const orgs = await listMyOrgs(myUserId);

  const memberLists = await Promise.all(
    orgs.map((o) =>
      listMembers(o.org_id)
        .then((members) => ({ orgId: o.org_id, members }))
        .catch(() => ({ orgId: o.org_id, members: [] })),
    ),
  );

  const byUser = new Map<number, Connection>();
  for (const { orgId, members } of memberLists) {
    for (const m of members) {
      if (m.user_id === myUserId) continue;
      const existing = byUser.get(m.user_id);
      if (existing) {
        if (!existing.org_ids.includes(orgId)) existing.org_ids.push(orgId);
      } else {
        byUser.set(m.user_id, {
          user_id: m.user_id,
          email: m.email,
          first_name: m.first_name,
          last_name: m.last_name,
          org_ids: [orgId],
        });
      }
    }
  }

  return Array.from(byUser.values());
}

/** Delete an organisation. */
export async function deleteOrganisation(orgId: number): Promise<void> {
  await apiFetch<void>(`/org/organisations/${orgId}`, {
    method: "DELETE",
  });
}
