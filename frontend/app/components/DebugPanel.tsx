"use client";

type Plan = {
  intermediate_queries: Array<{ query: string; weight: number }>;
  weights: { text: number; image: number };
  top_k: number;
  filters?: Record<string, any>;
};

export default function DebugPanel({
  plan,
  raw,
}: {
  plan: Plan | null;
  raw: any;
}) {
  const hasPlan = !!plan;

  return (
    <aside className="card debugCard">
      <div className="debugHeader">
        <div>
          <div className="debugTitle">Agent Debug</div>
          <div className="muted">What the planner decided + what search used</div>
        </div>
      </div>

      {!hasPlan ? (
        <div className="muted" style={{ marginTop: 10 }}>
          Search once — this panel will show plan JSON, weights, filters, and intermediate queries.
        </div>
      ) : (
        <>
          <div className="section">
            <div className="sectionTitle">Intermediate Queries</div>
            <div className="chips">
              {plan!.intermediate_queries?.map((q, idx) => (
                <span key={idx} className="chip">
                  {q.query} <span className="chipDim">· {q.weight}</span>
                </span>
              ))}
            </div>
          </div>

          <div className="section">
            <div className="sectionTitle">Weights</div>
            <div className="kv">
              <div className="kvRow">
                <span className="kvKey">text</span>
                <span className="kvVal">{plan!.weights?.text ?? 0}</span>
              </div>
              <div className="kvRow">
                <span className="kvKey">image</span>
                <span className="kvVal">{plan!.weights?.image ?? 0}</span>
              </div>
              <div className="kvRow">
                <span className="kvKey">top_k</span>
                <span className="kvVal">{plan!.top_k ?? "-"}</span>
              </div>
            </div>
          </div>

          <div className="section">
            <div className="sectionTitle">Filters</div>
            <pre className="code">
{JSON.stringify(plan!.filters ?? {}, null, 2)}
            </pre>
          </div>

          <details className="details">
            <summary>Raw response</summary>
            <pre className="code">
{JSON.stringify(raw, null, 2)}
            </pre>
          </details>
        </>
      )}
    </aside>
  );
}
