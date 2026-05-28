import { useEffect, useState } from "react";
import { listWeeklyReports } from "../services/weeklyReports";
import type { WeeklyReportRead } from "../types/weeklyReport";

function formatDateTime(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString();
}

export function WeeklyReportsPage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [items, setItems] = useState<WeeklyReportRead[]>([]);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const reports = await listWeeklyReports();
        if (!cancelled) setItems(reports);
      } catch (e) {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : "Unable to load weekly reports");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <main className="page page-wide">
      <h1>Weekly Reports</h1>
      {error && <p className="error">{error}</p>}
      <section className="card">
        <div className="card-header">
          <h2>Discovery reports</h2>
          <span className="meta">{items.length} total</span>
        </div>

        {loading ? (
          <p>Loading...</p>
        ) : items.length === 0 ? (
          <p className="meta">No weekly reports yet. Run a scheduled search to create one.</p>
        ) : (
          <ul className="workflow-results">
            {items.map((item) => (
              <li key={item.id} className="card">
                <strong>{item.title}</strong>
                <span className="meta">{formatDateTime(item.created_at)}</span>
                <pre className="report-content">{item.content}</pre>
              </li>
            ))}
          </ul>
        )}
      </section>
    </main>
  );
}
