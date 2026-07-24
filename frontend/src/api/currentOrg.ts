let currentOrgId: number | null = null;

/**
 * Holds the currently selected organisation id in a module-level
 * variable so the API layer can default to it without threading it
 * through every call. The OrgContext keeps this in sync with React state.
 */

/** Return the selected organisation id, or null when none is selected. */
export function getCurrentOrgId(): number | null {
  return currentOrgId;
}

/** Set (or clear) the selected organisation id. */
export function setCurrentOrgId(id: number | null): void {
  currentOrgId = id;
}

/**
 * Return the selected organisation id, throwing when none is selected.
 * Used as the default argument of org-scoped API calls.
 */
export function requireCurrentOrgId(): number {
  if (currentOrgId === null) {
    throw new Error("No organisation selected");
  }
  return currentOrgId;
}
