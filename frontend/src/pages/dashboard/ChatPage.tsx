import { useState, useRef, useEffect } from "react";
import { queryStream, getConversation } from "../../api/rag";
import type { Source } from "../../api/rag";
import Topbar from "../../components/dashboard/Topbar";
import Sidebar from "../../components/dashboard/Sidebar";
import BottomNav from "../../components/dashboard/BottomNav";
import ChatMenu from "../../components/dashboard/ChatMenu";
import { ArrowUp } from "lucide-react";
import { getFile, type FileRead } from "../../api/files";
import Modal from "../../components/Modal";
import FilePreview from "../../components/FilePreview";
import MessageContent from "../../components/dashboard/MessageContent";
import { me, type UserRead } from "../../api/auth";
import { useOrg } from "../../context/orgContextValue";

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  sources: Source[] | null;
}

/**
 * RAG chat page for the selected organisation. Streams answers token by
 * token, renders citations that open the cited file, and manages
 * conversations (new, load, delete) via the ChatMenu. Resets when the
 * organisation changes and prompts to pick one when none is selected.
 */
function ChatPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [conversationId, setConversationId] = useState<number | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);
  const [fileToView, setFileToView] = useState<FileRead | null>(null);
  const [sourceError, setSourceError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const [user, setUser] = useState<UserRead | null>(null);
  const { currentOrg, loading: orgLoading } = useOrg();
  const prevOrgId = useRef(currentOrg?.org_id);
  if (prevOrgId.current !== currentOrg?.org_id) {
    prevOrgId.current = currentOrg?.org_id;
    setMessages([]);
    setConversationId(null);
    setRefreshKey((k) => k + 1);
  }

  useEffect(() => {
    me()
      .then(setUser)
      .catch(() => setUser(null));
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  /** Open a cited source file in the preview modal, or show an error. */
  async function openSource(fileId: number) {
    setSourceError(null);
    try {
      const file = await getFile(fileId);
      setFileToView(file);
    } catch (err) {
      console.error("Could not open source file:", err);
      setSourceError(
        "Could not open this source file. It may have been deleted.",
      );
    }
  }

  /**
   * Send the current question, append the user and a placeholder
   * assistant message, then stream the answer, sources and any error into
   * that placeholder.
   */
  async function handleSend() {
    const question = input.trim();
    if (!question || streaming) return;

    setMessages((prev) => [
      ...prev,
      { role: "user", content: question, sources: null },
      { role: "assistant", content: "", sources: null },
    ]);
    setInput("");
    setStreaming(true);

    await queryStream(
      question,
      conversationId,
      {
        onConversation: (id) => {
          if (conversationId === null) {
            setRefreshKey((k) => k + 1);
          }
          setConversationId(id);
        },
        onSources: (sources) => updateLastAssistant((m) => ({ ...m, sources })),
        onToken: (text) =>
          updateLastAssistant((m) => ({ ...m, content: m.content + text })),
        onError: () =>
          updateLastAssistant((m) => ({
            ...m,
            content: m.content || "Something went wrong. Please try again.",
          })),
      },
      currentOrg!.org_id,
    );

    setStreaming(false);
  }

  /** Apply a transform to the last (assistant) message in the list. */
  function updateLastAssistant(transform: (m: ChatMessage) => ChatMessage) {
    setMessages((prev) => {
      const next = [...prev];
      next[next.length - 1] = transform(next[next.length - 1]);
      return next;
    });
  }

  /** Load an existing conversation's messages into the view. */
  async function loadConversation(id: number) {
    const detail = await getConversation(id, currentOrg!.org_id);
    setMessages(
      detail.messages.map((m) => ({
        role: m.role === "user" ? "user" : "assistant",
        content: m.content,
        sources: m.sources,
      })),
    );
    setConversationId(id);
  }

  /** Start a fresh conversation, clearing the current thread. */
  function newChat() {
    setMessages([]);
    setConversationId(null);
  }

  /** If the deleted conversation was open, reset to a new chat. */
  function handleDeleted(id: number) {
    if (id === conversationId) {
      newChat();
    }
  }

  return (
    <div className="flex h-screen flex-col overflow-hidden bg-bg">
      <Topbar />

      <div className="flex min-h-0 flex-1">
        <Sidebar />

        <main className="flex min-h-0 flex-1 flex-col">
          {orgLoading ? (
            <div className="flex flex-1 items-center justify-center">
              <p className="text-muted">Loading…</p>
            </div>
          ) : !currentOrg ? (
            <div className="flex flex-1 items-center justify-center p-6">
              <p className="text-center font-serif text-xl font-bold text-muted">
                Select or create an organisation to start chatting.
              </p>
            </div>
          ) : (
            <>
              <div className="flex justify-end px-6 py-3">
                <ChatMenu
                  orgId={currentOrg.org_id}
                  activeId={conversationId}
                  onSelect={loadConversation}
                  onDeleted={handleDeleted}
                  onNewChat={newChat}
                  refreshKey={refreshKey}
                />
              </div>
              {/* Chat zone */}
              <div className="flex-1 space-y-4 overflow-y-auto p-6">
                {messages.length === 0 ? (
                  <div className="flex h-full items-center justify-center">
                    <p className="font-serif text-center font-bold text-2xl text-muted lg:text-4xl">
                      {user ? (
                        <>
                          Welcome{" "}
                          <span className="text-keepr">{user.first_name}</span>,
                          how can I help you?
                        </>
                      ) : (
                        "Welcome, how can I help you?"
                      )}
                    </p>
                  </div>
                ) : (
                  messages.map((m, i) => (
                    <div
                      key={i}
                      className={m.role === "user" ? "text-right" : "text-left"}
                    >
                      <div
                        className={`inline-block max-w-6xl whitespace-pre-wrap text-sm ${
                          m.role === "user"
                            ? "rounded-lg bg-keepr px-4 py-2 text-white"
                            : "px-4 py-2 text-black"
                        }`}
                      >
                        <MessageContent
                          content={m.content}
                          sources={m.sources}
                          onOpenSource={openSource}
                        />
                      </div>
                    </div>
                  ))
                )}
                <div ref={bottomRef} />
              </div>

              {/* Input */}
              {sourceError && (
                <p className="px-6 pb-2 text-center text-sm text-red-500">
                  {sourceError}
                </p>
              )}

              <div className="p-6 pb-24 lg:pb-6">
                <div className="mx-auto flex max-w-8xl items-center gap-3 rounded-lg border border-keepr bg-white p-4 shadow-sm">
                  <input
                    className="flex-1 bg-transparent font-mono text-sm text-black placeholder:text-subtle focus:outline-none"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && handleSend()}
                    placeholder="Ask anything..."
                    disabled={streaming}
                  />
                  <button
                    type="button"
                    onClick={handleSend}
                    disabled={streaming || input.trim() === ""}
                    className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-keepr text-white transition-opacity transition-colors duration-200 hover:bg-blue-700 disabled:opacity-40"
                  >
                    <ArrowUp size={14} strokeWidth={3} />
                  </button>
                </div>
              </div>
            </>
          )}
        </main>
      </div>
      <Modal
        isOpen={fileToView !== null}
        onClose={() => setFileToView(null)}
        title={fileToView?.title ?? "Preview"}
        size="xl"
      >
        {fileToView && <FilePreview file={fileToView} />}
      </Modal>
      <BottomNav />
    </div>
  );
}

export default ChatPage;
