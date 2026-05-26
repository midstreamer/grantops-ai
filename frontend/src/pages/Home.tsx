import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { StatusBadge } from "../components/StatusBadge";
import { formatDate, recommendationClass } from "../constants/opportunity";
import { fetchHealth, getApiBaseUrl } from "../services/api";
import { fetchDashboardStats } from "../services/dashboard";
import type { DashboardStats } from "../types/dashboard";
import type { HealthResponse } from "../types/health";

type ConnectionState = "loading" | "connected" | "error";

export function Home() {
  const [connectionState, setConnectionState] = useState<ConnectionState>("loading");
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const [statsLoading, setStatsLoading] = useState(true);
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [statsError, setStatsError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setConnectionState("loading");
      setErrorMessage(null);
      try {
        const data = await fetchHealth();
        if (!cancelled) {
          setHealth(data);
          setConnectionState("connected");
        }
      } catch (error) {
        if (!cancelled) {
          setHealth(null);
          setConnectionState("error");
          setErrorMessage(
            error instanceof Error ? error.message : "Unable to reach backend",
          );
        }
      }
    }
    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    let cancelled = false;
    async function loadStats() {
      setStatsLoading(true);
      setStatsError(null);
      try {
        const data = await fetchDashboardStats();
        if (!cancelled) setStats(data);
      } catch (e) {
        if (!cancelled) {
          setStatsError(e instanceof Error ? e.message : "Unable to load dashboard");
        }
      } finally {
        if (!cancelled) setStatsLoading(false);
      }
    }
    void loadStats();
    return () => {
      cancelled = true;
    };
  }, []);

  const isConnected = connectionState === "connected";

  return (
    <main className="page page-wide">
      <header className="hero">
        <p className="eyebrow">Grant operations platform</p>
        <h1>Dashboard</h1>
        <p className="subtitle">Pipeline overview and highest-fit opportunities.</p>
      </header>

      {statsError && <p className="error">{statsError}</p>}

      {statsLoading ? (
        <p>Loading dashboard...</p>
      ) : stats ? (
        <>
          <div className="stat-grid">
            <div className="stat-card">
              <span className="stat-label">Total opportunities</span>
              <span className="stat-value">{stats.total_opportunities}</span>
            </div>
            <div className="stat-card pursue">
              <span className="stat-label">Pursue</span>
              <span className="stat-value">{stats.pursue_count}</span>
            </div>
            <div className="stat-card monitor">
              <span className="stat-label">Monitor</span>
              <span className="stat-value">{stats.monitor_count}</span>
            </div>
            <div className="stat-card decline">
              <span className="stat-label">Decline</span>
              <span className="stat-value">{stats.decline_count}</span>
            </div>
            <div className="stat-card">
              <span className="stat-label">Due in 30 days</span>
              <span className="stat-value">{stats.due_in_30_days}</span>
            </div>
            <div className="stat-card">
              <span className="stat-label">Due in 90 days</span>
              <span className="stat-value">{stats.due_in_90_days}</span>
            </div>
            <div className="stat-card">
              <span className="stat-label">Average fit score</span>
              <span className="stat-value">
                {stats.average_fit_score != null ? stats.average_fit_score : "—"}
              </span>
            </div>
          </div>

          <section className="card" style={{ marginTop: "1.25rem" }}>
            <div className="card-header">
              <h2>Top opportunities by fit score</h2>
              <Link className="link" to="/opportunities">
                View all →
              </Link>
            </div>

            {stats.top_opportunities.length === 0 ? (
              <p className="meta">No scored opportunities yet. Run Score All on Opportunities.</p>
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
                    </tr>
                  </thead>
                  <tbody>
                    {stats.top_opportunities.map((opp) => (
                      <tr key={opp.id}>
                        <td>
                          <Link className="link" to={`/opportunities/${opp.id}`}>
                            {opp.title}
                          </Link>
                        </td>
                        <td>{opp.agency ?? "—"}</td>
                        <td>{formatDate(opp.deadline)}</td>
                        <td>{opp.fit_score ?? "—"}</td>
                        <td>
                          <span className={recommendationClass(opp.recommendation)}>
                            {opp.recommendation}
                          </span>
                        </td>
                        <td>{opp.status}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        </>
      ) : null}

      <section className="card" style={{ marginTop: "1.25rem" }}>
        <div className="card-header">
          <h2>Backend connectivity</h2>
          <StatusBadge
            connected={isConnected}
            label={
              connectionState === "loading"
                ? "Checking…"
                : isConnected
                  ? "Reachable"
                  : "Unreachable"
            }
          />
        </div>

        <dl className="details">
          <div>
            <dt>API base URL</dt>
            <dd>{getApiBaseUrl()}</dd>
          </div>
          {health && (
            <div>
              <dt>Service version</dt>
              <dd>{health.version}</dd>
            </div>
          )}
          {errorMessage && (
            <div className="error-row">
              <dt>Error</dt>
              <dd>{errorMessage}</dd>
            </div>
          )}
        </dl>
      </section>
    </main>
  );
}
