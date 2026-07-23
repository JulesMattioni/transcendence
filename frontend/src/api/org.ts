import { apiFetch } from "./client";

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

export async function listMyOrgs(userId: number): Promise<OrgMembership[]> {
  const data = await apiFetch<UserOrganisationsResponse>(
    `/org/organisations/users/${userId}/organisations`,
  );
  return data.organisation ?? [];
}

export async function createOrg(name: string): Promise<OrganisationRead> {
  return apiFetch<OrganisationRead>("/org/organisations/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name }),
  });
}

export function isAdminRole(role: number | null | undefined): boolean {
  return role === OrgRole.Admin;
}

export function canManageMembers(role: number | null | undefined): boolean {
  return role === OrgRole.Admin;
}

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

export async function listMembers(orgId: number): Promise<OrgMember[]> {
  return apiFetch<OrgMember[]>(`/org/organisations/${orgId}/users`);
}

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

export async function listOrgInvitations(orgId: number): Promise<Invitation[]> {
  return apiFetch<Invitation[]>(`/org/organisations/${orgId}/invitations`);
}

export function roleName(roleId: number): string {
  if (roleId === OrgRole.Admin) return "Admin";
  if (roleId === OrgRole.Editor) return "Editor";
  if (roleId === OrgRole.Reader) return "Reader";
  return "Unknown";
}
