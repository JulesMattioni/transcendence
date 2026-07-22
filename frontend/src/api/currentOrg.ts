let currentOrgId: number | null = null;

export function getCurrentOrgId(): number | null {
  return currentOrgId;
}

export function setCurrentOrgId(id: number | null): void {
  currentOrgId = id;
}

export function requireCurrentOrgId(): number {
  if (currentOrgId === null) {
    throw new Error("No organisation selected");
  }
  return currentOrgId;
}
