import { apiFetch, ApiError } from "./client"

const ACCESS_KEY = 'access_token'
const REFRESH_KEY = 'refresh_token'

export interface UserCreate {
  first_name: string
  last_name: string
  email: string
  password: string
}

export interface UserLogin {
  email: string
  password: string
}

export interface UserRead {
  id: number
  first_name: string
  last_name: string
  email: string
  location: string | null
  avatar_id: number
  is_2fa_enabled: boolean
}

export interface UserUpdate {
  location: string
  avatar_id: number
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface LoginResponse {
  tokens: TokenResponse
  user: UserRead
}

export function getAccessToken(): string | null {
  return localStorage.getItem(ACCESS_KEY)
}

export function getRefreshToken(): string | null {
  return localStorage.getItem(REFRESH_KEY)
}

export function saveTokens(access: string, refresh: string): void {
  localStorage.setItem(ACCESS_KEY, access)
  localStorage.setItem(REFRESH_KEY, refresh)
}

export function clearSession(): void {
  localStorage.removeItem(ACCESS_KEY)
  localStorage.removeItem(REFRESH_KEY)
}

export async function signup(payload: UserCreate): Promise<LoginResponse> {
  const data = await apiFetch<LoginResponse>('/auth/signup', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  saveTokens(data.tokens.access_token, data.tokens.refresh_token)
  return data
}

export async function login(payload: UserLogin): Promise<LoginResult> {
  const data = await apiFetch<LoginResponse | TwoFactorRequired>('/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })

  if ('pending_token' in data) {
    return { kind: '2fa_required', pendingToken: data.pending_token }
  }

  saveTokens(data.tokens.access_token, data.tokens.refresh_token)
  return { kind: 'success', data }
}

export async function loginVerify2fa(
  pendingToken: string,
  code: string,
): Promise<LoginResponse> {
  const response = await fetch('/api/auth/login/2fa/verify', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${pendingToken}`,
    },
    body: JSON.stringify({ code }),
  })

  if (!response.ok) {
    let detail = 'Invalid code'
    try {
      const body = await response.json()
      if (typeof body?.detail === 'string') detail = body.detail
    } catch {
      detail = `Request failed with status ${response.status}`
    }
    throw new ApiError(response.status, detail)
  }

  const data = (await response.json()) as LoginResponse
  saveTokens(data.tokens.access_token, data.tokens.refresh_token)
  return data
}


export function me(): Promise<UserRead> {
  return apiFetch<UserRead>('/auth/me')
}

export async function refresh(): Promise<TokenResponse> {
  const token = getRefreshToken()
  const data = await apiFetch<TokenResponse>(
    `/auth/refresh?refresh_token=${encodeURIComponent(token ?? '')}`,
    { method: 'POST' },
  )
  saveTokens(data.access_token, data.refresh_token)
  return data
}

export async function logout(): Promise<void> {
  const token = getRefreshToken()
  try {
    await apiFetch<void>(
      `/auth/logout?refresh_token=${encodeURIComponent(token ?? '')}`,
      { method: 'POST' },
    )
  } finally {
    clearSession()
  }
}

export function updateProfile(payload: UserUpdate): Promise<UserRead> {
  return apiFetch<UserRead>('/auth/update', {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export interface TwoFactorCredentials {
  secret: string
  otpauth_uri: string
}

export function enable2fa(): Promise<TwoFactorCredentials> {
  return apiFetch<TwoFactorCredentials>('/auth/2fa/enable', {
    method: 'POST',
  })
}

export function verify2fa(code: string): Promise<void> {
  return apiFetch<void>('/auth/2fa/enable/verify', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ code }),
  })
}

export function disable2fa(): Promise<UserRead> {
  return apiFetch<UserRead>('/auth/2fa/disable', {
    method: 'POST',
  })
}

export interface TwoFactorRequired {
  pending_token: string
}

export type LoginResult =
  | { kind: 'success'; data: LoginResponse }
  | { kind: '2fa_required'; pendingToken: string }
