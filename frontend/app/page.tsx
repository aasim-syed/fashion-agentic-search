import Chat from "./components/Chat";

export default function Page() {
  return (
    <main className="pageWrap">
      <header className="topBar">
        <div className="brand">
          <div className="logo" />
          <div>
            <div className="brandTitle">Fashion Agentic Search</div>
            <div className="brandSub">
              Multimodal semantic search • Qdrant + CLIP • Planner-driven
            </div>
          </div>
        </div>

        <div style={{ display: "flex", gap: 10 }}>
          <a className="btn ghost" href="http://localhost:6333/dashboard" target="_blank">
            Qdrant
          </a>
          <a className="btn ghost" href="http://localhost:8000/docs" target="_blank">
            API Docs
          </a>
        </div>
      </header>

      <Chat />
    </main>
  );
}
