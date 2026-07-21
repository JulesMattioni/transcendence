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

export function getAvatarUrl(avatarId: number | null | undefined): string {
  if (avatarId != null && avatarById[avatarId]) {
    return avatarById[avatarId]
  }
  return avatarById[FALLBACK_ID] ?? Object.values(avatarById)[0]
}

export const availableAvatarIds: number[] = Object.keys(avatarById)
  .map(Number)
  .sort((a, b) => a - b)
