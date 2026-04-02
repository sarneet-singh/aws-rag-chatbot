import { useState, useEffect, useRef } from "react";
import { login, logout, getToken, handleCallback } from "./auth";
import { sendQuery, sendFeedback } from "./api";
import ChatMessage from "./components/ChatMessage";
import "./App.css";

const SESSION_ID = crypto.randomUUID();

const SUGGESTIONS = [
  "What is the AWS Well-Architected Framework?",
  "How does Amazon S3 handle data durability?",
  "When should I use SQS vs SNS?",
  "What are the best practices for Lambda cold starts?",
];

export default function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [token, setToken] = useState(getToken());
  const bottomRef = useRef(null);
  const textareaRef = useRef(null);

  useEffect(() => {
    if (window.location.pathname === "/callback")
      handleCallback().then(() => setToken(getToken()));
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  function autoResize() {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 140) + "px";
  }

  async function submit(e) {
    e?.preventDefault();
    if (!input.trim() || loading) return;
    const text = input.trim();
    setMessages(prev => [...prev, { role: "user", content: text }]);
    setInput("");
    if (textareaRef.current) textareaRef.current.style.height = "48px";
    setLoading(true);
    try {
      const data = await sendQuery(text, SESSION_ID, token);
      setMessages(prev => [...prev, { role: "assistant", ...data }]);
    } catch {
      setMessages(prev => [...prev, { role: "error", content: "Something went wrong. Please try again." }]);
    } finally {
      setLoading(false);
    }
  }

  function handleKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  }

  if (!token) return (
    <>
      <nav className="nav">
        <span className="nav-logo">aws<span>.</span>rag</span>
      </nav>
      <div className="landing">
        <span className="landing-badge">Powered by RAG + GPT-4o-mini</span>
        <h1>AWS Architecture<br /><span>Assistant</span></h1>
        <p>Ask anything about AWS architecture, services, and best practices. Answers are grounded in official AWS documentation with cited sources.</p>
        <button className="btn-primary" onClick={login}>Sign In to Continue</button>
      </div>
    </>
  );

  return (
    <div className="app">
      <nav className="nav">
        <span className="nav-logo">aws<span>.</span>rag</span>
        <button className="btn-ghost" onClick={logout}>Sign Out</button>
      </nav>

      <div className="chat-layout">
        <div className="messages">
          {messages.length === 0 && (
            <div className="empty-state">
              <h2>What can I help you with?</h2>
              <p>Ask about AWS services, architecture patterns, or best practices.</p>
              <div className="suggestion-grid">
                {SUGGESTIONS.map((s, i) => (
                  <button key={i} className="suggestion" onClick={() => { setInput(s); textareaRef.current?.focus(); }}>
                    {s}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((msg, i) => (
            <ChatMessage key={i} msg={msg} token={token} sessionId={SESSION_ID} onFeedback={sendFeedback} />
          ))}

          {loading && (
            <div className="thinking">
              <div className="thinking-dots">
                <span /><span /><span />
              </div>
              Thinking
            </div>
          )}

          <div ref={bottomRef} />
        </div>

        <div className="input-area">
          <form className="input-form" onSubmit={submit}>
            <textarea
              ref={textareaRef}
              className="input-field"
              value={input}
              onChange={e => { setInput(e.target.value); autoResize(); }}
              onKeyDown={handleKeyDown}
              placeholder="Ask an AWS architecture question..."
              disabled={loading}
              rows={1}
            />
            <button type="submit" className="btn-send" disabled={loading || !input.trim()}>
              Send
            </button>
          </form>
          <p className="input-hint">Press Enter to send · Shift+Enter for new line</p>
        </div>
      </div>
    </div>
  );
}
