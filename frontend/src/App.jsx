import { useState, useEffect } from "react";
import "./App.css";

const API = "http://localhost:8000";

function Card({ node, showRank }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div
      className={`card ${expanded ? "active" : ""} ${node.depth > 0 ? `depth-${node.depth}` : ""}`}
      onClick={() => setExpanded(!expanded)}
    >
      <div className="card-top">
        <h3>
          {node.depth > 0 && <span className="depth-indicator" />}
          {node.title}
        </h3>
        <div style={{ display: "flex", gap: 6 }}>
          {showRank && <span className="card-rank">Rank {node.rank.toFixed(3)}</span>}
          <span className="card-badge">
            Pages {node.start_page}–{node.end_page}
          </span>
        </div>
      </div>

      <p className="card-summary">
        {expanded ? node.summary : node.summary.slice(0, 150) + (node.summary.length > 150 ? "..." : "")}
      </p>

      {expanded && (
        <div className="card-detail">
          <a
            className="pdf-link"
            href={`${API}/static/${node.doc_name}#page=${node.start_page}`}
            target="_blank"
            rel="noopener noreferrer"
            onClick={(e) => e.stopPropagation()}
          >
            View in PDF (Page {node.start_page})
          </a>
        </div>
      )}

      <p className="card-hint">{expanded ? "Click to collapse" : "Click to expand"}</p>
    </div>
  );
}

function App() {
  const [nodes, setNodes] = useState([]);
  const [query, setQuery] = useState("");
  const [searchResults, setSearchResults] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetch(`${API}/api/nodes`)
      .then((r) => r.json())
      .then((data) => setNodes(data.nodes))
      .catch(console.error);
  }, []);

  async function handleSearch(e) {
    e.preventDefault();
    if (!query.trim()) {
      setSearchResults(null);
      return;
    }
    setLoading(true);
    try {
      const res = await fetch(`${API}/api/search?q=${encodeURIComponent(query)}&limit=10`);
      const data = await res.json();
      setSearchResults(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  function handleClear() {
    setQuery("");
    setSearchResults(null);
  }

  const displayNodes = searchResults ? searchResults.results : nodes;
  const isSearching = searchResults !== null;

  return (
    <div className="app">
      <header>
        <h1>PageIndex Search</h1>
        <p>2023 Annual Report — {nodes.length} sections indexed</p>
      </header>

      <form className="search-bar" onSubmit={handleSearch}>
        <input
          type="text"
          placeholder="Search sections... (e.g. monetary policy, cybersecurity)"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        {isSearching ? (
          <button type="button" onClick={handleClear}>Clear</button>
        ) : (
          <button type="submit" disabled={loading}>
            {loading ? "..." : "Search"}
          </button>
        )}
      </form>

      {isSearching && (
        <p className="search-info">
          {searchResults.total} results for "<strong>{searchResults.query}</strong>"
        </p>
      )}

      {displayNodes.map((node) => (
        <Card key={node.node_id} node={node} showRank={isSearching} />
      ))}

      {isSearching && displayNodes.length === 0 && (
        <p className="no-results">No results found. Try different keywords.</p>
      )}
    </div>
  );
}

export default App;
