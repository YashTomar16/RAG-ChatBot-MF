import { useEffect, useRef, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { postChat } from "../api/client";
import { ChatBubble } from "../components/ChatBubble";
import { FundCard } from "../components/FundCard";
import { InsightCard } from "../components/Widgets";
import { useBootstrap } from "../context/BootstrapContext";
import type { ChatMessage } from "../types";

function newId() {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

export function ChatPage() {
  const bootstrap = useBootstrap();
  const location = useLocation();
  const navigate = useNavigate();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  const sendQuestion = async (question: string) => {
    const trimmed = question.trim();
    if (!trimmed || loading) return;

    setError(null);
    setLoading(true);
    setMessages((prev) => [...prev, { id: newId(), role: "user", content: trimmed }]);

    try {
      const response = await postChat(trimmed);
      setMessages((prev) => [
        ...prev,
        {
          id: newId(),
          role: "assistant",
          content: response.answer,
          sourceUrl: response.source_url,
          lastUpdated: response.last_updated,
          isRefusal: response.is_refusal,
          product: response.product,
        },
      ]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Request failed");
    } finally {
      setLoading(false);
      setInput("");
    }
  };

  useEffect(() => {
    const state = location.state as { prompt?: string } | null;
    if (state?.prompt) {
      navigate(".", { replace: true, state: {} });
      void sendQuestion(state.prompt);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [location.state]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  return (
    <>
      <h1 className="large-title">Chat</h1>
      {messages.length === 0 && (
        <InsightCard
          title="Welcome"
          body="Ask factual questions about expense ratio, NAV, exit load, benchmarks, and minimum SIP for HDFC schemes."
        />
      )}

      {!bootstrap.index_ready && (
        <div className="error-banner">Backend index not ready — ingestion may be required on Railway.</div>
      )}
      {!bootstrap.groq_configured && (
        <div className="error-banner">GROQ_API_KEY not configured on the backend.</div>
      )}

      <p className="caption" style={{ marginBottom: 8 }}>
        Suggested prompts
      </p>
      <div className="chip-grid">
        {bootstrap.suggested_prompts.map((prompt) => (
          <button
            key={prompt}
            type="button"
            className="btn btn-chip"
            onClick={() => void sendQuestion(prompt)}
            disabled={loading}
          >
            {prompt}
          </button>
        ))}
      </div>

      <div className="chat-thread">
        {messages.map((message) => (
          <div key={message.id}>
            <ChatBubble message={message} />
            {message.role === "assistant" && message.product && (
              <FundCard product={message.product} />
            )}
          </div>
        ))}
        {loading && <div className="loading">Thinking…</div>}
      </div>

      {error && <div className="error-banner">{error}</div>}

      <form
        className="chat-input-row"
        onSubmit={(event) => {
          event.preventDefault();
          void sendQuestion(input);
        }}
      >
        <input
          className="chat-input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask a factual question about HDFC schemes…"
          aria-label="Chat message"
          disabled={loading}
        />
        <button type="submit" className="btn btn-primary" style={{ width: "auto" }} disabled={loading}>
          Send
        </button>
      </form>
      <div ref={bottomRef} />
    </>
  );
}
