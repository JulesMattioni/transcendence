import { apiFetch } from "./client";

export const OrgRole = {
  Admin: 1,
  Editor: 2,
  Reader: 3,
} as const

export type OrgRole = (typeof OrgRole)[keyof typeof OrgRole]

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
  return role === OrgRole.Admin
}

export function canWriteFiles(role: number | null | undefined): boolean {
  return role === OrgRole.Admin || role === OrgRole.Editor
}
