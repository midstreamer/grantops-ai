import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { runDiscoveryWorkflow } from "../services/agents";
import type { DiscoveryWorkflowResponse } from "../types/agentWorkflow";

const STEP_LABELS: Record<string, string> = {
  research_profile: "Load research profile",
  funding_discovery: "Search Grants.gov",
  fit_scoring: "Score opportunities",
  select_top_opportunities: "Select top opportunities",
  literature: "Find supporting literature",
  proposal: "Generate AI summaries",
};

function stepLabel(step: string): string {
  return STEP_LABELS[step] ?? step.replace(/_/g, " ");
}

function statusClass(status: string): string {
  if (status === "completed") return "workflow-status completed";
  if (status === "skipped") return "workflow-status skipped";
  if (status === "failed") return "workflow-status failed";
  return "workflow-status";
}

export function AgentWorkflowPage() {
  const [query, setQuery] = useState(
    "cybersecurity workforce human AI decision support",
  );
  const [rows, setRows] = useState(25);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [report, setReport] = useState<DiscoveryWorkflowResponse | null>(null);

  const canRun = useMemo(() => query.trim().length > 0 && rows >= 1, [query, rows]);

  async function onRun() {
    if (!canRun) return;
    setLoading(true);
    setError(null);
    setReport(null);
    try {
      const result = await runDiscoveryWorkflow({
        query: query.trim(),
        rows,
      });
      setReport(result);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Workflow failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="page page-wide">
      <div className="detail-header">
        <h1>Agent Workflow</h1>
        <Link className="link" to="/opportunities">
          View opportunities →
        </Link>
      </div>

      <section className="card">
        <div className="card-header">
          <h2>Discovery workflow</h2>
        </div>

        <p className="meta">
          Runs a multi-step pipeline: load your research profile, search Grants.gov,
          save and score opportunities, pick the top matches, find literature, and
          generate AI summaries when an LLM key is configured.
        </p>

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
          <button
            className="button"
            type="button"
            onClick={() => void onRun()}
            disabled={!canRun || loading}
          >
            {loading ? "Running workflow..." : "Run Discovery Workflow"}
          </button>
        </div>
      </section>

      {report && (
        <>
          <section className="card" style={{ marginTop: "1.25rem" }}>
            <div className="card-header">
              <h2>Workflow summary</h2>
              <span className={statusClass(report.status)}>{report.status}</span>
            </div>

            <dl className="summary-grid">
              <div>
                <dt>Opportunities saved</dt>
                <dd>{report.opportunities_saved}</dd>
              </div>
              <div>
                <dt>Opportunities scored</dt>
                <dd>{report.opportunities_scored}</dd>
              </div>
              <div>
                <dt>Profile</dt>
                <dd>{String(report.profile.researcher_name ?? "—")}</dd>
              </div>
            </dl>
          </section>

          <section className="card" style={{ marginTop: "1.25rem" }}>
            <div className="card-header">
              <h2>Workflow steps</h2>
            </div>
            <ol className="workflow-steps">
              {report.steps.map((step) => (
                <li key={step.step} className="workflow-step">
                  <div className="workflow-step-header">
                    <strong>{stepLabel(step.step)}</strong>
                    <span className={statusClass(step.status)}>{step.status}</span>
                  </div>
                  <p className="meta">{step.message}</p>
                </li>
              ))}
            </ol>
          </section>

          {report.top_opportunities.length > 0 && (
            <section className="card" style={{ marginTop: "1.25rem" }}>
              <div className="card-header">
                <h2>Top opportunities</h2>
              </div>
              <ul className="workflow-results">
                {report.top_opportunities.map((opp) => (
                  <li key={opp.id}>
                    <Link className="link" to={`/opportunities/${opp.id}`}>
                      {opp.title}
                    </Link>
                    <span className="meta">
                      {opp.agency ?? "—"} · fit {opp.fit_score ?? "—"} ·{" "}
                      {opp.recommendation ?? "unreviewed"}
                    </span>
                  </li>
                ))}
              </ul>
            </section>
          )}

          {(report.literature.length > 0 || report.ai_summaries.length > 0) && (
            <section className="card" style={{ marginTop: "1.25rem" }}>
              <div className="card-header">
                <h2>Deep-dive results (top 3)</h2>
              </div>

              {report.literature.length > 0 && (
                <>
                  <h3 className="workflow-subheading">Literature</h3>
                  <ul className="workflow-results">
                    {report.literature.map((item) => (
                      <li key={String(item.opportunity_id)}>
                        <strong>{String(item.title ?? "Opportunity")}</strong>
                        <span className="meta">
                          {String(item.items_saved ?? 0)} items saved ·{" "}
                          {String(item.status ?? "")}
                        </span>
                      </li>
                    ))}
                  </ul>
                </>
              )}

              {report.ai_summaries.length > 0 && (
                <>
                  <h3 className="workflow-subheading">AI summaries</h3>
                  <ul className="workflow-results">
                    {report.ai_summaries.map((item) => (
                      <li key={String(item.opportunity_id)}>
                        <Link
                          className="link"
                          to={`/opportunities/${String(item.opportunity_id)}`}
                        >
                          {String(item.title ?? "Opportunity")}
                        </Link>
                        <span className="meta">
                          {String(item.possible_proposal_title ?? "")}
                        </span>
                      </li>
                    ))}
                  </ul>
                </>
              )}
            </section>
          )}
        </>
      )}
    </main>
  );
}
