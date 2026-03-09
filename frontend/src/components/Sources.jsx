import { useState } from "react";

export default function Sources({ sources }) {
  const [open, setOpen] = useState(false);
  return (
    <div style={{ marginTop: 8, fontSize: 14 }}>
      <button onClick={() => setOpen(o => !o)} style={{ background: "none", border: "none", color: "#0070f3", cursor: "pointer", padding: 0 }}>
        {open ? "▾" : "▸"} Sources ({sources.length})
      </button>
      {open && (
        <ul style={{ margin: "4px 0 0 0", paddingLeft: 20 }}>
          {sources.map((s, i) => <li key={i}><a href={s.url} target="_blank" rel="noreferrer">{s.title}</a></li>)}
        </ul>
      )}
    </div>
  );
}
