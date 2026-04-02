import { useState } from "react";

export default function Sources({ sources }) {
  const [open, setOpen] = useState(false);

  return (
    <div className="sources">
      <button className="sources-toggle" onClick={() => setOpen(o => !o)}>
        <span>{open ? "▾" : "▸"}</span>
        Sources
        <span className="count">{sources.length}</span>
      </button>
      {open && (
        <div className="sources-list">
          {sources.map((s, i) => (
            <a key={i} href={s.url} target="_blank" rel="noreferrer" title={s.title}>
              {s.title || s.url}
            </a>
          ))}
        </div>
      )}
    </div>
  );
}
