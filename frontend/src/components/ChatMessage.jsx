import { useState } from "react";
import Sources from "./Sources";

export default function ChatMessage({ msg, token, sessionId, onFeedback }) {
  const [rated, setRated] = useState(null);

  async function rate(rating) {
    if (rated) return;
    await onFeedback(sessionId, msg.message_id, rating, token);
    setRated(rating);
  }

  if (msg.role === "user") return (
    <div className="msg-user">{msg.content}</div>
  );

  if (msg.role === "error") return (
    <div className="msg-error">{msg.content}</div>
  );

  return (
    <div className="msg-assistant">
      <div className="msg-assistant-bubble">{msg.answer}</div>

      {msg.sources?.length > 0 && <Sources sources={msg.sources} />}

      {msg.message_id && (
        <div className="feedback">
          <button
            className={`btn-feedback ${rated === "up" ? "active-up" : ""}`}
            onClick={() => rate("up")}
            disabled={!!rated}
            title="Helpful"
          >↑</button>
          <button
            className={`btn-feedback ${rated === "down" ? "active-down" : ""}`}
            onClick={() => rate("down")}
            disabled={!!rated}
            title="Not helpful"
          >↓</button>
        </div>
      )}
    </div>
  );
}
