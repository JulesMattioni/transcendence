import { getAccessToken } from "./auth";

const WS_PATH = "/ws/audit";

let socket: WebSocket | null = null;
let shouldRun = false;
let reconnectAttempts = 0;
let reconnectTimer: ReturnType<typeof setTimeout> | null = null;

function buildUrl(token: string): string {
  const proto = window.location.protocol === "https:" ? "wss" : "ws";
  return `${proto}://${window.location.host}${WS_PATH}?token=${encodeURIComponent(token)}`;
}

function scheduleReconnect(): void {
  if (!shouldRun) return;
  const delay = Math.min(1000 * 2 ** reconnectAttempts, 10000);
  reconnectAttempts += 1;
  reconnectTimer = setTimeout(openSocket, delay);
}

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

export function connectRealtime(): void {
  shouldRun = true;
  if (socket || reconnectTimer) return;
  reconnectAttempts = 0;
  openSocket();
}

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

function notifyListeners(): void {
  for (const listener of listeners) listener(events);
}

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

export async function fetchConnectedFriends(userId: number): Promise<number[]> {
  const token = getAccessToken();
  const response = await fetch(`/ws/connected_friends?user_id=${userId}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : undefined,
  });
  if (!response.ok) return [];
  const members: ConnectedMember[] = await response.json();
  return members.map((m) => m.user_id);
}
