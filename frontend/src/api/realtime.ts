import { getAccessToken } from "./auth";

const WS_PATH = "/ws/audit";

let socket: WebSocket | null = null;
let shouldRun = false;
let reconnectAttempts = 0;
let reconnectTimer: ReturnType<typeof setTimeout> | null = null;

/** Build the audit WebSocket URL, matching ws/wss to the page protocol. */
function buildUrl(token: string): string {
  const proto = window.location.protocol === "https:" ? "wss" : "ws";
  return `${proto}://${window.location.host}${WS_PATH}?token=${encodeURIComponent(token)}`;
}

/**
 * Schedule a reconnection with capped exponential backoff, unless the
 * socket was intentionally disconnected.
 */
function scheduleReconnect(): void {
  if (!shouldRun) return;
  const delay = Math.min(1000 * 2 ** reconnectAttempts, 10000);
  reconnectAttempts += 1;
  reconnectTimer = setTimeout(openSocket, delay);
}

/**
 * Open the audit WebSocket and wire its lifecycle: reset backoff on open,
 * reconnect on close, prepend incoming events (capped) and notify
 * subscribers, and close on error to trigger a reconnect.
 */
function openSocket(): void {
  const token = getAccessToken();
  if (!token) return;

  const ws = new WebSocket(buildUrl(token));
  socket = ws;

  ws.onopen = () => {
    reconnectAttempts = 0;
  };

  ws.onclose = () => {
    socket = null;
    scheduleReconnect();
  };

  ws.onmessage = (msg) => {
    let event: RealtimeEvent;
    try {
      event = JSON.parse(msg.data);
    } catch {
      return;
    }
    events = [event, ...events].slice(0, MAX_EVENTS);
    notifyListeners();
  };

  ws.onerror = () => {
    ws.close();
  };
}

/**
 * Start the realtime audit connection. Idempotent: does nothing if a
 * socket or a pending reconnect already exists.
 */
export function connectRealtime(): void {
  shouldRun = true;
  if (socket || reconnectTimer) return;
  reconnectAttempts = 0;
  openSocket();
}

/**
 * Tear down the realtime connection, cancel any reconnect, clear the
 * buffered events and notify subscribers of the empty state.
 */
export function disconnectRealtime(): void {
  shouldRun = false;
  if (reconnectTimer) {
    clearTimeout(reconnectTimer);
    reconnectTimer = null;
  }
  if (socket) {
    socket.onclose = null;
    socket.close();
    socket = null;
  }
  events = [];
  notifyListeners();
  reconnectAttempts = 0;
}

export type RealtimeEvent = {
  event_id: string;
  event_type:
    | "auth.login"
    | "auth.logout"
    | "file.created"
    | "file.updated"
    | "file.deleted";
  timestamp: string;
  user_id: number | null;
  first_name: string | null;
  last_name: string | null;
  org_id: number | null;
  org_name: string | null;
  file_name: string | null;
};

type Listener = (events: RealtimeEvent[]) => void;

const MAX_EVENTS = 100;

let events: RealtimeEvent[] = [];
const listeners = new Set<Listener>();

/** Push the current event buffer to every subscribed listener. */
function notifyListeners(): void {
  for (const listener of listeners) listener(events);
}

/**
 * Subscribe to the realtime event buffer. The listener is called
 * immediately with the current events and on every update; returns an
 * unsubscribe function.
 */
export function subscribeRealtime(listener: Listener): () => void {
  listeners.add(listener);
  listener(events);
  return () => {
    listeners.delete(listener);
  };
}

export type ConnectedMember = {
  user_id: number;
  first_name: string | null;
  last_name: string | null;
};

/**
 * Fetch the user ids of the user's connections currently online.
 * Returns an empty list on failure rather than throwing.
 */
export async function fetchConnectedFriends(userId: number): Promise<number[]> {
  const token = getAccessToken();
  const response = await fetch(`/ws/connected_friends?user_id=${userId}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : undefined,
  });
  if (!response.ok) return [];
  const members: ConnectedMember[] = await response.json();
  return members.map((m) => m.user_id);
}
