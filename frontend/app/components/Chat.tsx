"use client";

import { useMemo, useState, useEffect } from "react";
import DebugModal from "./DebugPanel";

import ProductCard from "./ProductCard";

type Plan = {
  intermediate_queries: Array<{ query: string; weight: number }>;
  weights: { text: number; image: number };
  top_k: number;
  filters?: Record<string, any>;
};

type ResultItem = {
  product_id: string;
  score: number;
  description?: string | null;
  image_path?: string | null;
};

type ChatResponse = {
  plan: Plan;
  query_used: string;
  results: ResultItem[];
};

const BACKEND_URL =
  process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

export default function Chat() {
  const [message, setMessage] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [hasSearched, setHasSearched] = useState(false);

  const [showDebug, setShowDebug] = useState(false);

  const [data, setData] = useState<ChatResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  // animations/state
  const [searched, setSearched] = useState(false);
  const [isZooping, setIsZooping] = useState(false);

  // debug modal
  const [debugOpen, setDebugOpen] = useState(false);

  const canSend = message.trim().length > 0 || !!file;

  async function handleSend() {
    setErr(null);
    if (!canSend || loading) return;

    if (!searched) {
      setIsZooping(true);
      setSearched(true);
      setTimeout(() => setIsZooping(false), 450);
    }

    setLoading(true);
    setHasSearched(true);

    try {
      const fd = new FormData();
      if (message.trim()) fd.append("message", message.trim());
      if (file) fd.append("image", file);

      const res = await fetch(`${BACKEND_URL}/api/chat`, {
        method: "POST",
        body: fd,
      });

      if (!res.ok) {
        const t = await res.text().catch(() => "");
        throw new Error(`Backend ${res.status}: ${t || "Request failed"}`);
      }

      const json = (await res.json()) as ChatResponse;
      setData(json);
    } catch (e: any) {
      setErr(e?.message || "Something failed");
    } finally {
      setLoading(false);
    }
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Enter") handleSend();
  }

  // ESC closes modal
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") setDebugOpen(false);
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  const results = data?.results || [];
  const plan = data?.plan || null;

  const topSummary = useMemo(() => {
    if (!data) return null;
    return {
      query: data.query_used,
      count: data.results?.length || 0,
      topScore: data.results?.[0]?.score ?? null,
    };
  }, [data]);

  return (
    <section className={hasSearched ? "modeActive" : "modeIdle"}>
      <div className="hero card searchCard">
        <div className="heroInner">
          <div className="searchRow">
            <input
              className="input"
              placeholder='Try: "black dress", "red floral skirt", "denim jacket"...'
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={loading}
            />
  
            <label className="fileBtn" title="Upload image">
              <input
                type="file"
                accept="image/*"
                onChange={(e) => setFile(e.target.files?.[0] || null)}
                disabled={loading}
              />
              {file ? "Image ✓" : "Image"}
            </label>
  
            <button className="btn primary" onClick={handleSend} disabled={!canSend || loading}>
              {loading ? (
                <span className="btnSpin">
                  <span className="spinner" />
                  Searching…
                </span>
              ) : (
                "Search"
              )}
            </button>
          </div>
  
          <div className="hintRow">
            <span className="hint">
              Tip: add attributes like <b>color</b>, <b>material</b>, <b>occasion</b>.
            </span>
            {file ? <span className="hint">Attached: {file.name}</span> : null}
          </div>
  
          <div className="summaryRow" style={{ marginTop: 2 }}>
            {["black dress", "red floral skirt", "denim jacket", "wedding gown"].map((q) => (
              <button
                key={q}
                className="pill"
                style={{ cursor: "pointer" }}
                onClick={() => setMessage(q)}
                disabled={loading}
                type="button"
              >
                {q}
              </button>
            ))}
          </div>
  
          {err ? <div className="errorBanner">❌ {err}</div> : null}
  
          {hasSearched && data ? (
            <div className="afterSearchActions">
              <button className="btn ghost" onClick={() => setShowDebug(true)} type="button">
                Agent Debug
              </button>
              <button
                className="btn ghost"
                onClick={() => {
                  setData(null);
                  setErr(null);
                  setHasSearched(false);
                }}
                type="button"
              >
                Reset
              </button>
            </div>
          ) : null}
  
          {hasSearched && data ? (
            <div className="summaryRow" style={{ marginTop: 0 }}>
              <span className="pill">Query used: {data.query_used}</span>
              <span className="pill">{data.results?.length || 0} hits</span>
              {data.results?.[0]?.score != null ? (
                <span className="pill">Top: {data.results[0].score.toFixed(2)}</span>
              ) : null}
            </div>
          ) : null}
        </div>
      </div>
  
      <div className="resultsArea">
        {loading ? (
          <div className="gridCards" style={{ marginTop: 14 }}>
            {Array.from({ length: 8 }).map((_, i) => (
              <div key={i} className="skeletonCard" />
            ))}
          </div>
        ) : results.length ? (
          <div className="gridCards" style={{ marginTop: 14 }}>
            {results.map((r) => (
              <ProductCard key={r.product_id} item={r} backendUrl={BACKEND_URL} />
            ))}
          </div>
        ) : (
          hasSearched && (
            <div className="emptyState">
              <div className="emptyTitle">No results</div>
              <div className="muted">
                Try <b>"black dress"</b> or <b>"blue denim jacket"</b>.
              </div>
            </div>
          )
        )}
      </div>
  
      {showDebug ? (
  <DebugModal
    plan={plan}
    raw={data}
    onClose={() => setShowDebug(false)}
  />
) : null}

    </section>
  );
  
}
