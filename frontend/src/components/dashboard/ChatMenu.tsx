import { useEffect, useRef, useState } from "react";
import { Menu, Trash2, Plus } from "lucide-react";
import {
  listConversations,
  deleteConversation,
  type Conversation,
} from "../../api/rag";

interface ChatMenuProps {
  orgId: number;
  activeId: number | null;
  onSelect: (id: number) => void;
  onDeleted: (id: number) => void;
  onNewChat: () => void;
  refreshKey: number;
}

function ChatMenu({
  orgId,
  activeId,
  onSelect,
  onDeleted,
  onNewChat,
  refreshKey,
}: ChatMenuProps) {
  const [open, setOpen] = useState(false);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    listConversations(orgId)
      .then(setConversations)
      .catch(() => setConversations([]));
  }, [refreshKey, orgId]);

  useEffect(() => {
    if (!open) return;
    function onClickOutside(e: MouseEvent) {
      if (
        containerRef.current &&
        !containerRef.current.contains(e.target as Node)
      ) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", onClickOutside);
    return () => document.removeEventListener("mousedown", onClickOutside);
  }, [open]);

  async function handleDelete(id: number) {
    await deleteConversation(id, orgId);
    setConversations((prev) => prev.filter((c) => c.id !== id));
    onDeleted(id);
  }

  function handleSelect(id: number) {
    onSelect(id);
    setOpen(false);
  }

  function handleNewChat() {
    onNewChat();
    setOpen(false);
  }

  return (
    <div ref={containerRef} className="relative">
      {/* Icon */}
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="flex h-9 w-9 items-center justify-center text-muted transition-colors duration-200 hover:text-black"
      >
        <Menu size={20} />
      </button>

      {/* Dropdown */}
      {open && (
        <div className="absolute right-0 z-50 mt-2 w-72 overflow-hidden rounded bg-white shadow-lg ring-1 ring-black/5">
          {/* New chat */}
          <button
            type="button"
            onClick={handleNewChat}
            className="flex w-full items-center gap-2 border-b border-gray-100 px-4 py-3 text-sm text-keepr hover:bg-blue-50"
          >
            <Plus size={16} /> New chat
          </button>

          {/* List */}
          <nav className="max-h-80 overflow-y-auto">
            {conversations.length === 0 && (
              <p className="px-4 py-3 text-sm text-gray-400">
                No conversations yet.
              </p>
            )}
            {conversations.map((c) => (
              <div
                key={c.id}
                className={`group flex items-center justify-between px-4 py-3 text-sm transition-colors duration-200 ${
                  c.id === activeId
                    ? "bg-blue-100 text-keepr"
                    : "text-muted hover:bg-blue-50"
                }`}
              >
                <button
                  type="button"
                  onClick={() => handleSelect(c.id)}
                  className="flex-1 truncate text-left"
                >
                  {c.title}
                </button>
                <button
                  type="button"
                  onClick={() => handleDelete(c.id)}
                  className="ml-2 block text-gray-400 transition-colors duration-200 hover:text-red-500 lg:hidden lg:group-hover:block"
                >
                  <Trash2 size={16} />
                </button>
              </div>
            ))}
          </nav>
        </div>
      )}
    </div>
  );
}

export default ChatMenu;
