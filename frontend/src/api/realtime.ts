import { getAccessToken } from './auth'

const WS_PATH = '/ws/audit'

let socket: WebSocket | null = null
let shouldRun = false
let reconnectAttempts = 0
let reconnectTimer: ReturnType<typeof setTimeout> | null = null

function buildUrl(token: string): string {
  const proto = window.location.protocol === 'https:' ? 'wss' : 'ws'
  return `${proto}://${window.location.host}${WS_PATH}?token=${encodeURIComponent(token)}`
}

function scheduleReconnect(): void {
  if (!shouldRun) return
  const delay = Math.min(1000 * 2 ** reconnectAttempts, 10000)
  reconnectAttempts += 1
  reconnectTimer = setTimeout(openSocket, delay)
}

function openSocket(): void {
  const token = getAccessToken()
  if (!token) return

  const ws = new WebSocket(buildUrl(token))
  socket = ws

  ws.onopen = () => {
    reconnectAttempts = 0
  }

  ws.onclose = () => {
    socket = null
    scheduleReconnect()
  }

  ws.onerror = () => {
    ws.close()
  }
}

export function connectRealtime(): void {
  shouldRun = true
  if (socket || reconnectTimer) return
  reconnectAttempts = 0
  openSocket()
}

export function disconnectRealtime(): void {
  shouldRun = false
  if (reconnectTimer) {
    clearTimeout(reconnectTimer)
    reconnectTimer = null
  }
  if (socket) {
    socket.onclose = null
    socket.close()
    socket = null
  }
  reconnectAttempts = 0
}
