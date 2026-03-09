const API_URL = import.meta.env.VITE_API_URL;

export async function sendQuery(query, sessionId, token) {
  const res = await fetch(`${API_URL}/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify({ query, session_id: sessionId }),
  });
  if (!res.ok) throw new Error("Query failed");
  return res.json();
}

export async function sendFeedback(sessionId, messageId, rating, token) {
  await fetch(`${API_URL}/feedback`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify({ session_id: sessionId, message_id: messageId, rating }),
  });
}
