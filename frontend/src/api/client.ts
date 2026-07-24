const API_BASE = '/api'

/**
 * Error thrown by the API layer, carrying the HTTP status code alongside
 * a human-readable message extracted from the response.
 */
export class ApiError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

interface ApiFetchConfig {
  skipAuthRefresh?: boolean
}

/**
 * Central fetch wrapper for the API: attaches the bearer token, parses
 * the JSON body, and throws an ApiError on failure. On a 401 it
 * transparently refreshes the token once and retries, or clears the
 * session and redirects to login if the refresh fails.
 */
export async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
  config: ApiFetchConfig = {},
): Promise<T> {
  let response = await doFetch(path, options)

  if (response.status === 401 && !config.skipAuthRefresh) {
    const refreshed = await tryRefresh()
    if (refreshed) {
      response = await doFetch(path, options)
    } else {
      clearLocalSession()
      redirectToLogin()
    }
  }

  if (!response.ok) {
    const detail = await extractError(response)
    throw new ApiError(response.status, detail)
  }

  if (response.status === 204) {
    return undefined as T
  }

  const text = await response.text()
  if (!text) {
    return undefined as T
  }
  return JSON.parse(text) as T
}

/**
 * Perform a single fetch against the API base, injecting the current
 * access token as a bearer header when one is stored.
 */
async function doFetch(path: string, options: RequestInit): Promise<Response> {
  const headers = new Headers(options.headers)
  const token = localStorage.getItem('access_token')
  if (token) {
    headers.set('Authorization', `Bearer ${token}`)
  }
  return fetch(`${API_BASE}${path}`, { ...options, headers })
}

let refreshInFlight: Promise<boolean> | null = null

/**
 * Refresh the access token, deduplicating concurrent callers so several
 * 401s triggered at once share a single refresh request.
 */
function tryRefresh(): Promise<boolean> {
  if (!refreshInFlight) {
    refreshInFlight = doRefresh().finally(() => {
      refreshInFlight = null
    })
  }
  return refreshInFlight
}

/**
 * Exchange the stored refresh token for a new token pair, persisting it
 * on success. Returns whether the refresh succeeded.
 */
async function doRefresh(): Promise<boolean> {
  const refreshToken = localStorage.getItem('refresh_token')
  if (!refreshToken) return false

  const response = await fetch(
    `${API_BASE}/auth/refresh?refresh_token=${encodeURIComponent(refreshToken)}`,
    { method: 'POST' },
  )
  if (!response.ok) return false

  try {
    const tokens = await response.json()
    if (tokens?.access_token && tokens?.refresh_token) {
      localStorage.setItem('access_token', tokens.access_token)
      localStorage.setItem('refresh_token', tokens.refresh_token)
      return true
    }
  } catch {
    return false
  }
  return false
}

/** Drop the stored token pair, ending the local session. */
function clearLocalSession(): void {
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
}

/** Navigate to the login page unless already there. */
function redirectToLogin(): void {
  if (window.location.pathname !== '/login') {
    window.location.assign('/login')
  }
}

/**
 * Pull a readable error message out of a failed response, handling both
 * the string and the FastAPI validation-array shapes of `detail`, with a
 * status-based fallback.
 */
async function extractError(response: Response): Promise<string> {
  try {
    const body = await response.json()
    const detail = body?.detail
    if (typeof detail === 'string') {
      return detail
    }
    if (Array.isArray(detail) && detail.length > 0) {
      return detail[0]?.msg ?? 'Validation error'
    }
  } catch {
    return `Request failed with status ${response.status}`
  }
  return `Request failed with status ${response.status}`
}
