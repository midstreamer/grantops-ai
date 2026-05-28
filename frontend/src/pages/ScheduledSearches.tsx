import { useCallback, useEffect, useMemo, useState } from "react";
import {
  createScheduledSearch,
  deleteScheduledSearch,
  listScheduledSearches,
  runScheduledSearchNow,
  updateScheduledSearch,
} from "../services/scheduledSearches";
import type { ScheduledSearchCreate, ScheduledSearchRead } from "../types/scheduledSearch";

const SUGGESTED_QUERIES = [
  "human centered AI cybersecurity",
  "cybersecurity workforce development",
  "immersive learning cybersecurity",
  "critical infrastructure cybersecurity",
  "AI decision support cyber operations",
  "trustworthy AI human factors",
];

function formatDateTime(value: string | null): string {
  if (!value) return "Never";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString();
}

export function ScheduledSearchesPage() {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [items, setItems] = useState<ScheduledSearchRead[]>([]);
  const [form, setForm] = useState<ScheduledSearchCreate>({
    name: "Weekly Cybersecurity Discovery",
    query: SUGGESTED_QUERIES[0],
    rows: 25,
    frequency: "weekly",
    active: true,
  });

  const canSubmit = useMemo(
    () => form.name.trim().length > 0 && form.query.trim().length > 0,
    [form.name, form.query],
  );

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await listScheduledSearches();
      setItems(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unable to load scheduled searches");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function onCreate() {
    if (!canSubmit) return;
    setSaving(true);
    setError(null);
    setSuccess(null);
    try {
      const created = await createScheduledSearch({
        ...form,
        name: form.name.trim(),
        query: form.query.trim(),
      });
      setItems((prev) => [created, ...prev]);
      setSuccess("Scheduled search created.");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unable to create scheduled search");
    } finally {
      setSaving(false);
    }
  }

  async function onToggleActive(item: ScheduledSearchRead) {
    setError(null);
    setSuccess(null);
    try {
      const updated = await updateScheduledSearch(item.id, { active: !item.active });
      setItems((prev) => prev.map((s) => (s.id === item.id ? updated : s)));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unable to update scheduled search");
    }
  }

  async function onRunNow(id: number) {
    setError(null);
    setSuccess(null);
    try {
      const result = await runScheduledSearchNow(id);
      setSuccess(`Run completed. Weekly report generated: ${result.title}`);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unable to run scheduled search");
    }
  }

  async function onDelete(id: number) {
    const ok = window.confirm("Delete this scheduled search?");
    if (!ok) return;
    setError(null);
    setSuccess(null);
    try {
      await deleteScheduledSearch(id);
      setItems((prev) => prev.filter((s) => s.id !== id));
      setSuccess("Scheduled search deleted.");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unable to delete scheduled search");
    }
  }

  return (
    <main className="page page-wide">
      <h1>Scheduled Searches</h1>
      <section className="card">
        <div className="card-header">
          <h2>Create weekly search</h2>
        </div>

        {error && <p className="error">{error}</p>}
        {success && <p className="success">{success}</p>}

        <div className="form-grid">
          <label className="field">
            <span>Name</span>
            <input
              value={form.name}
              onChange={(e) => setForm((prev) => ({ ...prev, name: e.target.value }))}
            />
          </label>

          <label className="field">
            <span>Rows</span>
            <select
              value={form.rows}
              onChange={(e) => setForm((prev) => ({ ...prev, rows: Number(e.target.value) }))}
            >
              {[10, 25, 50, 100].map((n) => (
                <option key={n} value={n}>
                  {n}
                </option>
              ))}
            </select>
          </label>

          <label className="field full">
            <span>Query</span>
            <input
              value={form.query}
              onChange={(e) => setForm((prev) => ({ ...prev, query: e.target.value }))}
            />
          </label>
        </div>

        <p className="meta">
          Suggestions:{" "}
          {SUGGESTED_QUERIES.map((q) => (
            <button
              key={q}
              type="button"
              className="query-chip"
              onClick={() => setForm((prev) => ({ ...prev, query: q }))}
            >
              {q}
            </button>
          ))}
        </p>

        <div className="form-actions">
          <button className="button" type="button" disabled={!canSubmit || saving} onClick={() => void onCreate()}>
            {saving ? "Creating..." : "Create Weekly Search"}
          </button>
        </div>
      </section>

      <section className="card" style={{ marginTop: "1.25rem" }}>
        <div className="card-header">
          <h2>Scheduled searches</h2>
          <span className="meta">{items.length} total</span>
        </div>

        {loading ? (
          <p>Loading...</p>
        ) : items.length === 0 ? (
          <p className="meta">No scheduled searches yet.</p>
        ) : (
          <div className="table-wrap">
            <table className="table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Query</th>
                  <th>Rows</th>
                  <th>Active</th>
                  <th>Last run</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {items.map((item) => (
                  <tr key={item.id}>
                    <td>{item.name}</td>
                    <td className="truncate">{item.query}</td>
                    <td>{item.rows}</td>
                    <td>{item.active ? "Yes" : "No"}</td>
                    <td>{formatDateTime(item.last_run_at)}</td>
                    <td>
                      <div className="row-actions">
                        <button
                          type="button"
                          className="button button-secondary"
                          onClick={() => void onToggleActive(item)}
                        >
                          {item.active ? "Pause" : "Activate"}
                        </button>
                        <button
                          type="button"
                          className="button button-secondary"
                          onClick={() => void onRunNow(item.id)}
                        >
                          Run now
                        </button>
                        <button
                          type="button"
                          className="button button-secondary"
                          onClick={() => void onDelete(item.id)}
                        >
                          Delete
                        </button>
                      </div>
                    </td>
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
