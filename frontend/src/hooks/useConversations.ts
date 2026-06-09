import { useCallback, useEffect, useState } from "react";
import type { ChatMessage, Conversation } from "../types";

const STORAGE_KEY = "hdfc-fund-chat-sessions";

function newId() {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

function loadConversations(): Conversation[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw) as Conversation[];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function saveConversations(conversations: Conversation[]) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(conversations));
}

function makeConversation(): Conversation {
  const now = Date.now();
  return {
    id: newId(),
    title: "New chat",
    createdAt: now,
    updatedAt: now,
    messages: [],
  };
}

function titleFromMessages(messages: ChatMessage[]): string {
  const firstUser = messages.find((message) => message.role === "user");
  if (!firstUser) return "New chat";
  const text = firstUser.content.trim();
  if (text.length <= 42) return text;
  return `${text.slice(0, 42)}…`;
}

export function useConversations() {
  const [conversations, setConversations] = useState<Conversation[]>(() => {
    const stored = loadConversations();
    return stored.length > 0 ? stored : [makeConversation()];
  });
  const [activeId, setActiveId] = useState<string>(() => {
    const stored = loadConversations();
    const list = stored.length > 0 ? stored : [makeConversation()];
    return [...list].sort((a, b) => b.updatedAt - a.updatedAt)[0].id;
  });

  useEffect(() => {
    saveConversations(conversations);
  }, [conversations]);

  useEffect(() => {
    if (!conversations.some((conversation) => conversation.id === activeId)) {
      setActiveId(conversations[0]?.id ?? makeConversation().id);
    }
  }, [conversations, activeId]);

  const activeConversation =
    conversations.find((conversation) => conversation.id === activeId) ?? conversations[0] ?? null;

  const createConversation = useCallback(() => {
    const conversation = makeConversation();
    setConversations((prev) => [conversation, ...prev]);
    setActiveId(conversation.id);
    return conversation.id;
  }, []);

  const selectConversation = useCallback((id: string) => {
    setActiveId(id);
  }, []);

  const deleteConversation = useCallback(
    (id: string) => {
      setConversations((prev) => {
        const next = prev.filter((conversation) => conversation.id !== id);
        if (next.length === 0) {
          const fresh = makeConversation();
          setActiveId(fresh.id);
          return [fresh];
        }
        if (id === activeId) {
          setActiveId([...next].sort((a, b) => b.updatedAt - a.updatedAt)[0].id);
        }
        return next;
      });
    },
    [activeId],
  );

  const updateMessages = useCallback((conversationId: string, messages: ChatMessage[]) => {
    setConversations((prev) =>
      prev.map((conversation) =>
        conversation.id === conversationId
          ? {
              ...conversation,
              messages,
              title: titleFromMessages(messages),
              updatedAt: Date.now(),
            }
          : conversation,
      ),
    );
  }, []);

  return {
    conversations,
    activeConversation,
    activeId,
    createConversation,
    selectConversation,
    deleteConversation,
    updateMessages,
  };
}

export function createMessageId() {
  return newId();
}
