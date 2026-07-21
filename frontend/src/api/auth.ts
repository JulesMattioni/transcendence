import { apiFetch } from "./client"
import { disconnectRealtime } from "./realtime"

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

export async function login(payload: UserLogin): Promise<LoginResponse> {
  const data = await apiFetch<LoginResponse>('/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
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
    disconnectRealtime()
  }
}

export function updateProfile(payload: UserUpdate): Promise<UserRead> {
  return apiFetch<UserRead>('/auth/update', {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}
