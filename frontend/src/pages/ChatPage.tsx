import { useEffect, useRef, useState } from "react";
import { postChat } from "../api/client";
import { ChatBackground } from "../components/ChatBackground";
import { ChatBubble } from "../components/ChatBubble";
import { ChatSidebar } from "../components/ChatSidebar";
import { FundCard } from "../components/FundCard";
import { GrowwLogo } from "../components/GrowwLogo";
import { useBootstrap } from "../context/BootstrapContext";
import { createMessageId, useConversations } from "../hooks/useConversations";
import { useTheme } from "../hooks/useTheme";
import type { ChatMessage } from "../types";

export function ChatPage() {
  const bootstrap = useBootstrap();
  const { dark, toggle } = useTheme();
  const {
    conversations,
    activeConversation,
    activeId,
    createConversation,
    selectConversation,
    deleteConversation,
    updateMessages,
  } = useConversations();

  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  const messages = activeConversation?.messages ?? [];

  const sendQuestion = async (question: string) => {
    const trimmed = question.trim();
    if (!trimmed || loading || !activeConversation) return;

    setError(null);
    setLoading(true);

    const pending: ChatMessage[] = [
      ...messages,
      { id: createMessageId(), role: "user", content: trimmed },
    ];
    updateMessages(activeConversation.id, pending);

    try {
      const response = await postChat(trimmed);
      updateMessages(activeConversation.id, [
        ...pending,
        {
          id: createMessageId(),
          role: "assistant",
          content: response.answer,
          sourceUrl: response.source_url,
          lastUpdated: response.last_updated,
          isRefusal: response.is_refusal,
          product: response.product,
        },
      ]);
    } catch (err) {
      updateMessages(activeConversation.id, messages);
      setError(err instanceof Error ? err.message : "Request failed");
    } finally {
      setLoading(false);
      setInput("");
    }
  };

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading, activeId]);

  return (
    <div className="chat-app" data-theme={dark ? "dark" : "light"}>
      <ChatSidebar
        conversations={conversations}
        activeId={activeId}
        sidebarOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        onSelect={selectConversation}
        onCreate={() => {
          createConversation();
          setError(null);
          setInput("");
        }}
        onDelete={deleteConversation}
      />

      <main className="chat-main chat-main-groww">
        <ChatBackground />

        <div className="chat-main-content">
          <header className="chat-main-header">
            <button
              type="button"
              className="chat-menu-btn"
              aria-label="Open chat history"
              onClick={() => setSidebarOpen(true)}
            >
              ☰
            </button>
            <div className="chat-main-title-wrap">
              <div className="chat-main-title-row">
                <GrowwLogo size={28} />
                <h1 className="chat-main-title">{activeConversation?.title ?? "HDFC Mutual Funds"}</h1>
              </div>
              <p className="chat-main-caption">Ask factual questions about HDFC schemes on Groww</p>
            </div>
            <button type="button" className="theme-toggle" onClick={toggle} aria-label="Toggle dark mode">
              {dark ? "Light" : "Dark"}
            </button>
          </header>

          {!bootstrap.index_ready && (
            <div className="error-banner chat-status-banner">
              Backend index not ready — ingestion may be required on Railway.
            </div>
          )}
          {!bootstrap.groq_configured && (
            <div className="error-banner chat-status-banner">
              GROQ_API_KEY not configured on the backend.
            </div>
          )}

          <div className="chat-messages">
            {messages.length === 0 ? (
              <div className="chat-empty">
                <GrowwLogo size={48} className="chat-empty-logo" />
                <h2 className="chat-empty-title">How can I help with HDFC mutual funds?</h2>
                <p className="chat-empty-body">
                  Ask about expense ratio, NAV, exit load, benchmarks, and minimum SIP for 12 HDFC
                  schemes. I provide facts only — no investment advice.
                </p>
                <div className="chat-prompt-grid">
                  {bootstrap.suggested_prompts.map((prompt) => (
                    <button
                      key={prompt}
                      type="button"
                      className="btn btn-chip btn-chip-groww"
                      onClick={() => void sendQuestion(prompt)}
                      disabled={loading}
                    >
                      {prompt}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              <div className="chat-thread">
                {messages.map((message) => (
                  <div key={message.id}>
                    <ChatBubble message={message} />
                    {message.role === "assistant" && message.product && (
                      <FundCard product={message.product} />
                    )}
                  </div>
                ))}
                {loading && <div className="loading chat-thinking">Thinking…</div>}
                <div ref={bottomRef} />
              </div>
            )}
          </div>

          {error && <div className="error-banner chat-composer-error">{error}</div>}

          <form
            className="chat-composer chat-composer-groww"
            onSubmit={(event) => {
              event.preventDefault();
              void sendQuestion(input);
            }}
          >
            <input
              className="chat-input chat-input-groww"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask a factual question about HDFC schemes…"
              aria-label="Chat message"
              disabled={loading}
            />
            <button type="submit" className="btn btn-primary chat-send-btn" disabled={loading || !input.trim()}>
              Send
            </button>
          </form>
        </div>
      </main>
    </div>
  );
}
