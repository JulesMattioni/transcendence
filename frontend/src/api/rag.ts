import { apiFetch } from "./client";
import { requireCurrentOrgId } from "./currentOrg";

export interface Source {
  file_id: number;
  chunk_index: number;
  excerpt: string;
}

export interface Message {
  id: number;
  role: string;
  content: string;
  sources: Source[] | null;
  created_at: string;
}

export interface Conversation {
  id: number;
  organisation_id: number;
  user_id: number;
  title: string;
  created_at: string;
}

export interface ConversationDetail extends Conversation {
  messages: Message[];
}

/** List the current user's conversations in an organisation. */
export function listConversations(
  orgId: number = requireCurrentOrgId(),
): Promise<Conversation[]> {
  return apiFetch<Conversation[]>(
    `/rag/conversations?organisation_id=${orgId}`,
  );
}

/** Fetch a single conversation with its full message history. */
export function getConversation(
  id: number,
  orgId: number = requireCurrentOrgId(),
): Promise<ConversationDetail> {
  return apiFetch<ConversationDetail>(
    `/rag/conversations/${id}?organisation_id=${orgId}`,
  );
}

/** Delete a conversation and its messages. */
export function deleteConversation(
  id: number,
  orgId: number = requireCurrentOrgId(),
): Promise<void> {
  return apiFetch<void>(`/rag/conversations/${id}?organisation_id=${orgId}`, {
    method: "DELETE",
  });
}

export interface QueryStreamHandlers {
  onConversation?: (conversationId: number) => void;
  onSources?: (sources: Source[]) => void;
  onToken?: (text: string) => void;
  onDone?: () => void;
  onError?: (error: unknown) => void;
}

/**
 * Ask a question and stream the answer over SSE, invoking the matching
 * handler for each event (conversation id, sources, tokens, done). Never
 * rejects: network and parsing failures are reported through onError.
 * Bypasses apiFetch to read the streaming response body directly.
 */
export async function queryStream(
  question: string,
  conversationId: number | null,
  handlers: QueryStreamHandlers,
  orgId: number = requireCurrentOrgId(),
): Promise<void> {
  try {
    const token = localStorage.getItem("access_token");
    const response = await fetch("/api/rag/query/stream", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({
        question,
        organisation_id: orgId,
        conversation_id: conversationId,
      }),
    });

    if (!response.ok || !response.body) {
      throw new Error(`Chat request failed (${response.status})`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      const events = buffer.split("\n\n");
      buffer = events.pop() ?? "";

      for (const raw of events) {
        dispatchEvent(raw, handlers);
      }
    }

    handlers.onDone?.();
  } catch (error) {
    handlers.onError?.(error);
  }
}

/**
 * Parse one raw SSE frame ("event:"/"data:" lines) and route its decoded
 * payload to the corresponding handler.
 */
function dispatchEvent(raw: string, handlers: QueryStreamHandlers): void {
  let event = "";
  let data = "";
  for (const line of raw.split("\n")) {
    if (line.startsWith("event:")) event = line.slice(6).trim();
    else if (line.startsWith("data:")) data += line.slice(5).trim();
  }
  if (!event || !data) return;

  const parsed = JSON.parse(data);
  switch (event) {
    case "conversation":
      handlers.onConversation?.(parsed.conversation_id);
      break;
    case "sources":
      handlers.onSources?.(parsed.sources);
      break;
    case "token":
      handlers.onToken?.(parsed.text);
      break;
    case "done":
      break;
  }
}
