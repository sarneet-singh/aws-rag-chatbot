import { useState, useEffect, useRef } from "react";
import { login, logout, getToken, handleCallback } from "./auth";
import { sendQuery, sendFeedback } from "./api";
import ChatMessage from "./components/ChatMessage";

const SESSION_ID = crypto.randomUUID();

export default function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [token, setToken] = useState(getToken());
  const bottomRef = useRef(null);

  useEffect(() => {
    if (window.location.pathname === "/callback") handleCallback().then(() => setToken(getToken()));
  }, []);

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages]);

  async function submit(e) {
    e.preventDefault();
    if (!input.trim() || loading) return;
    const userMsg = { role: "user", content: input };
    setMessages(prev => [...prev, userMsg]);
    setInput("");
    setLoading(true);
    try {
      const data = await sendQuery(input, SESSION_ID, token);
      setMessages(prev => [...prev, { role: "assistant", ...data }]);
    } catch {
      setMessages(prev => [...prev, { role: "error", content: "Something went wrong. Try again." }]);
    } finally {
      setLoading(false);
    }
  }

  if (!token) return (
    <div style={{ display: "flex", justifyContent: "center", alignItems: "center", height: "100vh", flexDirection: "column", gap: 16 }}>
      <h1>AWS Architecture Assistant</h1>
      <button onClick={login} style={{ padding: "12px 24px", fontSize: 16, cursor: "pointer" }}>Sign In</button>
    </div>
  );

  return (
    <div style={{ maxWidth: 800, margin: "0 auto", padding: 24, display: "flex", flexDirection: "column", height: "100vh" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
        <h2 style={{ margin: 0 }}>AWS Architecture Assistant</h2>
        <button onClick={logout}>Sign Out</button>
      </div>
      <div style={{ flex: 1, overflowY: "auto", display: "flex", flexDirection: "column", gap: 16, paddingBottom: 16 }}>
        {messages.map((msg, i) => <ChatMessage key={i} msg={msg} token={token} sessionId={SESSION_ID} onFeedback={sendFeedback} />)}
        {loading && <div style={{ color: "#888" }}>Thinking...</div>}
        <div ref={bottomRef} />
      </div>
      <form onSubmit={submit} style={{ display: "flex", gap: 8 }}>
        <input value={input} onChange={e => setInput(e.target.value)} placeholder="Ask an AWS architecture question..." style={{ flex: 1, padding: 12, fontSize: 16 }} disabled={loading} />
        <button type="submit" disabled={loading || !input.trim()} style={{ padding: "12px 20px" }}>Send</button>
      </form>
    </div>
  );
}
