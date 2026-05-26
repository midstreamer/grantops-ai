import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { searchGrantsGov } from "../services/grantsGovSearch";
import type { GrantOpportunityRead } from "../types/opportunity";

function formatDate(value: string | null) {
  if (!value) return "—";
  const date = new Date(`${value}T00:00:00`);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleDateString();
}

export function GrantSearchPage() {
  const [query, setQuery] = useState("cybersecurity education");
  const [rows, setRows] = useState(25);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<GrantOpportunityRead[]>([]);

  const canSearch = useMemo(() => query.trim().length > 0 && rows >= 1, [query, rows]);

  async function onSearch() {
    if (!canSearch) return;
    setLoading(true);
    setError(null);
    try {
      const saved = await searchGrantsGov(query.trim(), rows);
      setResults(saved);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Search failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="page">
      <div style={{ display: "flex", justifyContent: "space-between", gap: "1rem" }}>
        <h1>Grant Search</h1>
        <Link className="link" to="/opportunities">
          View Opportunities →
        </Link>
      </div>

      <section className="card">
        <div className="card-header">
          <h2>Search Grants.gov</h2>
        </div>

        {error && <p className="error">{error}</p>}

        <div className="form-grid">
          <label className="field full">
            <span>Query</span>
            <input value={query} onChange={(e) => setQuery(e.target.value)} />
          </label>

          <label className="field">
            <span>Rows</span>
            <select value={rows} onChange={(e) => setRows(Number(e.target.value))}>
              {[10, 25, 50, 100].map((n) => (
                <option key={n} value={n}>
                  {n}
                </option>
              ))}
            </select>
          </label>
        </div>

        <div className="form-actions">
          <button className="button" type="button" onClick={() => void onSearch()} disabled={!canSearch || loading}>
            {loading ? "Searching..." : "Search Grants.gov"}
          </button>
        </div>

        <p className="meta" style={{ marginTop: "0.75rem" }}>
          Results are automatically saved to the Opportunities database (de-duped by source + source_id).
        </p>
      </section>

      <section className="card" style={{ marginTop: "1.25rem" }}>
        <div className="card-header">
          <h2>Results</h2>
          <span className="meta">{results.length} saved</span>
        </div>

        {results.length === 0 ? (
          <p className="meta">No results yet. Run a search above.</p>
        ) : (
          <div className="table-wrap">
            <table className="table">
              <thead>
                <tr>
                  <th>Title</th>
                  <th>Agency</th>
                  <th>Deadline</th>
                  <th>Fit</th>
                  <th>Recommendation</th>
                  <th>Status</th>
                  <th>Next action</th>
                </tr>
              </thead>
              <tbody>
                {results.map((opp) => (
                  <tr key={opp.id}>
                    <td>
                      <Link className="link" to={`/opportunities/${opp.id}`}>
                        {opp.title}
                      </Link>
                    </td>
                    <td>{opp.agency ?? "—"}</td>
                    <td>{formatDate(opp.deadline)}</td>
                    <td>{opp.fit_score ?? "—"}</td>
                    <td>{opp.recommendation}</td>
                    <td>{opp.status}</td>
                    <td className="truncate">{opp.next_action ?? "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </main>
  );
}

