"use client";

import { useMemo, useState } from "react";
import DebugPanel from "./DebugPanel";
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

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

export default function Chat() {
  const [message, setMessage] = useState("");
  const [file, setFile] = useState<File | null>(null);

  const [data, setData] = useState<ChatResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const canSend = message.trim().length > 0 || !!file;

  async function handleSend() {
    setErr(null);

    if (!canSend) return;

    setLoading(true);
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
    <section className="grid2">
      {/* LEFT */}
      <div className="leftCol">
        <div className="card searchCard">
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

            <button className="btn" onClick={handleSend} disabled={!canSend || loading}>
              {loading ? "Searching..." : "Search"}
            </button>
          </div>

          <div className="hintRow">
            <span className="hint">
              Tip: add attributes like <b>color</b>, <b>material</b>, <b>occasion</b>.
            </span>
            {file ? <span className="hint">Attached: {file.name}</span> : null}
          </div>

          {err ? <div className="errorBanner">❌ {err}</div> : null}
        </div>

        {/* RESULTS HEADER */}
        <div className="resultsHeader">
          <div>
            <div className="resultsTitle">Results</div>
            <div className="resultsMeta">
              {topSummary ? (
                <>
                  <span className="pill soft">Query used: {topSummary.query}</span>
                  <span className="pill soft">{topSummary.count} hits</span>
                  {topSummary.topScore !== null ? (
                    <span className="pill soft">Top score: {topSummary.topScore.toFixed(2)}</span>
                  ) : null}
                </>
              ) : (
                <span className="muted">Search to see results.</span>
              )}
            </div>
          </div>

          <div className="rightActions">
            {data ? (
              <button
                className="btn ghost"
                onClick={() => {
                  setData(null);
                  setErr(null);
                }}
              >
                Clear
              </button>
            ) : null}
          </div>
        </div>

        {/* RESULTS GRID */}
        {loading ? (
          <div className="gridCards">
            {Array.from({ length: 9 }).map((_, i) => (
              <div key={i} className="skeletonCard" />
            ))}
          </div>
        ) : results.length ? (
          <div className="gridCards">
            {results.map((r) => (
              <ProductCard key={r.product_id} item={r} backendUrl={BACKEND_URL} />
            ))}
          </div>
        ) : (
          <div className="emptyState">
            <div className="emptyTitle">No results yet</div>
            <div className="muted">
              Try a different query like <b>"black dress"</b> or <b>"blue denim jacket"</b>.
            </div>
          </div>
        )}
      </div>

      {/* RIGHT */}
      <div className="rightCol">
        <DebugPanel plan={plan} raw={data} />
      </div>
    </section>
  );
}
