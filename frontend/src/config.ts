// Temporary front-end configuration constants.
//
// CURRENT_ORG_ID: the core backend requires an `organisation_id` on every
// file call, but the `org` service (which picks the current organisation)
// does not exist yet. So we hardcode organisation 1 in a single place, to
// make it easy to remove once `org` is ready.
//
// TODO(org): replace with the organisation selected in the Topbar once the
// org service is wired in.
export const CURRENT_ORG_ID = 1
