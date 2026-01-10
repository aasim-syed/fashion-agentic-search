"use client";

import { useEffect, useMemo, useState } from "react";

export default function DebugModal({
  plan,
  raw,
  onClose,
}: {
  plan: any;
  raw: any;
  onClose: () => void;
}) {
  const [tab, setTab] = useState<"plan" | "raw">("plan");

  useEffect(() => {
    function esc(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    window.addEventListener("keydown", esc);
    return () => window.removeEventListener("keydown", esc);
  }, [onClose]);

  const planPretty = useMemo(() => JSON.stringify(plan ?? {}, null, 2), [plan]);
  const rawPretty = useMemo(() => JSON.stringify(raw ?? {}, null, 2), [raw]);

  return (
    <div className="modalOverlay" onMouseDown={onClose}>
      <div className="modalCard" onMouseDown={(e) => e.stopPropagation()}>
        <div className="modalHeader">
          <div className="modalTitle">🧠 Agent Debug</div>
          <button className="iconBtn" onClick={onClose} title="Close">
            ✕
          </button>
        </div>

        <div className="modalTabs">
          <button
            className={`tabBtn ${tab === "plan" ? "active" : ""}`}
            onClick={() => setTab("plan")}
          >
            Plan
          </button>
          <button
            className={`tabBtn ${tab === "raw" ? "active" : ""}`}
            onClick={() => setTab("raw")}
          >
            Raw Response
          </button>
        </div>

        <div className="modalBody">
          <pre className="codeBlock">{tab === "plan" ? planPretty : rawPretty}</pre>
        </div>

        <div className="modalFooter">
          <button className="btn ghost" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
