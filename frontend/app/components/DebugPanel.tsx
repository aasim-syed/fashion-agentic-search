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
  return (
    <div className="card debugCard">
      <div className="debugTitle">🧠 Agent Debug</div>

      {plan ? (
        <>
          <div className="kv">
            <div className="k">Top-K</div>
            <div className="v">{plan.top_k}</div>
          </div>
          <div className="kv">
            <div className="k">Weights</div>
            <div className="v">
              text {plan.weights?.text ?? 0} • image {plan.weights?.image ?? 0}
            </div>
          </div>

          <div className="kv">
            <div className="k">Filters</div>
            <div className="v">
              {plan.filters && Object.keys(plan.filters).length
                ? "Applied"
                : "None"}
            </div>
          </div>

          <div className="kv" style={{ borderBottom: "none", paddingBottom: 0 }}>
            <div className="k">Intermediate Queries</div>
            <div className="v">{plan.intermediate_queries?.length ?? 0}</div>
          </div>

          <pre>{JSON.stringify(plan, null, 2)}</pre>
        </>
      ) : (
        <div className="muted">Run a search to see the planner + retrieval plan.</div>
      )}

      {raw ? (
        <>
          <div style={{ height: 10 }} />
          <div className="debugTitle" style={{ fontSize: 13, marginBottom: 6 }}>
            Raw Response
          </div>
          <pre>{JSON.stringify(raw, null, 2)}</pre>
        </>
      ) : null}
    </div>
  );
}
