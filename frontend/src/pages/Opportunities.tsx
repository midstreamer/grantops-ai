import { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  formatDate,
  RECOMMENDATION_OPTIONS,
  recommendationClass,
  STATUS_OPTIONS,
  type SortDirection,
  type SortField,
} from "../constants/opportunity";
import {
  createOpportunity,
  downloadOpportunitiesCsv,
  exportOpportunitiesToGoogleSheets,
  listOpportunities,
  scoreAllOpportunities,
  updateOpportunity,
} from "../services/opportunities";
import type {
  GrantOpportunityCreate,
  GrantOpportunityRead,
  OpportunityRecommendation,
  OpportunityStatus,
} from "../types/opportunity";

function matchesKeyword(opp: GrantOpportunityRead, keyword: string): boolean {
  const q = keyword.trim().toLowerCase();
  if (!q) return true;
  const haystack = [
    opp.title,
    opp.agency,
    opp.program,
    opp.description,
    opp.eligibility,
    opp.next_action,
  ]
    .filter(Boolean)
    .join(" ")
    .toLowerCase();
  return haystack.includes(q);
}

export function OpportunitiesPage() {
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [scoringAll, setScoringAll] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [exportingSheets, setExportingSheets] = useState(false);
  const [exportMessage, setExportMessage] = useState<{
    type: "success" | "error";
    text: string;
  } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [items, setItems] = useState<GrantOpportunityRead[]>([]);

  const [keyword, setKeyword] = useState("");
  const [filterRecommendation, setFilterRecommendation] = useState<
    OpportunityRecommendation | "all"
  >("all");
  const [filterStatus, setFilterStatus] = useState<OpportunityStatus | "all">("all");
  const [sortField, setSortField] = useState<SortField>("deadline");
  const [sortDirection, setSortDirection] = useState<SortDirection>("asc");

  const [form, setForm] = useState<GrantOpportunityCreate>({
    source: "manual",
    title: "",
    agency: "",
    deadline: "",
    recommendation: "unreviewed",
    status: "new",
    next_action: "",
  });

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await listOpportunities();
      setItems(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unable to load opportunities");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const filteredItems = useMemo(() => {
    let list = items.filter((opp) => matchesKeyword(opp, keyword));
    if (filterRecommendation !== "all") {
      list = list.filter((opp) => opp.recommendation === filterRecommendation);
    }
    if (filterStatus !== "all") {
      list = list.filter((opp) => opp.status === filterStatus);
    }

    list = [...list].sort((a, b) => {
      if (sortField === "deadline") {
        const aDate = a.deadline ? new Date(`${a.deadline}T00:00:00`).getTime() : Infinity;
        const bDate = b.deadline ? new Date(`${b.deadline}T00:00:00`).getTime() : Infinity;
        return sortDirection === "asc" ? aDate - bDate : bDate - aDate;
      }
      const aFit = a.fit_score ?? -1;
      const bFit = b.fit_score ?? -1;
      return sortDirection === "asc" ? aFit - bFit : bFit - aFit;
    });

    return list;
  }, [items, keyword, filterRecommendation, filterStatus, sortField, sortDirection]);

  const canSubmit = useMemo(() => {
    return form.title.trim().length > 0 && form.source.trim().length > 0;
  }, [form.source, form.title]);

  async function onSubmit() {
    if (!canSubmit) return;
    setSubmitting(true);
    setError(null);
    try {
      const payload: GrantOpportunityCreate = {
        ...form,
        title: form.title.trim(),
        source: form.source.trim(),
        agency: form.agency?.trim() ? form.agency.trim() : null,
        deadline: form.deadline?.trim() ? form.deadline.trim() : null,
        next_action: form.next_action?.trim() ? form.next_action.trim() : null,
      };

      await createOpportunity(payload);
      setForm({
        source: "manual",
        title: "",
        agency: "",
        deadline: "",
        recommendation: "unreviewed",
        status: "new",
        next_action: "",
      });
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unable to create opportunity");
    } finally {
      setSubmitting(false);
    }
  }

  async function onScoreAll() {
    setScoringAll(true);
    setError(null);
    try {
      await scoreAllOpportunities();
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unable to score opportunities");
    } finally {
      setScoringAll(false);
    }
  }

  async function onExportCsv() {
    setExporting(true);
    setExportMessage(null);
    setError(null);
    try {
      await downloadOpportunitiesCsv();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unable to export CSV");
    } finally {
      setExporting(false);
    }
  }

  async function onExportGoogleSheets() {
    setExportingSheets(true);
    setExportMessage(null);
    setError(null);
    try {
      const result = await exportOpportunitiesToGoogleSheets();
      setExportMessage({
        type: "success",
        text: `Exported ${result.total_rows} row(s) to Google Sheets (${result.rows_updated} updated, ${result.rows_appended} appended).`,
      });
    } catch (e) {
      setExportMessage({
        type: "error",
        text: e instanceof Error ? e.message : "Unable to export to Google Sheets",
      });
    } finally {
      setExportingSheets(false);
    }
  }

  async function quickUpdate(
    id: number,
    patch: { status?: OpportunityStatus; next_action?: string | null },
  ) {
    setError(null);
    try {
      const updated = await updateOpportunity(id, patch);
      setItems((prev) => prev.map((o) => (o.id === id ? updated : o)));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unable to update opportunity");
    }
  }

  return (
    <main className="page page-wide">
      <h1>Opportunities</h1>

      {error && <p className="error">{error}</p>}
      {exportMessage && (
        <p className={exportMessage.type === "success" ? "success" : "error"}>
          {exportMessage.text}
        </p>
      )}

      <section className="card">
        <div className="card-header">
          <h2>Manual entry</h2>
        </div>

        <form
          onSubmit={(e) => {
            e.preventDefault();
            void onSubmit();
          }}
        >
          <div className="form-grid">
            <label className="field">
              <span>Title</span>
              <input
                value={form.title}
                onChange={(e) => setForm({ ...form, title: e.target.value })}
                placeholder="Opportunity title"
              />
            </label>

            <label className="field">
              <span>Agency</span>
              <input
                value={form.agency ?? ""}
                onChange={(e) => setForm({ ...form, agency: e.target.value })}
                placeholder="e.g., NSF"
              />
            </label>

            <label className="field">
              <span>Deadline</span>
              <input
                value={form.deadline ?? ""}
                onChange={(e) => setForm({ ...form, deadline: e.target.value })}
                placeholder="YYYY-MM-DD"
              />
            </label>

            <label className="field">
              <span>Status</span>
              <select
                value={form.status ?? "new"}
                onChange={(e) =>
                  setForm({ ...form, status: e.target.value as OpportunityStatus })
                }
              >
                {STATUS_OPTIONS.map((opt) => (
                  <option key={opt} value={opt}>
                    {opt}
                  </option>
                ))}
              </select>
            </label>
          </div>

          <div className="form-actions">
            <button className="button" type="submit" disabled={!canSubmit || submitting}>
              {submitting ? "Adding..." : "Add opportunity"}
            </button>
          </div>
        </form>
      </section>

      <section className="card" style={{ marginTop: "1.25rem" }}>
        <div className="card-header">
          <h2>Opportunity list</h2>
          <div className="header-actions">
            <button
              className="button button-secondary"
              type="button"
              onClick={() => void onExportCsv()}
              disabled={exporting || exportingSheets || loading}
            >
              {exporting ? "Exporting..." : "Export CSV"}
            </button>
            <button
              className="button button-secondary"
              type="button"
              onClick={() => void onExportGoogleSheets()}
              disabled={exporting || exportingSheets || loading}
            >
              {exportingSheets ? "Exporting..." : "Export to Google Sheets"}
            </button>
            <button
              className="button"
              type="button"
              onClick={() => void onScoreAll()}
              disabled={scoringAll || loading || items.length === 0}
            >
              {scoringAll ? "Scoring..." : "Score All"}
            </button>
          </div>
        </div>

        <div className="filters-bar">
          <label className="field">
            <span>Search</span>
            <input
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
              placeholder="Title, agency, description..."
            />
          </label>

          <label className="field">
            <span>Recommendation</span>
            <select
              value={filterRecommendation}
              onChange={(e) =>
                setFilterRecommendation(e.target.value as OpportunityRecommendation | "all")
              }
            >
              <option value="all">All</option>
              {RECOMMENDATION_OPTIONS.map((opt) => (
                <option key={opt} value={opt}>
                  {opt}
                </option>
              ))}
            </select>
          </label>

          <label className="field">
            <span>Status</span>
            <select
              value={filterStatus}
              onChange={(e) =>
                setFilterStatus(e.target.value as OpportunityStatus | "all")
              }
            >
              <option value="all">All</option>
              {STATUS_OPTIONS.map((opt) => (
                <option key={opt} value={opt}>
                  {opt}
                </option>
              ))}
            </select>
          </label>

          <label className="field">
            <span>Sort by</span>
            <select
              value={`${sortField}-${sortDirection}`}
              onChange={(e) => {
                const [field, dir] = e.target.value.split("-") as [SortField, SortDirection];
                setSortField(field);
                setSortDirection(dir);
              }}
            >
              <option value="deadline-asc">Deadline (soonest)</option>
              <option value="deadline-desc">Deadline (latest)</option>
              <option value="fit_score-desc">Fit score (high)</option>
              <option value="fit_score-asc">Fit score (low)</option>
            </select>
          </label>
        </div>

        <p className="meta" style={{ marginBottom: "0.75rem" }}>
          Showing {filteredItems.length} of {items.length}
        </p>

        {loading ? (
          <p>Loading...</p>
        ) : filteredItems.length === 0 ? (
          <p className="meta">No opportunities match your filters.</p>
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
                {filteredItems.map((opp) => (
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
                    <td>
                      <select
                        className="table-select"
                        value={opp.status}
                        onChange={(e) =>
                          void quickUpdate(opp.id, {
                            status: e.target.value as OpportunityStatus,
                          })
                        }
                      >
                        {STATUS_OPTIONS.map((opt) => (
                          <option key={opt} value={opt}>
                            {opt}
                          </option>
                        ))}
                      </select>
                    </td>
                    <td>
                      <input
                        className="table-input"
                        defaultValue={opp.next_action ?? ""}
                        placeholder="Next action"
                        onBlur={(e) => {
                          const value = e.target.value.trim();
                          if (value !== (opp.next_action ?? "")) {
                            void quickUpdate(opp.id, {
                              next_action: value || null,
                            });
                          }
                        }}
                      />
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
