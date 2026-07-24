import { apiFetch, ApiError } from "./client";
import { disconnectRealtime } from "./realtime";

const ACCESS_KEY = "access_token";
const REFRESH_KEY = "refresh_token";

export interface UserCreate {
  first_name: string;
  last_name: string;
  email: string;
  password: string;
}

export interface UserLogin {
  email: string;
  password: string;
}

export interface UserRead {
  id: number;
  first_name: string;
  last_name: string;
  email: string;
  location: string | null;
  avatar_id: number;
  is_2fa_enabled: boolean;
}

export interface UserUpdate {
  location: string;
  avatar_id: number;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface LoginResponse {
  tokens: TokenResponse;
  user: UserRead;
}

/** Return the stored access token, or null when signed out. */
export function getAccessToken(): string | null {
  return localStorage.getItem(ACCESS_KEY);
}

/** Return the stored refresh token, or null when signed out. */
export function getRefreshToken(): string | null {
  return localStorage.getItem(REFRESH_KEY);
}

/** Persist a new access/refresh token pair to local storage. */
export function saveTokens(access: string, refresh: string): void {
  localStorage.setItem(ACCESS_KEY, access);
  localStorage.setItem(REFRESH_KEY, refresh);
}

/** Remove the stored tokens, ending the local session. */
export function clearSession(): void {
  localStorage.removeItem(ACCESS_KEY);
  localStorage.removeItem(REFRESH_KEY);
}

/**
 * Register a new account and immediately sign in, persisting the returned
 * tokens.
 */
export async function signup(payload: UserCreate): Promise<LoginResponse> {
  const data = await apiFetch<LoginResponse>("/auth/signup", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  saveTokens(data.tokens.access_token, data.tokens.refresh_token);
  return data;
}

/**
 * Sign in with email and password. Either completes the login and stores
 * the tokens, or reports that a second factor is required so the caller
 * can prompt for the 2FA code.
 */
export async function login(payload: UserLogin): Promise<LoginResult> {
  const data = await apiFetch<LoginResponse | TwoFactorRequired>(
    "/auth/login",
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    },
  );

  if ("pending_token" in data) {
    return { kind: "2fa_required", pendingToken: data.pending_token };
  }

  saveTokens(data.tokens.access_token, data.tokens.refresh_token);
  return { kind: "success", data };
}

/**
 * Complete a 2FA-gated login by verifying the code against the pending
 * token, storing the tokens on success. Bypasses apiFetch because the
 * pending token, not the access token, must be sent as the bearer.
 */
export async function loginVerify2fa(
  pendingToken: string,
  code: string,
): Promise<LoginResponse> {
  const response = await fetch("/api/auth/login/2fa/verify", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${pendingToken}`,
    },
    body: JSON.stringify({ code }),
  });

  if (!response.ok) {
    let detail = "Invalid code";
    try {
      const body = await response.json();
      if (typeof body?.detail === "string") detail = body.detail;
    } catch {
      detail = `Request failed with status ${response.status}`;
    }
    throw new ApiError(response.status, detail);
  }

  const data = (await response.json()) as LoginResponse;
  saveTokens(data.tokens.access_token, data.tokens.refresh_token);
  return data;
}

/** Fetch the currently authenticated user's profile. */
export function me(): Promise<UserRead> {
  return apiFetch<UserRead>("/auth/me");
}

/** Refresh the token pair from the stored refresh token and persist it. */
export async function refresh(): Promise<TokenResponse> {
  const token = getRefreshToken();
  const data = await apiFetch<TokenResponse>(
    `/auth/refresh?refresh_token=${encodeURIComponent(token ?? "")}`,
    { method: "POST" },
  );
  saveTokens(data.access_token, data.refresh_token);
  return data;
}

/**
 * Sign out: revoke the refresh token server-side, then always clear the
 * local session and drop the realtime connection.
 */
export async function logout(): Promise<void> {
  const token = getRefreshToken();
  try {
    await apiFetch<void>(
      `/auth/logout?refresh_token=${encodeURIComponent(token ?? "")}`,
      { method: "POST" },
    );
  } finally {
    clearSession();
    disconnectRealtime();
  }
}

/** Update the current user's editable profile fields. */
export function updateProfile(payload: UserUpdate): Promise<UserRead> {
  return apiFetch<UserRead>("/auth/update", {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export interface TwoFactorCredentials {
  secret: string;
  otpauth_uri: string;
}

/**
 * Begin 2FA enrolment, returning the shared secret and otpauth URI to
 * render as a QR code. The user must confirm with verify2fa before it
 * takes effect.
 */
export function enable2fa(): Promise<TwoFactorCredentials> {
  return apiFetch<TwoFactorCredentials>("/auth/2fa/enable", {
    method: "POST",
  });
}

/** Confirm 2FA enrolment by proving the user can generate a valid code. */
export function verify2fa(code: string): Promise<void> {
  return apiFetch<void>("/auth/2fa/enable/verify", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ code }),
  });
}

/** Turn off 2FA for the current user and return the updated profile. */
export function disable2fa(): Promise<UserRead> {
  return apiFetch<UserRead>("/auth/2fa/disable", {
    method: "POST",
  });
}

export interface TwoFactorRequired {
  pending_token: string;
}

export type LoginResult =
  | { kind: "success"; data: LoginResponse }
  | { kind: "2fa_required"; pendingToken: string };

interface OAuthRedirect {
  authorization_url: string;
}

/** Kick off Google OAuth by redirecting to the provider's consent page. */
export async function startGoogleLogin(): Promise<void> {
  const data = await apiFetch<OAuthRedirect>("/auth/oauth/google/login");
  window.location.assign(data.authorization_url);
}

/**
 * Exchange the one-time OAuth code from the provider callback for a
 * session, persisting the returned tokens.
 */
export async function exchangeOAuthCode(
  exchangeCode: string,
): Promise<LoginResponse> {
  const data = await apiFetch<LoginResponse>("/auth/oauth/exchange", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ exchange_code: exchangeCode }),
  });
  saveTokens(data.tokens.access_token, data.tokens.refresh_token);
  return data;
}

/** Kick off 42 OAuth by redirecting to the provider's consent page. */
export async function startFtLogin(): Promise<void> {
  const data = await apiFetch<OAuthRedirect>("/auth/oauth/42/login");
  window.location.assign(data.authorization_url);
}
