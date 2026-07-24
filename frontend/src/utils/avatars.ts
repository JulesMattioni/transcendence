/**
 * Eagerly import every bundled profile picture and index it by the
 * numeric id in its filename, so avatars can be looked up by avatar_id.
 */
const modules = import.meta.glob<{ default: string }>(
  '../assets/profile_pictures/*.png',
  { eager: true },
)

const avatarById: Record<number, string> = {}
for (const [path, mod] of Object.entries(modules)) {
  const match = path.match(/\/(\d+)\.png$/)
  if (match) {
    avatarById[Number(match[1])] = mod.default
  }
}

const FALLBACK_ID = 1

/**
 * Resolve an avatar id to its image URL, falling back to a default
 * avatar when the id is missing or unknown.
 */
export function getAvatarUrl(avatarId: number | null | undefined): string {
  if (avatarId != null && avatarById[avatarId]) {
    return avatarById[avatarId]
  }
  return avatarById[FALLBACK_ID] ?? Object.values(avatarById)[0]
}

/** Sorted list of avatar ids available for selection. */
export const availableAvatarIds: number[] = Object.keys(avatarById)
  .map(Number)
  .sort((a, b) => a - b)
