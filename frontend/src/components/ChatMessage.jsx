import { useState } from "react";
import Sources from "./Sources";

export default function ChatMessage({ msg, token, sessionId, onFeedback }) {
  const [rated, setRated] = useState(null);

  async function rate(rating) {
    if (rated) return;
    await onFeedback(sessionId, msg.message_id, rating, token);
    setRated(rating);
  }

  if (msg.role === "user") return <div style={{ alignSelf: "flex-end", background: "#0070f3", color: "#fff", padding: "10px 16px", borderRadius: 12, maxWidth: "80%" }}>{msg.content}</div>;
  if (msg.role === "error") return <div style={{ color: "red" }}>{msg.content}</div>;

  return (
    <div style={{ alignSelf: "flex-start", maxWidth: "85%" }}>
      <div style={{ background: "#f4f4f4", padding: "12px 16px", borderRadius: 12 }}>{msg.answer}</div>
      {msg.sources?.length > 0 && <Sources sources={msg.sources} />}
      {msg.message_id && (
        <div style={{ display: "flex", gap: 8, marginTop: 6 }}>
          <button onClick={() => rate("up")} disabled={!!rated} style={{ opacity: rated && rated !== "up" ? 0.3 : 1 }}>👍</button>
          <button onClick={() => rate("down")} disabled={!!rated} style={{ opacity: rated && rated !== "down" ? 0.3 : 1 }}>👎</button>
        </div>
      )}
    </div>
  );
}
