import type { ChatMessage } from "../types";

export function ChatBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";
  const bubbleClass = isUser ? "user" : message.isRefusal ? "refusal assistant" : "assistant";

  return (
    <div className={`bubble-row ${message.role}`}>
      <div className={`bubble ${bubbleClass}`}>
        {message.content}
        {!isUser && message.sourceUrl && (
          <div className="citation">
            <a href={message.sourceUrl} target="_blank" rel="noopener noreferrer">
              Source: Groww
            </a>
            {message.lastUpdated && (
              <>
                <br />
                Last updated: {message.lastUpdated}
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
