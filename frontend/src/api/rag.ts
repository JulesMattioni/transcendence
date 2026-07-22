import { apiFetch } from './client'
import { requireCurrentOrgId } from './currentOrg'

export interface Source {
  file_id: number
  chunk_index: number
  excerpt: string
}

export interface Message {
  id: number
  role: string
  content: string
  sources: Source[] | null
  created_at: string
}

export interface Conversation {
  id: number
  organisation_id: number
  user_id: number
  title: string
  created_at: string
}

export interface ConversationDetail extends Conversation {
  messages: Message[]
}

export function listConversations(): Promise<Conversation[]> {
  const orgId = requireCurrentOrgId()
  return apiFetch<Conversation[]>(
    `/rag/conversations?organisation_id=${orgId}`,
  )
}

export function getConversation(id: number): Promise<ConversationDetail> {
  const orgId = requireCurrentOrgId()
  return apiFetch<ConversationDetail>(
    `/rag/conversations/${id}?organisation_id=${orgId}`,
  )
}

export function deleteConversation(id: number): Promise<void> {
  const orgId = requireCurrentOrgId()
  return apiFetch<void>(
    `/rag/conversations/${id}?organisation_id=${orgId}`,
    { method: 'DELETE' },
  )
}

export interface QueryStreamHandlers {
  onConversation?: (conversationId: number) => void
  onSources?: (sources: Source[]) => void
  onToken?: (text: string) => void
  onDone?: () => void
  onError?: (error: unknown) => void
}

export async function queryStream(
  question: string,
  conversationId: number | null,
  handlers: QueryStreamHandlers,
): Promise<void> {
  try {
    const orgId = requireCurrentOrgId()
    const token = localStorage.getItem('access_token')
    const response = await fetch('/api/rag/query/stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({
        question,
        organisation_id: orgId,
        conversation_id: conversationId,
      }),
    })

    if (!response.ok || !response.body) {
      throw new Error(`Chat request failed (${response.status})`)
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    for (;;) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })

      const events = buffer.split('\n\n')
      buffer = events.pop() ?? ''

      for (const raw of events) {
        dispatchEvent(raw, handlers)
      }
    }

    handlers.onDone?.()
  } catch (error) {
    handlers.onError?.(error)
  }
}

function dispatchEvent(raw: string, handlers: QueryStreamHandlers): void {
  let event = ''
  let data = ''
  for (const line of raw.split('\n')) {
    if (line.startsWith('event:')) event = line.slice(6).trim()
    else if (line.startsWith('data:')) data += line.slice(5).trim()
  }
  if (!event || !data) return

  const parsed = JSON.parse(data)
  switch (event) {
    case 'conversation':
      handlers.onConversation?.(parsed.conversation_id)
      break
    case 'sources':
      handlers.onSources?.(parsed.sources)
      break
    case 'token':
      handlers.onToken?.(parsed.text)
      break
    case 'done':
      break
  }
}
