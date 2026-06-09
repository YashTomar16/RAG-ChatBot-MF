import type { Conversation } from "../types";
import { GrowwLogo } from "./GrowwLogo";

interface ChatSidebarProps {
  conversations: Conversation[];
  activeId: string;
  sidebarOpen: boolean;
  onClose: () => void;
  onSelect: (id: string) => void;
  onCreate: () => void;
  onDelete: (id: string) => void;
}

function formatWhen(timestamp: number) {
  return new Date(timestamp).toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
  });
}

export function ChatSidebar({
  conversations,
  activeId,
  sidebarOpen,
  onClose,
  onSelect,
  onCreate,
  onDelete,
}: ChatSidebarProps) {
  const sorted = [...conversations].sort((a, b) => b.updatedAt - a.updatedAt);

  return (
    <>
      <div
        className={`chat-sidebar-backdrop ${sidebarOpen ? "open" : ""}`}
        onClick={onClose}
        aria-hidden={!sidebarOpen}
      />
      <aside className={`chat-sidebar ${sidebarOpen ? "open" : ""}`} aria-label="Chat history">
        <div className="chat-sidebar-header">
          <div className="chat-sidebar-brand-row">
            <GrowwLogo size={36} />
            <div>
              <p className="chat-sidebar-brand">HDFC Mutual Funds</p>
              <p className="chat-sidebar-caption">Powered by Groww corpus</p>
            </div>
          </div>
          <button type="button" className="btn btn-new-chat" onClick={onCreate}>
            + New chat
          </button>
        </div>

        <div className="chat-sidebar-list">
          {sorted.map((conversation) => (
            <div key={conversation.id} className="chat-sidebar-item-wrap">
              <button
                type="button"
                className={`chat-sidebar-item ${conversation.id === activeId ? "active" : ""}`}
                onClick={() => {
                  onSelect(conversation.id);
                  onClose();
                }}
              >
                <span className="chat-sidebar-item-title">{conversation.title}</span>
                <span className="chat-sidebar-item-date">{formatWhen(conversation.updatedAt)}</span>
              </button>
              {sorted.length > 1 && (
                <button
                  type="button"
                  className="chat-sidebar-delete"
                  aria-label={`Delete ${conversation.title}`}
                  onClick={() => onDelete(conversation.id)}
                >
                  ×
                </button>
              )}
            </div>
          ))}
        </div>

        <div className="chat-sidebar-footer">
          <p className="chat-sidebar-disclaimer">Facts-only. No investment advice.</p>
        </div>
      </aside>
    </>
  );
}
