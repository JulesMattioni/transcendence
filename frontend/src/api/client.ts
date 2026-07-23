const API_BASE = '/api'

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

async function doFetch(path: string, options: RequestInit): Promise<Response> {
  const headers = new Headers(options.headers)
  const token = localStorage.getItem('access_token')
  if (token) {
    headers.set('Authorization', `Bearer ${token}`)
  }
  return fetch(`${API_BASE}${path}`, { ...options, headers })
}

let refreshInFlight: Promise<boolean> | null = null

function tryRefresh(): Promise<boolean> {
  if (!refreshInFlight) {
    refreshInFlight = doRefresh().finally(() => {
      refreshInFlight = null
    })
  }
  return refreshInFlight
}

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

function clearLocalSession(): void {
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
}

function redirectToLogin(): void {
  if (window.location.pathname !== '/login') {
    window.location.assign('/login')
  }
}

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
